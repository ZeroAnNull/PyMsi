"""
hexvid.py — 十六进制 RGB 视频模块 (v1.5.8)

将文本编码为十六进制, 再将每个 hex 数字映射为 RGB 纯色帧, 输出为 AVI 视频

编码规则:
  - 纯白色 (255,255,255) 25帧 = 开头标记 / 空格
  - 每个 hex 数字 (0-9, a-f) = 25帧特定 RGB 颜色
  - 格式: 无压缩 AVI (BGR24, top-down)

颜色映射表:
  0=黑  1=红  2=绿  3=蓝  4=黄  5=品红  6=青  7=橙
  8=紫  9=青柠  a=蓝绿  b=粉  c=深蓝  d=深红  e=橄榄  f=灰

用法:
  import PyMsi as PM
  PM.hexvid("Hello World", output="hello.avi")
  PM.hexvid("Hi", output="hi.avi", size=(640, 480))
"""

import os
import struct
from .morse import _AVIWriter  # 复用已验证的 AVI 写入器


# ─── 常量 ──────────────────────────────────────────────

FIXED_TEXT = "Convert string to Hex, then to RGB"

WHITE = (255, 255, 255)

# 16 个 hex 数字 → RGB 颜色 (全部互相区分, 易于辨认)
HEX_COLORS = {
    '0': (  0,   0,   0),   # 黑
    '1': (255,   0,   0),   # 红
    '2': (  0, 255,   0),   # 绿
    '3': (  0,   0, 255),   # 蓝
    '4': (255, 255,   0),   # 黄
    '5': (255,   0, 255),   # 品红
    '6': (  0, 255, 255),   # 青
    '7': (255, 128,   0),   # 橙
    '8': (128,   0, 255),   # 紫
    '9': (128, 255,   0),   # 青柠
    'a': (  0, 128, 128),   # 蓝绿
    'b': (255, 128, 192),   # 粉
    'c': (  0,   0, 128),   # 深蓝
    'd': (128,   0,   0),   # 深红
    'e': (128, 128,   0),   # 橄榄
    'f': (128, 128, 128),   # 灰
}

DEFAULT_SIZE = (320, 240)
DEFAULT_FPS = 25
FRAMES_PER_COLOR = 25  # 每个颜色 25 帧 (1 秒)


# ─── 核心函数 ──────────────────────────────────────────

def text_to_hex(text):
    """将文本转换为十六进制字符串 (无 0x 前缀)

    Args:
        text: str  输入文本

    Returns:
        str  十六进制表示, 如 "Hi" → "4869"
    """
    return text.encode('utf-8').hex()


def string_to_hex_video(text, output="hexvid.avi", size=None, fps=DEFAULT_FPS, readme=True):
    """将文本编码为十六进制 RGB 视频

    流程:
      1. 开头 25 帧纯白色 (标记)
      2. 逐字符处理:
         - 空格 → 25 帧白色
         - 其他字符 → 转 hex, 每个 hex 数字 25 帧对应颜色
      3. 输出 AVI + 说明文档

    Args:
        text:     str   输入文本
        output:   str   输出 AVI 路径
        size:     tuple 视频分辨率 (宽, 高), 默认 (320, 240)
        fps:      int   帧率, 默认 25
        readme:   bool  是否生成说明文档

    Returns:
        str  AVI 文件路径
    """
    if size is None:
        size = DEFAULT_SIZE

    w, h = size
    frame_bytes = w * h * 3  # BGR24

    # 生成颜色帧序列
    color_sequence = _build_color_sequence(text)

    # 写 AVI
    avi_path = os.path.abspath(output)
    writer = _AVIWriter(avi_path, w, h, fps)

    for rgb in color_sequence:
        # RGB → BGR (AVI 使用 BGR 格式)
        bgr = (rgb[2], rgb[1], rgb[0])
        pixel = bytes(bgr)
        frame_data = pixel * (w * h)
        for _ in range(FRAMES_PER_COLOR):
            writer.add_frame(frame_data)

    writer.close()

    # 生成说明文档
    if readme:
        _generate_readme(text, output, color_sequence, size, fps)

    print(f"[hexvid] AVI 已生成: {avi_path}")
    print(f"[hexvid] 总帧数: {len(color_sequence) * FRAMES_PER_COLOR}")
    print(f"[hexvid] 颜色段数: {len(color_sequence)}")
    return avi_path


