# cython: language_level=3
# ═══════════════════════════════════════════════════════════════
#  PyMsi._excl_cipher — 独家加密 Cython 版 (Python int, 无 GMP)
#  ───────────────────────────────────────────────────────────────
#
#  算法 (encrypt):
#    1) 每个字符 → Unicode 码点 → 7 位十进制 (前补零)
#    2) digits = "1" + 所有码点 7 位拼接   (前导 "1" 防前导零丢失)
#    3) 随机分三份 p1/p2/p3
#    4) perm = random(0..5), 6 种排列随机打乱
#    5) shuffled = p[perm[0]] + p[perm[1]] + p[perm[2]]
#    6) final = "1" + shuffled               (再加前导 1)
#    7) N = int(final)                        (Python 任意精度 int, 等价 GMP)
#    8) result = N × 10!                     (10! = 3628800)
#    9) 密文 = str(result)
#   10) FILEKEY 存: p1_len, p2_len, p3_len, perm, char_count
#
#  解密 (decrypt): 上述逆运算 (精确整除校验余数为 0 → 防篡改)
#
#  Cython 版与纯 Python 版 (_py_encrypt/_py_decrypt) 算法完全一致,
#  密文/FILEKEY 完全互通。
#
#  编译: 需要 Cython + C 编译器 (gcc/MSVC/clang)
#    cythonize _excl_cipher.pyx → _excl_cipher.c → .so/.pyd
#  运行: 无需任何额外库 (不再依赖 libgmp)
#
#  完整源代码公开发布 (见 GitHub Release Assets)
# ═══════════════════════════════════════════════════════════════

import random
import struct
import sys

# ─── 常量 ────────────────────────────────────────────────
DEF CODEPOINT_WIDTH = 7          # 每码点 7 位十进制
DEF LEADING_MARK = "1"            # 前导标记
DEF FACTORIAL_10 = 3628800       # 10! = 1×2×3×4×5×6×7×8×9×10
DEF FILEKEY_SIZE = 30

EXCKEY_MAGIC = b"EXCKEY01"
EXCKEY_VERSION = 1

# 6 种排列
_PERMS = [
    (0, 1, 2), (0, 2, 1), (1, 0, 2),
    (1, 2, 0), (2, 0, 1), (2, 1, 0),
]


