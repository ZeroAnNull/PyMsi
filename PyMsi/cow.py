"""
cow.py — .cow 文件格式引擎 (v1.9.0)

.cow 格式规范:
  ┌─────────────────────────────────────────────────────────┐
  │  .cow File Format v1.0                                  │
  ├─────────────────────────────────────────────────────────┤
  │  1. 无魔数 (no magic number) — 看不出是什么文件          │
  │  2. 全文纯 base-32 编码 (A-Z, 2-7), 谁看都是乱码         │
  │  3. 去掉 padding (=), 更加混乱                            │
  │  4. 无换行, 无头部, 纯纯就是内容                          │
  │  5. 解码后内容: 原始文件名\x00 + 原始文件二进制            │
  │  6. \x00 空字节分隔文件名和内容                           │
  └─────────────────────────────────────────────────────────┘

打开 .cow 文件的流程:
  1. 读取 .cow → base-32 解码 → 得到 原始文件名 + 原始内容
  2. 写入临时目录
  3. 系统默认程序打开
  4. 用户看完退出
  5. 自动删除临时文件 — 不占内存!

用法:
  import PyMsi as PM
  PM.cow.pack("photo.jpg")            # 打包 → photo.jpg.cow
  PM.cow.unpack("photo.jpg.cow")      # 解包 → photo.jpg
  PM.cow.run("photo.jpg.cow")         # 解包→临时目录→打开→退出后清理
  PM.cow.info("photo.jpg.cow")        # 显示 .cow 文件信息
  PM.cow.encode(b"hello")            # base-32 编码
  PM.cow.decode("NBSWY3DP")           # base-32 解码
  PM.cow.batch_pack(["a.txt","b.txt"])# 批量打包
  PM.cow.verify("photo.jpg.cow")      # 校验完整性
  PM.cow.moo()                        # 🐮
"""

import os
import sys
import base64
import hashlib
import tempfile
import subprocess
import zlib
import shutil


# ═══════════════════════════════════════════════════════════════
# 核心: base-32 编解码 (去掉 padding, 纯乱码)
# ═══════════════════════════════════════════════════════════════

def _b32encode(data):
    """Base-32 编码, 去掉 padding (=), 让内容更加混乱

    base-32 字符集: A-Z + 2-7 (共 32 个字符)
    去掉 = 后, 看起来就是一串无意义的字母数字

    示例:
      _b32encode(b"hello") → "NBSWY3DP"
      _b32encode(b"\\xff\\xd8\\xff") → "74XHRAC"
    """
    encoded = base64.b32encode(data).decode('ascii')
    return encoded.rstrip('=')


def _b32decode(text):
    """Base-32 解码, 自动补 padding

    输入可以带或不带 padding, 都能正确解码
    """
    text = text.strip().replace('\n', '').replace('\r', '').replace(' ', '')
    # 补齐 padding
    padding_needed = (8 - len(text) % 8) % 8
    text += '=' * padding_needed
    return base64.b32decode(text)


# ═══════════════════════════════════════════════════════════════
# pack — 打包文件为 .cow
# ═══════════════════════════════════════════════════════════════