def _build_color_sequence(text):
    """构建颜色序列

    Returns:
        list[(r,g,b)]  RGB 颜色列表
    """
    colors = []

    # 开头: 25 帧纯白色 (标记)
    colors.append(WHITE)

    # 逐字符处理
    for ch in text:
        if ch == ' ':
            # 空格 → 白色
            colors.append(WHITE)
        else:
            # 转为 hex
            hex_str = ch.encode('utf-8').hex()
            for hex_digit in hex_str:
                colors.append(HEX_COLORS[hex_digit])

    return colors


def _generate_readme(text, avi_path, color_sequence, size, fps):
    """生成说明文档 txt"""
    w, h = size
    readme_path = avi_path.rsplit('.', 1)[0] + "_说明.txt"

    hex_str = text_to_hex(text)

    lines = []
    lines.append("=" * 60)
    lines.append(FIXED_TEXT)
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"原始文本: {text}")
    lines.append(f"十六进制: {hex_str}")
    lines.append(f"视频路径: {avi_path}")
    lines.append(f"分辨率: {w}x{h}")
    lines.append(f"帧率: {fps} fps")
    lines.append(f"每色帧数: {FRAMES_PER_COLOR} 帧 ({FRAMES_PER_COLOR / fps:.1f} 秒)")
    lines.append(f"颜色段数: {len(color_sequence)}")
    lines.append(f"总帧数: {len(color_sequence) * FRAMES_PER_COLOR}")
    lines.append(f"总时长: {len(color_sequence) * FRAMES_PER_COLOR / fps:.1f} 秒")
    lines.append("")
    lines.append("-" * 60)
    lines.append("颜色映射表 (hex 数字 → RGB)")
    lines.append("-" * 60)

    for digit in '0123456789abcdef':
        r, g, b = HEX_COLORS[digit]
        color_name = _color_name(digit)
        lines.append(f"  {digit} → RGB({r:3d}, {g:3d}, {b:3d})  {color_name}")

    lines.append(f"  空格 → RGB(255, 255, 255)  纯白 (与开头标记相同)")
    lines.append("")
    lines.append("-" * 60)
    lines.append("解码方法")
    lines.append("-" * 60)
    lines.append("1. 识别开头 25 帧白色 (标记开始)")
    lines.append("2. 后续每 25 帧为一个颜色段")
    lines.append("3. 白色段 = 空格")
    lines.append("4. 其他颜色段 → 查表得到 hex 数字")
    lines.append("5. 将 hex 数字两两组合 → 还原字符")
    lines.append("6. 示例: 48 → 'H', 69 → 'i'")
    lines.append("")
    lines.append("-" * 60)
    lines.append("颜色序列 (本次编码)")
    lines.append("-" * 60)

    for i, (r, g, b) in enumerate(color_sequence):
        if (r, g, b) == WHITE:
            label = "纯白 (标记/空格)"
        else:
            # 反查 hex 数字
            digit = '?'
            for d, c in HEX_COLORS.items():
                if c == (r, g, b):
                    digit = d
                    break
            label = f"hex {digit} ({_color_name(digit)})"
        lines.append(f"  [{i:4d}] RGB({r:3d}, {g:3d}, {b:3d})  {label}")

    lines.append("")
    lines.append("=" * 60)

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"[hexvid] 说明文档已生成: {readme_path}")
    return readme_path


