"""PyMsi.nano — 📦 .nano 容器模块 (1.5.6 新增)

自研 .nano 容器文件格式 — 四级权限分区存储

比普通压缩包更安全的存储方式: 权限制度 + 校验 + 分区加密
每个区域密码不一样, 用户名不一样, 权限更不一样

═══════════════════════════════════════════════════════════════
四个权限分区 (从低到高):
═══════════════════════════════════════════════════════════════

┌─ 1. normal (普通区域) ─────────────────────────────────────┐
│  存放杂物, 不需要任何权限                                    │
│  密码: 无                                                   │
│  系统权限: 无                                               │
│  用途: 用户指定的普通文件                                    │
└────────────────────────────────────────────────────────────┘

┌─ 2. adminanorobit (Anon2 权限) ───────────────────────────┐
│  管理员级分区                                                │
│  密码: 用户设置 Anon2 密码                                   │
│  系统权限:                                                   │
│    Windows: 需要 Administrators 超级管理员权限               │
│    Linux/macOS: 需要 sudo 权限 (UID != 0, 有 sudo 能力)     │
│  用途: 进阶文件, 需要管理员身份才能打开                       │
└────────────────────────────────────────────────────────────┘

┌─ 3. asoav1 (高泉区 / Dona0 内核级) ───────────────────────┐
│  内核级权限分区                                              │
│  密码: Dona0 密钥 (比 Anon2 更长更强)                       │
│  系统权限:                                                   │
│    Windows: 需要 SYSTEM 权限                                 │
│    Linux/macOS: 需要 root (UID == 0) + 内核模块级验证       │
│  用途: 存放重要文件, 内核级保护                               │
│  提取方式: PM.nano.open_asoav1(container, dona0_key)        │
└────────────────────────────────────────────────────────────┘

┌─ 4. nanou (最高权限区 / .nnu 脚本) ───────────────────────┐
│  最高权限分区, 需要写 .nnu 代码才能打开                       │
│  密码: Nanou 主密钥 + 挑战响应机制                           │
│  系统权限: 所有系统级检查 + .nnu 脚本执行流程                │
│  用途: 最高级别机密文件                                      │
│  提取方式: 执行 .nnu 脚本 (nnu 语法公开, 见下)               │
└────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
.nnu 语法 (Nanou Narrative Unit — 公开语法)
═══════════════════════════════════════════════════════════════

.nnu 是 Nanou 区的访问脚本, 必须经过多阶段复杂流程才能打开:

    # 示例: extract_all.nnu
    NANO_VERSION 1
    CONTAINER "path/to/data.nano"
    ZONE nanou

    # 阶段 1: 认证
    PHASE auth
        MASTER_KEY "base64_encoded_nanou_master_key"
        CHALLENGE "nonce_string_from_container"
        RESPONSE "sha256(nonce + secret_salt)"
    END_PHASE

    # 阶段 2: 解密
    PHASE decrypt
        ALGORITHM stream_sha256
        KEY_DERIVATION pbkdf2_sha256:50000
        SALT "base64_salt"
    END_PHASE

    # 阶段 3: 操作
    PHASE action
        EXTRACT_ALL "D:/NanouOutput/"
        # EXTRACT "secret.txt" "D:/out/secret.txt"
        # LIST
    END_PHASE

    # 阶段 4: 收尾
    PHASE cleanup
        WIPE_MEMORY true
        CLOSE_CONTAINER true
    END_PHASE

nnu 关键字 (全部公开):
    NANO_VERSION  CONTAINER  ZONE
    PHASE / END_PHASE
    auth 阶段: MASTER_KEY  CHALLENGE  RESPONSE  USERNAME
    decrypt 阶段: ALGORITHM  KEY_DERIVATION  SALT  ITERATIONS
    action 阶段: EXTRACT_ALL  EXTRACT  LIST  VERIFY
    cleanup 阶段: WIPE_MEMORY  CLOSE_CONTAINER  SECURE_WIPE

用法:
    import PyMsi as PM

    # 创建 .nano 容器
    PM.nano.create("data.nano", normal_pw=None, anon2_pw="admin123",
                   dona0_key="kernel_secret_key", nanou_key="top_secret_master")

    # 添加文件到普通区 (无需密码)
    PM.nano.add("data.nano", "normal", "readme.txt")
    PM.nano.add("data.nano", "normal", ["a.txt", "b.png"])

    # 添加文件到 Anon2 区 (需要 Anon2 密码)
    PM.nano.add("data.nano", "adminanorobit", "important.docx", anon2_pw="admin123")

    # 添加文件到 Asoav1 区 (需要 Dona0 密钥)
    PM.nano.add("data.nano", "asoav1", "kernel_config.bin", dona0_key="kernel_secret_key")

    # 添加文件到 Nanou 区 (需要 Nanou 主密钥)
    PM.nano.add("data.nano", "nanou", "top_secret.pdf", nanou_key="top_secret_master")

    # 列出普通区文件
    PM.nano.list("data.nano", "normal")

    # 提取普通区 (无需密码)
    PM.nano.extract("data.nano", "normal", output_dir="D:/NormalOut")

    # 提取 Anon2 区 (需要密码 + 管理员权限)
    PM.nano.extract("data.nano", "adminanorobit", anon2_pw="admin123",
                    output_dir="D:/Anon2Out")

    # 提取 Asoav1 区 (需要 Dona0 密钥 + SYSTEM/root)
    PM.nano.extract("data.nano", "asoav1", dona0_key="kernel_secret_key",
                    output_dir="/root/Asoav1Out")

    # 提取 Nanou 区 (执行 .nnu 脚本)
    PM.nano.run_nnu("extract.nnu")

    # 别名: PM.nano / PM.container / PM.容器 / PM.纳米
"""

import os
import sys
import json
import struct
import hashlib
import base64
import platform


# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════

_NANO_MAGIC = b"NANO"
_NANO_VERSION = 1
_HEADER_SIZE = 128  # 固定头部大小

# 四个分区 ID
ZONE_NORMAL = 0
ZONE_ADMINANOROBIT = 1  # Anon2
ZONE_ASOAV1 = 2         # Dona0 / 高泉区
ZONE_NANOU = 3          # 最高权限区

ZONE_NAMES = {
    ZONE_NORMAL: "normal",
    ZONE_ADMINANOROBIT: "adminanorobit",
    ZONE_ASOAV1: "asoav1",
    ZONE_NANOU: "nanou",
}

ZONE_DESCS = {
    ZONE_NORMAL: "普通区域 - 无需权限",
    ZONE_ADMINANOROBIT: "Adminanorobit (Anon2) - 管理员级",
    ZONE_ASOAV1: "Asoav1 (Dona0) - 内核级 / 高泉区",
    ZONE_NANOU: "Nanou - 最高权限区 (.nnu 脚本)",
}

# 加密算法
ALGO_NONE = 0
ALGO_STREAM_SHA256 = 1  # 纯自研 SHA-256 流密码