def pack(input_path, output_path=None, compress=False):
    """打包文件为 .cow 格式

    Args:
        input_path: 原始文件路径
        output_path: .cow 输出路径 (默认: 原路径 + .cow)
        compress: 是否启用 zlib 压缩 (更小, 但解码稍慢)

    Returns:
        .cow 文件路径

    示例:
        PM.cow.pack("photo.jpg")              # → photo.jpg.cow
        PM.cow.pack("data.bin", "secret.cow") # → secret.cow
        PM.cow.pack("big.zip", compress=True) # 压缩后打包
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    # 读取原始文件
    with open(input_path, 'rb') as f:
        content = f.read()

    filename = os.path.basename(input_path)

    # 可选压缩
    if compress:
        content = zlib.compress(content, 9)
        # 压缩标记: 在文件名后加 \x01 标记
        decoded = filename.encode('utf-8') + b'\x00\x01' + content
    else:
        decoded = filename.encode('utf-8') + b'\x00\x00' + content

    # base-32 编码 (去掉 padding)
    encoded = _b32encode(decoded)

    # 确定输出路径
    if output_path is None:
        output_path = input_path + '.cow'
    if not output_path.endswith('.cow'):
        output_path += '.cow'

    # 写入 .cow 文件 (纯 ASCII 文本)
    with open(output_path, 'w', encoding='ascii') as f:
        f.write(encoded)

    original_size = os.path.getsize(input_path)
    cow_size = len(encoded)
    ratio = cow_size / original_size * 100 if original_size > 0 else 0

    print(f"[.cow] 打包完成: {output_path}")
    print(f"       原始: {original_size:,} bytes → .cow: {cow_size:,} bytes ({ratio:.0f}%)")

    return output_path


# ═══════════════════════════════════════════════════════════════
# unpack — 解包 .cow 为原始文件
# ═══════════════════════════════════════════════════════════════

def unpack(cow_path, output_dir=None):
    """解包 .cow 文件为原始文件

    Args:
        cow_path: .cow 文件路径
        output_dir: 输出目录 (默认: .cow 同目录)

    Returns:
        解包后的文件路径

    示例:
        PM.cow.unpack("photo.jpg.cow")        # → photo.jpg (同目录)
        PM.cow.unpack("secret.cow", "/tmp")     # → /tmp/原始文件名
    """
    if not os.path.exists(cow_path):
        raise FileNotFoundError(f".cow 文件不存在: {cow_path}")

    # 读取 .cow (纯 base-32 文本)
    with open(cow_path, 'r', encoding='ascii') as f:
        encoded = f.read()

    # base-32 解码
    decoded = _b32decode(encoded)

    # 分割: filename\x00 + flag + content
    null_pos = decoded.index(b'\x00')
    filename = decoded[:null_pos].decode('utf-8')
    flag = decoded[null_pos + 1:null_pos + 2]
    content = decoded[null_pos + 2:]

    # 解压 (如果标记了压缩)
    if flag == b'\x01':
        content = zlib.decompress(content)

    # 确定输出路径
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(cow_path))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    # 写入原始文件
    with open(output_path, 'wb') as f:
        f.write(content)

    print(f"[.cow] 解包完成: {cow_path} → {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# run — 解包→临时目录→打开→退出后清理 (不占内存)
# ═══════════════════════════════════════════════════════════════

def run(cow_path):
    """运行 .cow 文件: 解包到临时目录→打开→退出后自动清理

    完整流程:
      1. 读取 .cow, base-32 解码
      2. 写入系统临时目录
      3. 用系统默认程序打开
      4. 等待用户操作完毕
      5. 自动删除临时文件 — 不占内存!

    Args:
        cow_path: .cow 文件路径

    示例:
        PM.cow.run("photo.jpg.cow")   # 打开图片, 看完后自动清理
        PM.cow.run("doc.pdf.cow")     # 打开 PDF, 看完后自动清理
    """
    if not os.path.exists(cow_path):
        raise FileNotFoundError(f".cow 文件不存在: {cow_path}")

    # 读取并解码
    with open(cow_path, 'r', encoding='ascii') as f:
        encoded = f.read()
    decoded = _b32decode(encoded)

    null_pos = decoded.index(b'\x00')
    filename = decoded[:null_pos].decode('utf-8')
    flag = decoded[null_pos + 1:null_pos + 2]
    content = decoded[null_pos + 2:]

    if flag == b'\x01':
        content = zlib.decompress(content)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix='cow_')
    temp_path = os.path.join(temp_dir, filename)

    # 写入临时文件
    with open(temp_path, 'wb') as f:
        f.write(content)

    print(f"[.cow] 已解码到临时目录: {temp_path}")
    print(f"[.cow] 正在打开...")

    # 系统默认程序打开
    _open_file(temp_path)

    print(f"\n[.cow] 文件已打开, 查看完毕后按回车清理临时文件...")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

    # 清理临时文件
    try:
        os.remove(temp_path)
        os.rmdir(temp_dir)
        print(f"[.cow] 临时文件已清理: {temp_path}")
        print(f"[.cow] 不占内存! 🐮")
    except Exception as e:
        # 强制清理
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"[.cow] 临时目录已强制清理")
        except Exception:
            print(f"[.cow] 警告: 无法清理临时目录: {temp_dir}")


def _open_file(path):
    """用系统默认程序打开文件 (跨平台)"""
    if sys.platform == 'win32':
        # Windows
        os.startfile(path)
    elif sys.platform == 'darwin':
        # macOS
        subprocess.Popen(['open', path])
    else:
        # Linux / 其他
        # 尝试 xdg-open, 如果失败尝试其他方式
        try:
            subprocess.Popen(['xdg-open', path])
        except FileNotFoundError:
            # 备选: 尝试用 python 的 webbrowser
            import webbrowser
            webbrowser.open('file://' + os.path.abspath(path))


# ═══════════════════════════════════════════════════════════════
# info — 显示 .cow 文件信息
# ═══════════════════════════════════════════════════════════════

def info(cow_path):
    """显示 .cow 文件的详细信息

    Args:
        cow_path: .cow 文件路径

    Returns:
        dict: 文件信息 (原始文件名, 原始大小, .cow大小, 压缩标记, SHA256)

    示例:
        info = PM.cow.info("photo.jpg.cow")
        print(info)
    """
    if not os.path.exists(cow_path):
        raise FileNotFoundError(f".cow 文件不存在: {cow_path}")

    cow_size = os.path.getsize(cow_path)

    # 读取并解码头部
    with open(cow_path, 'r', encoding='ascii') as f:
        encoded = f.read()

    decoded = _b32decode(encoded)
    null_pos = decoded.index(b'\x00')
    filename = decoded[:null_pos].decode('utf-8')
    flag = decoded[null_pos + 1:null_pos + 2]
    content = decoded[null_pos + 2:]
    is_compressed = (flag == b'\x01')

    if is_compressed:
        original_content = zlib.decompress(content)
    else:
        original_content = content

    original_size = len(original_content)
    sha256 = hashlib.sha256(original_content).hexdigest()
    ratio = cow_size / original_size * 100 if original_size > 0 else 0

    result = {
        'cow_file': cow_path,
        'original_filename': filename,
        'original_size': original_size,
        'cow_size': cow_size,
        'size_ratio': round(ratio, 1),
        'compressed': is_compressed,
        'sha256': sha256,
        'encoded_preview': encoded[:60] + ('...' if len(encoded) > 60 else ''),
    }

    print(f"[.cow] 文件信息:")
    print(f"  原始文件名: {filename}")
    print(f"  原始大小:   {original_size:,} bytes")
    print(f"  .cow 大小:  {cow_size:,} bytes ({ratio:.1f}%)")
    print(f"  压缩:       {'是' if is_compressed else '否'}")
    print(f"  SHA256:     {sha256[:32]}...")
    print(f"  编码预览:   {result['encoded_preview']}")

    return result


# ═══════════════════════════════════════════════════════════════
# encode / decode — 原始 base-32 编解码
# ═══════════════════════════════════════════════════════════════

def encode(data):
    """将二进制数据 base-32 编码为文本

    Args:
        data: bytes 二进制数据

    Returns:
        str base-32 编码文本 (无 padding)

    示例:
        PM.cow.encode(b"hello")  # → "NBSWY3DP"
        PM.cow.encode(b"\\x00\\xff")  # → "AAASE"
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return _b32encode(data)


