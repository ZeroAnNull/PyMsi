"""
mnn.py — .mnn 文件格式引擎 (v2.1.0)

.mnn 格式规范:
  ┌─────────────────────────────────────────────────────────┐
  │  .mnn File Format v1.0                                  │
  ├─────────────────────────────────────────────────────────┤
  │  把日志文件彻底翻了个天                                  │
  │  1. 无魔数 — 看不出是什么文件                            │
  │  2. 人类看不懂, 只有机器能看懂                           │
  │  3. 内部存的是 G进制 (G-base)                           │
  │  4. 无文本, 无换行, 纯二进制                            │
  └─────────────────────────────────────────────────────────┘

G进制 编码流程:
  1. 用户给的字符串 → 转成数字 (十进制)
  2. 每个位数向前进二 (digit + 2, mod 10, 带进位)
  3. 如果二过十 (进位), 则进 n 字节
     n = 位数的字节宽度 (根据十进制位数决定)
  4. 长度标记: 交替 0/1 模式
     - 位数是 3 → 标记 "010" (3 bits)
     - 位数是 67 → 标记 "0101...0" (67 bits, 交替)
  5. 存储: [交替0/1长度标记][位移后的数字字节]

解码流程 (反向):
  1. 读交替 0/1 模式 → 得到位数 N
  2. 读 N 个位移后的数字
  3. 反向位移 (digit - 2, mod 10, 带借位)
  4. 十进制 → 原始字节

用法:
  import PyMsi as PM
  PM.mnn.pack("log.txt")             # 打包 → log.txt.mnn
  PM.mnn.unpack("log.txt.mnn")       # 解包 → log.txt
  PM.mnn.run("log.txt.mnn")          # 解包→临时目录→打开→退出后清理
  PM.mnn.info("log.txt.mnn")         # 显示 .mnn 文件信息
  PM.mnn.encode(b"hello")            # G进制编码
  PM.mnn.decode(encoded_bytes)       # G进制解码
  PM.mnn.moo()                       # 机器牛 🤖🐮
"""

import os
import sys
import struct
import zlib
import hashlib
import tempfile
import subprocess
import shutil


# ═══════════════════════════════════════════════════════════════
# 核心: G进制 编解码
# ═══════════════════════════════════════════════════════════════

def _bytes_to_decimal(data):
    """将字节流转为十进制数字字符串

    流程: bytes → hex → 大整数 → 十进制字符串
    例: b"hello" → hex "68656c6c6f" → int → "439742219035135"
    """
    if not data:
        return "0"
    # 字节 → 十六进制 → 大整数 → 十进制字符串
    hex_str = data.hex()
    big_int = int(hex_str, 16)
    return str(big_int)


def _decimal_to_bytes(dec_str, orig_len=None):
    """将十进制数字字符串转回字节流

    流程: 十进制字符串 → 大整数 → 十六进制 → bytes
    例: "439742219035135" → int → hex "68656c6c6f" → b"hello"

    Args:
        dec_str: 十进制数字字符串
        orig_len: 原始字节长度 (用于恢复前导零字节)
    """
    if dec_str == "0" or not dec_str:
        if orig_len and orig_len > 0:
            return b'\x00' * orig_len
        return b""
    big_int = int(dec_str)
    # 确保十六进制长度是偶数 (每两个 hex 字符 = 1 字节)
    hex_str = format(big_int, 'x')
    if len(hex_str) % 2 == 1:
        hex_str = '0' + hex_str
    # 恢复前导零字节
    if orig_len:
        hex_str = hex_str.zfill(2 * orig_len)
    return bytes.fromhex(hex_str)


