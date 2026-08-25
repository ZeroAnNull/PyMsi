/* ═══════════════════════════════════════════════════════════════
 *  PyMsi._excl_cipher — 独家加密 C 扩展 (GMP 大整数实现)
 *  ───────────────────────────────────────────────────────────────
 *
 *  算法 (encrypt):
 *    1) 每个字符 → Unicode 码点 → 7 位十进制 (前补零)
 *    2) digits = "1" + 所有码点 7 位拼接   (前导 "1" 防前导零丢失)
 *    3) 随机分三份 p1/p2/p3
 *    4) perm = random(0..5), 6 种排列随机打乱
 *    5) shuffled = p[perm[0]] + p[perm[1]] + p[perm[2]]
 *    6) final = "1" + shuffled               (再加前导 1, 防 GMP 丢前导零)
 *    7) N = GMP_bignum(final)
 *    8) result = N × 10!                     (10! = 3628800)
 *    9) 密文 = result 的十进制字符串
 *   10) FILEKEY 存: p1_len, p2_len, p3_len, perm, char_count
 *
 *  解密 (decrypt): 上述逆运算, 用 GMP 精确整除 (校验余数为 0)
 *
 *  编译: 需要 libgmp (gcc ... -lgmp)
 *  运行: 需要 libgmp10 (大多数 Linux 自带)
 *
 *  完整源代码公开发布 (见 GitHub Release Assets)
 * ═══════════════════════════════════════════════════════════════ */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <gmp.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

/* ─── 常量 ──────────────────────────────────────────────── */
#define EXCKEY_MAGIC   "EXCKEY01"          /* FILEKEY 魔数 */
#define EXCKEY_VERSION 1
#define CODEPOINT_WIDTH 7                   /* 每码点 7 位十进制 (Unicode max 0x10FFFF=1114111) */
#define LEADING_MARK    '1'                 /* 前导标记, 防 GMP 丢前导零 */
#define FACTORIAL_10    3628800UL           /* 10! = 1×2×3×4×5×6×7×8×9×10 */

/* 6 种排列: PERMS[i] = (a, b, c) 表示 shuffled = p[a] + p[b] + p[c] */
static const int PERMS[6][3] = {
    {0, 1, 2},  /* p1 p2 p3 */
    {0, 2, 1},  /* p1 p3 p2 */
    {1, 0, 2},  /* p2 p1 p3 */
    {1, 2, 0},  /* p2 p3 p1 */
    {2, 0, 1},  /* p3 p1 p2 */
    {2, 1, 0},  /* p3 p2 p1 */
};

/* FILEKEY 二进制布局:
 *   offset 0   : magic[8]      = "EXCKEY01"
 *   offset 8   : version (1B)
 *   offset 9   : p1_len  (uint32 LE)
 *   offset 13  : p2_len  (uint32 LE)
 *   offset 17  : p3_len  (uint32 LE)
 *   offset 21  : perm     (1B)
 *   offset 22  : char_count (uint32 LE)
 *   offset 26  : checksum (uint32 LE, 简单加和校验)
 *   total: 30 字节
 */
#define FILEKEY_SIZE 30

/* ─── 工具: 写/读 uint32 小端 ───────────────────────────── */
static void put_u32le(unsigned char* p, unsigned int v) {
    p[0] = v & 0xFF;
    p[1] = (v >> 8) & 0xFF;
    p[2] = (v >> 16) & 0xFF;
    p[3] = (v >> 24) & 0xFF;
}
static unsigned int get_u32le(const unsigned char* p) {
    return (unsigned int)p[0]
         | ((unsigned int)p[1] << 8)
         | ((unsigned int)p[2] << 16)
         | ((unsigned int)p[3] << 24);
}

/* ─── 工具: 简单随机数 (seed 一次) ──────────────────────── */
static int rng_seeded = 0;
static void seed_rng(void) {
    if (!rng_seeded) {
        /* 用 time + 一个熵源混合 */
        unsigned int seed = (unsigned int)time(NULL);
        seed ^= (unsigned int)((uintptr_t)&seed_rng);  /* ASLR 地址熵 */
        srandom(seed);
        rng_seeded = 1;
    }
}

