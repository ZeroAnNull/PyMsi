"""
PyMsi.hex — 文件 Hex 解析模块
==============================
输入文件地址 → 找到对应文件 → 解析 16 进制 → 全部输出到终端

用法:
    import PyMsi as PM

    # 方式一：直接给文件路径，dump 全部 hex 到终端
    PM.hex("C:/some/file.bin")

    # 方式二：在某个目录里按文件名搜索，找到后解析
    PM.hex.find("C:/my_project", "config.dat")

    # 带参数: 控制每行字节数、起始偏移、最大字节数等
    PM.hex.dump("C:/file.bin", bytes_per_line=16, start_offset=0, max_bytes=512)

    # 别名都行:
    #   PM.hexdump(...)  PM.hd(...)   PM.hexview(...)
    #   PM.hex(...)      PM.hex.find / search / locate
    #   PM.hex.dump / view / show / print / parse / read

输出格式 (类似 xxd / hexdump -C):
    00000000: 7F45 4C46 0201 0100 0000 0000 0000 0000  .ELF............
    00000010: 0300 3E00 0100 0000 6055 4800 0000 0000  ..>.....`UH.....
      ↑偏移        ↑16 字节, 每两字节一组             ↑可打印 ASCII
"""

import os
import sys


# ─── 内部工具 ─────────────────────────────────────────────

def _is_printable(b):
    """字节是否可打印 (0x20 ~ 0x7E)"""
    return 0x20 <= b <= 0x7E


def _format_offset(offset, base="hex", width=8):
    """格式化偏移量显示"""
    if base == "dec":
        return str(offset).rjust(width)
    # 默认 hex
    return format(offset, "08X")


def _dump_bytes(data, start_offset=0, bytes_per_line=16,
                group_size=2, show_ascii=True, uppercase=True,
                offset_base="hex", out=sys.stdout):
    """
    把一段 bytes 按 hex dump 格式写入 out 流

    Args:
        data:            bytes 数据
        start_offset:    起始字节偏移 (显示用)
        bytes_per_line:  每行字节数 (默认 16)
        group_size:      每组字节数 (默认 2), 0 = 不分组
        show_ascii:      是否显示右侧 ASCII
        uppercase:       hex 是否大写
        offset_base:     偏移显示进制 'hex' / 'dec'
        out:             输出流 (默认 stdout)
    """
    hex_fmt = "02X" if uppercase else "02x"
    total = len(data)
    pos = 0

    while pos < total:
        line_bytes = data[pos:pos + bytes_per_line]
        line_len = len(line_bytes)

        # 偏移
        offset_str = _format_offset(start_offset + pos, base=offset_base)
        parts = [f"{offset_str}:"]

        # hex 部分
        hex_parts = []
        for i in range(bytes_per_line):
            if i < line_len:
                hex_parts.append(format(line_bytes[i], hex_fmt))
            else:
                hex_parts.append("  ")  # 对齐空位

        # 分组
        if group_size and group_size > 0:
            grouped = []
            for i in range(0, bytes_per_line, group_size):
                grouped.append("".join(hex_parts[i:i + group_size]))
            hex_line = " ".join(grouped)
        else:
            hex_line = " ".join(hex_parts)

        parts.append(hex_line)

        # ASCII 部分
        if show_ascii:
            ascii_str = ""
            for b in line_bytes:
                ascii_str += chr(b) if _is_printable(b) else "."
            parts.append(ascii_str)

        print("  ".join(parts), file=out)
        pos += bytes_per_line


# ═══════════════════════════════════════════════════════════════
# Hex 模块: PM.hex(...)
# ═══════════════════════════════════════════════════════════════