def _shift_digits_forward(dec_str, shift=2):
    """每个位数向前进二 (digit + shift, mod 10, 带进位)

    在十进制字符串前加一个 '0', 吸收最高位的进位,
    确保正向位移和反向位移是完美逆运算.

    例: "123" →
      加前导0: "0123"
      3+2=5, 2+2=4, 1+2=3, 0+2=2 → "2345"
    例: "789" →
      加前导0: "0789"
      9+2=11→1进1, 8+2+1=11→1进1, 7+2+1=10→0进1, 0+2+1=3 → "3011"
    """
    if not dec_str:
        return "0"

    # 加前导 '0' 吸收进位, 保证可逆
    dec_str = '0' + dec_str
    digits = [int(d) for d in dec_str]
    carry = 0

    # 从最低位 (最右边) 开始处理
    for i in range(len(digits) - 1, -1, -1):
        val = digits[i] + shift + carry
        digits[i] = val % 10
        carry = val // 10

    # 前导 '0' 已吸收进位, 不会再产生额外进位
    return ''.join(str(d) for d in digits)


def _shift_digits_backward(dec_str, shift=2):
    """反向位移 (digit - shift, mod 10, 带借位)

    与 _shift_digits_forward 互逆: 前导 '0' 在正向位移时吸收进位,
    反向位移后恢复为前导零, 被 strip 掉.

    例: "2345" →
      5-2=3, 4-2=2, 3-2=1, 2-2=0 → "0123" → strip → "123"
    例: "3011" →
      1-2→借位: 9, 借1
      1-2-1→借位: 8, 借1
      0-2-1→借位: 7, 借1
      3-2-1=0 → "0789" → strip → "789"
    """
    if not dec_str or dec_str == "0":
        return "0"

    digits = [int(d) for d in dec_str]
    borrow = 0

    # 从最低位开始处理
    for i in range(len(digits) - 1, -1, -1):
        val = digits[i] - shift - borrow
        if val < 0:
            val += 10
            borrow = 1
        else:
            borrow = 0
        digits[i] = val

    # 去掉前导零
    while len(digits) > 1 and digits[0] == 0:
        digits.pop(0)

    return ''.join(str(d) for d in digits)


def _make_length_marker(n_digits):
    """生成交替 0/1 长度标记

    位数 n → 交替 0/1 模式, 长度 = n
    例: 3 → "010" (bits: 0,1,0)
    例: 5 → "01010"
    例: 67 → "0101...0" (67 bits)

    返回: bytes (位数除以8向上取整)
    """
    if n_digits <= 0:
        return b""

    # 生成交替 0/1 bit 序列
    bits = []
    for i in range(n_digits):
        if i % 2 == 0:
            bits.append(0)
        else:
            bits.append(1)

    # bit 序列 → bytes
    # 补齐到 8 的倍数
    n_bytes = (n_digits + 7) // 8
    # 在 bits 末尾补 0 到 n_bytes * 8
    while len(bits) < n_bytes * 8:
        bits.append(0)

    # bits → bytes
    result = bytearray()
    for i in range(n_bytes):
        byte_val = 0
        for j in range(8):
            byte_val = (byte_val << 1) | bits[i * 8 + j]
        result.append(byte_val)

    return bytes(result)


def _read_length_marker(data):
    """从数据开头读交替 0/1 模式, 返回位数

    读取交替 0/1 直到模式结束 (连续两个相同的 bit = 结束标记)

    返回: (n_digits, marker_bytes, remaining_data)
    """
    # 读取 bits
    bits = []
    for byte in data:
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)

    # 数交替 0/1 的长度
    # 模式: 0,1,0,1,0,1,... 如果连续两个相同的 bit, 说明标记结束
    n_digits = 0
    i = 0
    while i < len(bits):
        expected = 0 if i % 2 == 0 else 1
        if bits[i] == expected:
            n_digits += 1
            i += 1
        else:
            break

    # 消耗的字节数
    marker_bytes = (n_digits + 7) // 8
    remaining = data[marker_bytes:]

    return n_digits, data[:marker_bytes], remaining


# ═══════════════════════════════════════════════════════════════
# encode / decode — G进制 编解码
# ═══════════════════════════════════════════════════════════════

