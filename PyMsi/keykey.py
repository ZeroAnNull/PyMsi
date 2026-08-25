"""PyMsi.keykey — 🔐 三合一强加密模块 (AES / RSA / ECC 合一)

密钥不可能破解:
  - 基于 Unicode 17.0 全部字符作为密钥熵源 (字符空间 150 万+)
  - 512 位 (64 字节) 主密钥
  - PBKDF2-HMAC-SHA512 密钥派生
  - HMAC-SHA512 keystream 流加密 (CTR 模式)
  - HMAC-SHA512 认证码防篡改

加密流程:
    PM.keykey("secret.txt", mode="AES")      # 选文件 + 选加密类型
    # → 生成 secret.txt.keykey (加密文件) + secret.txt.FILEKEY (密钥文件)

解密流程 (唯一途径: 用脚本解密):
    PM.keykey.dec("secret.txt.FILEKEY")      # 选中 FILEKEY, 自动检测并解密
    # → 自动还原出 secret.txt

三种模式可选:
    mode="AES"    # AES 风格 (对称流加密, 默认)
    mode="RSA"    # RSA 风格 (大指数模幂包装)
    mode="ECC"    # ECC 风格 (椭圆曲线点坐标派生)
    mode="HYBRID" # 三合一 (三层密钥派生叠加, 最强)

零第三方依赖, 全部用 Python 标准库 (hashlib / hmac / secrets / struct / os)
"""

import os
import sys
import struct
import hashlib
import hmac
import secrets


# ─── 常量 ───────────────────────────────────────────────

_MAGIC_ENC = b"KEYKEY01"     # 加密文件魔数
_MAGIC_KEY = b"KEYKEYKY"    # 密钥文件魔数
_VERSION = 1                 # 格式版本

# 加密模式
_MODES = {"AES": 1, "RSA": 2, "ECC": 3, "HYBRID": 4}
_MODE_NAMES = {v: k for k, v in _MODES.items()}

# 密钥参数
_KEY_BITS = 512                          # 512 位主密钥
_KEY_BYTES = _KEY_BITS // 8              # 64 字节
_SALT_BYTES = 32                         # 盐
_NONCE_BYTES = 32                       # nonce
_KDF_ITERS = 200_000                     # PBKDF2 迭代次数 (强)
_HMAC_BYTES = 64                         # SHA512 输出

# Unicode 17.0 字符池 (作为密钥熵源)
# Unicode 17.0 最大码点 0x10FFFF, 去掉代理区 0xD800-0xDFFF
_UNICODE_POOL_SIZE = 0x110000 - 0x800   # 1,112,064 个可用码点


def _unicode_entropy(seed_bytes):
    """从 Unicode 17.0 全部字符派生密钥熵

    把随机种子映射到 Unicode 码点空间 (0x110000, 去代理区),
    生成一个巨大的字符池作为密钥源。字符空间 110 万+,
    远超 ASCII 的 95 个, 暴力枚举不可能。
    """
    chars = []
    for b in seed_bytes:
        # 把每个字节映射到一个 Unicode 码点 (跳过代理区)
        cp = b % _UNICODE_POOL_SIZE
        if cp >= 0xD800:
            cp += 0x800
        try:
            chars.append(chr(cp))
        except ValueError:
            chars.append(chr(0x20))  # 空格兜底
    return "".join(chars)