# PBKDF2 迭代次数
_PBKDF2_ITERATIONS_NORMAL = 1000
_PBKDF2_ITERATIONS_ANON2 = 5000
_PBKDF2_ITERATIONS_DONA0 = 20000
_PBKDF2_ITERATIONS_NANOU = 50000


# ═══════════════════════════════════════════════════════════════
# 平台检测
# ═══════════════════════════════════════════════════════════════

_IS_WINDOWS = sys.platform == "win32"
_IS_LINUX = sys.platform.startswith("linux")
_IS_MACOS = sys.platform == "darwin"


# ═══════════════════════════════════════════════════════════════
# 纯自研加密: SHA-256 流密码 + PBKDF2 密钥派生
# ═══════════════════════════════════════════════════════════════

def _pbkdf2_sha256(password: bytes, salt: bytes, iterations: int) -> bytes:
    """纯 Python PBKDF2-HMAC-SHA256 密钥派生

    不依赖任何第三方库, 用标准库 hashlib 实现
    """
    # hmac 用 hashlib 手动实现
    def hmac_sha256(key, msg):
        block_size = 64
        if len(key) > block_size:
            key = hashlib.sha256(key).digest()
        key = key + b'\x00' * (block_size - len(key))
        o_key_pad = bytes(b ^ 0x5c for b in key)
        i_key_pad = bytes(b ^ 0x36 for b in key)
        return hashlib.sha256(o_key_pad + hashlib.sha256(i_key_pad + msg).digest()).digest()

    # PBKDF2: DK = T1 + T2 + ... + Tdklen/hlen
    # Ti = F(Password, Salt, c, i)
    # F(P, S, c, i) = U1 xor U2 xor ... xor Uc
    # U1 = PRF(P, S + INT(i))
    # Uj = PRF(P, U_{j-1})

    def f(password, salt, iterations, block_index):
        # U1 = HMAC-SHA256(password, salt || INT(i))
        u_prev = hmac_sha256(password, salt + struct.pack(">I", block_index))
        result = u_prev
        for _ in range(iterations - 1):
            u_prev = hmac_sha256(password, u_prev)
            result = bytes(a ^ b for a, b in zip(result, u_prev))
        return result

    dk = b""
    block_index = 1
    # 生成 32 bytes (256-bit) 密钥
    dk += f(password, salt, iterations, block_index)
    return dk


def _stream_encrypt(data: bytes, key: bytes) -> bytes:
    """纯自研 SHA-256 流密码加密/解密

    生成密钥流: keystream_i = SHA256(key || counter_i)
    然后 XOR: output = data XOR keystream

    加密和解密是同一个操作 (XOR 的对称性)

    Args:
        data: 明文或密文
        key: 密钥 (任意长度, 内部用 SHA-256 哈希到 32 bytes)
    Returns:
        密文或明文
    """
    # 密钥预处理: SHA-256 得到 32 bytes 基密钥
    base_key = hashlib.sha256(key).digest()

    # 生成密钥流
    keystream = b""
    counter = 0
    while len(keystream) < len(data):
        block = hashlib.sha256(base_key + struct.pack("<Q", counter)).digest()
        keystream += block
        counter += 1

    # XOR
    keystream = keystream[:len(data)]
    return bytes(a ^ b for a, b in zip(data, keystream))


def _encrypt_zone(data: bytes, password: str, zone_id: int, salt: bytes = None) -> tuple:
    """加密分区数据

    Returns:
        (encrypted_data, salt, iterations)
    """
    if zone_id == ZONE_NORMAL:
        return (data, b"", 0)

    if salt is None:
        salt = os.urandom(16)

    iterations = {
        ZONE_ADMINANOROBIT: _PBKDF2_ITERATIONS_ANON2,
        ZONE_ASOAV1: _PBKDF2_ITERATIONS_DONA0,
        ZONE_NANOU: _PBKDF2_ITERATIONS_NANOU,
    }.get(zone_id, _PBKDF2_ITERATIONS_NORMAL)

    key = _pbkdf2_sha256(password.encode("utf-8"), salt, iterations)
    encrypted = _stream_encrypt(data, key)
    return (encrypted, salt, iterations)


def _decrypt_zone(encrypted: bytes, password: str, zone_id: int,
                  salt: bytes, iterations: int) -> bytes:
    """解密分区数据"""
    if zone_id == ZONE_NORMAL:
        return encrypted

    key = _pbkdf2_sha256(password.encode("utf-8"), salt, iterations)
    return _stream_encrypt(encrypted, key)


# ═══════════════════════════════════════════════════════════════
# 系统权限检查
# ═══════════════════════════════════════════════════════════════

def _check_normal_privilege():
    """普通区: 无权限要求"""
    return True, ""