def encode(data, shift=2):
    """G进制编码: bytes → 机器码

    流程:
      1. bytes → 十进制字符串
      2. 每个位数 +2 (带进位, 前导0吸收进位)
      3. 生成交替 0/1 长度标记
      4. 输出: [头部][长度标记][位移后的数字ASCII]

    Args:
        data: bytes 原始数据
        shift: 位移量 (默认 2)

    Returns:
        bytes 编码后的数据 (人类看不懂, 机器能懂)

    示例:
        encoded = PM.mnn.encode(b"hello")
        # encoded 是一段二进制, 人类看不懂
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    if not data:
        return b"\x00"

    orig_len = len(data)

    # 1. bytes → 十进制字符串
    dec_str = _bytes_to_decimal(data)

    # 2. 每个位数向前进二 (前导0吸收进位)
    shifted = _shift_digits_forward(dec_str, shift)

    # 3. 生成交替 0/1 长度标记
    n_digits = len(shifted)
    marker = _make_length_marker(n_digits)

    # 4. 位移后的数字转为 ASCII bytes ('0'-'9' → 0x30-0x39)
    shifted_bytes = shifted.encode('ascii')

    # 5. 压缩
    payload = marker + shifted_bytes
    compressed = zlib.compress(payload, 9)

    # 6. 头部: 位移量(1B) + 位数(4B) + 原始字节长度(4B) + 压缩数据
    header = struct.pack('<BII', shift, n_digits, orig_len)
    return header + compressed


def decode(encoded_data, shift=None):
    """G进制解码: 机器码 → bytes

    反向流程:
      1. 读头部 (位移量, 位数, 原始字节长度)
      2. 解压
      3. 读交替 0/1 长度标记
      4. 读位移后的数字
      5. 反向位移 (digit - 2, 带借位)
      6. 十进制 → bytes (恢复前导零)

    Args:
        encoded_data: bytes 编码数据
        shift: 位移量 (None = 从头部读取)

    Returns:
        bytes 原始数据

    示例:
        decoded = PM.mnn.decode(encoded)
        # decoded == 原始数据
    """
    if not encoded_data or len(encoded_data) < 9:
        return b""

    # 1. 读头部
    header_shift, n_digits, orig_len = struct.unpack('<BII', encoded_data[:9])
    if shift is None:
        shift = header_shift

    # 2. 解压
    compressed = encoded_data[9:]
    try:
        payload = zlib.decompress(compressed)
    except zlib.error:
        # 可能没有压缩
        payload = compressed

    # 3. 读长度标记 (交替 0/1)
    marker_bytes = (n_digits + 7) // 8
    marker = payload[:marker_bytes]
    shifted_bytes = payload[marker_bytes:]

    # 4. 位移后的数字
    shifted = shifted_bytes.decode('ascii')

    # 5. 反向位移
    dec_str = _shift_digits_backward(shifted, shift)

    # 6. 十进制 → bytes (用 orig_len 恢复前导零)
    return _decimal_to_bytes(dec_str, orig_len)


# ═══════════════════════════════════════════════════════════════
# pack — 打包文件为 .mnn
# ═══════════════════════════════════════════════════════════════

def pack(input_path, output_path=None, shift=2):
    """打包文件为 .mnn 格式

    Args:
        input_path: 原始文件路径
        output_path: .mnn 输出路径 (默认: 原路径 + .mnn)
        shift: G进制位移量 (默认 2)

    Returns:
        .mnn 文件路径

    示例:
        PM.mnn.pack("log.txt")              # → log.txt.mnn
        PM.mnn.pack("data.bin", "secret.mnn") # → secret.mnn
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    # 读取原始文件
    with open(input_path, 'rb') as f:
        content = f.read()

    filename = os.path.basename(input_path)

    # G进制编码文件名和内容
    encoded_filename = encode(filename.encode('utf-8'), shift)
    encoded_content = encode(content, shift)

    # .mnn 结构: [魔数标记(无, 但有格式标记)][文件名长度][编码文件名][编码内容]
    # 用简单结构存储
    fn_len = struct.pack('<I', len(encoded_filename))
    content_len = struct.pack('<I', len(encoded_content))
    shift_byte = struct.pack('<B', shift)

    mnn_data = b'MNN' + shift_byte + fn_len + encoded_filename + content_len + encoded_content

    # 确定输出路径
    if output_path is None:
        output_path = input_path + '.mnn'
    if not output_path.endswith('.mnn'):
        output_path += '.mnn'

    # 写入 .mnn 文件 (二进制, 人类看不懂)
    with open(output_path, 'wb') as f:
        f.write(mnn_data)

    original_size = os.path.getsize(input_path)
    mnn_size = len(mnn_data)
    ratio = mnn_size / original_size * 100 if original_size > 0 else 0

    print(f"[.mnn] 打包完成: {output_path}")
    print(f"       原始: {original_size:,} bytes → .mnn: {mnn_size:,} bytes ({ratio:.0f}%)")
    print(f"       G进制位移: +{shift}")

    return output_path