def decode(text):
    """将 base-32 文本解码为二进制数据

    Args:
        text: str base-32 编码文本

    Returns:
        bytes 原始二进制数据

    示例:
        PM.cow.decode("NBSWY3DP")  # → b"hello"
    """
    return _b32decode(text)


# ═══════════════════════════════════════════════════════════════
# batch_pack / batch_unpack — 批量操作
# ═══════════════════════════════════════════════════════════════

def batch_pack(file_list, output_dir=None, compress=False):
    """批量打包多个文件为 .cow

    Args:
        file_list: 文件路径列表
        output_dir: .cow 输出目录 (默认: 各文件同目录)
        compress: 是否压缩

    Returns:
        [.cow 文件路径, ...]

    示例:
        PM.cow.batch_pack(["a.txt", "b.jpg", "c.pdf"])
    """
    results = []
    for f in file_list:
        if output_dir:
            name = os.path.basename(f) + '.cow'
            out = os.path.join(output_dir, name)
        else:
            out = None
        results.append(pack(f, output_path=out, compress=compress))
    print(f"[.cow] 批量打包完成: {len(results)} 个文件")
    return results


def batch_unpack(cow_list, output_dir=None):
    """批量解包多个 .cow 文件

    Args:
        cow_list: .cow 文件路径列表
        output_dir: 输出目录

    Returns:
        [解包后文件路径, ...]
    """
    results = []
    for c in cow_list:
        results.append(unpack(c, output_dir=output_dir))
    print(f"[.cow] 批量解包完成: {len(results)} 个文件")
    return results