/* ═══════════════════════════════════════════════════════════════
 *  encrypt(text) -> (ciphertext_str, filekey_bytes)
 * ═══════════════════════════════════════════════════════════════ */
static PyObject* excl_encrypt(PyObject* self, PyObject* args) {
    PyObject* uni_obj = NULL;
    if (!PyArg_ParseTuple(args, "U", &uni_obj)) {
        return NULL;  /* 要求 str */
    }

    /* 拿到 Unicode 码点序列 */
    if (PyUnicode_READY(uni_obj) < 0) {
        return NULL;
    }
    Py_ssize_t char_count = PyUnicode_GET_LENGTH(uni_obj);
    int kind = PyUnicode_KIND(uni_obj);
    const void* data = PyUnicode_DATA(uni_obj);

    if (char_count == 0) {
        PyErr_SetString(PyExc_ValueError, "不能加密空字符串");
        return NULL;
    }

    /* 1) 构造 digits_str = "1" + 每码点 7 位十进制 */
    /*   最长: char_count * 7 + 1 */
    size_t digits_cap = (size_t)char_count * CODEPOINT_WIDTH + 2;
    char* digits = (char*)malloc(digits_cap);
    if (!digits) {
        PyErr_NoMemory();
        return NULL;
    }
    size_t pos = 0;
    digits[pos++] = LEADING_MARK;
    for (Py_ssize_t i = 0; i < char_count; i++) {
        Py_UCS4 cp = PyUnicode_READ(kind, data, i);
        /* 7 位十进制, 前补零 */
        snprintf(digits + pos, digits_cap - pos, "%07u", (unsigned int)cp);
        pos += CODEPOINT_WIDTH;
    }
    digits[pos] = '\0';
    size_t digits_len = pos;   /* 含前导 "1" */

    /* 2) 随机分三份 */
    seed_rng();
    unsigned int p1_len, p2_len, p3_len;
    if (digits_len < 3) {
        /* 太短, 直接均分 */
        p1_len = digits_len / 3;
        p2_len = digits_len / 3;
        p3_len = digits_len - p1_len - p2_len;
        if (p3_len == 0) { p3_len = 1; p2_len = (p2_len > 0 ? p2_len - 1 : 0); }
    } else {
        /* p1_len ∈ [1, digits_len/2] */
        p1_len = (unsigned int)(random() % (digits_len / 2)) + 1;
        size_t rest = digits_len - p1_len;
        if (rest < 2) {
            p2_len = 1; p3_len = rest - 1;
        } else {
            p2_len = (unsigned int)(random() % (rest / 2)) + 1;
            p3_len = (unsigned int)(rest - p2_len);
        }
    }
    /* 保底: 保证 p3_len >= 1 */
    if (p3_len == 0) {
        if (p2_len > 1) { p2_len--; p3_len = 1; }
        else if (p1_len > 1) { p1_len--; p3_len = 1; }
    }

    /* 切三份 (指针指向 digits 内部) */
    const char* p_parts[3];
    p_parts[0] = digits;                     /* p1 */
    p_parts[1] = digits + p1_len;            /* p2 */
    p_parts[2] = digits + p1_len + p2_len;   /* p3 */
    unsigned int p_lens[3] = {p1_len, p2_len, p3_len};

    /* 3) 随机选排列 */
    int perm = (int)(random() % 6);

    /* 4) shuffled = p[perm[0]] + p[perm[1]] + p[perm[2]] */
    size_t shuffled_len = (size_t)p1_len + p2_len + p3_len;
    char* shuffled = (char*)malloc(shuffled_len + 2);
    if (!shuffled) {
        free(digits);
        PyErr_NoMemory();
        return NULL;
    }
    size_t sp = 0;
    for (int k = 0; k < 3; k++) {
        int idx = PERMS[perm][k];
        memcpy(shuffled + sp, p_parts[idx], p_lens[idx]);
        sp += p_lens[idx];
    }

    /* 5) final = "1" + shuffled */
    char* final_str = (char*)malloc(shuffled_len + 2);
    if (!final_str) {
        free(digits); free(shuffled);
        PyErr_NoMemory();
        return NULL;
    }
    final_str[0] = LEADING_MARK;
    memcpy(final_str + 1, shuffled, shuffled_len);
    final_str[shuffled_len + 1] = '\0';

    /* 6) GMP: N = bignum(final_str); result = N × 10! */
    mpz_t N, result;
    mpz_init(N);
    mpz_init(result);
    if (mpz_set_str(N, final_str, 10) != 0) {
        mpz_clear(N); mpz_clear(result);
        free(digits); free(shuffled); free(final_str);
        PyErr_SetString(PyExc_RuntimeError, "GMP: 解析大整数失败");
        return NULL;
    }
    mpz_mul_ui(result, N, FACTORIAL_10);

    /* 7) 密文 = result 的十进制字符串 */
    char* ct_str = mpz_get_str(NULL, 10, result);

    /* 8) 构造 FILEKEY */
    unsigned char filekey[FILEKEY_SIZE];
    memset(filekey, 0, sizeof(filekey));
    memcpy(filekey, EXCKEY_MAGIC, 8);
    filekey[8] = EXCKEY_VERSION;
    put_u32le(filekey + 9,  p1_len);
    put_u32le(filekey + 13, p2_len);
    put_u32le(filekey + 17, p3_len);
    filekey[21] = (unsigned char)perm;
    put_u32le(filekey + 22, (unsigned int)char_count);
    /* checksum: 简单加和 (低 32 位) */
    unsigned int cksum = p1_len + p2_len + p3_len + (unsigned int)perm
                       + (unsigned int)char_count + EXCKEY_VERSION;
    put_u32le(filekey + 26, cksum);

    /* 9) 组装返回 (ciphertext_str, filekey_bytes) */
    PyObject* ct_py = PyUnicode_FromString(ct_str);
    PyObject* fk_py = PyBytes_FromStringAndSize((const char*)filekey, FILEKEY_SIZE);

    /* 释放 GMP/C 内存 */
    free(ct_str);
    mpz_clear(N);
    mpz_clear(result);
    free(digits);
    free(shuffled);
    free(final_str);

    if (!ct_py || !fk_py) {
        Py_XDECREF(ct_py);
        Py_XDECREF(fk_py);
        return NULL;
    }
    return Py_BuildValue("(NN)", ct_py, fk_py);
}