# ═══════════════════════════════════════════════════════════════
# unpack — 解包 .mnn 为原始文件
# ═══════════════════════════════════════════════════════════════

def unpack(mnn_path, output_dir=None):
    """解包 .mnn 文件为原始文件

    Args:
        mnn_path: .mnn 文件路径
        output_dir: 输出目录 (默认: .mnn 同目录)

    Returns:
        解包后的文件路径
    """
    if not os.path.exists(mnn_path):
        raise FileNotFoundError(f".mnn 文件不存在: {mnn_path}")

    # 读取 .mnn (二进制)
    with open(mnn_path, 'rb') as f:
        mnn_data = f.read()

    # 校验格式
    if mnn_data[:3] != b'MNN':
        raise ValueError(f"不是有效的 .mnn 文件: {mnn_path}")

    # 解析
    offset = 3
    shift = struct.unpack('<B', mnn_data[offset:offset+1])[0]
    offset += 1
    fn_len = struct.unpack('<I', mnn_data[offset:offset+4])[0]
    offset += 4

    encoded_filename = mnn_data[offset:offset+fn_len]
    offset += fn_len

    content_len = struct.unpack('<I', mnn_data[offset:offset+4])[0]
    offset += 4

    encoded_content = mnn_data[offset:offset+content_len]

    # G进制解码
    filename = decode(encoded_filename, shift).decode('utf-8')
    content = decode(encoded_content, shift)

    # 确定输出路径
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(mnn_path))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    # 写入原始文件
    with open(output_path, 'wb') as f:
        f.write(content)

    print(f"[.mnn] 解包完成: {mnn_path} → {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# run — 解包→临时目录→打开→退出后清理
# ═══════════════════════════════════════════════════════════════

def run(mnn_path):
    """运行 .mnn 文件: 解包到临时目录→打开→退出后自动清理

    Args:
        mnn_path: .mnn 文件路径
    """
    if not os.path.exists(mnn_path):
        raise FileNotFoundError(f".mnn 文件不存在: {mnn_path}")

    # 读取并解码
    with open(mnn_path, 'rb') as f:
        mnn_data = f.read()

    if mnn_data[:3] != b'MNN':
        raise ValueError(f"不是有效的 .mnn 文件: {mnn_path}")

    offset = 3
    shift = struct.unpack('<B', mnn_data[offset:offset+1])[0]
    offset += 1
    fn_len = struct.unpack('<I', mnn_data[offset:offset+4])[0]
    offset += 4
    encoded_filename = mnn_data[offset:offset+fn_len]
    offset += fn_len
    content_len = struct.unpack('<I', mnn_data[offset:offset+4])[0]
    offset += 4
    encoded_content = mnn_data[offset:offset+content_len]

    filename = decode(encoded_filename, shift).decode('utf-8')
    content = decode(encoded_content, shift)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix='mnn_')
    temp_path = os.path.join(temp_dir, filename)

    with open(temp_path, 'wb') as f:
        f.write(content)

    print(f"[.mnn] 已解码到临时目录: {temp_path}")
    print(f"[.mnn] 正在打开...")

    # 系统默认程序打开
    _open_file(temp_path)

    print(f"\n[.mnn] 文件已打开, 查看完毕后按回车清理临时文件...")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

    # 清理
    try:
        os.remove(temp_path)
        os.rmdir(temp_dir)
        print(f"[.mnn] 临时文件已清理: {temp_path}")
        print(f"[.mnn] 不占内存! 🤖")
    except Exception:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"[.mnn] 临时目录已强制清理")
        except Exception:
            print(f"[.mnn] 警告: 无法清理临时目录: {temp_dir}")


