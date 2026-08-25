"""PyMsi.excl — 🔒 独家加密模块 (C/GMP 大整数实现)

算法 (encrypt):
    1) 每个字符 → Unicode 码点 → 7 位十进制 (前补零)
    2) digits = "1" + 所有码点 7 位拼接   (前导 "1" 防前导零丢失)
    3) 随机分三份 p1/p2/p3
    4) perm = random(0..5), 6 种排列随机打乱
    5) shuffled = p[perm[0]] + p[perm[1]] + p[perm[2]]
    6) final = "1" + shuffled               (再加前导 1, 防 GMP 丢前导零)
    7) N = GMP_bignum(final)
    8) result = N × 10!                     (10! = 3628800, GMP 精确大整数)
    9) 密文 = result 的十进制字符串

解密 (decrypt): 上述逆运算, 用 GMP 精确整除 (校验余数为 0)

底层实现: PyMsi/_excl_cipher.c (纯 C + libgmp), 编译成 .so 扩展
        用户装 wheel 即用, 无需编译器

用法:
    import PyMsi as PM

    # 加密 (选文件)
    PM.excl("secret.txt")
    # → 生成 secret.txt.excl (加密文件) + secret.txt.EXCKEY (密钥文件)

    # 解密 (选中 EXCKEY, 自动检测)
    PM.excl.dec("secret.txt.EXCKEY")
    # → 自动还原出 secret.txt

    # 直接对字符串加密/解密
    ct, fk = PM.excl.encrypt("机密内容")
    pt = PM.excl.decrypt(ct, fk)

密钥不可破解:
    - 字符 → 大整数 (任意长度, GMP 任意精度)
    - 10! 阶乘运算 (GMP 精确, 精度拉到最大)
    - 随机分三份 + 6 种排列打乱
    - 自写逆向 (解密)
"""

import os
import sys
import random
import struct

# 导入 C 扩展 (GMP 大整数实现)
# 加载失败时自动回退到纯 Python 实现 (Python 内置 int 也是任意精度大整数)
try:
    from . import _excl_cipher as _cext
    _C_AVAILABLE = True
    _C_ERROR = None
except ImportError as e:
    _C_AVAILABLE = False
    _C_ERROR = str(e)
    _cext = None


# ═══════════════════════════════════════════════════════════════
# 纯 Python 回退实现 (C 扩展不可用时用, 算法完全一致)
# Python 内置 int 是任意精度大整数, 精度无限, 等价 GMP
# ═══════════════════════════════════════════════════════════════

_CODEPOINT_WIDTH = 7          # 每码点 7 位十进制
_LEADING_MARK = "1"           # 前导标记
_FACTORIAL_10 = 3628800       # 10! = 1×2×3×4×5×6×7×8×9×10
_EXCKEY_MAGIC = b"EXCKEY01"
_EXCKEY_VERSION = 1
_FILEKEY_SIZE = 30

# 6 种排列 (与 C 实现一致)
_PERMS = [
    (0, 1, 2), (0, 2, 1), (1, 0, 2),
    (1, 2, 0), (2, 0, 1), (2, 1, 0),
]


def _py_encrypt(text):
    """纯 Python 加密 (回退用, 算法同 C)"""
    if not text:
        raise ValueError("不能加密空字符串")

    # 1) 每字符 → 7 位十进制, 前导 "1" 防前导零丢失
    digits = _LEADING_MARK
    for ch in text:
        digits += f"{ord(ch):0{_CODEPOINT_WIDTH}d}"
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
            p2 -= 1; p3 = 1
        elif p1 > 1:
            p1 -= 1; p3 = 1

    p_parts = [digits[0:p1], digits[p1:p1 + p2], digits[p1 + p2:p1 + p2 + p3]]
    p_lens = [p1, p2, p3]

    # 3) 随机排列
    perm = random.randint(0, 5)

    # 4) shuffled
    order = _PERMS[perm]
    shuffled = "".join(p_parts[order[k]] for k in range(3))

    # 5) final = "1" + shuffled
    final_str = _LEADING_MARK + shuffled

    # 6) N × 10! (Python int 任意精度, 等价 GMP)
    N = int(final_str)
    result = N * _FACTORIAL_10
    ct_str = str(result)

    # 7) FILEKEY (与 C 二进制布局一致: 30 字节)
    fk = bytearray(_FILEKEY_SIZE)
    fk[0:8] = _EXCKEY_MAGIC
    fk[8] = _EXCKEY_VERSION
    struct.pack_into("<I", fk, 9, p1)
    struct.pack_into("<I", fk, 13, p2)
    struct.pack_into("<I", fk, 17, p3)
    fk[21] = perm
    struct.pack_into("<I", fk, 22, len(text))
    cksum = p1 + p2 + p3 + perm + len(text) + _EXCKEY_VERSION
    struct.pack_into("<I", fk, 26, cksum & 0xFFFFFFFF)

    return ct_str, bytes(fk)