# ═══════════════════════════════════════════════════════════════
# verify — 校验 .cow 文件完整性
# ═══════════════════════════════════════════════════════════════

def verify(cow_path, original_path=None):
    """校验 .cow 文件完整性

    Args:
        cow_path: .cow 文件路径
        original_path: 原始文件路径 (可选, 用于比对)

    Returns:
        bool 是否完整无损

    示例:
        PM.cow.verify("photo.jpg.cow")
        PM.cow.verify("photo.jpg.cow", "photo.jpg")  # 和原始文件比对
    """
    try:
        with open(cow_path, 'r', encoding='ascii') as f:
            encoded = f.read()
        decoded = _b32decode(encoded)

        null_pos = decoded.index(b'\x00')
        filename = decoded[:null_pos].decode('utf-8')
        flag = decoded[null_pos + 1:null_pos + 2]
        content = decoded[null_pos + 2:]

        if flag == b'\x01':
            content = zlib.decompress(content)

        sha256 = hashlib.sha256(content).hexdigest()

        if original_path and os.path.exists(original_path):
            with open(original_path, 'rb') as f:
                orig_content = f.read()
            orig_sha256 = hashlib.sha256(orig_content).hexdigest()
            match = (sha256 == orig_sha256)
            print(f"[.cow] 校验: {'通过 ✓' if match else '失败 ✗'}")
            print(f"  .cow SHA256:  {sha256}")
            print(f"  原始 SHA256:  {orig_sha256}")
            return match
        else:
            print(f"[.cow] 校验: 通过 ✓ (可正常解码)")
            print(f"  原始文件名: {filename}")
            print(f"  内容大小:   {len(content):,} bytes")
            print(f"  SHA256:     {sha256}")
            return True

    except Exception as e:
        print(f"[.cow] 校验: 失败 ✗ ({e})")
        return False


# ═══════════════════════════════════════════════════════════════
# is_cow — 判断是否为 .cow 文件
# ═══════════════════════════════════════════════════════════════

def is_cow(path):
    """判断文件是否为有效的 .cow 文件

    检查: 扩展名 + 内容是否为合法 base-32

    示例:
        PM.cow.is_cow("photo.jpg.cow")  # → True
        PM.cow.is_cow("photo.jpg")       # → False
    """
    if not path.endswith('.cow'):
        return False
    if not os.path.exists(path):
        return False
    try:
        with open(path, 'r', encoding='ascii') as f:
            content = f.read().strip()
        # 检查是否为合法 base-32 字符
        valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567=')
        if not all(c in valid_chars for c in content):
            return False
        # 尝试解码
        _b32decode(content)
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# list_cows — 列出目录下所有 .cow 文件
# ═══════════════════════════════════════════════════════════════