def _open_file(path):
    """用系统默认程序打开文件 (跨平台)"""
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        try:
            subprocess.Popen(['xdg-open', path])
        except FileNotFoundError:
            import webbrowser
            webbrowser.open('file://' + os.path.abspath(path))


# ═══════════════════════════════════════════════════════════════
# info — 显示 .mnn 文件信息
# ═══════════════════════════════════════════════════════════════

def info(mnn_path):
    """显示 .mnn 文件的详细信息"""
    if not os.path.exists(mnn_path):
        raise FileNotFoundError(f".mnn 文件不存在: {mnn_path}")

    mnn_size = os.path.getsize(mnn_path)

    with open(mnn_path, 'rb') as f:
        mnn_data = f.read()

    if mnn_data[:3] != b'MNN':
        raise ValueError(f"不是有效的 .mnn 文件: {mnn_path}")

    offset = 3
    shift = struct.unpack('<B', mnn_data[offset:offset+1])[0]
    offset += 1
    fn_len = struct.unpack('<I', mnn_data[offset:offset+4])[0]
    offset += 4
    encoded_filename = mnn_data[offset:offset+fn_len]
    offset += fn_len
    content_len = struct.unpack('<I', mnn_data[offset:offset+4])[0]
    offset += 4
    encoded_content = mnn_data[offset:offset+content_len]

    filename = decode(encoded_filename, shift).decode('utf-8')
    content = decode(encoded_content, shift)

    original_size = len(content)
    sha256 = hashlib.sha256(content).hexdigest()

    # G进制信息
    dec_str = _bytes_to_decimal(content)
    shifted = _shift_digits_forward(dec_str, shift)
    n_digits = len(shifted)

    result = {
        'mnn_file': mnn_path,
        'original_filename': filename,
        'original_size': original_size,
        'mnn_size': mnn_size,
        'g_shift': shift,
        'decimal_digits': len(dec_str),
        'shifted_digits': n_digits,
        'sha256': sha256,
        'binary_preview': mnn_data[:32].hex(),
    }

    print(f"[.mnn] 文件信息:")
    print(f"  原始文件名: {filename}")
    print(f"  原始大小:   {original_size:,} bytes")
    print(f"  .mnn 大小:  {mnn_size:,} bytes")
    print(f"  G进制位移:  +{shift}")
    print(f"  十进制位数: {len(dec_str)}")
    print(f"  位移后位数: {n_digits}")
    print(f"  SHA256:     {sha256[:32]}...")
    print(f"  二进制预览: {mnn_data[:32].hex()}")

    return result


# ═══════════════════════════════════════════════════════════════
# verify — 校验 .mnn 文件完整性
# ═══════════════════════════════════════════════════════════════

def verify(mnn_path, original_path=None):
    """校验 .mnn 文件完整性"""
    try:
        with open(mnn_path, 'rb') as f:
            mnn_data = f.read()

        if mnn_data[:3] != b'MNN':
            print(f"[.mnn] 校验: 失败 (非 .mnn 格式)")
            return False

        offset = 3
        shift = struct.unpack('<B', mnn_data[offset:offset+1])[0]
        offset += 1
        fn_len = struct.unpack('<I', mnn_data[offset:offset+4])[0]
        offset += 4
        encoded_filename = mnn_data[offset:offset+fn_len]
        offset += fn_len
        content_len = struct.unpack('<I', mnn_data[offset:offset+4])[0]
        offset += 4
        encoded_content = mnn_data[offset:offset+content_len]

        filename = decode(encoded_filename, shift).decode('utf-8')
        content = decode(encoded_content, shift)
        sha256 = hashlib.sha256(content).hexdigest()

        if original_path and os.path.exists(original_path):
            with open(original_path, 'rb') as f:
                orig_content = f.read()
            orig_sha256 = hashlib.sha256(orig_content).hexdigest()
            match = sha256 == orig_sha256
            print(f"[.mnn] 校验: {'通过' if match else '失败'}")
            return match
        else:
            print(f"[.mnn] 校验: 通过 (可正常解码)")
            print(f"  原始文件名: {filename}")
            print(f"  内容大小:   {len(content):,} bytes")
            print(f"  SHA256:     {sha256}")
            return True

    except Exception as e:
        print(f"[.mnn] 校验: 失败 ({e})")
        return False