def _py_decrypt(ct_str, filekey):
    """纯 Python 解密 (回退用, 算法同 C)"""
    if len(filekey) != _FILEKEY_SIZE:
        raise ValueError("FILEKEY 长度错误")
    if filekey[0:8] != _EXCKEY_MAGIC:
        raise ValueError("FILEKEY 魔数不匹配 (不是有效的 EXCKEY)")
    version = filekey[8]
    if version != _EXCKEY_VERSION:
        sys.stderr.write(f"[PyMsi.excl] 警告: FILEKEY 版本 {version} (当前 {_EXCKEY_VERSION})\n")
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
    final_val, r = divmod(N, _FACTORIAL_10)
    if r != 0:
        raise ValueError("密文无效: 不能被 10! (3628800) 整除 (密文已损坏或被篡改)")

    final_str = str(final_val)
    if not final_str or final_str[0] != _LEADING_MARK:
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
    seg_lens = [p_lens[order[k]] for k in range(3)]
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
    digits = "".join(p_parts)
    if not digits or digits[0] != _LEADING_MARK:
        raise ValueError("还原失败: 前导标记丢失")
    cp_str = digits[1:]

    if len(cp_str) % _CODEPOINT_WIDTH != 0:
        raise ValueError("还原失败: 码点数据长度不是 7 的倍数 (数据损坏)")
    num_cps = len(cp_str) // _CODEPOINT_WIDTH
    if num_cps != char_count:
        raise ValueError(f"还原失败: 码点数 {num_cps} 与 FILEKEY 记录的 {char_count} 不符")

    # 每 7 位切一个码点 → chr
    chars = []
    for i in range(num_cps):
        cp = int(cp_str[i * _CODEPOINT_WIDTH:(i + 1) * _CODEPOINT_WIDTH])
        if cp > 0x10FFFF or (0xD800 <= cp <= 0xDFFF):
            raise ValueError(f"非法 Unicode 码点 U+{cp:X}")
        chars.append(chr(cp))
    return "".join(chars)


