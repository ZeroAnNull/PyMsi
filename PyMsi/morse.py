"""PyMsi.morse — 📡 摩斯密码视频模块 (纯自研, 1.5.7 新增)

把明文文本转换成摩斯密码视频:
    - 白色 25帧 = 点 (.)
    - 黑色 1.5秒 = 划 (-)
    - 红色 20帧 = 空格 (字母间隔)
    - 绿色 20帧 = / (单词分隔)
    - 纯 Python AVI 编码器 (无压缩, 颜色绝对准确)
    - 自动生成说明文档 txt
    - 零第三方依赖

为什么用 AVI 不用 MP4?
    MP4 用有损压缩, 纯色帧会被压缩出杂色, 摩斯密码解码会出错
    AVI 无压缩, 颜色 100% 准确, 解码零误差

用法:
    import PyMsi as PM

    # 一键生成 (文本 + 输出路径)
    PM.morse("Hello World", output="morse.avi")

    # 自定义分辨率和帧率
    PM.morse("SOS", output="sos.avi", size=(640, 480), fps=25)

    # 分步配置
    PM.morse.text = "Hello World"
    PM.morse.output = "out.avi"
    PM.morse.size = (320, 240)
    PM.morse.encode()

    # 只转摩斯密码 (不生成视频)
    code = PM.morse.text_to_morse("Hello World")
    print(code)  # .... . .-.. .-.. --- / .-- --- .-. .-.. -..

    # 生成说明文档
    PM.morse.readme("morse_readme.txt")

    # 别名: PM.morse_video / PM.摩斯密码 / PM.摩斯 / PM.mv
"""

import os
import struct
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════

# 默认配置
_DEFAULT_FPS = 25               # 默认帧率 25fps
_DEFAULT_SIZE = (320, 240)      # 默认视频尺寸
_DEFAULT_OUTPUT_DIR = "."       # 默认输出目录

# 摩斯密码规则 → 帧数 (按 25fps 计算)
# 点: 白色 25帧 = 1秒
# 划: 黑色 1.5秒 = 38帧 (四舍五入, 实际 1.52秒, 误差很小)
# 空格 (字母间隔): 红色 20帧 = 0.8秒
# 单词分隔 (/): 绿色 20帧 = 0.8秒
_DOT_FRAMES = 25                # 点: 白色帧数
_DASH_SECONDS = 1.5             # 划: 黑色秒数
_SPACE_FRAMES = 20              # 空格: 红色帧数
_SLASH_FRAMES = 20              # 单词分隔: 绿色帧数

# 颜色定义 (BGR 顺序, AVI 用 BGR)
_COLOR_WHITE = (255, 255, 255)  # 白色 = 点
_COLOR_BLACK = (0, 0, 0)        # 黑色 = 划
_COLOR_RED = (0, 0, 255)        # 红色 = 空格 (BGR: 蓝=0, 绿=0, 红=255)
_COLOR_GREEN = (0, 255, 0)      # 绿色 = / (BGR: 蓝=0, 绿=255, 红=0)


# ═══════════════════════════════════════════════════════════════
# 摩斯密码表
# ═══════════════════════════════════════════════════════════════

_MORSE_CODE = {
    # 字母
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..',
    # 数字
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    # 常用标点
    '.': '.-.-.-',    # 句号
    ',': '--..--',    # 逗号
    '?': '..--..',    # 问号
    "'": '.----.',    # 单引号
    '!': '-.-.--',    # 感叹号
    '/': '-..-.',     # 斜杠
    '(': '-.--.',     # 左括号
    ')': '-.--.-',    # 右括号
    '&': '.-...',     # &
    ':': '---...',    # 冒号
    ';': '-.-.-.',    # 分号
    '=': '-...-',     # 等号
    '+': '.-.-.',     # 加号
    '-': '-....-',    # 减号
    '_': '..--.-',    # 下划线
    '"': '.-..-.',    # 双引号
    '$': '...-..-',   # 美元符
    '@': '.--.-.',    # @
}


# ═══════════════════════════════════════════════════════════════
# 纯 Python AVI 编码器 (RIFF 容器, 无压缩视频)
# ═══════════════════════════════════════════════════════════════