/* ═══════════════════════════════════════════════════════════════
 *  decrypt(ciphertext_str, filekey_bytes) -> text_str
 * ═══════════════════════════════════════════════════════════════ */
static PyObject* excl_decrypt(PyObject* self, PyObject* args) {
    const char* ct_str;
    Py_ssize_t fk_len;
    const unsigned char* fk_data;

    if (!PyArg_ParseTuple(args, "sy#", &ct_str, &fk_data, &fk_len)) {
        return NULL;
    }

    /* 1) 解析 FILEKEY */
    if (fk_len != FILEKEY_SIZE) {
        PyErr_SetString(PyExc_ValueError, "FILEKEY 长度错误");
        return NULL;
    }
    if (memcmp(fk_data, EXCKEY_MAGIC, 8) != 0) {
        PyErr_SetString(PyExc_ValueError, "FILEKEY 魔数不匹配 (不是有效的 EXCKEY)");
        return NULL;
    }
    unsigned int version = fk_data[8];
    if (version != EXCKEY_VERSION) {
        /* 警告但不中止 */
        fprintf(stderr, "[PyMsi.excl] 警告: FILEKEY 版本 %u (当前 %d)\n",
                version, EXCKEY_VERSION);
    }
    unsigned int p1_len = get_u32le(fk_data + 9);
    unsigned int p2_len = get_u32le(fk_data + 13);
    unsigned int p3_len = get_u32le(fk_data + 17);
    unsigned char perm = fk_data[21];
    unsigned int char_count = get_u32le(fk_data + 22);
    unsigned int cksum_stored = get_u32le(fk_data + 26);

    /* 校验 */
    if (perm >= 6) {
        PyErr_SetString(PyExc_ValueError, "FILEKEY 损坏: perm 越界");
        return NULL;
    }
    unsigned int cksum_calc = p1_len + p2_len + p3_len + (unsigned int)perm
                           + char_count + version;
    if (cksum_calc != cksum_stored) {
        PyErr_SetString(PyExc_ValueError, "FILEKEY 校验失败 (checksum 不匹配, 文件损坏)");
        return NULL;
    }
    if (char_count == 0) {
        PyErr_SetString(PyExc_ValueError, "FILEKEY 损坏: char_count=0");
        return NULL;
    }

    /* 2) GMP: N = bignum(ct_str); final_val = N / 10! (校验余数 0) */
    mpz_t N, factorial, q, r;
    mpz_init(N);
    mpz_init(factorial);
    mpz_init(q);
    mpz_init(r);

    if (mpz_set_str(N, ct_str, 10) != 0) {
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_SetString(PyExc_ValueError, "密文不是有效的大整数");
        return NULL;
    }
    if (mpz_sgn(N) < 0) {
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_SetString(PyExc_ValueError, "密文不能是负数");
        return NULL;
    }
    mpz_set_ui(factorial, FACTORIAL_10);
    mpz_tdiv_qr(q, r, N, factorial);    /* q = N / 10!, r = N % 10! */
    if (mpz_sgn(r) != 0) {
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_SetString(PyExc_ValueError,
            "密文无效: 不能被 10! (3628800) 整除 (密文已损坏或被篡改)");
        return NULL;
    }

    /* 3) final_str = q 的十进制 → 去掉前导 "1" → shuffled */
    char* final_str = mpz_get_str(NULL, 10, q);
    size_t final_len = strlen(final_str);
    if (final_len < 1 || final_str[0] != LEADING_MARK) {
        free(final_str);
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_SetString(PyExc_ValueError,
            "密文无效: 前导标记丢失 (密文与 FILEKEY 不配对, 或密码错误)");
        return NULL;
    }
    /* shuffled = final_str + 1 (跳过前导 '1') */
    char* shuffled = final_str + 1;
    size_t shuffled_len_have = final_len - 1;

    /* 4) shuffled 总长度应为 p1+p2+p3, 前导零可能丢失, 需补零 */
    size_t shuffled_len_want = (size_t)p1_len + p2_len + p3_len;
    /* 申请缓冲区装补零后的 shuffled */
    char* shuf_full = (char*)malloc(shuffled_len_want + 1);
    if (!shuf_full) {
        free(final_str);
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_NoMemory();
        return NULL;
    }
    if (shuffled_len_have < shuffled_len_want) {
        /* 前面补零 */
        size_t pad = shuffled_len_want - shuffled_len_have;
        memset(shuf_full, '0', pad);
        memcpy(shuf_full + pad, shuffled, shuffled_len_have);
    } else if (shuffled_len_have == shuffled_len_want) {
        memcpy(shuf_full, shuffled, shuffled_len_want);
    } else {
        /* have > want: 异常 */
        free(shuf_full);
        free(final_str);
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_SetString(PyExc_ValueError, "密文与 FILEKEY 长度不匹配 (数据损坏)");
        return NULL;
    }
    shuf_full[shuffled_len_want] = '\0';

    /* 5) 按 perm 切三段, 反推 p1/p2/p3 原始顺序 */
    /* shuffled = seg0 + seg1 + seg2, 其中 seg_k = p[PERMS[perm][k]] */
    /* 所以 p[PERMS[perm][0]] = seg0, ... */
    const char* segs[3];
    unsigned int p_lens[3] = {p1_len, p2_len, p3_len};
    unsigned int seg_lens[3];
    for (int k = 0; k < 3; k++) {
        seg_lens[k] = p_lens[PERMS[perm][k]];
    }
    /* 切分 shuffled: */
    size_t off = 0;
    for (int k = 0; k < 3; k++) {
        segs[k] = shuf_full + off;
        off += seg_lens[k];
    }
    /* 把 segs 放回 p 的位置: p[PERMS[perm][k]] = segs[k] */
    const char* p_parts[3];
    for (int k = 0; k < 3; k++) {
        int idx = PERMS[perm][k];
        p_parts[idx] = segs[k];
    }

    /* 6) digits = p1 + p2 + p3 (原始顺序) */
    size_t digits_len = (size_t)p1_len + p2_len + p3_len;
    char* digits = (char*)malloc(digits_len + 1);
    if (!digits) {
        free(shuf_full); free(final_str);
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_NoMemory();
        return NULL;
    }
    off = 0;
    for (int k = 0; k < 3; k++) {
        memcpy(digits + off, p_parts[k], p_lens[k]);
        off += p_lens[k];
    }
    digits[digits_len] = '\0';

    /* 7) 去掉开头 "1" (前导标记) */
    if (digits_len < 1 || digits[0] != LEADING_MARK) {
        free(digits); free(shuf_full); free(final_str);
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_SetString(PyExc_ValueError, "还原失败: 前导标记丢失");
        return NULL;
    }
    char* cp_str = digits + 1;
    size_t cp_str_len = digits_len - 1;

    /* 8) 每 7 位切一个码点 → chr() 还原 */
    if (cp_str_len % CODEPOINT_WIDTH != 0) {
        free(digits); free(shuf_full); free(final_str);
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_SetString(PyExc_ValueError, "还原失败: 码点数据长度不是 7 的倍数 (数据损坏)");
        return NULL;
    }
    size_t num_cps = cp_str_len / CODEPOINT_WIDTH;
    if (num_cps != (size_t)char_count) {
        free(digits); free(shuf_full); free(final_str);
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_Format(PyExc_ValueError,
            "还原失败: 码点数 %zu 与 FILEKEY 记录的 %u 不符 (数据损坏或 FILEKEY 不配对)",
            num_cps, char_count);
        return NULL;
    }

    /* 用 Py_UCS4 数组 + FromKindAndData 构造字符串
     * (PyUnicode_New + WRITE 在 3.14 有 == 比较陷阱, FromKindAndData 创建标准 ready 字符串) */
    Py_UCS4* buf = (Py_UCS4*)malloc(num_cps * sizeof(Py_UCS4));
    if (!buf) {
        free(digits); free(shuf_full); free(final_str);
        mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
        PyErr_NoMemory();
        return NULL;
    }
    for (size_t i = 0; i < num_cps; i++) {
        /* 解析 7 位十进制 */
        unsigned int cp = 0;
        for (int d = 0; d < CODEPOINT_WIDTH; d++) {
            char c = cp_str[i * CODEPOINT_WIDTH + d];
            if (c < '0' || c > '9') {
                free(buf);
                free(digits); free(shuf_full); free(final_str);
                mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
                PyErr_Format(PyExc_ValueError, "码点数据含非数字字符 '%c' (数据损坏)", c);
                return NULL;
            }
            cp = cp * 10 + (unsigned int)(c - '0');
        }
        if (cp > 0x10FFFF || (cp >= 0xD800 && cp <= 0xDFFF)) {
            free(buf);
            free(digits); free(shuf_full); free(final_str);
            mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);
            PyErr_Format(PyExc_ValueError, "非法 Unicode 码点 U+%X", cp);
            return NULL;
        }
        buf[i] = (Py_UCS4)cp;
    }

    /* FromKindAndData 创建标准 ready 字符串 (== 可正确比较) */
    PyObject* result_str = PyUnicode_FromKindAndData(
        PyUnicode_4BYTE_KIND, buf, (Py_ssize_t)num_cps);

    /* 释放内存 */
    free(buf);
    free(final_str);
    free(shuf_full);
    free(digits);
    mpz_clear(N); mpz_clear(factorial); mpz_clear(q); mpz_clear(r);

    if (!result_str) {
        return NULL;
    }
    return result_str;
}

/* ─── 模块定义 ──────────────────────────────────────────── */
static PyMethodDef _excl_cipher_methods[] = {
    {"encrypt",  excl_encrypt,  METH_VARARGS,
     "encrypt(text) -> (ciphertext_str, filekey_bytes)\n\n"
     "独家加密: 字符→十进制→分3份→打乱→×10! (GMP 大整数)"},
    {"decrypt",  excl_decrypt,  METH_VARARGS,
     "decrypt(ciphertext_str, filekey_bytes) -> text_str\n\n"
     "解密: 上述逆运算 (GMP 精确整除)"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef _excl_cipher_module = {
    PyModuleDef_HEAD_INIT,
    "_excl_cipher",
    "PyMsi 独家加密 C 扩展 (GMP 大整数, 字符→十进制→分3份→打乱→×10!)",
    -1,
    _excl_cipher_methods,
    NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit__excl_cipher(void) {
    return PyModule_Create(&_excl_cipher_module);
}