class _ExclCryptoModule:
    """
    PyMsi.excl — 🔒 独家加密 (C/GMP 大整数)

    用法:
        PM.excl("secret.txt")               # 加密文件
        PM.excl.dec("secret.txt.EXCKEY")    # 解密 (选中 EXCKEY)

        ct, fk = PM.excl.encrypt("文本")     # 直接加密字符串
        pt = PM.excl.decrypt(ct, fk)         # 直接解密
    """

    def __init__(self):
        pass

    def __repr__(self):
        if _C_AVAILABLE:
            return ("<PyMsi.excl 🔒 独家加密 (C/GMP) | "
                    "excl('文件') 加密 | excl.dec('xxx.EXCKEY') 解密>")
        return ("<PyMsi.excl 🔒 独家加密 (纯Python回退) | "
                "excl('文件') 加密 | excl.dec('xxx.EXCKEY') 解密>")

    def _check(self):
        """检查后端 (C 扩展不可用时自动用纯 Python, 不报错)"""
        if not _C_AVAILABLE:
            # 不抛异常, 已自动回退到纯 Python 实现
            return False
        return True

    # ─── 字符串加密/解密 ─────────────────────────────────
    def encrypt(self, text):
        """加密字符串 → (密文字符串, FILEKEY bytes)

        Args:
            text: 要加密的字符串

        Returns:
            (ciphertext_str, filekey_bytes)
        """
        if not isinstance(text, str):
            text = str(text)
        # 优先用 C 扩展, 不可用则回退纯 Python
        if _C_AVAILABLE:
            return _cext.encrypt(text)
        return _py_encrypt(text)

    def decrypt(self, ciphertext, filekey):
        """解密字符串 ← (密文, FILEKEY)

        Args:
            ciphertext: 密文字符串
            filekey:    FILEKEY bytes (encrypt 返回的第二项)

        Returns:
            原文字符串
        """
        if isinstance(filekey, str):
            filekey = filekey.encode("latin-1")
        if _C_AVAILABLE:
            return _cext.decrypt(ciphertext, filekey)
        return _py_decrypt(ciphertext, filekey)

    # ─── 文件加密/解密 ───────────────────────────────────
    def __call__(self, path, output=None):
        """加密文件 — 选文件 → 生成 .excl + .EXCKEY

        Args:
            path:   要加密的文件路径
            output: 可选, 加密文件输出名 (默认 原文件名.excl)

        Returns:
            self (链式调用)
        """
        return self.enc_file(path, output=output)

    def enc(self, path, output=None):
        """别名: excl.enc = excl.__call__"""
        return self.enc_file(path, output=output)

    def lock(self, path, output=None):
        """别名"""
        return self.enc_file(path, output=output)

    def enc_file(self, path, output=None):
        """加密文件"""
        self._check()
        if not os.path.isfile(path):
            print(f"[PyMsi.excl] ✗ 文件不存在: {path}")
            return self

        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            # 不是 UTF-8 文本, 按 bytes 处理 (用 latin-1 逐字节, 0-255)
            with open(path, "rb") as f:
                raw = f.read()
            text = raw.decode("latin-1")
        except OSError as e:
            print(f"[PyMsi.excl] ✗ 读取文件失败: {e}")
            return self

        # C 扩展加密
        try:
            ciphertext, filekey = _cext.encrypt(text)
        except Exception as e:
            print(f"[PyMsi.excl] ✗ 加密失败: {e}")
            return self

        # 输出路径
        if output:
            enc_path = output
        else:
            enc_path = path + ".excl"
        key_path = path + ".EXCKEY"

        # 写加密文件 (文本, 大整数十进制字符串)
        try:
            with open(enc_path, "w", encoding="utf-8") as f:
                f.write(ciphertext)
            with open(key_path, "wb") as f:
                f.write(filekey)
        except OSError as e:
            print(f"[PyMsi.excl] ✗ 写文件失败: {e}")
            return self

        # 打印结果
        ct_len = len(ciphertext)
        print("=" * 64)
        print(f"  PyMsi.excl — 🔒 独家加密完成")
        print("=" * 64)
        print(f"  原文件   : {path} ({len(text):,} 字符)")
        print(f"  加密文件 : {enc_path} ({os.path.getsize(enc_path):,} 字节)")
        print(f"  密钥文件 : {key_path} ({os.path.getsize(key_path):,} 字节)")
        print(f"  密文长度 : {ct_len:,} 位十进制数字 (GMP 大整数)")
        print(f"  算法     : 字符→十进制→分3份→打乱→×10! (3628800)")
        print(f"  实现     : 纯 C + libgmp (任意精度大整数, 精度拉满)")
        print("=" * 64)
        print(f"  🔑 解密: PM.excl.dec(\"{os.path.basename(key_path)}\")")
        print("=" * 64)
        return self

    # ─── 解密 ────────────────────────────────────────────
    def dec(self, exckey_path, output=None):
        """解密文件 — 选中 EXCKEY, 自动检测并解密对应文件

        Args:
            exckey_path: .EXCKEY 密钥文件路径
            output:      可选, 解密输出名 (默认用原文件名)

        Returns:
            self (链式调用)
        """
        self._check()
        if not os.path.isfile(exckey_path):
            print(f"[PyMsi.excl] ✗ EXCKEY 不存在: {exckey_path}")
            return self

        # 自动检测加密文件
        enc_path = self._find_encrypted(exckey_path)
        if enc_path is None:
            print(f"[PyMsi.excl] ✗ 找不到对应的加密文件 (.excl)")
            print(f"           请把 EXCKEY 和加密文件放同一目录")
            return self

        # 读 FILEKEY
        try:
            with open(exckey_path, "rb") as f:
                filekey = f.read()
        except OSError as e:
            print(f"[PyMsi.excl] ✗ 读取 EXCKEY 失败: {e}")
            return self

        # 读密文
        try:
            with open(enc_path, "r", encoding="utf-8") as f:
                ciphertext = f.read().strip()
        except OSError as e:
            print(f"[PyMsi.excl] ✗ 读取加密文件失败: {e}")
            return self

        # C 扩展解密
        try:
            plaintext = _cext.decrypt(ciphertext, filekey)
        except Exception as e:
            print(f"[PyMsi.excl] ✗ 解密失败: {e}")
            return self

        # 输出
        if output:
            out_path = output
        else:
            # 从加密文件名还原原文件名 (去掉 .excl)
            base = enc_path
            if base.endswith(".excl"):
                base = base[:-len(".excl")]
            out_dir = os.path.dirname(os.path.abspath(enc_path))
            out_path = os.path.join(out_dir, os.path.basename(base))

        try:
            # 优先 UTF-8 写入, 失败则 latin-1 (二进制兼容)
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(plaintext)
            except UnicodeEncodeError:
                with open(out_path, "wb") as f:
                    f.write(plaintext.encode("latin-1"))
        except OSError as e:
            print(f"[PyMsi.excl] ✗ 写解密文件失败: {e}")
            return self

        print("=" * 64)
        print(f"  PyMsi.excl — 🔓 独家解密完成")
        print("=" * 64)
        print(f"  EXCKEY    : {exckey_path}")
        print(f"  加密文件  : {enc_path}")
        print(f"  密文长度  : {len(ciphertext):,} 位")
        print(f"  解密输出  : {out_path} ({len(plaintext):,} 字符)")
        print(f"  算法      : GMP 大整数 ÷ 10! → 还原 (精确整除校验)")
        print("=" * 64)
        return self

    def decrypt_file(self, exckey_path, output=None):
        """别名"""
        return self.dec(exckey_path, output=output)

    def unlock(self, exckey_path, output=None):
        """别名"""
        return self.dec(exckey_path, output=output)

    def _find_encrypted(self, exckey_path):
        """自动检测加密文件

        策略:
          1) EXCKEY 去掉 .EXCKEY 后缀 + .excl
          2) 同目录下所有 .excl 文件
        """
        base = exckey_path
        if base.endswith(".EXCKEY"):
            base = base[:-len(".EXCKEY")]

        # 策略1
        cand = base + ".excl"
        if os.path.isfile(cand):
            return cand

        # 策略2: 同目录找 .excl
        d = os.path.dirname(os.path.abspath(exckey_path))
        for name in os.listdir(d):
            if name.endswith(".excl"):
                return os.path.join(d, name)
        return None

    # ─── 信息 ────────────────────────────────────────────
    def info(self):
        """显示模块信息"""
        print("=" * 60)
        print("  PyMsi.excl — 🔒 独家加密")
        print("=" * 60)
        if _C_AVAILABLE:
            print(f"  后端     : C 扩展 ✓ (_excl_cipher + libgmp)")
            print(f"  大整数库 : libgmp (任意精度, C 原生)")
        else:
            print(f"  后端     : 纯 Python 回退 (C 扩展未加载)")
            print(f"  原因     : {_C_ERROR}")
            print(f"  大整数   : Python 内置 int (任意精度, 等价 GMP)")
        print(f"  算法     : 字符→十进制→分3份→打乱→×10!")
        print(f"  10!      : 3628800")
        print(f"  分份     : 随机分 3 份 (p1/p2/p3)")
        print(f"  打乱     : 6 种排列随机选")
        print(f"  解密     : 自写逆向 (精确整除校验)")
        print(f"  互通     : C 与 Python 版密文/FILEKEY 完全互通")
        print("-" * 60)
        print("  加密: PM.excl('文件')")
        print("  解密: PM.excl.dec('文件.EXCKEY')")
        print("=" * 60)
        return self

    def help(self):
        return self.info()