class _HexModule:
    """
    PyMsi.hex — 文件 Hex 解析模块

      PM.hex("file.bin")         # 直接 dump
      PM.hex.find(dir, name)    # 搜索文件后 dump
      PM.hex.dump(path, ...)    # 带参数 dump
    """

    def __init__(self):
        pass

    def __repr__(self):
        return ("<PyMsi.hex> 文件 Hex 解析 | "
                "hex('文件路径') / hex.find(目录, 文件名) / hex.dump(path, ...)")

    # ─── 主调用: PM.hex(path) ───
    def __call__(self, path, **kwargs):
        """
        输入文件地址, 找到对应文件并解析 hex 全部输出到终端

        Args:
            path:         文件路径 (字符串)
            bytes_per_line: 每行字节数 (默认 16)
            group_size:   每组字节数 (默认 2), 0=不分组
            show_ascii:   是否显示 ASCII 列 (默认 True)
            uppercase:    hex 大写 (默认 True)
            start_offset: 读取起始字节偏移 (默认 0)
            max_bytes:    最多读取字节数 (默认 None=全部)
            offset_base:  偏移显示进制 'hex'/'dec' (默认 'hex')

        Returns:
            成功返回解析的字节数, 失败返回 None
        """
        return self.dump(path, **kwargs)

    # ─── 核心方法 ───
    def dump(self, path, bytes_per_line=16, group_size=2,
             show_ascii=True, uppercase=True,
             start_offset=0, max_bytes=None, offset_base="hex"):
        """
        解析指定文件, 把全部 16 进制输出到终端

        Args:
            path:            文件路径
            bytes_per_line:  每行字节数
            group_size:      每组字节数 (0=不分组)
            show_ascii:      显示 ASCII 列
            uppercase:       hex 大写
            start_offset:     起始字节偏移 (从文件哪个位置开始读)
            max_bytes:        最多读取多少字节 (None=读全部)
            offset_base:     'hex' 或 'dec'

        Returns:
            成功返回解析字节数, 失败返回 None
        """
        # 1) 解析路径, 找到对应文件
        resolved = self._resolve_path(path)
        if resolved is None:
            return None

        # 2) 读取二进制数据
        try:
            file_size = os.path.getsize(resolved)
        except OSError as e:
            print(f"[PyMsi.hex] ✗ 无法获取文件大小: {e}")
            return None

        # 安全限制: 超大文件默认给个上限提示
        if max_bytes is None and file_size > 64 * 1024 * 1024:  # > 64MB
            print(f"[PyMsi.hex] ⚠ 文件较大 ({file_size} 字节, "
                  f"{file_size / 1024 / 1024:.2f} MB), "
                  f"仅解析前 64MB。如需全部请显式传 max_bytes")
            max_bytes = 64 * 1024 * 1024

        try:
            with open(resolved, "rb") as f:
                if start_offset:
                    f.seek(start_offset)
                data = f.read(max_bytes) if max_bytes else f.read()
        except OSError as e:
            print(f"[PyMsi.hex] ✗ 读取文件失败: {e}")
            return None

        # 3) 打印文件头信息
        print("=" * 72)
        print(f"  PyMsi.hex — 文件 Hex 解析")
        print("=" * 72)
        print(f"  文件路径 : {resolved}")
        print(f"  文件大小 : {file_size} 字节 "
              f"({file_size / 1024:.2f} KB)")
        print(f"  解析范围 : 偏移 {start_offset} → "
              f"{start_offset + len(data)} (共 {len(data)} 字节)")
        print(f"  格式     : 每行 {bytes_per_line} 字节, "
              f"每组 {group_size if group_size else bytes_per_line} 字节"
              f"{', 大写' if uppercase else ', 小写'}"
              f"{', 含 ASCII' if show_ascii else ', 无 ASCII'}")
        print("=" * 72)

        # 4) 全部 hex 输出到终端
        _dump_bytes(
            data,
            start_offset=start_offset,
            bytes_per_line=bytes_per_line,
            group_size=group_size,
            show_ascii=show_ascii,
            uppercase=uppercase,
            offset_base=offset_base,
        )

        print("=" * 72)
        print(f"  解析完成: 共输出 {len(data)} 字节")
        print("=" * 72)
        return len(data)

    def find(self, directory, name, **kwargs):
        """
        在目录中递归搜索文件名匹配的文件, 找到后解析 hex

        Args:
            directory: 搜索起始目录
            name:      文件名 (支持大小写不敏感包含匹配)
            **kwargs:  传给 dump() 的参数

        Returns:
            成功返回 (匹配数, 解析字节数), 失败返回 None
        """
        if not os.path.isdir(directory):
            print(f"[PyMsi.hex.find] ✗ 目录不存在: {directory}")
            return None

        name_lower = name.lower()
        matches = []
        for root, dirs, files in os.walk(directory):
            for f in files:
                if name_lower in f.lower():
                    matches.append(os.path.join(root, f))

        if not matches:
            print(f"[PyMsi.hex.find] ✗ 在 {directory} 下未找到匹配 "
                  f"'{name}' 的文件")
            return None

        print(f"[PyMsi.hex.find] 找到 {len(matches)} 个匹配文件:")
        for i, m in enumerate(matches, 1):
            print(f"  {i}. {m}")
        print()

        total_parsed = 0
        for m in matches:
            print(f"\n>>> 解析: {m}")
            r = self.dump(m, **kwargs)
            if r:
                total_parsed += r

        return (len(matches), total_parsed)

    def search(self, directory, name, **kwargs):
        """别名: hex.search(...) = hex.find(...)"""
        return self.find(directory, name, **kwargs)

    def locate(self, directory, name, **kwargs):
        """别名: hex.locate(...) = hex.find(...)"""
        return self.find(directory, name, **kwargs)

    # ─── dump 的别名方法 ───
    def view(self, path, **kwargs):
        """别名: hex.view = hex.dump"""
        return self.dump(path, **kwargs)

    def show(self, path, **kwargs):
        """别名: hex.show = hex.dump"""
        return self.dump(path, **kwargs)

    def print(self, path, **kwargs):
        """别名: hex.print = hex.dump"""
        return self.dump(path, **kwargs)

    def parse(self, path, **kwargs):
        """别名: hex.parse = hex.dump"""
        return self.dump(path, **kwargs)

    def read(self, path, **kwargs):
        """别名: hex.read = hex.dump"""
        return self.dump(path, **kwargs)

    # ─── 辅助: 解析路径, 找到对应文件 ───
    @staticmethod
    def _resolve_path(path):
        """解析路径, 处理不存在 / 是目录的情况"""
        if path is None:
            print("[PyMsi.hex] ✗ 未提供文件路径")
            return None

        # 展开 ~ 和环境变量
        expanded = os.path.expanduser(os.path.expandvars(str(path)))
        # 相对路径转绝对
        abs_path = os.path.abspath(expanded)

        if not os.path.exists(abs_path):
            print(f"[PyMsi.hex] ✗ 文件不存在: {abs_path}")
            print("        提示: 用 hex.find(目录, 文件名) 可在目录中搜索")
            return None

        if os.path.isdir(abs_path):
            print(f"[PyMsi.hex] ⚠ 路径是目录而非文件: {abs_path}")
            print("        已列出目录下文件:")
            try:
                entries = sorted(os.listdir(abs_path))
                for e in entries:
                    full = os.path.join(abs_path, e)
                    tag = "/" if os.path.isdir(full) else ""
                    print(f"          {e}{tag}")
                print("        请用具体文件路径, 或用 hex.find(目录, 文件名) 搜索")
            except OSError as e:
                print(f"        读取目录失败: {e}")
            return None

        return abs_path