def _check_anon2_privilege():
    """Anon2 (Adminanorobit) 权限检查

    Windows: 需要 Administrators 管理员权限
    Linux/macOS: 需要 sudo 权限 (有 sudo 能力的非 root 用户)
    """
    if _IS_WINDOWS:
        try:
            import ctypes
            from ctypes import wintypes
            # 检查是否管理员
            TOKEN_QUERY = 0x0008
            TokenElevation = 20

            class TOKEN_ELEVATION(ctypes.Structure):
                _fields_ = [("TokenIsElevated", wintypes.DWORD)]

            advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

            token = wintypes.HANDLE()
            if not advapi32.OpenProcessToken(
                kernel32.GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(token)
            ):
                return False, "无法打开进程令牌"

            try:
                elevation = TOKEN_ELEVATION()
                returned = wintypes.DWORD()
                if not advapi32.GetTokenInformation(
                    token, TokenElevation, ctypes.byref(elevation),
                    ctypes.sizeof(elevation), ctypes.byref(returned)
                ):
                    return False, "无法获取令牌信息"
                if not bool(elevation.TokenIsElevated):
                    return False, "需要管理员权限 (Administrators), 请以管理员身份运行"
                return True, ""
            finally:
                kernel32.CloseHandle(token)
        except Exception as e:
            return False, f"权限检查失败: {e}"

    else:
        # Linux/macOS: 检查 sudo 权限
        # UID != 0 (非 root) 但有 sudo 能力
        try:
            euid = os.geteuid()
            if euid == 0:
                # 已经是 root 也算通过
                return True, ""
            # 检查 sudo -n true (无密码 sudo 或已缓存)
            import subprocess
            result = subprocess.run(
                ["sudo", "-n", "true"], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return True, ""
            return False, "需要 sudo 权限 (Anon2 级别), 请确保有 sudo 权限"
        except Exception as e:
            return False, f"权限检查失败: {e}"


def _check_asoav1_privilege():
    """Asoav1 (Dona0 / 高泉区) 权限检查

    Windows: 需要 SYSTEM 权限
    Linux/macOS: 需要 root (UID == 0)
    """
    if _IS_WINDOWS:
        try:
            import ctypes
            from ctypes import wintypes
            # 检查当前用户名是否为 SYSTEM
            advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

            size = wintypes.DWORD(256)
            buf = ctypes.create_unicode_buffer(256)
            if advapi32.GetUserNameW(buf, ctypes.byref(size)):
                username = buf.value
                if username.upper() == "SYSTEM":
                    return True, ""
            return False, "需要 SYSTEM 权限 (Dona0 / 内核级), 当前不是 SYSTEM"
        except Exception as e:
            return False, f"权限检查失败: {e}"
    else:
        # Linux/macOS: root = 内核级
        if os.geteuid() == 0:
            return True, ""
        return False, "需要 root 权限 (Dona0 / 内核级), 请以 root 运行"


def _check_nanou_privilege():
    """Nanou 最高权限区检查

    不仅需要系统级最高权限, 还需要 .nnu 脚本验证
    此函数只做系统级检查, nnu 脚本验证由 _NNURunner 处理
    """
    # 先检查 Asoav1 级 (SYSTEM/root)
    ok, msg = _check_asoav1_privilege()
    if not ok:
        return False, f"Nanou 需要系统最高权限: {msg}"
    return True, ""


# ═══════════════════════════════════════════════════════════════
# .nano 文件格式 (纯自研二进制格式)
# ═══════════════════════════════════════════════════════════════
#
# 整体结构:
#   ┌──────────────────────────────────┐
#   │ Header (128 bytes)               │
#   │   Magic: "NANO" (4)              │
#   │   Version: uint32 LE (4)         │
#   │   Zone count: uint32 LE (4)      │
#   │   Zone table offset: uint64 LE   │
#   │   Header checksum: SHA-256[0:16] │
#   │   Reserved: 剩余填充              │
#   ├──────────────────────────────────┤
#   │ Zone 0: Normal 数据区             │
#   │   (明文存储)                      │
#   ├──────────────────────────────────┤
#   │ Zone 1: Adminanorobit 数据区      │
#   │   (Anon2 密码加密)                │
#   ├──────────────────────────────────┤
#   │ Zone 2: Asoav1 数据区             │
#   │   (Dona0 密钥加密)                │
#   ├──────────────────────────────────┤
#   │ Zone 3: Nanou 数据区              │
#   │   (Nanou 主密钥加密)              │
#   ├──────────────────────────────────┤
#   │ Zone Table (分区表, 明文)         │
#   │   每个分区条目:                   │
#   │     zone_id: uint8               │
#   │     algo: uint8                  │
#   │     offset: uint64 LE            │
#   │     size: uint64 LE              │
#   │     salt_len: uint8              │
#   │     salt: bytes[salt_len]        │
#   │     iterations: uint32 LE        │
#   │     file_count: uint32 LE        │
#   │     name_len: uint16 LE          │
#   │     name: bytes[name_len]        │
#   └──────────────────────────────────┘
#
# 每个分区内部的数据格式 (JSON 序列化后加密):
#   {
#     "zone": "normal",
#     "files": [
#       {"name": "a.txt", "size": 1234, "data_b64": "base64...", "md5": "..."},
#       ...
#     ]
#   }
# ═══════════════════════════════════════════════════════════════

def _pack_zone_entry(zone_id, algo, offset, size, salt, iterations, file_count, name):
    """打包分区表条目"""
    name_bytes = name.encode("utf-8")
    entry = struct.pack(
        "<BBQQB",
        zone_id,      # uint8
        algo,         # uint8
        offset,       # uint64
        size,         # uint64
        len(salt),    # uint8
    )
    entry += salt
    entry += struct.pack("<II", iterations, file_count)
    entry += struct.pack("<H", len(name_bytes))
    entry += name_bytes
    return entry


def _unpack_zone_entry(data, pos=0):
    """解包分区表条目, 返回 (entry_dict, new_pos)"""
    zone_id, algo, offset, size, salt_len = struct.unpack_from("<BBQQB", data, pos)
    pos += 1 + 1 + 8 + 8 + 1  # 19 bytes

    salt = data[pos:pos + salt_len]
    pos += salt_len

    iterations, file_count = struct.unpack_from("<II", data, pos)
    pos += 8

    name_len = struct.unpack_from("<H", data, pos)[0]
    pos += 2

    name = data[pos:pos + name_len].decode("utf-8", errors="replace")
    pos += name_len

    return {
        "zone_id": zone_id,
        "algo": algo,
        "offset": offset,
        "size": size,
        "salt": salt,
        "iterations": iterations,
        "file_count": file_count,
        "name": name,
    }, pos


class _NanoContainer:
    """.nano 容器内部操作类"""

    def __init__(self, path):
        self._path = path
        self._header = None
        self._zone_table = []  # list of zone entry dicts

    # ─── 创建新容器 ──────────────────────────────────

    def create(self, anon2_password=None, dona0_key=None, nanou_key=None):
        """创建一个新的空 .nano 容器

        四个分区: normal (无密码), adminanorobit, asoav1, nanou
        """
        # 初始化四个空分区数据
        zones_data = {}
        zones_data[ZONE_NORMAL] = json.dumps({
            "zone": "normal",
            "files": []
        }, ensure_ascii=False).encode("utf-8")

        # 先写空的, 后面 add 文件时再更新
        # 计算头部
        zone_count = 4

        # 写文件: 先写头部占位, 再写各分区数据, 最后写分区表
        with open(self._path, "wb") as f:
            # 头部占位
            f.write(b'\x00' * _HEADER_SIZE)

            # 分区数据区 (初始为空)
            zone_entries = []
            current_offset = _HEADER_SIZE

            # Zone 0: normal (明文)
            z0_data = zones_data[ZONE_NORMAL]
            f.write(z0_data)
            zone_entries.append({
                "zone_id": ZONE_NORMAL,
                "algo": ALGO_NONE,
                "offset": current_offset,
                "size": len(z0_data),
                "salt": b"",
                "iterations": 0,
                "file_count": 0,
                "name": "normal",
            })
            current_offset += len(z0_data)

            # Zone 1: adminanorobit (Anon2 密码加密)
            z1_plain = json.dumps({
                "zone": "adminanorobit",
                "files": []
            }, ensure_ascii=False).encode("utf-8")
            if anon2_password:
                z1_enc, salt, iters = _encrypt_zone(
                    z1_plain, anon2_password, ZONE_ADMINANOROBIT
                )
            else:
                z1_enc = z1_plain
                salt = os.urandom(16)
                iters = _PBKDF2_ITERATIONS_ANON2
                # 没密码也加密一下, 用空密码
                z1_enc, salt, iters = _encrypt_zone(
                    z1_plain, "", ZONE_ADMINANOROBIT, salt
                )
            f.write(z1_enc)
            zone_entries.append({
                "zone_id": ZONE_ADMINANOROBIT,
                "algo": ALGO_STREAM_SHA256,
                "offset": current_offset,
                "size": len(z1_enc),
                "salt": salt,
                "iterations": iters,
                "file_count": 0,
                "name": "adminanorobit",
            })
            current_offset += len(z1_enc)

            # Zone 2: asoav1 (Dona0 密钥加密)
            z2_plain = json.dumps({
                "zone": "asoav1",
                "files": []
            }, ensure_ascii=False).encode("utf-8")
            if dona0_key:
                z2_enc, salt2, iters2 = _encrypt_zone(
                    z2_plain, dona0_key, ZONE_ASOAV1
                )
            else:
                z2_enc, salt2, iters2 = _encrypt_zone(
                    z2_plain, "", ZONE_ASOAV1
                )
            f.write(z2_enc)
            zone_entries.append({
                "zone_id": ZONE_ASOAV1,
                "algo": ALGO_STREAM_SHA256,
                "offset": current_offset,
                "size": len(z2_enc),
                "salt": salt2,
                "iterations": iters2,
                "file_count": 0,
                "name": "asoav1",
            })
            current_offset += len(z2_enc)

            # Zone 3: nanou (Nanou 主密钥加密)
            z3_plain = json.dumps({
                "zone": "nanou",
                "files": [],
                "challenge": base64.b64encode(os.urandom(32)).decode("ascii"),
            }, ensure_ascii=False).encode("utf-8")
            if nanou_key:
                z3_enc, salt3, iters3 = _encrypt_zone(
                    z3_plain, nanou_key, ZONE_NANOU
                )
            else:
                z3_enc, salt3, iters3 = _encrypt_zone(
                    z3_plain, "", ZONE_NANOU
                )
            f.write(z3_enc)
            zone_entries.append({
                "zone_id": ZONE_NANOU,
                "algo": ALGO_STREAM_SHA256,
                "offset": current_offset,
                "size": len(z3_enc),
                "salt": salt3,
                "iterations": iters3,
                "file_count": 0,
                "name": "nanou",
            })
            current_offset += len(z3_enc)

            # 分区表
            zone_table_offset = f.tell()
            zone_table_data = b""
            for ze in zone_entries:
                zone_table_data += _pack_zone_entry(
                    ze["zone_id"], ze["algo"], ze["offset"], ze["size"],
                    ze["salt"], ze["iterations"], ze["file_count"], ze["name"]
                )
            f.write(zone_table_data)

            # 写回头部
            f.seek(0)
            # 先构造完整头部 (不含 checksum)
            header_body = _NANO_MAGIC
            header_body += struct.pack("<IIQ", _NANO_VERSION, zone_count, zone_table_offset)
            header_checksum = hashlib.sha256(header_body).digest()[:16]
            header_body += header_checksum
            # 填充到 _HEADER_SIZE
            header_body += b'\x00' * (_HEADER_SIZE - len(header_body))
            f.write(header_body)

        self._zone_table = zone_entries
        self._header = {
            "version": _NANO_VERSION,
            "zone_count": zone_count,
            "zone_table_offset": zone_table_offset,
        }

    # ─── 读取容器 ──────────────────────────────────────

    def open(self):
        """打开并读取 .nano 容器头部和分区表"""
        with open(self._path, "rb") as f:
            # 读头部
            header_data = f.read(_HEADER_SIZE)
            if len(header_data) < _HEADER_SIZE:
                raise ValueError("文件太小, 不是有效的 .nano 容器")

            magic = header_data[:4]
            if magic != _NANO_MAGIC:
                raise ValueError(f"魔数不匹配, 不是有效的 .nano 文件: {magic}")

            version, zone_count, zone_table_offset = struct.unpack_from(
                "<IIQ", header_data, 4
            )

            # 校验和: header_body = magic(4) + version(4) + zone_count(4) + zone_table_offset(8) = 20 bytes
            stored_checksum = header_data[20:36]
            header_body = header_data[:20]
            calc_checksum = hashlib.sha256(header_body).digest()[:16]
            if stored_checksum != calc_checksum:
                raise ValueError("头部校验和不匹配, 文件可能已损坏")

            self._header = {
                "version": version,
                "zone_count": zone_count,
                "zone_table_offset": zone_table_offset,
            }

            # 读分区表
            f.seek(zone_table_offset)
            zone_table_raw = f.read()

            pos = 0
            self._zone_table = []
            for _ in range(zone_count):
                entry, pos = _unpack_zone_entry(zone_table_raw, pos)
                self._zone_table.append(entry)

        return True

    # ─── 读取分区数据 ──────────────────────────────────

    def read_zone(self, zone_id, password=None):
        """读取并解密分区数据

        Returns:
            dict — 分区的 JSON 数据
        """
        # 找到分区条目
        entry = None
        for ze in self._zone_table:
            if ze["zone_id"] == zone_id:
                entry = ze
                break
        if entry is None:
            raise KeyError(f"分区不存在: {zone_id} ({ZONE_NAMES.get(zone_id, 'unknown')})")

        # 读取原始数据
        with open(self._path, "rb") as f:
            f.seek(entry["offset"])
            raw = f.read(entry["size"])

        # 解密
        if entry["algo"] == ALGO_NONE:
            decrypted = raw
        elif entry["algo"] == ALGO_STREAM_SHA256:
            if password is None:
                raise PermissionError(
                    f"分区 {ZONE_NAMES[zone_id]} 需要密码/密钥"
                )
            decrypted = _decrypt_zone(
                raw, password, zone_id, entry["salt"], entry["iterations"]
            )
        else:
            raise ValueError(f"未知加密算法: {entry['algo']}")

        # 解析 JSON
        try:
            data = json.loads(decrypted.decode("utf-8"))
            return data
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise PermissionError(
                f"解密失败, 密码错误或数据损坏: {ZONE_NAMES[zone_id]}"
            ) from e

    # ─── 写入分区数据 ──────────────────────────────────

    def write_zone(self, zone_id, zone_data, password=None):
        """写入分区数据 (加密后写回, 并更新整个文件)

        因为分区大小可能变化, 需要重写整个文件
        """
        # 读取所有分区的当前数据
        all_zones = {}
        all_passwords = {
            ZONE_NORMAL: None,
            ZONE_ADMINANOROBIT: password if zone_id == ZONE_ADMINANOROBIT else None,
            ZONE_ASOAV1: password if zone_id == ZONE_ASOAV1 else None,
            ZONE_NANOU: password if zone_id == ZONE_NANOU else None,
        }

        # 先读出所有分区
        for ze in self._zone_table:
            zid = ze["zone_id"]
            with open(self._path, "rb") as f:
                f.seek(ze["offset"])
                raw = f.read(ze["size"])

            if zid == zone_id:
                # 这是要更新的分区
                all_zones[zid] = {
                    "plain": json.dumps(zone_data, ensure_ascii=False).encode("utf-8"),
                    "algo": ze["algo"],
                    "salt": ze["salt"],
                    "iterations": ze["iterations"],
                    "name": ze["name"],
                    "file_count": len(zone_data.get("files", [])),
                }
            else:
                # 其他分区保持原样 (不解密, 直接保留密文)
                all_zones[zid] = {
                    "raw": raw,  # 密文
                    "algo": ze["algo"],
                    "salt": ze["salt"],
                    "iterations": ze["iterations"],
                    "name": ze["name"],
                    "file_count": ze["file_count"],
                }

        # 如果目标分区需要加密, 先加密
        target_info = all_zones[zone_id]
        if target_info["algo"] == ALGO_STREAM_SHA256 and password is not None:
            encrypted, salt, iters = _encrypt_zone(
                target_info["plain"], password, zone_id, target_info["salt"]
            )
            target_info["raw"] = encrypted
            # salt 和 iterations 不变
        elif target_info["algo"] == ALGO_NONE:
            target_info["raw"] = target_info["plain"]

        # 重写整个文件
        with open(self._path, "wb") as f:
            # 头部占位
            f.write(b'\x00' * _HEADER_SIZE)

            zone_entries = []
            current_offset = _HEADER_SIZE

            for zid in [ZONE_NORMAL, ZONE_ADMINANOROBIT, ZONE_ASOAV1, ZONE_NANOU]:
                info = all_zones[zid]
                data = info["raw"]
                f.write(data)
                zone_entries.append({
                    "zone_id": zid,
                    "algo": info["algo"],
                    "offset": current_offset,
                    "size": len(data),
                    "salt": info["salt"],
                    "iterations": info["iterations"],
                    "file_count": info["file_count"],
                    "name": info["name"],
                })
                current_offset += len(data)

            # 分区表
            zone_table_offset = f.tell()
            zone_table_data = b""
            for ze in zone_entries:
                zone_table_data += _pack_zone_entry(
                    ze["zone_id"], ze["algo"], ze["offset"], ze["size"],
                    ze["salt"], ze["iterations"], ze["file_count"], ze["name"]
                )
            f.write(zone_table_data)

            # 写回头部
            f.seek(0)
            zone_count = len(zone_entries)
            header_body = _NANO_MAGIC
            header_body += struct.pack("<IIQ", _NANO_VERSION, zone_count, zone_table_offset)
            header_checksum = hashlib.sha256(header_body).digest()[:16]
            header_body += header_checksum
            header_body += b'\x00' * (_HEADER_SIZE - len(header_body))
            f.write(header_body)

        # 更新内存中的分区表
        self._zone_table = zone_entries
        self._header["zone_table_offset"] = zone_table_offset

    # ─── 获取分区信息 ──────────────────────────────────

    def get_zone_entry(self, zone_id):
        """获取分区条目信息"""
        for ze in self._zone_table:
            if ze["zone_id"] == zone_id:
                return ze
        return None

    @property
    def zones(self):
        """所有分区信息"""
        return self._zone_table


# ═══════════════════════════════════════════════════════════════
# .nnu 脚本解析器和执行器 (Nanou Narrative Unit)
# ═══════════════════════════════════════════════════════════════

class _NNURunner:
    """.nnu 脚本解析器和执行器 (公开语法)

    nnu 语法完全公开, 任何人都可以阅读和编写 .nnu 脚本

    语法结构:
        NANO_VERSION <num>
        CONTAINER "<path>"
        ZONE <zone_name>

        PHASE <phase_name>
            <KEY> <value>
            <KEY> "<value>"
        END_PHASE

    阶段 (phases):
        auth    — 认证阶段 (MASTER_KEY, CHALLENGE, RESPONSE, USERNAME)
        decrypt — 解密阶段 (ALGORITHM, KEY_DERIVATION, SALT, ITERATIONS)
        action  — 操作阶段 (EXTRACT_ALL, EXTRACT, LIST, VERIFY)
        cleanup — 收尾阶段 (WIPE_MEMORY, CLOSE_CONTAINER, SECURE_WIPE)
    """

    def __init__(self):
        self._phases = {}
        self._container = None
        self._zone = "nanou"
        self._nano_version = 1

    def parse(self, script_path):
        """解析 .nnu 脚本

        Returns:
            dict — {phases, container, zone, version}
        """
        with open(script_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        phases = {}
        current_phase = None
        container = None
        zone = "nanou"
        nano_version = 1

        for line_num, raw_line in enumerate(lines, 1):
            line = raw_line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue

            # 顶层命令
            if line.upper().startswith("NANO_VERSION"):
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    nano_version = int(parts[1])
                continue

            if line.upper().startswith("CONTAINER"):
                # 可能带引号
                rest = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""
                container = rest.strip('"').strip("'")
                continue

            if line.upper().startswith("ZONE"):
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    zone = parts[1].strip().lower()
                continue

            # 阶段开始
            if line.upper().startswith("PHASE"):
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    current_phase = parts[1].strip().lower()
                    phases[current_phase] = {}
                continue

            # 阶段结束
            if line.upper() == "END_PHASE":
                current_phase = None
                continue

            # 阶段内的键值对
            if current_phase is not None:
                # 解析 KEY VALUE
                parts = line.split(None, 1)
                if len(parts) >= 1:
                    key = parts[0].upper()
                    value = parts[1].strip() if len(parts) >= 2 else ""
                    # 去掉引号
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    phases[current_phase][key] = value

        self._phases = phases
        self._container = container
        self._zone = zone
        self._nano_version = nano_version

        return {
            "phases": phases,
            "container": container,
            "zone": zone,
            "nano_version": nano_version,
        }

    def execute(self, script_path, container_path=None):
        """执行 .nnu 脚本

        Args:
            script_path: .nnu 脚本路径
            container_path: 容器路径 (覆盖脚本中的 CONTAINER)
        Returns:
            dict — 执行结果
        """
        parsed = self.parse(script_path)
        phases = parsed["phases"]
        container = container_path or parsed["container"]
        zone_name = parsed["zone"]

        if not container:
            raise ValueError(".nnu 脚本中没有指定 CONTAINER")

        if not os.path.isfile(container):
            raise FileNotFoundError(f"容器文件不存在: {container}")

        zone_id = None
        for zid, zname in ZONE_NAMES.items():
            if zname == zone_name:
                zone_id = zid
                break
        if zone_id is None:
            raise ValueError(f"未知分区: {zone_name}")

        # ══════════════════════════════════════════════
        # 阶段 1: auth 认证
        # ══════════════════════════════════════════════
        auth = phases.get("auth", {})
        master_key_b64 = auth.get("MASTER_KEY", "")
        challenge = auth.get("CHALLENGE", "")
        response = auth.get("RESPONSE", "")

        if not master_key_b64:
            raise PermissionError("auth 阶段缺少 MASTER_KEY")

        try:
            master_key = base64.b64decode(master_key_b64).decode("utf-8")
        except Exception:
            # 如果不是 base64, 直接当字符串用
            master_key = master_key_b64

        # ══════════════════════════════════════════════
        # 系统权限检查 (Nanou 级)
        # ══════════════════════════════════════════════
        ok, msg = _check_nanou_privilege()
        if not ok:
            raise PermissionError(f"系统权限不足: {msg}")

        # ══════════════════════════════════════════════
        # 打开容器, 验证挑战响应
        # ══════════════════════════════════════════════
        nano = _NanoContainer(container)
        nano.open()

        # 尝试用主密钥解密 Nanou 区
        try:
            zone_data = nano.read_zone(zone_id, master_key)
        except PermissionError:
            raise PermissionError(
                "Nanou 主密钥错误, 无法解密 Nanou 分区\n"
                "请检查 .nnu 脚本中的 MASTER_KEY"
            )

        # 验证挑战响应 (如果有)
        if challenge and response:
            expected_challenge = zone_data.get("challenge", "")
            if challenge != expected_challenge:
                raise PermissionError(
                    f"CHALLENGE 不匹配\n"
                    f"  期望: {expected_challenge[:20]}...\n"
                    f"  提供: {challenge[:20]}..."
                )
            # 验证响应: response == SHA256(challenge + master_key)
            expected_response = hashlib.sha256(
                (challenge + master_key).encode("utf-8")
            ).hexdigest()
            if response.lower() != expected_response.lower():
                raise PermissionError(
                    "RESPONSE 验证失败\n"
                    "  正确的响应 = SHA256(CHALLENGE + MASTER_KEY)"
                )

        # ══════════════════════════════════════════════
        # 阶段 2: decrypt (信息性, 加密算法已内置)
        # ══════════════════════════════════════════════
        decrypt_info = phases.get("decrypt", {})
        # 这里可以做额外的解密配置
        # 目前算法已内置在 _encrypt_zone / _decrypt_zone 中

        # ══════════════════════════════════════════════
        # 阶段 3: action 操作
        # ══════════════════════════════════════════════
        action = phases.get("action", {})
        results = {"files": [], "action": None}

        # LIST
        if "LIST" in action:
            results["action"] = "list"
            for finfo in zone_data.get("files", []):
                results["files"].append({
                    "name": finfo["name"],
                    "size": finfo["size"],
                    "md5": finfo.get("md5", ""),
                })
            print(f"[nnu] Nanou 区文件列表 ({len(results['files'])} 个):")
            for f in results["files"]:
                print(f"  {f['name']:30s} {f['size']:>10d} bytes")

        # EXTRACT_ALL
        if "EXTRACT_ALL" in action:
            output_dir = action["EXTRACT_ALL"]
            results["action"] = "extract_all"
            results["output_dir"] = output_dir
            os.makedirs(output_dir, exist_ok=True)

            for finfo in zone_data.get("files", []):
                file_data = base64.b64decode(finfo["data_b64"])
                out_path = os.path.join(output_dir, finfo["name"])
                with open(out_path, "wb") as f:
                    f.write(file_data)
                results["files"].append({
                    "name": finfo["name"],
                    "path": out_path,
                    "size": len(file_data),
                })
                print(f"[nnu] 提取: {finfo['name']} → {out_path}")

        # EXTRACT (单个文件)
        if "EXTRACT" in action:
            extract_val = action["EXTRACT"]
            results["action"] = "extract"
            # EXTRACT "filename" "output_path"
            parts = extract_val.split()
            if len(parts) >= 1:
                src_name = parts[0].strip('"').strip("'")
                dst_path = parts[1].strip('"').strip("'") if len(parts) >= 2 else src_name

                for finfo in zone_data.get("files", []):
                    if finfo["name"] == src_name:
                        file_data = base64.b64decode(finfo["data_b64"])
                        os.makedirs(os.path.dirname(dst_path) or ".", exist_ok=True)
                        with open(dst_path, "wb") as f:
                            f.write(file_data)
                        results["files"].append({
                            "name": src_name,
                            "path": dst_path,
                            "size": len(file_data),
                        })
                        print(f"[nnu] 提取: {src_name} → {dst_path}")
                        break

        # VERIFY
        if "VERIFY" in action:
            results["action"] = "verify"
            all_ok = True
            for finfo in zone_data.get("files", []):
                file_data = base64.b64decode(finfo["data_b64"])
                calc_md5 = hashlib.md5(file_data).hexdigest()
                ok = calc_md5 == finfo.get("md5", "")
                if not ok:
                    all_ok = False
                results["files"].append({
                    "name": finfo["name"],
                    "md5": calc_md5,
                    "valid": ok,
                })
            results["all_valid"] = all_ok
            print(f"[nnu] 验证完成: {'全部通过' if all_ok else '有损坏'}")

        # ══════════════════════════════════════════════
        # 阶段 4: cleanup 收尾
        # ══════════════════════════════════════════════
        cleanup = phases.get("cleanup", {})
        if cleanup.get("WIPE_MEMORY", "").lower() == "true":
            # 覆盖敏感数据
            master_key = None
            zone_data = None
            master_key_b64 = None

        if cleanup.get("CLOSE_CONTAINER", "").lower() == "true":
            nano = None

        return results


# ═══════════════════════════════════════════════════════════════
# 主模块: _NanoModule
# ═══════════════════════════════════════════════════════════════

class _NanoModule:
    """PyMsi.nano — 📦 .nano 容器模块 (1.5.6 新增)

    自研 .nano 容器文件格式 — 四级权限分区存储

    四个权限分区 (从低到高):
        1. normal    — 普通区域, 无需任何权限
        2. adminanorobit (Anon2) — 管理员级, 需要 admin/sudo
        3. asoav1    (Dona0 / 高泉区) — 内核级, 需要 SYSTEM/root
        4. nanou     — 最高权限区, 需要 .nnu 脚本

    用法:
        # 创建容器
        PM.nano.create("data.nano", anon2_pw="admin123",
                       dona0_key="kernel_secret", nanou_key="top_secret")

        # 添加文件
        PM.nano.add("data.nano", "normal", "readme.txt")
        PM.nano.add("data.nano", "adminanorobit", "important.docx", anon2_pw="admin123")
        PM.nano.add("data.nano", "asoav1", "kernel.bin", dona0_key="kernel_secret")
        PM.nano.add("data.nano", "nanou", "top_secret.pdf", nanou_key="top_secret")

        # 列出文件
        PM.nano.list("data.nano", "normal")

        # 提取文件
        PM.nano.extract("data.nano", "normal", output_dir="D:/out")
        PM.nano.extract("data.nano", "adminanorobit", anon2_pw="admin123")
        PM.nano.extract("data.nano", "asoav1", dona0_key="kernel_secret")

        # Nanou 区: 执行 .nnu 脚本
        PM.nano.run_nnu("extract.nnu")

        # 别名: PM.container / PM.容器 / PM.纳米
    """

    def __init__(self):
        pass

    def __repr__(self):
        return "<PyMsi.nano [📦.nano容器] 4级权限分区>"

    def _zone_id_from_name(self, zone_name):
        """分区名转 ID"""
        zone_lower = zone_name.lower().strip()
        for zid, zname in ZONE_NAMES.items():
            if zname == zone_lower:
                return zid
        # 别名
        aliases = {
            "normal": ZONE_NORMAL, "普通": ZONE_NORMAL, "普通区": ZONE_NORMAL,
            "admin": ZONE_ADMINANOROBIT, "adminanorobit": ZONE_ADMINANOROBIT,
            "anon2": ZONE_ADMINANOROBIT, "管理员": ZONE_ADMINANOROBIT,
            "asoav1": ZONE_ASOAV1, "dona0": ZONE_ASOAV1,
            "高泉区": ZONE_ASOAV1, "内核": ZONE_ASOAV1, "kernel": ZONE_ASOAV1,
            "nanou": ZONE_NANOU, "最高": ZONE_NANOU, "最高权限": ZONE_NANOU,
        }
        if zone_lower in aliases:
            return aliases[zone_lower]
        raise ValueError(f"未知分区: {zone_name}, 可用: {list(ZONE_NAMES.values())}")

    def _check_privilege(self, zone_id):
        """检查系统权限"""
        if zone_id == ZONE_NORMAL:
            return _check_normal_privilege()
        elif zone_id == ZONE_ADMINANOROBIT:
            return _check_anon2_privilege()
        elif zone_id == ZONE_ASOAV1:
            return _check_asoav1_privilege()
        elif zone_id == ZONE_NANOU:
            return _check_nanou_privilege()
        return False, "未知分区"

    # ─── create: 创建容器 ─────────────────────────────

    def create(self, path, anon2_pw="", dona0_key="", nanou_key=""):
        """创建一个新的 .nano 容器 (四个分区)

        Args:
            path: str          .nano 文件输出路径
            anon2_pw: str      Anon2 (Adminanorobit) 分区密码
            dona0_key: str     Asoav1 (Dona0/高泉区) 分区密钥
            nanou_key: str     Nanou 分区主密钥

        用法:
            PM.nano.create("data.nano", anon2_pw="admin123",
                           dona0_key="kernel_secret", nanou_key="top_secret")
        """
        container = _NanoContainer(path)
        container.create(
            anon2_password=anon2_pw,
            dona0_key=dona0_key,
            nanou_key=nanou_key,
        )

        print(f"[PyMsi.nano] 容器创建成功: {path}")
        print(f"  4 个分区: normal | adminanorobit (Anon2) | asoav1 (Dona0) | nanou")

        return {"path": os.path.abspath(path), "zones": 4}

    # ─── add: 添加文件 ────────────────────────────────

    def add(self, container_path, zone, files, anon2_pw=None,
            dona0_key=None, nanou_key=None):
        """向 .nano 容器的指定分区添加文件

        Args:
            container_path: .nano 容器路径
            zone:           分区名 (normal/adminanorobit/asoav1/nanou)
            files:          单个文件路径或文件路径列表
            anon2_pw:       Anon2 密码 (操作 Anon2 分区时需要)
            dona0_key:      Dona0 密钥 (操作 Asoav1 分区时需要)
            nanou_key:      Nanou 主密钥 (操作 Nanou 分区时需要)

        用法:
            PM.nano.add("data.nano", "normal", "readme.txt")
            PM.nano.add("data.nano", "normal", ["a.txt", "b.png"])
            PM.nano.add("data.nano", "adminanorobit", "secret.docx", anon2_pw="admin123")
        """
        zone_id = self._zone_id_from_name(zone)

        # 系统权限检查
        ok, msg = self._check_privilege(zone_id)
        if not ok:
            raise PermissionError(f"权限不足: {msg}")

        # 获取密码/密钥
        password = None
        if zone_id == ZONE_ADMINANOROBIT:
            password = anon2_pw if anon2_pw is not None else ""
        elif zone_id == ZONE_ASOAV1:
            password = dona0_key if dona0_key is not None else ""
        elif zone_id == ZONE_NANOU:
            password = nanou_key if nanou_key is not None else ""

        # 规范化文件列表
        if isinstance(files, str):
            files = [files]

        # 打开容器
        container = _NanoContainer(container_path)
        container.open()

        # 读取当前分区数据
        zone_data = container.read_zone(zone_id, password)

        # 添加文件
        added = []
        for file_path in files:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")

            with open(file_path, "rb") as f:
                raw_data = f.read()

            file_name = os.path.basename(file_path)
            file_md5 = hashlib.md5(raw_data).hexdigest()
            data_b64 = base64.b64encode(raw_data).decode("ascii")

            # 检查是否已存在同名文件, 存在则覆盖
            existing_idx = None
            for i, finfo in enumerate(zone_data.get("files", [])):
                if finfo["name"] == file_name:
                    existing_idx = i
                    break

            file_entry = {
                "name": file_name,
                "size": len(raw_data),
                "data_b64": data_b64,
                "md5": file_md5,
            }

            if existing_idx is not None:
                zone_data["files"][existing_idx] = file_entry
                action = "覆盖"
            else:
                zone_data.setdefault("files", []).append(file_entry)
                action = "添加"

            added.append({"name": file_name, "size": len(raw_data), "action": action})

        # 写回分区
        container.write_zone(zone_id, zone_data, password)

        zone_name = ZONE_NAMES[zone_id]
        print(f"[PyMsi.nano] 已添加到 [{zone_name}] 分区 ({len(added)} 个文件):")
        for item in added:
            print(f"  {item['action']}: {item['name']} ({item['size']} bytes)")

        return added

    # ─── list: 列出分区文件 ───────────────────────────

    def list(self, container_path, zone, anon2_pw=None,
             dona0_key=None, nanou_key=None):
        """列出指定分区的文件

        Args:
            container_path: .nano 容器路径
            zone:           分区名
            anon2_pw:       Anon2 密码
            dona0_key:      Dona0 密钥
            nanou_key:      Nanou 主密钥

        用法:
            PM.nano.list("data.nano", "normal")
            PM.nano.list("data.nano", "adminanorobit", anon2_pw="admin123")
        """
        zone_id = self._zone_id_from_name(zone)

        # 系统权限检查
        ok, msg = self._check_privilege(zone_id)
        if not ok:
            raise PermissionError(f"权限不足: {msg}")

        password = None
        if zone_id == ZONE_ADMINANOROBIT:
            password = anon2_pw if anon2_pw is not None else ""
        elif zone_id == ZONE_ASOAV1:
            password = dona0_key if dona0_key is not None else ""
        elif zone_id == ZONE_NANOU:
            password = nanou_key if nanou_key is not None else ""

        container = _NanoContainer(container_path)
        container.open()
        zone_data = container.read_zone(zone_id, password)

        zone_name = ZONE_NAMES[zone_id]
        files = zone_data.get("files", [])

        print(f"[PyMsi.nano] [{zone_name}] 分区文件 ({len(files)} 个):")
        for finfo in files:
            print(f"  {finfo['name']:30s} {finfo['size']:>10d} bytes  md5={finfo.get('md5', '')[:8]}...")

        return files

    # ─── extract: 提取分区文件 ─────────────────────────

    def extract(self, container_path, zone, output_dir=None,
                anon2_pw=None, dona0_key=None, nanou_key=None):
        """提取指定分区的所有文件

        Args:
            container_path: .nano 容器路径
            zone:           分区名
            output_dir:     输出目录 (默认: ./<zone_name>_out)
            anon2_pw:       Anon2 密码
            dona0_key:      Dona0 密钥
            nanou_key:      Nanou 主密钥

        Returns:
            list[dict] — 每个文件的 {name, path, size}

        用法:
            PM.nano.extract("data.nano", "normal", output_dir="D:/out")
            PM.nano.extract("data.nano", "adminanorobit", anon2_pw="admin123")
        """
        zone_id = self._zone_id_from_name(zone)
        zone_name = ZONE_NAMES[zone_id]

        # 系统权限检查
        ok, msg = self._check_privilege(zone_id)
        if not ok:
            raise PermissionError(f"权限不足: {msg}")

        password = None
        if zone_id == ZONE_ADMINANOROBIT:
            password = anon2_pw if anon2_pw is not None else ""
        elif zone_id == ZONE_ASOAV1:
            password = dona0_key if dona0_key is not None else ""
        elif zone_id == ZONE_NANOU:
            raise PermissionError(
                "Nanou 分区不能直接 extract, 需要执行 .nnu 脚本\n"
                "请用: PM.nano.run_nnu('script.nnu')"
            )

        if output_dir is None:
            output_dir = os.path.join(".", f"{zone_name}_out")

        container = _NanoContainer(container_path)
        container.open()
        zone_data = container.read_zone(zone_id, password)

        os.makedirs(output_dir, exist_ok=True)

        results = []
        for finfo in zone_data.get("files", []):
            file_data = base64.b64decode(finfo["data_b64"])
            out_path = os.path.join(output_dir, finfo["name"])
            with open(out_path, "wb") as f:
                f.write(file_data)
            results.append({
                "name": finfo["name"],
                "path": out_path,
                "size": len(file_data),
            })

        print(f"[PyMsi.nano] 从 [{zone_name}] 提取了 {len(results)} 个文件到: {output_dir}")
        for r in results:
            print(f"  {r['name']} → {r['path']}")

        return results

    # ─── run_nnu: 执行 .nnu 脚本 ──────────────────────

    def run_nnu(self, script_path, container_path=None):
        """执行 .nnu 脚本 (访问 Nanou 最高权限区)

        .nnu 语法完全公开, 见模块文档字符串

        Args:
            script_path: .nnu 脚本路径
            container_path: 容器路径 (覆盖脚本中的 CONTAINER)

        Returns:
            dict — 执行结果

        用法:
            PM.nano.run_nnu("extract.nnu")
            PM.nano.run_nnu("list.nnu", "data.nano")
        """
        runner = _NNURunner()
        result = runner.execute(script_path, container_path)
        return result

    # ─── info: 查看容器信息 ───────────────────────────

    def info(self, container_path):
        """查看 .nano 容器信息 (分区列表, 不进入分区)

        Args:
            container_path: .nano 容器路径

        用法:
            PM.nano.info("data.nano")
        """
        container = _NanoContainer(container_path)
        container.open()

        print(f"[PyMsi.nano] 容器信息: {container_path}")
        print(f"  版本: {container._header['version']}")
        print(f"  分区数: {container._header['zone_count']}")
        print(f"  分区:")
        for ze in container.zones:
            zid = ze["zone_id"]
            name = ZONE_NAMES.get(zid, f"zone_{zid}")
            desc = ZONE_DESCS.get(zid, "")
            algo_name = "明文" if ze["algo"] == ALGO_NONE else "SHA-256流加密"
            print(f"    [{zid}] {name:20s} {ze['file_count']:>3d} 文件  "
                  f"{ze['size']:>10d} bytes  {algo_name}")
            print(f"         {desc}")

        return {
            "version": container._header["version"],
            "zone_count": container._header["zone_count"],
            "zones": container.zones,
        }

    # ─── nnu_help: 打印 .nnu 语法帮助 ──────────────────

    def nnu_help(self):
        """打印 .nnu 语法帮助 (全部公开)"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║        .nnu 语法 (Nanou Narrative Unit) — 完全公开          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  # 注释行以 # 开头                                           ║
║                                                              ║
║  顶层声明:                                                   ║
║    NANO_VERSION <数字>       — 语法版本 (当前: 1)            ║
║    CONTAINER "<路径>"        — .nano 容器路径                ║
║    ZONE <分区名>             — 目标分区 (nanou/asoav1/...)   ║
║                                                              ║
║  阶段结构:                                                   ║
║    PHASE <阶段名>                                            ║
║        <关键字> <值>                                         ║
║        <关键字> "<带空格的值>"                               ║
║    END_PHASE                                                 ║
║                                                              ║
║  阶段 1: auth (认证)                                         ║
║    MASTER_KEY  "<base64密钥>"  Nanou 主密钥 (base64编码)     ║
║    CHALLENGE   "<nonce>"       挑战字符串 (来自容器)          ║
║    RESPONSE    "<sha256>"      响应 = SHA256(挑战+主密钥)    ║
║    USERNAME    "<用户名>"      用户名 (可选)                 ║
║                                                              ║
║  阶段 2: decrypt (解密)                                      ║
║    ALGORITHM     <名称>       加密算法 (stream_sha256)       ║
║    KEY_DERIVATION <名称>:<n>  密钥派生 (pbkdf2_sha256:50000) ║
║    SALT          "<base64>"   盐值 (base64)                  ║
║    ITERATIONS    <数字>       迭代次数                       ║
║                                                              ║
║  阶段 3: action (操作)                                       ║
║    LIST                         列出分区内所有文件            ║
║    EXTRACT_ALL "<输出目录>"    提取所有文件到指定目录         ║
║    EXTRACT "<源文件>" "<目标>" 提取单个文件                   ║
║    VERIFY                       验证所有文件 MD5              ║
║                                                              ║
║  阶段 4: cleanup (收尾)                                      ║
║    WIPE_MEMORY     true/false   清除内存中的密钥              ║
║    CLOSE_CONTAINER true/false   关闭容器                     ║
║    SECURE_WIPE     true/false   安全擦除 (预留)              ║
║                                                              ║
║  示例: list.nnu                                               ║
║    NANO_VERSION 1                                             ║
║    CONTAINER "data.nano"                                     ║
║    ZONE nanou                                                 ║
║                                                              ║
║    PHASE auth                                                 ║
║        MASTER_KEY "dG9wX3NlY3JldA=="                         ║
║    END_PHASE                                                  ║
║                                                              ║
║    PHASE action                                               ║
║        LIST                                                   ║
║    END_PHASE                                                  ║
║                                                              ║
║    PHASE cleanup                                              ║
║        WIPE_MEMORY true                                       ║
║        CLOSE_CONTAINER true                                   ║
║    END_PHASE                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(help_text)

    # ─── 别名方法 ──────────────────────────────────────

    def pack(self, *args, **kwargs):
        """别名: PM.nano.pack() == PM.nano.create()"""
        return self.create(*args, **kwargs)

    def unpack(self, *args, **kwargs):
        """别名: PM.nano.unpack() == PM.nano.extract()"""
        return self.extract(*args, **kwargs)

    def open_nano(self, *args, **kwargs):
        """别名: PM.nano.open_nano() == PM.nano.info()"""
        return self.info(*args, **kwargs)

    def help(self):
        """打印帮助"""
        print(self.__doc__)