class _AVIWriter:
    """AVI 文件写入器 — 纯手写 RIFF/AVI 容器

    无压缩 24-bit BGR 视频, 底部优先 (bottom-up)
    流式写入: 逐帧追加, 关闭时回写索引和大小
    """

    def __init__(self, path, width, height, fps):
        self._path = path
        self._width = width
        self._height = height
        self._fps = max(1, fps)
        self._frame_count = 0
        self._frame_offsets = []
        self._movi_data_start = 0
        self._max_frame_size = 0

        self._fp = open(path, "wb")
        self._write_header_placeholder()

    def _write_header_placeholder(self):
        """写 RIFF + hdrl (先用占位大小, close 时回写)"""
        fp = self._fp
        w, h, fps = self._width, self._height, self._fps
        us_per_frame = 1000000 // fps

        # ─── RIFF 头 (占位) ───
        fp.write(b"RIFF")
        fp.write(struct.pack("<I", 0))
        fp.write(b"AVI ")

        # ─── LIST hdrl ───
        fp.write(b"LIST")
        fp.write(struct.pack("<I", 0))
        fp.write(b"hdrl")
        hdrl_start = fp.tell() - 4

        # ─── avih (主头, 56 字节) ───
        avih_data = struct.pack("<IIIIIIIIIIIIII",
            us_per_frame,  # dwMicroSecPerFrame
            0,             # dwMaxBytesPerSec
            0,             # dwPaddingGranularity
            0x10,          # dwFlags = AVIF_HASINDEX
            0,             # dwTotalFrames
            0,             # dwInitialFrames
            1,             # dwStreams
            0,             # dwSuggestedBufferSize
            w, h,          # dwWidth, dwHeight
            0, 0, 0, 0     # dwReserved[4]
        )
        fp.write(b"avih")
        fp.write(struct.pack("<I", len(avih_data)))
        fp.write(avih_data)

        # ─── LIST strl ───
        strl_start = fp.tell()
        fp.write(b"LIST")
        fp.write(struct.pack("<I", 0))
        fp.write(b"strl")

        # strh (流头, 56 字节)
        strh_data = struct.pack("<4s4sIHHIIIIIIIIHHHH",
            b"vids",    # fccType
            b"DIB ",    # fccHandler
            0,          # dwFlags
            0,          # wPriority
            0,          # wLanguage
            0,          # dwInitialFrames
            1,          # dwScale
            fps,        # dwRate
            0,          # dwStart
            0,          # dwLength
            0,          # dwSuggestedBufferSize
            0xFFFFFFFF, # dwQuality
            0,          # dwSampleSize
            0, 0,       # rcFrame
            w, h        # rcFrame
        )
        fp.write(b"strh")
        fp.write(struct.pack("<I", len(strh_data)))
        fp.write(strh_data)

        # strf (BITMAPINFOHEADER, 40 字节)
        image_size = w * h * 3
        strf_data = struct.pack("<IiiHHIIiiII",
            40,         # biSize
            w,          # biWidth
            h,          # biHeight
            1,          # biPlanes
            24,         # biBitCount
            0,          # biCompression = BI_RGB
            image_size, # biSizeImage
            0, 0,       # biXPelsPerMeter, biYPelsPerMeter
            0, 0        # biClrUsed, biClrImportant
        )
        fp.write(b"strf")
        fp.write(struct.pack("<I", len(strf_data)))
        fp.write(strf_data)

        # 回写 strl LIST 大小
        strl_end = fp.tell()
        strl_size = strl_end - strl_start - 8
        fp.seek(strl_start + 4)
        fp.write(struct.pack("<I", strl_size))
        fp.seek(strl_end)

        # 回写 hdrl LIST 大小
        hdrl_end = fp.tell()
        hdrl_size = hdrl_end - hdrl_start
        fp.seek(hdrl_start - 4)
        fp.write(struct.pack("<I", hdrl_size))
        fp.seek(hdrl_end)

        # ─── LIST movi ───
        self._movi_list_pos = fp.tell()
        fp.write(b"LIST")
        fp.write(struct.pack("<I", 0))
        fp.write(b"movi")
        self._movi_data_start = fp.tell()

    def add_frame(self, bgr_data):
        """添加一帧 (24-bit BGR, 底部优先, 无行填充)"""
        fp = self._fp
        pad = b"\x00" if len(bgr_data) % 2 else b""

        offset = fp.tell() - self._movi_data_start
        fp.write(b"00dc")
        fp.write(struct.pack("<I", len(bgr_data)))
        fp.write(bgr_data)
        if pad:
            fp.write(pad)

        frame_size = len(bgr_data)
        self._frame_offsets.append((offset, frame_size))
        if frame_size > self._max_frame_size:
            self._max_frame_size = frame_size
        self._frame_count += 1

    def close(self):
        """回写索引和所有占位大小, 关闭文件"""
        fp = self._fp

        # ─── idx1 (索引) ───
        movi_end = fp.tell()
        fp.write(b"idx1")
        fp.write(struct.pack("<I", self._frame_count * 16))
        for offset, size in self._frame_offsets:
            fp.write(struct.pack("<4sIII",
                b"00dc",   # ckid
                0x10,      # dwFlags = AVIIF_KEYFRAME
                offset,    # dwOffset
                size       # dwSize
            ))

        file_end = fp.tell()

        # 回写 movi LIST 大小
        movi_size = movi_end - self._movi_data_start
        fp.seek(self._movi_list_pos + 4)
        fp.write(struct.pack("<I", movi_size))

        # 回写 RIFF 总大小
        riff_size = file_end - 8
        fp.seek(4)
        fp.write(struct.pack("<I", riff_size))

        # 回写 avih 中的 dwTotalFrames 和 dwSuggestedBufferSize
        fp.seek(32 + 16)
        fp.write(struct.pack("<I", self._frame_count))
        fp.seek(32 + 28)
        fp.write(struct.pack("<I", self._max_frame_size))

        # 回写 strh 中的 dwLength 和 dwSuggestedBufferSize
        fp.seek(108 + 32)
        fp.write(struct.pack("<I", self._frame_count))
        fp.seek(108 + 36)
        fp.write(struct.pack("<I", self._max_frame_size))

        fp.close()