def _color_name(digit):
    """返回 hex 数字对应的中文名称"""
    names = {
        '0': '黑',
        '1': '红',
        '2': '绿',
        '3': '蓝',
        '4': '黄',
        '5': '品红',
        '6': '青',
        '7': '橙',
        '8': '紫',
        '9': '青柠',
        'a': '蓝绿',
        'b': '粉',
        'c': '深蓝',
        'd': '深红',
        'e': '橄榄',
        'f': '灰',
    }
    return names.get(digit, '?')


# ─── 模块入口 ──────────────────────────────────────────

class _HexVideoModule:
    """PyMsi.hexvid — 🎨 十六进制 RGB 视频模块 (1.5.8 新增)

    把文本编码为十六进制, 每个 hex 数字映射到一种 RGB 纯色:
        - 白色 25帧 = 开头标记 / 空格
        - 每个 hex 数字 (0-9, a-f) = 25帧对应 RGB 颜色
        - 纯 Python AVI (无压缩, 颜色绝对准确)
        - 自动生成说明文档 txt
        - 零第三方依赖

    用法:
        # 一键生成
        PM.hexvid("Hello", output="hello.avi")

        # 自定义
        PM.hexvid("Hi", output="hi.avi", size=(640, 480))

        # 分步
        PM.hexvid.text = "Hello"
        PM.hexvid.output = "out.avi"
        PM.hexvid.encode()

        # 只转 hex (不生成视频)
        code = PM.hexvid.text_to_hex("Hello")

        # 别名: PM.hex_video / PM.hv / PM.十六进制视频
    """

    def __init__(self):
        self.text = ""
        self.output = "hexvid.avi"
        self.size = DEFAULT_SIZE
        self.fps = DEFAULT_FPS
        self.readme = True

    def __repr__(self):
        return (f"<PyMsi.hexvid [十六进制RGB视频] text='{self.text[:20]}...' "
                f"size={self.size} fps={self.fps}>")

    def __call__(self, text, output=None, size=None, fps=None, readme=True):
        """一键生成十六进制 RGB 视频

        Args:
            text: str     要编码的文本
            output: str   输出 AVI 文件路径, 默认 "hexvid.avi"
            size: tuple   (宽, 高), 默认 (320, 240)
            fps: int      帧率, 默认 25
            readme: bool  是否生成说明文档, 默认 True

        Returns:
            str  输出 AVI 文件路径
        """
        self.text = text
        if output is not None:
            self.output = output
        if size is not None:
            self.size = size
        if fps is not None:
            self.fps = fps
        self.readme = readme

        return self.encode()

    def encode(self, text=None, output=None, size=None, fps=None, readme=None):
        """生成十六进制 RGB 视频

        不传参数则用当前配置
        """
        if text is not None:
            self.text = text
        if output is not None:
            self.output = output
        if size is not None:
            self.size = size
        if fps is not None:
            self.fps = fps
        if readme is not None:
            self.readme = readme

        if not self.text:
            raise ValueError("文本不能为空, 请设置 PM.hexvid.text 或传入 text 参数")

        return string_to_hex_video(
            self.text,
            output=self.output,
            size=self.size,
            fps=self.fps,
            readme=self.readme,
        )

    def text_to_hex(self, text=None):
        """文本 → 十六进制字符串 (不生成视频)

        Args:
            text: str  输入文本, 不传则用 self.text

        Returns:
            str  十六进制表示, 如 "Hi" → "4869"
        """
        if text is None:
            text = self.text
        return text_to_hex(text)


# ─── 自测 ──────────────────────────────────────────────

if __name__ == '__main__':
    import sys

    test_text = sys.argv[1] if len(sys.argv) > 1 else "Hi"
    test_output = sys.argv[2] if len(sys.argv) > 2 else "test_hexvid.avi"

    print(f"输入: {test_text!r}")
    print(f"Hex:  {text_to_hex(test_text)}")
    print()

    path = string_to_hex_video(test_text, output=test_output)

    import os
    size = os.path.getsize(path)
    print(f"\n文件大小: {size} bytes ({size / 1024:.1f} KB)")
    print("测试通过!")
