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

# 导入 C 扩展 (GMP 大整数实现)
try:
    from . import _excl_cipher as _cext
    _C_AVAILABLE = True
    _C_ERROR = None
except ImportError as e:
    _C_AVAILABLE = False
    _C_ERROR = str(e)
    _cext = None


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
        return ("<PyMsi.excl 🔒 独家加密 [C扩展未加载] | "
                f"错误: {_C_ERROR}>")

    def _check(self):
        if not _C_AVAILABLE:
            raise RuntimeError(
                f"独家加密 C 扩展未加载: {_C_ERROR}\n"
                "可能原因: 系统缺少 libgmp (请安装 libgmp10 / libgmp-dev)\n"
                "或 wheel 与当前平台不匹配"
            )

    # ─── 字符串加密/解密 ─────────────────────────────────
    def encrypt(self, text):
        """加密字符串 → (密文字符串, FILEKEY bytes)

        Args:
            text: 要加密的字符串

        Returns:
            (ciphertext_str, filekey_bytes)
        """
        self._check()
        if not isinstance(text, str):
            text = str(text)
        return _cext.encrypt(text)

    def decrypt(self, ciphertext, filekey):
        """解密字符串 ← (密文, FILEKEY)

        Args:
            ciphertext: 密文字符串
            filekey:    FILEKEY bytes (encrypt 返回的第二项)

        Returns:
            原文字符串
        """
        self._check()
        if isinstance(filekey, str):
            # 允许传 str (会编码), 但推荐 bytes
            filekey = filekey.encode("latin-1")
        return _cext.decrypt(ciphertext, filekey)

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
        print("  PyMsi.excl — 🔒 独家加密 (C/GMP 大整数)")
        print("=" * 60)
        if _C_AVAILABLE:
            print(f"  C 扩展   : 已加载 ✓ (_excl_cipher)")
            print(f"  大整数库 : libgmp (任意精度)")
        else:
            print(f"  C 扩展   : 未加载 ✗")
            print(f"  错误     : {_C_ERROR}")
        print(f"  算法     : 字符→十进制→分3份→打乱→×10!")
        print(f"  10!      : 3628800")
        print(f"  分份     : 随机分 3 份 (p1/p2/p3)")
        print(f"  打乱     : 6 种排列随机选")
        print(f"  解密     : 自写逆向 (GMP 精确整除)")
        print("-" * 60)
        print("  加密: PM.excl('文件')")
        print("  解密: PM.excl.dec('文件.EXCKEY')")
        print("=" * 60)
        return self

    def help(self):
        return self.info()