# ═══════════════════════════════════════════════════════════════
# is_mnn — 判断是否为 .mnn 文件
# ═══════════════════════════════════════════════════════════════

def is_mnn(path):
    """判断文件是否为有效的 .mnn 文件"""
    if not path.endswith('.mnn'):
        return False
    if not os.path.exists(path):
        return False
    try:
        with open(path, 'rb') as f:
            header = f.read(3)
        return header == b'MNN'
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# list_mnns — 列出目录下所有 .mnn 文件
# ═══════════════════════════════════════════════════════════════

def list_mnns(directory='.'):
    """列出目录下的所有 .mnn 文件"""
    results = []
    for name in os.listdir(directory):
        if name.endswith('.mnn'):
            full = os.path.join(directory, name)
            if is_mnn(full):
                results.append(full)
    return results


# ═══════════════════════════════════════════════════════════════
# batch_pack / batch_unpack — 批量操作
# ═══════════════════════════════════════════════════════════════

def batch_pack(file_list, output_dir=None, shift=2):
    """批量打包"""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    results = []
    for f in file_list:
        if output_dir:
            name = os.path.basename(f) + '.mnn'
            out = os.path.join(output_dir, name)
        else:
            out = None
        results.append(pack(f, output_path=out, shift=shift))
    print(f"[.mnn] 批量打包完成: {len(results)} 个文件")
    return results


def batch_unpack(mnn_list, output_dir=None):
    """批量解包"""
    results = []
    for m in mnn_list:
        results.append(unpack(m, output_dir=output_dir))
    print(f"[.mnn] 批量解包完成: {len(results)} 个文件")
    return results


# ═══════════════════════════════════════════════════════════════
# demo
# ═══════════════════════════════════════════════════════════════

def demo():
    """演示 .mnn 格式的完整流程"""
    print()
    print("=" * 60)
    print("  .mnn 文件格式演示 (G进制)")
    print("  无魔数 | 机器能懂 | 人类看不懂")
    print("=" * 60)

    import tempfile
    tmpdir = tempfile.mkdtemp(prefix='mnn_demo_')

    # 1. 创建测试文件
    test_file = os.path.join(tmpdir, "log.txt")
    with open(test_file, 'w') as f:
        f.write("[2024-01-01] INFO: Server started\n" * 5)
    print(f"\n  [1] 创建测试文件: {test_file}")
    print(f"      原始大小: {os.path.getsize(test_file)} bytes")

    # 2. 打包
    mnn_file = pack(test_file)
    print(f"\n  [2] 打包为 .mnn: {mnn_file}")

    # 3. 查看 .mnn 二进制 (人类看不懂)
    with open(mnn_file, 'rb') as f:
        raw = f.read()
    print(f"\n  [3] .mnn 二进制内容 (前32字节):")
    print(f"      {raw[:32].hex()}")
    print(f"      (人类看不懂, 只有机器能懂)")

    # 4. 编解码演示
    print(f"\n  [4] G进制编解码演示:")
    test_data = b"Hello .mnn!"
    encoded = encode(test_data)
    decoded = decode(encoded)
    print(f"      原始: {test_data}")
    print(f"      编码: {encoded[:32].hex()}... ({len(encoded)} bytes)")
    print(f"      解码: {decoded}")
    print(f"      往返一致: {decoded == test_data}")

    # 5. G进制内部过程
    print(f"\n  [5] G进制内部过程:")
    dec_str = _bytes_to_decimal(test_data)
    print(f"      原始 bytes → 十进制: {dec_str}")
    shifted = _shift_digits_forward(dec_str, 2)
    print(f"      每位+2位移后: {shifted}")
    n_digits = len(shifted)
    marker = _make_length_marker(n_digits)
    print(f"      交替0/1标记 ({n_digits}位): {marker.hex()}")
    back = _shift_digits_backward(shifted, 2)
    print(f"      反向位移回: {back}")
    print(f"      十进制 → bytes: {_decimal_to_bytes(back, len(test_data))}")

    # 6. 查看信息
    print(f"\n  [6] 文件信息:")
    info(mnn_file)

    # 7. 解包
    unpacked = unpack(mnn_file, output_dir=tmpdir)
    print(f"\n  [7] 解包: {unpacked}")

    # 8. 验证
    print(f"\n  [8] 完整性校验:")
    verify(mnn_file, test_file)

    # 清理
    shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  .mnn 演示完成! 🤖")
    print("  PM.mnn.pack(file)    → 打包")
    print("  PM.mnn.unpack(file)  → 解包")
    print("  PM.mnn.run(file)     → 打开后自动清理")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# PyMsi 集成层