def list_cows(directory='.'):
    """列出目录下的所有 .cow 文件

    Args:
        directory: 目录路径 (默认当前目录)

    Returns:
        [.cow 文件路径, ...]

    示例:
        PM.cow.list_cows("/home/user")
    """
    results = []
    for name in os.listdir(directory):
        if name.endswith('.cow'):
            full = os.path.join(directory, name)
            if is_cow(full):
                results.append(full)
    return results


# ═══════════════════════════════════════════════════════════════
# to_text / from_text — .cow 内容与文本互转
# ═══════════════════════════════════════════════════════════════

def to_text(cow_path):
    """读取 .cow 文件, 返回 base-32 文本 (不写文件)

    示例:
        text = PM.cow.to_text("photo.jpg.cow")
        print(text)  # 一大串乱码
    """
    with open(cow_path, 'r', encoding='ascii') as f:
        return f.read()


def from_text(text, output_path):
    """从 base-32 文本创建 .cow 文件

    示例:
        PM.cow.from_text("NBSWY3DP...", "photo.cow")
    """
    if not output_path.endswith('.cow'):
        output_path += '.cow'
    with open(output_path, 'w', encoding='ascii') as f:
        f.write(text.strip())
    print(f"[.cow] 从文本创建: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# moo — 🐮
# ═══════════════════════════════════════════════════════════════

def moo():
    """🐮 Moo!

    打印一头牛, 说 Moo!
    """
    cow = r"""
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
    """
    print("        ___")
    print("       /   \\")
    print("      | Moo!|")
    print("       \\___/")
    print(cow)
    return cow


# ═══════════════════════════════════════════════════════════════
# demo — 演示
# ═══════════════════════════════════════════════════════════════

def demo():
    """演示 .cow 格式的完整流程"""
    print()
    print("=" * 60)
    print("  .cow 文件格式演示")
    print("  无魔数 | 纯 base-32 | 看起来就是乱码")
    print("=" * 60)

    import tempfile
    tmpdir = tempfile.mkdtemp(prefix='cow_demo_')

    # 1. 创建测试文件
    test_file = os.path.join(tmpdir, "hello.txt")
    with open(test_file, 'w') as f:
        f.write("Hello, World! This is a test file for .cow format.\n" * 10)
    print(f"\n  [1] 创建测试文件: {test_file}")
    print(f"      原始大小: {os.path.getsize(test_file)} bytes")

    # 2. 打包
    cow_file = pack(test_file)
    print(f"\n  [2] 打包为 .cow: {cow_file}")

    # 3. 查看 .cow 内容 (乱码!)
    with open(cow_file, 'r') as f:
        cow_content = f.read()
    print(f"\n  [3] .cow 文件内容 (乱码):")
    print(f"      {cow_content[:80]}...")
    print(f"      (共 {len(cow_content)} 字符的 base-32)")

    # 4. 查看信息
    print(f"\n  [4] 文件信息:")
    info(cow_file)

    # 5. 解包
    unpacked = unpack(cow_file, output_dir=tmpdir)
    print(f"\n  [5] 解包: {unpacked}")

    # 6. 验证
    print(f"\n  [6] 完整性校验:")
    verify(cow_file, test_file)

    # 7. 编解码演示
    print(f"\n  [7] 原始 base-32 编解码:")
    encoded = encode(b"Hello .cow!")
    decoded = decode(encoded)
    print(f"      encode(b'Hello .cow!') = {encoded}")
    print(f"      decode('{encoded}') = {decoded}")

    # 8. 压缩模式
    big_file = os.path.join(tmpdir, "repeated.txt")
    with open(big_file, 'w') as f:
        f.write("AABBCC" * 1000)
    print(f"\n  [8] 压缩模式:")
    print(f"      原始: {os.path.getsize(big_file)} bytes")
    cow_compressed = pack(big_file, compress=True)
    cow_normal = pack(big_file, compress=False, output_path=os.path.join(tmpdir, "repeated_nocompress.cow"))
    print(f"      不压缩: {os.path.getsize(cow_normal)} bytes")
    print(f"      压缩:   {os.path.getsize(cow_compressed)} bytes")

    # 9. 牛!
    print(f"\n  [9] 🐮")
    moo()

    # 清理
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  .cow 演示完成!")
    print("  PM.cow.pack(file)    → 打包")
    print("  PM.cow.unpack(file)  → 解包")
    print("  PM.cow.run(file)     → 打开后自动清理")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# PyMsi 集成层
# ═══════════════════════════════════════════════════════════════

class _CowModule:
    """PyMsi.cow — .cow 文件格式引擎

    无魔数, 纯 base-32 内容, 看起来就是乱码.
    打开后: 解码→临时目录→系统默认程序打开→退出后自动清理, 不占内存.

    用法:
        PM.cow.pack("photo.jpg")            # 打包 → photo.jpg.cow
        PM.cow.unpack("photo.jpg.cow")      # 解包 → photo.jpg
        PM.cow.run("photo.jpg.cow")         # 打开→退出后自动清理
        PM.cow.info("photo.jpg.cow")        # 显示文件信息
        PM.cow.encode(b"hello")             # base-32 编码
        PM.cow.decode("NBSWY3DP")           # base-32 解码
        PM.cow.batch_pack(["a.txt"])        # 批量打包
        PM.cow.verify("photo.jpg.cow")       # 校验完整性
        PM.cow.is_cow("file.cow")            # 判断是否 .cow
        PM.cow.list_cows(".")               # 列出目录下 .cow
        PM.cow.moo()                         # 🐮
        PM.cow.demo()                        # 演示
    """

    def __repr__(self):
        return "<PyMsi.cow [.cow 文件格式引擎] v1.9.0 🐮>"

    # --- 核心功能 ---
    def pack(self, input_path, output_path=None, compress=False):
        """打包文件为 .cow 格式"""
        return pack(input_path, output_path, compress)

    def unpack(self, cow_path, output_dir=None):
        """解包 .cow 文件"""
        return unpack(cow_path, output_dir)

    def run(self, cow_path):
        """运行 .cow: 解包→临时目录→打开→退出后自动清理"""
        return run(cow_path)

    def info(self, cow_path):
        """显示 .cow 文件信息"""
        return info(cow_path)

    # --- base-32 原始编解码 ---
    def encode(self, data):
        """base-32 编码"""
        return encode(data)

    def decode(self, text):
        """base-32 解码"""
        return decode(text)

    # --- 批量 ---
    def batch_pack(self, file_list, output_dir=None, compress=False):
        """批量打包"""
        return batch_pack(file_list, output_dir, compress)

    def batch_unpack(self, cow_list, output_dir=None):
        """批量解包"""
        return batch_unpack(cow_list, output_dir)

    # --- 工具 ---
    def verify(self, cow_path, original_path=None):
        """校验 .cow 完整性"""
        return verify(cow_path, original_path)

    def is_cow(self, path):
        """判断是否为 .cow 文件"""
        return is_cow(path)

    def list_cows(self, directory='.'):
        """列出目录下所有 .cow 文件"""
        return list_cows(directory)

    def to_text(self, cow_path):
        """读取 .cow 内容为文本"""
        return to_text(cow_path)

    def from_text(self, text, output_path):
        """从文本创建 .cow 文件"""
        return from_text(text, output_path)

    # --- 娱乐 ---
    def moo(self):
        """🐮 Moo!"""
        return moo()

    def demo(self):
        """演示"""
        return demo()