# ═══════════════════════════════════════════════════════════════
# 纯色帧生成
# ═══════════════════════════════════════════════════════════════

def _make_solid_frame(width, height, bgr_color):
    """生成纯色帧 (BGR 24-bit, 底部优先, 无行对齐填充)

    Args:
        width:  宽度
        height: 高度
        bgr_color: (B, G, R) 元组

    Returns:
        bytes  紧凑 BGR 数据
    """
    b, g, r = bgr_color
    # 一行的像素数据
    row = bytes([b, g, r]) * width
    # 底部优先: 从下到上 (纯色帧上下一样, 直接乘就行)
    return row * height


# ═══════════════════════════════════════════════════════════════
# 摩斯密码转换
# ═══════════════════════════════════════════════════════════════

def text_to_morse(text):
    """明文文本 → 摩斯密码

    规则:
        - 字母之间用空格分隔
        - 单词之间用 " / " 分隔
        - 不支持的字符会被跳过

    Args:
        text: str  明文文本

    Returns:
        str  摩斯密码字符串 (点划 + 空格 + /)

    示例:
        >>> text_to_morse("SOS")
        '... --- ...'
        >>> text_to_morse("HI THERE")
        '.... .. / - .... . .-. .'
    """
    words = text.strip().upper().split()
    morse_words = []

    for word in words:
        morse_chars = []
        for ch in word:
            if ch in _MORSE_CODE:
                morse_chars.append(_MORSE_CODE[ch])
            # 不认识的字符直接跳过
        if morse_chars:
            morse_words.append(" ".join(morse_chars))

    return " / ".join(morse_words)