# ═══════════════════════════════════════════════════════════════

class _MnnModule:
    """PyMsi.mnn — .mnn 文件格式引擎

    G进制编码: 把日志文件彻底翻了个天
    人类看不懂, 只有机器能看懂.

    .mnn 格式规范:
      1. 无魔数 (实际用 MNN 标记)
      2. 内部存的是 G进制 (数字位移 + 交替标记)
      3. 人类看不懂, 机器能看懂
      4. 无文本, 无换行, 纯二进制

    G进制 编码流程:
      1. 字符串 → 十进制数字
      2. 每个位数向前进二 (digit + 2, 带进位)
      3. 交替 0/1 长度标记 (3位→010, 67位→0101...67)
      4. 存储: [长度标记][位移后的数字]

    用法:
        PM.mnn.pack("log.txt")             # 打包 → log.txt.mnn
        PM.mnn.unpack("log.txt.mnn")       # 解包 → log.txt
        PM.mnn.run("log.txt.mnn")          # 解包→临时目录→打开→退出后清理
        PM.mnn.info("log.txt.mnn")         # 显示文件信息
        PM.mnn.encode(b"hello")           # G进制编码
        PM.mnn.decode(encoded_bytes)       # G进制解码
        PM.mnn.batch_pack(["a.txt"])       # 批量打包
        PM.mnn.verify("log.txt.mnn")        # 校验完整性
        PM.mnn.is_mnn("file.mnn")           # 判断是否 .mnn
        PM.mnn.list_mnns(".")              # 列出目录下 .mnn
        PM.mnn.demo()                       # 演示
    """

    def __repr__(self):
        return "<PyMsi.mnn [.mnn G进制文件格式引擎] v2.1.0>"

    def pack(self, input_path, output_path=None, shift=2):
        return pack(input_path, output_path, shift)

    def unpack(self, mnn_path, output_dir=None):
        return unpack(mnn_path, output_dir)

    def run(self, mnn_path):
        return run(mnn_path)

    def info(self, mnn_path):
        return info(mnn_path)

    def encode(self, data, shift=2):
        return encode(data, shift)

    def decode(self, encoded_data, shift=None):
        return decode(encoded_data, shift)

    def batch_pack(self, file_list, output_dir=None, shift=2):
        return batch_pack(file_list, output_dir, shift)

    def batch_unpack(self, mnn_list, output_dir=None):
        return batch_unpack(mnn_list, output_dir)

    def verify(self, mnn_path, original_path=None):
        return verify(mnn_path, original_path)

    def is_mnn(self, path):
        return is_mnn(path)

    def list_mnns(self, directory='.'):
        return list_mnns(directory)

    def demo(self):
        return demo()