def encrypt(text):
    """加密字符串 → (密文字符串, FILEKEY bytes)

    Args:
        text: 要加密的字符串

    Returns:
        (ciphertext_str, filekey_bytes)
    """
    if not text:
        raise ValueError("不能加密空字符串")

    # 1) 每字符 → 7 位十进制, 前导 "1" 防前导零丢失
    digits = LEADING_MARK
    for ch in text:
        digits += "%07d" % (ord(ch))
    digits_len = len(digits)

    # 2) 随机分三份
    if digits_len < 3:
        p1 = digits_len // 3
        p2 = digits_len // 3
        p3 = digits_len - p1 - p2
        if p3 == 0:
            p3 = 1
            p2 = max(0, p2 - 1)
    else:
        p1 = random.randint(1, digits_len // 2)
        rest = digits_len - p1
        if rest < 2:
            p2, p3 = 1, rest - 1
        else:
            p2 = random.randint(1, rest // 2)
            p3 = rest - p2
    if p3 == 0:
        if p2 > 1:
            p2 -= 1
            p3 = 1
        elif p1 > 1:
            p1 -= 1
            p3 = 1

    p_parts = [digits[0:p1], digits[p1:p1 + p2], digits[p1 + p2:p1 + p2 + p3]]

    # 3) 随机排列
    perm = random.randint(0, 5)

    # 4) shuffled
    order = _PERMS[perm]
    shuffled = p_parts[order[0]] + p_parts[order[1]] + p_parts[order[2]]

    # 5) final = "1" + shuffled
    final_str = LEADING_MARK + shuffled

    # 6) N × 10! (Python int 任意精度, 等价 GMP)
    N = int(final_str)
    result = N * FACTORIAL_10
    ct_str = str(result)

    # 7) FILEKEY (与 C/Python 版二进制布局一致: 30 字节)
    fk = bytearray(FILEKEY_SIZE)
    fk[0:8] = EXCKEY_MAGIC
    fk[8] = EXCKEY_VERSION
    struct.pack_into("<I", fk, 9, p1)
    struct.pack_into("<I", fk, 13, p2)
    struct.pack_into("<I", fk, 17, p3)
    fk[21] = perm
    struct.pack_into("<I", fk, 22, len(text))
    cksum = p1 + p2 + p3 + perm + len(text) + EXCKEY_VERSION
    struct.pack_into("<I", fk, 26, cksum & 0xFFFFFFFF)

    return ct_str, bytes(fk)


def decrypt(ct_str, filekey):
    """解密字符串 ← (密文, FILEKEY)

    Args:
        ciphertext: 密文字符串
        filekey:    FILEKEY bytes

    Returns:
        原文字符串
    """
    if len(filekey) != FILEKEY_SIZE:
        raise ValueError("FILEKEY 长度错误")
    if filekey[0:8] != EXCKEY_MAGIC:
        raise ValueError("FILEKEY 魔数不匹配 (不是有效的 EXCKEY)")
    version = filekey[8]
    if version != EXCKEY_VERSION:
        sys.stderr.write("[PyMsi.excl] 警告: FILEKEY 版本 %d (当前 %d)\n" % (version, EXCKEY_VERSION))
    p1 = struct.unpack_from("<I", filekey, 9)[0]
    p2 = struct.unpack_from("<I", filekey, 13)[0]
    p3 = struct.unpack_from("<I", filekey, 17)[0]
    perm = filekey[21]
    char_count = struct.unpack_from("<I", filekey, 22)[0]
    cksum_stored = struct.unpack_from("<I", filekey, 26)[0]

    if perm >= 6:
        raise ValueError("FILEKEY 损坏: perm 越界")
    cksum_calc = p1 + p2 + p3 + perm + char_count + version
    if cksum_calc != cksum_stored:
        raise ValueError("FILEKEY 校验失败 (checksum 不匹配, 文件损坏)")
    if char_count == 0:
        raise ValueError("FILEKEY 损坏: char_count=0")

    # N ÷ 10! (Python int 精确整除, 校验余数)
    try:
        N = int(ct_str)
    except ValueError:
        raise ValueError("密文不是有效的大整数")
    if N < 0:
        raise ValueError("密文不能是负数")
    final_val, r = divmod(N, FACTORIAL_10)
    if r != 0:
        raise ValueError("密文无效: 不能被 10! (3628800) 整除 (密文已损坏或被篡改)")

    final_str = str(final_val)
    if not final_str or final_str[0] != LEADING_MARK:
        raise ValueError("密文无效: 前导标记丢失 (密文与 FILEKEY 不配对)")
    shuffled = final_str[1:]
    shuffled_len_have = len(shuffled)

    # 补零到应有长度
    shuffled_len_want = p1 + p2 + p3
    if shuffled_len_have < shuffled_len_want:
        shuffled = "0" * (shuffled_len_want - shuffled_len_have) + shuffled
    elif shuffled_len_have != shuffled_len_want:
        raise ValueError("密文与 FILEKEY 长度不匹配 (数据损坏)")

    # 按 perm 切三段, 反推 p1/p2/p3 原始顺序
    order = _PERMS[perm]
    p_lens = [p1, p2, p3]
    seg_lens = [p_lens[order[0]], p_lens[order[1]], p_lens[order[2]]]
    segs = []
    off = 0
    for k in range(3):
        segs.append(shuffled[off:off + seg_lens[k]])
        off += seg_lens[k]
    # p[order[k]] = segs[k]
    p_parts = [None, None, None]
    for k in range(3):
        p_parts[order[k]] = segs[k]

    # digits = p1 + p2 + p3
    digits = p_parts[0] + p_parts[1] + p_parts[2]
    if not digits or digits[0] != LEADING_MARK:
        raise ValueError("还原失败: 前导标记丢失")
    cp_str = digits[1:]

    if len(cp_str) % CODEPOINT_WIDTH != 0:
        raise ValueError("还原失败: 码点数据长度不是 7 的倍数 (数据损坏)")
    num_cps = len(cp_str) // CODEPOINT_WIDTH
    if num_cps != char_count:
        raise ValueError("还原失败: 码点数 %d 与 FILEKEY 记录的 %d 不符" % (num_cps, char_count))

    # 每 7 位切一个码点 → chr
    chars = []
    for i in range(num_cps):
        cp = int(cp_str[i * CODEPOINT_WIDTH:(i + 1) * CODEPOINT_WIDTH])
        if cp > 0x10FFFF or (0xD800 <= cp <= 0xDFFF):
            raise ValueError("非法 Unicode 码点 U+%X" % cp)
        chars.append(chr(cp))
    return "".join(chars)