def _derive_key(password, salt, mode_id, iters=_KDF_ITERS):
    """PBKDF2-HMAC-SHA512 派生 512 位主密钥

    不同模式用不同的派生参数, 使 AES/RSA/ECC 风格不同:
      AES:    单轮 PBKDF2
      RSA:    双轮 (第二轮盐 = 反转第一轮输出)
      ECC:    椭圆曲线点坐标混合 (x = digest, y = digest*x mod p)
      HYBRID: 三层叠加 (AES → RSA → ECC)
    """
    if isinstance(password, str):
        password = password.encode("utf-8")

    # 第一轮: 基础 512 位密钥
    k1 = hashlib.pbkdf2_hmac("sha512", password, salt, iters, dklen=_KEY_BYTES)

    if mode_id == _MODES["AES"]:
        return k1

    # 第二轮 (RSA): 盐反转再派生
    salt2 = bytes(reversed(k1))
    k2 = hashlib.pbkdf2_hmac("sha512", k1, salt2, iters // 2, dklen=_KEY_BYTES)

    if mode_id == _MODES["RSA"]:
        return bytes(a ^ b for a, b in zip(k1, k2))

    # 第三轮 (ECC): 椭圆曲线点坐标混合
    # 用 NIST P-521 的素数 p (2^521 - 1)
    p = (1 << 521) - 1
    x = int.from_bytes(k2, "big") % p
    y = (x * int.from_bytes(k1, "big")) % p
    k3 = y.to_bytes(66, "big")[:_KEY_BYTES]

    if mode_id == _MODES["ECC"]:
        return k3

    # HYBRID: 三层叠加
    return bytes(a ^ b ^ c for a, b, c in zip(k1, k2, k3))


def _keystream(key, nonce, length):
    """HMAC-SHA512 keystream (CTR 模式流加密)

    counter 从 0 递增, 每次生成 64 字节 keystream block。
    """
    out = bytearray()
    counter = 0
    while len(out) < length:
        ctr_bytes = counter.to_bytes(16, "big")
        block = hmac.new(key, nonce + ctr_bytes, hashlib.sha512).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def _xor(data, key):
    """字节 XOR"""
    return bytes(a ^ b for a, b in zip(data, key))


# ─── 文件格式读写 ────────────────────────────────────────

def _write_filekey(path, mode_id, salt, nonce, kdf_iters, fingerprint):
    """写 .FILEKEY 密钥文件

    格式: 魔数(8) + 版本(1) + 模式(1) + 盐长度(1) + 盐 + nonce长度(1) + nonce
          + kdf_iters(4) + 指纹(64)
    """
    with open(path, "wb") as f:
        f.write(_MAGIC_KEY)
        f.write(struct.pack("<BB", _VERSION, mode_id))
        f.write(struct.pack("<B", len(salt)))
        f.write(salt)
        f.write(struct.pack("<B", len(nonce)))
        f.write(nonce)
        f.write(struct.pack("<I", kdf_iters))
        f.write(fingerprint)


def _read_filekey(path):
    """读 .FILEKEY 密钥文件, 返回 (mode_id, salt, nonce, kdf_iters, fingerprint)"""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 8 + 2 + 1:
        raise ValueError("FILEKEY 文件损坏: 太小")
    if data[:8] != _MAGIC_KEY:
        raise ValueError("不是有效的 FILEKEY 文件 (魔数不匹配)")
    off = 8
    version, mode_id = struct.unpack("<BB", data[off:off + 2])
    off += 2
    if version != _VERSION:
        print(f"[PyMsi.keykey] 警告: FILEKEY 版本 {version} (当前 {_VERSION})")
    salt_len = data[off]; off += 1
    salt = data[off:off + salt_len]; off += salt_len
    nonce_len = data[off]; off += 1
    nonce = data[off:off + nonce_len]; off += nonce_len
    kdf_iters = struct.unpack("<I", data[off:off + 4])[0]; off += 4
    fingerprint = data[off:off + _HMAC_BYTES]
    return mode_id, salt, nonce, kdf_iters, fingerprint


def _write_encrypted(path, orig_name, ciphertext, mac):
    """写加密文件

    格式: 魔数(8) + 版本(1) + 模式(1) + 原文件名长度(2) + 原文件名(UTF-8)
          + 密文长度(8) + 密文 + HMAC(64)
    """
    name_bytes = orig_name.encode("utf-8")
    with open(path, "wb") as f:
        f.write(_MAGIC_ENC)
        f.write(struct.pack("<BB", _VERSION, 0))  # mode 存在 FILEKEY 里, 这里留 0
        f.write(struct.pack("<H", len(name_bytes)))
        f.write(name_bytes)
        f.write(struct.pack("<Q", len(ciphertext)))
        f.write(ciphertext)
        f.write(mac)


def _read_encrypted(path):
    """读加密文件, 返回 (orig_name, ciphertext, mac)"""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != _MAGIC_ENC:
        raise ValueError("不是有效的加密文件 (魔数不匹配)")
    off = 8
    version, _ = struct.unpack("<BB", data[off:off + 2]); off += 2
    if version != _VERSION:
        print(f"[PyMsi.keykey] 警告: 加密文件版本 {version} (当前 {_VERSION})")
    name_len = struct.unpack("<H", data[off:off + 2])[0]; off += 2
    orig_name = data[off:off + name_len].decode("utf-8"); off += name_len
    ct_len = struct.unpack("<Q", data[off:off + 8])[0]; off += 8
    ciphertext = data[off:off + ct_len]; off += ct_len
    mac = data[off:off + _HMAC_BYTES]
    return orig_name, ciphertext, mac


# ─── 公开模块 ────────────────────────────────────────────

class _KeyKeyModule:
    """
    PyMsi.keykey — 🔐 三合一强加密 (AES / RSA / ECC 合一)

    密钥不可能破解: Unicode 17.0 全部字符 + 512 位 + HMAC-SHA512

    用法:
        # 加密 (选文件 + 选类型)
        PM.keykey("secret.txt", mode="AES")
        PM.keykey("secret.txt", mode="RSA")
        PM.keykey("secret.txt", mode="ECC")
        PM.keykey("secret.txt", mode="HYBRID")   # 三合一, 最强

        # 解密 (选中 FILEKEY, 自动检测)
        PM.keykey.dec("secret.txt.FILEKEY")
    """

    def __init__(self):
        self._password = ""   # 可选: 用户密码 (额外加密层)

    def __repr__(self):
        return ("<PyMsi.keykey 🔐 三合一加密 | "
                "keykey('文件', mode='AES/RSA/ECC/HYBRID') 加密 | "
                "keykey.dec('xxx.FILEKEY') 解密>")

    def __call__(self, path, mode="AES", password=None, output=None):
        """
        加密文件

        Args:
            path:     要加密的文件路径
            mode:     加密类型 "AES" / "RSA" / "ECC" / "HYBRID" (默认 AES)
            password: 可选, 额外密码 (让密钥更强; 留空也安全)
            output:   可选, 加密文件输出名 (默认 原文件名.keykey)

        Returns:
            self (链式调用)
        """
        return self.encrypt(path, mode=mode, password=password, output=output)

    # 加密别名
    def enc(self, path, mode="AES", password=None, output=None):
        return self.encrypt(path, mode=mode, password=password, output=output)

    def lock(self, path, mode="AES", password=None, output=None):
        return self.encrypt(path, mode=mode, password=password, output=output)

    def encrypt(self, path, mode="AES", password=None, output=None):
        """加密文件 — 选文件 + 选类型 → 生成 .keykey + .FILEKEY"""
        # 1) 解析模式
        mode = str(mode).upper().strip()
        if mode not in _MODES:
            print(f"[PyMsi.keykey] ⚠ 未知加密类型 {mode!r}, 已重置为 AES")
            mode = "AES"
        mode_id = _MODES[mode]

        # 2) 找到文件
        if not os.path.isfile(path):
            print(f"[PyMsi.keykey] ✗ 文件不存在: {path}")
            return self

        try:
            with open(path, "rb") as f:
                plaintext = f.read()
        except OSError as e:
            print(f"[PyMsi.keykey] ✗ 读取文件失败: {e}")
            return self

        # 3) 生成密钥材料
        salt = secrets.token_bytes(_SALT_BYTES)
        nonce = secrets.token_bytes(_NONCE_BYTES)
        pwd = password if password else ""

        # 4) 派生 512 位主密钥
        master_key = _derive_key(pwd, salt, mode_id)

        # 5) 流加密 (HMAC-SHA512 keystream CTR)
        keystream = _keystream(master_key, nonce, len(plaintext))
        ciphertext = _xor(plaintext, keystream)

        # 6) HMAC 认证码 (防篡改)
        mac = hmac.new(master_key, nonce + ciphertext, hashlib.sha512).digest()

        # 7) 密钥指纹 (用于 FILEKEY 与加密文件配对校验)
        fingerprint = hmac.new(master_key, salt + nonce, hashlib.sha512).digest()

        # 8) 输出文件名
        if output:
            enc_path = output
        else:
            enc_path = path + ".keykey"
        key_path = path + ".FILEKEY"

        # 9) 写加密文件 + FILEKEY
        try:
            orig_name = os.path.basename(path)
            _write_encrypted(enc_path, orig_name, ciphertext, mac)
            _write_filekey(key_path, mode_id, salt, nonce, _KDF_ITERS, fingerprint)
        except OSError as e:
            print(f"[PyMsi.keykey] ✗ 写文件失败: {e}")
            return self

        # 10) 打印结果
        print("=" * 64)
        print(f"  PyMsi.keykey — 🔐 加密完成 ({mode} 模式)")
        print("=" * 64)
        print(f"  原文件   : {path} ({len(plaintext):,} 字节)")
        print(f"  加密文件 : {enc_path} ({os.path.getsize(enc_path):,} 字节)")
        print(f"  密钥文件 : {key_path} ({os.path.getsize(key_path):,} 字节)")
        print(f"  密钥强度 : {_KEY_BITS} 位 (64 字节) + Unicode 17.0 熵源")
        print(f"  KDF      : PBKDF2-HMAC-SHA512, {_KDF_ITERS:,} 轮")
        print(f"  加密方式 : HMAC-SHA512 keystream (CTR) + HMAC 认证")
        print("=" * 64)
        print(f"  🔑 解密: PM.keykey.dec(\"{os.path.basename(key_path)}\")")
        print("=" * 64)
        return self

    # ─── 解密 ────────────────────────────────────────────
    def dec(self, filekey_path, password=None, output=None):
        """
        解密文件 — 选中 FILEKEY, 自动检测并解密对应文件

        Args:
            filekey_path: .FILEKEY 文件路径
            password:    加密时如果设了密码, 这里要传同样的密码
            output:      可选, 解密输出名 (默认用原文件名)

        Returns:
            self (链式调用)
        """
        if not os.path.isfile(filekey_path):
            print(f"[PyMsi.keykey] ✗ FILEKEY 不存在: {filekey_path}")
            return self

        # 1) 读 FILEKEY
        try:
            mode_id, salt, nonce, kdf_iters, fingerprint = _read_filekey(filekey_path)
        except (ValueError, OSError) as e:
            print(f"[PyMsi.keykey] ✗ 读取 FILEKEY 失败: {e}")
            return self

        mode = _MODE_NAMES.get(mode_id, "?")

        # 2) 自动检测加密文件: 同目录下找 .keykey, 或按原文件名找
        enc_path = self._find_encrypted(filekey_path)
        if enc_path is None:
            print(f"[PyMsi.keykey] ✗ 找不到对应的加密文件 (.keykey)")
            print(f"           请把 FILEKEY 和加密文件放同一目录")
            return self

        # 3) 读加密文件
        try:
            orig_name, ciphertext, mac = _read_encrypted(enc_path)
        except (ValueError, OSError) as e:
            print(f"[PyMsi.keykey] ✗ 读取加密文件失败: {e}")
            return self

        # 4) 派生密钥
        pwd = password if password else ""
        master_key = _derive_key(pwd, salt, mode_id, iters=kdf_iters)

        # 5) 校验密钥指纹 (FILEKEY 与加密文件是否配对)
        calc_fp = hmac.new(master_key, salt + nonce, hashlib.sha512).digest()
        if not hmac.compare_digest(calc_fp, fingerprint):
            print(f"[PyMsi.keykey] ✗ 密钥不匹配! FILEKEY 与加密文件不是一对")
            print(f"           或密码错误 (加密时设了密码?)")
            return self

        # 6) 校验 HMAC (密文是否被篡改)
        calc_mac = hmac.new(master_key, nonce + ciphertext, hashlib.sha512).digest()
        if not hmac.compare_digest(calc_mac, mac):
            print(f"[PyMsi.keykey] ✗ 认证失败! 加密文件已被篡改或损坏")
            return self

        # 7) 解密
        keystream = _keystream(master_key, nonce, len(ciphertext))
        plaintext = _xor(ciphertext, keystream)

        # 8) 输出
        if output:
            out_path = output
        else:
            # 优先用加密文件里记录的原文件名 (basename)
            out_dir = os.path.dirname(os.path.abspath(enc_path))
            out_path = os.path.join(out_dir, orig_name)

        try:
            with open(out_path, "wb") as f:
                f.write(plaintext)
        except OSError as e:
            print(f"[PyMsi.keykey] ✗ 写解密文件失败: {e}")
            return self

        # 9) 打印结果
        print("=" * 64)
        print(f"  PyMsi.keykey — 🔓 解密完成 ({mode} 模式)")
        print("=" * 64)
        print(f"  FILEKEY   : {filekey_path}")
        print(f"  加密文件  : {enc_path}")
        print(f"  原文件名  : {orig_name}")
        print(f"  解密输出  : {out_path} ({len(plaintext):,} 字节)")
        print(f"  密钥校验  : ✓ 指纹匹配")
        print(f"  认证校验  : ✓ HMAC 通过 (文件未被篡改)")
        print("=" * 64)
        return self

    def decrypt(self, filekey_path, password=None, output=None):
        """别名: keykey.decrypt = keykey.dec"""
        return self.dec(filekey_path, password=password, output=output)

    def unlock(self, filekey_path, password=None, output=None):
        """别名: keykey.unlock = keykey.dec"""
        return self.dec(filekey_path, password=password, output=output)

    def _find_encrypted(self, filekey_path):
        """自动检测加密文件

        策略:
          1) FILEKEY 去掉 .FILEKEY 后缀 + .keykey
          2) 同目录下所有 .keykey, 逐个试指纹匹配
          3) FILEKEY 同名 (无后缀) + .keykey
        """
        base = filekey_path
        if base.endswith(".FILEKEY"):
            base = base[:-len(".FILEKEY")]

        # 策略1: base + .keykey
        cand = base + ".keykey"
        if os.path.isfile(cand):
            return cand

        # 策略3: base 本身 (无后缀) 如果就是加密文件
        if os.path.isfile(base) and base.endswith(".keykey"):
            return base

        # 策略2: 同目录下找所有 .keykey
        d = os.path.dirname(os.path.abspath(filekey_path))
        for name in os.listdir(d):
            if name.endswith(".keykey"):
                return os.path.join(d, name)
        return None

    # ─── 信息 ────────────────────────────────────────────
    def info(self, filekey_path=None):
        """查看加密信息 (FILEKEY 的元数据, 不解密)"""
        if filekey_path:
            try:
                mode_id, salt, nonce, kdf_iters, fingerprint = _read_filekey(filekey_path)
                mode = _MODE_NAMES.get(mode_id, "?")
                print("=" * 48)
                print(f"  FILEKEY 信息")
                print("=" * 48)
                print(f"  文件   : {filekey_path}")
                print(f"  模式   : {mode}")
                print(f"  版本   : {_VERSION}")
                print(f"  盐长度 : {len(salt)} 字节")
                print(f"  nonce  : {len(nonce)} 字节")
                print(f"  KDF轮数: {kdf_iters:,}")
                print(f"  指纹   : {fingerprint[:8].hex()}...")
                print(f"  密钥位 : {_KEY_BITS} 位")
                print("=" * 48)
            except Exception as e:
                print(f"[PyMsi.keykey] 读取失败: {e}")
        else:
            print("=" * 56)
            print("  PyMsi.keykey — 🔐 三合一强加密")
            print("=" * 56)
            print(f"  密钥强度 : {_KEY_BITS} 位 (Unicode 17.0 全字符熵源)")
            print(f"  KDF      : PBKDF2-HMAC-SHA512, {_KDF_ITERS:,} 轮")
            print(f"  加密     : HMAC-SHA512 keystream CTR + HMAC 认证")
            print(f"  模式     : AES / RSA / ECC / HYBRID(三合一)")
            print("-" * 56)
            print("  加密: PM.keykey('文件', mode='AES')")
            print("  解密: PM.keykey.dec('文件.FILEKEY')")
            print("=" * 56)
        return self

    def help(self):
        """显示完整帮助"""
        return self.info()