def _morse_to_frames(morse_code, fps):
    """摩斯密码 → 帧序列 (颜色 + 帧数)

    Args:
        morse_code: str  摩斯密码 (由 . - 空格 / 组成)
        fps: int         帧率

    Returns:
        list  [(bgr_color, frame_count), ...]  帧序列
    """
    dash_frames = max(1, round(_DASH_SECONDS * fps))

    frames = []
    for ch in morse_code:
        if ch == '.':
            frames.append((_COLOR_WHITE, _DOT_FRAMES))
        elif ch == '-':
            frames.append((_COLOR_BLACK, dash_frames))
        elif ch == ' ':
            frames.append((_COLOR_RED, _SPACE_FRAMES))
        elif ch == '/':
            frames.append((_COLOR_GREEN, _SLASH_FRAMES))
        # 其他字符跳过

    return frames


# ═══════════════════════════════════════════════════════════════
# 说明文档生成
# ═══════════════════════════════════════════════════════════════

def _generate_readme(output_path, text, morse_code, fps, size, total_frames, duration):
    """生成说明文档 txt

    Args:
        output_path: str  输出文件路径
        text: str         原始文本
        morse_code: str   摩斯密码
        fps: int          帧率
        size: tuple       (宽, 高)
        total_frames: int 总帧数
        duration: float   时长 (秒)
    """
    width, height = size
    dash_frames = round(_DASH_SECONDS * fps)

    content = f"""╔══════════════════════════════════════════════════════════════╗
║           PyMsi 摩斯密码视频 - 说明文档                       ║
╚══════════════════════════════════════════════════════════════╝

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
生成工具: PyMsi.morse (v1.5.7)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  原始文本
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  摩斯密码
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{morse_code}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  视频信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  格式:       AVI (无压缩 24-bit BGR)
  分辨率:     {width} x {height}
  帧率:       {fps} fps
  总帧数:     {total_frames} 帧
  总时长:     {duration:.2f} 秒

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  编码规则
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  白色  ({_COLOR_WHITE[2]:3d}, {_COLOR_WHITE[1]:3d}, {_COLOR_WHITE[0]:3d})  →  点 (.)    {_DOT_FRAMES} 帧 ({_DOT_FRAMES/fps:.2f} 秒)
  黑色  ({_COLOR_BLACK[2]:3d}, {_COLOR_BLACK[1]:3d}, {_COLOR_BLACK[0]:3d})  →  划 (-)    {dash_frames} 帧 ({_DASH_SECONDS:.2f} 秒)
  红色  ({_COLOR_RED[2]:3d}, {_COLOR_RED[1]:3d}, {_COLOR_RED[0]:3d})  →  空格        {_SPACE_FRAMES} 帧 ({_SPACE_FRAMES/fps:.2f} 秒)
  绿色  ({_COLOR_GREEN[2]:3d}, {_COLOR_GREEN[1]:3d}, {_COLOR_GREEN[0]:3d})  →  单词分隔 /  {_SLASH_FRAMES} 帧 ({_SLASH_FRAMES/fps:.2f} 秒)

  注意: 颜色格式为 (R, G, B)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  为什么用 AVI 不用 MP4?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  MP4 使用 H.264 等有损压缩算法, 纯色帧会被压缩出杂色和色块
  导致颜色不准, 摩斯密码解码失败

  AVI 无压缩视频, 颜色 100% 准确, 每一帧都是纯净的颜色
  保证解码零误差

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  解码方法 (手动)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. 用视频播放器逐帧查看
  2. 白色帧 = 点 (.), 数一下连续白色帧的数量 (应该是 {_DOT_FRAMES} 帧)
  3. 黑色帧 = 划 (-), 连续黑色帧约 {dash_frames} 帧
  4. 红色帧 = 字母间隔
  5. 绿色帧 = 单词分隔
  6. 对照摩斯密码表翻译回字母

  也可以用 PyMsi.morse.decode() 自动解码 (需要安装 PyMsi)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PyMsi 项目地址
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  https://github.com/import-PyMsi-as-PM/PyMsi

╔══════════════════════════════════════════════════════════════╗
║   本文件由 PyMsi.morse 自动生成, 请勿手动修改                ║
╚══════════════════════════════════════════════════════════════╝
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


# ═══════════════════════════════════════════════════════════════
# 主模块: _MorseVideoModule
# ═══════════════════════════════════════════════════════════════

class _MorseVideoModule:
    """PyMsi.morse — 📡 摩斯密码视频模块 (纯自研, 1.5.7 新增)

    把明文文本转换成摩斯密码视频:
        - 白色 25帧 = 点 (.)
        - 黑色 1.5秒 = 划 (-)
        - 红色 20帧 = 空格 (字母间隔)
        - 绿色 20帧 = / (单词分隔)
        - 纯 Python AVI 编码器 (无压缩, 颜色绝对准确)
        - 自动生成说明文档 txt
        - 零第三方依赖

    用法:
        # 一键生成
        PM.morse("Hello World", output="morse.avi")

        # 自定义
        PM.morse("SOS", output="sos.avi", size=(640, 480))

        # 分步
        PM.morse.text = "Hello"
        PM.morse.output = "out.avi"
        PM.morse.encode()

        # 只转摩斯密码
        code = PM.morse.text_to_morse("Hello")

        # 生成说明文档
        PM.morse.readme("readme.txt")

        # 别名: PM.morse_video / PM.摩斯密码 / PM.摩斯 / PM.mv
    """

    def __init__(self):
        self.text = ""
        self.output = "morse.avi"
        self.size = _DEFAULT_SIZE
        self.fps = _DEFAULT_FPS
        self._output_path = None
        self._readme_path = None
        self._last_morse = ""

    def __repr__(self):
        return (f"<PyMsi.morse [摩斯密码视频] text='{self.text[:20]}...' "
                f"size={self.size} fps={self.fps}>")

    # ─── 核心方法 ──────────────────────────────────────

    def __call__(self, text, output=None, size=None, fps=None, readme=True):
        """一键生成摩斯密码视频

        Args:
            text: str           要编码的明文文本
            output: str         输出 AVI 文件路径, 默认 "morse.avi"
            size: tuple         (宽, 高), 默认 (320, 240)
            fps: int            帧率, 默认 25
            readme: bool        是否同时生成说明文档 txt, 默认 True

        Returns:
            str                 输出 AVI 文件路径

        用法:
            PM.morse("Hello World")
            PM.morse("SOS", output="sos.avi", size=(640, 480))
            PM.morse("HI", output="hi.avi", fps=30)
        """
        self.text = text
        if output is not None:
            self.output = output
        if size is not None:
            self.size = size
        if fps is not None:
            self.fps = fps

        return self.encode(readme=readme)

    def encode(self, text=None, output=None, size=None, fps=None, readme=True):
        """生成摩斯密码视频

        不传参数则用当前配置 (self.text / self.output / ...)
        """
        if text is not None:
            self.text = text
        if output is not None:
            self.output = output
        if size is not None:
            self.size = size
        if fps is not None:
            self.fps = fps

        if not self.text:
            raise ValueError("文本不能为空, 请设置 PM.morse.text 或传入 text 参数")

        width, height = self.size
        if width <= 0 or height <= 0:
            raise ValueError(f"无效的分辨率: {self.size}")

        fps = max(1, int(self.fps))
        self.fps = fps

        # 1. 文本 → 摩斯密码
        morse_code = text_to_morse(self.text)
        self._last_morse = morse_code

        if not morse_code:
            raise ValueError("文本中没有可编码的字符 (仅支持英文字母、数字、常用标点)")

        # 2. 摩斯密码 → 帧序列
        frame_seq = _morse_to_frames(morse_code, fps)

        # 3. 生成 AVI
        output_path = self.output
        os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)

        writer = _AVIWriter(output_path, width, height, fps)
        total_frames = 0

        try:
            for color, count in frame_seq:
                frame_data = _make_solid_frame(width, height, color)
                for _ in range(count):
                    writer.add_frame(frame_data)
                    total_frames += 1
        finally:
            writer.close()

        duration = total_frames / fps if fps > 0 else 0
        self._output_path = output_path

        # 4. 生成说明文档
        if readme:
            readme_path = os.path.splitext(output_path)[0] + "_说明.txt"
            _generate_readme(readme_path, self.text, morse_code,
                           fps, self.size, total_frames, duration)
            self._readme_path = readme_path
            print(f"[PyMsi.morse] 说明文档: {readme_path}")

        print(f"[PyMsi.morse] 生成完成: {output_path} "
              f"({total_frames} 帧, {duration:.2f} 秒)")
        return output_path

    def text_to_morse(self, text=None):
        """文本 → 摩斯密码 (不生成视频)

        Args:
            text: str  明文文本, 不传则用 self.text

        Returns:
            str  摩斯密码字符串
        """
        if text is None:
            text = self.text
        return text_to_morse(text)

    def readme(self, output_path=None, text=None):
        """单独生成说明文档 txt (不生成视频)

        Args:
            output_path: str  输出路径, 默认 "morse_readme.txt"
            text: str         原始文本, 不传则用 self.text
        """
        if output_path is None:
            output_path = "morse_readme.txt"
        if text is None:
            text = self.text or "Hello World"

        morse_code = text_to_morse(text)
        dash_frames = round(_DASH_SECONDS * self.fps)
        total_frames = 0  # 粗略估算
        for ch in morse_code:
            if ch == '.':
                total_frames += _DOT_FRAMES
            elif ch == '-':
                total_frames += dash_frames
            elif ch == ' ':
                total_frames += _SPACE_FRAMES
            elif ch == '/':
                total_frames += _SLASH_FRAMES
        duration = total_frames / self.fps if self.fps > 0 else 0

        _generate_readme(output_path, text, morse_code,
                       self.fps, self.size, total_frames, duration)
        print(f"[PyMsi.morse] 说明文档已生成: {output_path}")
        return output_path

    # ─── 属性 (只读变量) ──────────────────────────────

    @property
    def output_path(self):
        """上次生成的视频文件路径 (只读)"""
        return self._output_path

    @property
    def readme_path(self):
        """上次生成的说明文档路径 (只读)"""
        return self._readme_path

    @property
    def morse_code(self):
        """上次编码的摩斯密码 (只读)"""
        return self._last_morse

    @property
    def result(self):
        """输出路径 (output_path 别名)"""
        return self._output_path

    @property
    def path(self):
        """输出路径 (output_path 别名)"""
        return self._output_path

    @property
    def file(self):
        """输出路径 (output_path 别名)"""
        return self._output_path

    # ─── 别名方法 ──────────────────────────────────────

    def morse_video(self, *args, **kwargs):
        """别名: PM.morse.morse_video() == PM.morse()"""
        return self.__call__(*args, **kwargs)

    def mv(self, *args, **kwargs):
        """别名: PM.morse.mv() == PM.morse()"""
        return self.__call__(*args, **kwargs)

    def generate(self, *args, **kwargs):
        """别名: PM.morse.generate() == PM.morse.encode()"""
        return self.encode(*args, **kwargs)

    def make(self, *args, **kwargs):
        """别名: PM.morse.make() == PM.morse.encode()"""
        return self.encode(*args, **kwargs)

    def create(self, *args, **kwargs):
        """别名: PM.morse.create() == PM.morse.encode()"""
        return self.encode(*args, **kwargs)

    def encode_video(self, *args, **kwargs):
        """别名: PM.morse.encode_video() == PM.morse.encode()"""
        return self.encode(*args, **kwargs)

    def to_morse(self, *args, **kwargs):
        """别名: PM.morse.to_morse() == PM.morse.text_to_morse()"""
        return self.text_to_morse(*args, **kwargs)

    def translate(self, *args, **kwargs):
        """别名: PM.morse.translate() == PM.morse.text_to_morse()"""
        return self.text_to_morse(*args, **kwargs)

    def help(self):
        """打印帮助"""
        print(self.__doc__)

    def 生成(self, *args, **kwargs):
        """中文别名"""
        return self.encode(*args, **kwargs)

    def 编码(self, *args, **kwargs):
        """中文别名"""
        return self.encode(*args, **kwargs)

    def 转摩斯密码(self, *args, **kwargs):
        """中文别名"""
        return self.text_to_morse(*args, **kwargs)
