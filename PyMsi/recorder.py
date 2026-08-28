"""PyMsi.recorder — 📹 录屏模块 (纯自研, 1.5.3 新增)

⚠️ 平台限制: 仅支持 Windows
    截屏底层调用 Win32 GDI (ctypes → user32/gdi32/kernal32),
    在 macOS 和 Linux 上调用 PM.record() 会抛出 RuntimeError。
    macOS 用户请用 screencapture, Linux 用户请用 ffmpeg/x11grab。

纯手搓、纯自研的屏幕录制功能:
    - Win32 GDI 截屏 (ctypes 调系统 API, 零第三方依赖)
    - 纯 Python AVI 编码器 (无压缩视频流, RIFF 容器手写)
    - 纯 Python GIF 动画编码器 (3-3-2 量化 + LZW 压缩手写)
    - 30+ 输出格式 (纯自研 AVI/GIF + ffmpeg 转码)
    - 自动隐藏控制台窗口, 后台静默录制
    - 默认 D:/Videos, 录完自动输出文件路径

用法:
    import PyMsi as PM

    # 一键录屏 (默认: 1分钟, 最高4K, AVI, D:/Videos)
    PM.record()

    # 自定义参数
    PM.record(duration=60, resolution="4K", fmt="mp4", output_dir="D:/Videos")

    # 分步配置
    PM.record.duration = 60       # 录屏时长 (秒)
    PM.record.resolution = "4K"   # 清晰度 (最高4K)
    PM.record.format = "gif"      # 输出格式
    PM.record.start()

    # 查看支持的格式
    PM.record.formats()           # 打印 30+ 格式列表

    # 录完后的输出路径
    print(PM.record.output)       # 文件路径

    # 别名: PM.rec / PM.capture / PM.录屏 / PM.录像

注意:
    - ⚠️ 截屏用 Win32 GDI (ctypes), 仅支持 Windows (macOS/Linux 会报错)
    - AVI/GIF 编码纯手写, 不依赖任何第三方库
    - MP4/MKV/WebM 等格式需要 ffmpeg (自动检测, 有就用)
    - 录制时自动隐藏控制台, 录完自动恢复并输出路径
"""

import os
import sys
import time
import struct
import subprocess
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════

# 默认配置 (在代码里写死的默认值)
_DEFAULT_DURATION = 60          # 录屏时长 1 分钟
_DEFAULT_RESOLUTION = "4K"      # 清晰度最高 4K
_DEFAULT_FORMAT = "avi"         # 默认输出格式
_DEFAULT_OUTPUT_DIR = "D:/Videos"  # 默认输出目录
_DEFAULT_FPS = 24               # 默认帧率

# 清晰度 → 最大分辨率
_RESOLUTIONS = {
    "4K":     (3840, 2160),
    "2K":     (2560, 1440),
    "1440p":  (2560, 1440),
    "1080p":  (1920, 1080),
    "720p":   (1280, 720),
    "480p":   (854, 480),
    "360p":   (640, 360),
    "native": (0, 0),       # 用屏幕原始分辨率
    "auto":   (0, 0),
}

# 不同分辨率下的帧率 (4K 帧大, 降低帧率保证流畅)
_FPS_MAP = {
    "4K":    15,
    "2K":    20,
    "1440p": 20,
    "1080p": 24,
    "720p":  30,
    "480p":  30,
    "360p":  30,
    "native": 24,
    "auto":   24,
}

# ═══════════════════════════════════════════════════════════════
# 30+ 输出格式定义
# ═══════════════════════════════════════════════════════════════
# 纯自研格式 (不依赖 ffmpeg)
_PURE_FORMATS = {
    "avi": ("AVI 无压缩视频 (纯自研)", "pure"),
    "gif": ("GIF 动画 (纯自研, LZW 压缩)", "pure"),
    "bmp": ("BMP 帧序列 (纯自研)", "pure"),
}

# ffmpeg 转码格式 (需要 ffmpeg, 先录 AVI 再转)
_FFMPEG_FORMATS = {
    "mp4":     {"ext": "mp4",  "codec": "libx264",  "extra": ["-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23"]},
    "mkv":     {"ext": "mkv",  "codec": "libx264",  "extra": ["-preset", "fast", "-crf", "23"]},
    "webm":    {"ext": "webm", "codec": "libvpx",   "extra": ["-b:v", "1M", "-deadline", "realtime"]},
    "mov":     {"ext": "mov",  "codec": "libx264",  "extra": ["-pix_fmt", "yuv420p", "-preset", "fast"]},
    "flv":     {"ext": "flv",  "codec": "libx264",  "extra": ["-preset", "fast"]},
    "wmv":     {"ext": "wmv",  "codec": "wmv2",     "extra": ["-qscale", "2"]},
    "mpeg":    {"ext": "mpeg", "codec": "mpeg1video", "extra": ["-qscale", "2"]},
    "mpg":     {"ext": "mpg",  "codec": "mpeg1video", "extra": ["-qscale", "2"]},
    "ts":      {"ext": "ts",   "codec": "libx264",  "extra": ["-preset", "fast"]},
    "mts":     {"ext": "mts",  "codec": "libx264",  "extra": ["-preset", "fast"]},
    "m2ts":    {"ext": "m2ts", "codec": "libx264",  "extra": ["-preset", "fast"]},
    "vob":     {"ext": "vob",  "codec": "mpeg2video", "extra": ["-qscale", "2"]},
    "ogv":     {"ext": "ogv",  "codec": "libtheora", "extra": ["-qscale", "5"]},
    "3gp":     {"ext": "3gp",  "codec": "libx264",  "extra": ["-preset", "fast", "-s", "352x288"]},
    "3g2":     {"ext": "3g2",  "codec": "libx264",  "extra": ["-preset", "fast"]},
    "asf":     {"ext": "asf",  "codec": "wmv2",     "extra": ["-qscale", "2"]},
    "dv":      {"ext": "dv",   "codec": "dvvideo",  "extra": []},
    "amv":     {"ext": "amv",  "codec": "amv",      "extra": []},
    "mxf":     {"ext": "mxf",  "codec": "libx264",  "extra": ["-preset", "fast"]},
    "gxf":     {"ext": "gxf",  "codec": "libx264",  "extra": ["-preset", "fast"]},
    "swf":     {"ext": "swf",  "codec": "libx264",  "extra": ["-preset", "fast"]},
    "rm":      {"ext": "rm",   "codec": "libx264",  "extra": ["-preset", "fast"]},
    "rmvb":    {"ext": "rmvb", "codec": "libx264",  "extra": ["-preset", "fast"]},
    "nsv":     {"ext": "nsv",  "codec": "libx264",  "extra": ["-preset", "fast"]},
    "y4m":     {"ext": "y4m",  "codec": "rawvideo", "extra": ["-pix_fmt", "yuv420p"]},
    "f4v":     {"ext": "f4v",  "codec": "libx264",  "extra": ["-preset", "fast"]},
    "avi_mjpg": {"ext": "avi",  "codec": "mjpeg",    "extra": ["-qscale", "2"]},
    "mkv_hevc": {"ext": "mkv",  "codec": "libx265",  "extra": ["-preset", "fast"]},
    "mp4_hevc": {"ext": "mp4",  "codec": "libx265",  "extra": ["-pix_fmt", "yuv420p", "-preset", "fast"]},
    "av1":      {"ext": "mp4",  "codec": "libaom-av1", "extra": ["-cpu-used", "8"]},
    "vp9":      {"ext": "webm", "codec": "libvpx-vp9", "extra": ["-b:v", "1M", "-deadline", "realtime"]},
}

# 全部格式 (纯自研 + ffmpeg)
_ALL_FORMATS = {}
_ALL_FORMATS.update({k: (v[0], v[1]) for k, v in _PURE_FORMATS.items()})
for k, v in _FFMPEG_FORMATS.items():
    _ALL_FORMATS[k] = (f"{v['codec']} (ffmpeg 转码)", "ffmpeg")

# GIF 最大分辨率 (GIF 帧太大编码极慢, 限制到 480p)
_GIF_MAX_WIDTH = 854
_GIF_MAX_HEIGHT = 480
_GIF_FPS = 10  # GIF 帧率

# Win32 常量
_SRCCOPY = 0x00CC0020
_CAPTUREBLT = 0x40000000
_DIB_RGB_COLORS = 0
_BI_RGB = 0
_SW_HIDE = 0
_SW_SHOW = 5

# Win32 API 绑定 (仅 Windows 初始化)
_user32 = None
_gdi32 = None
_kernel32 = None
_is_windows = sys.platform == "win32"


def _init_win32():
    """初始化 Win32 API 绑定 (仅 Windows)"""
    global _user32, _gdi32, _kernel32
    if not _is_windows:
        return False
    if _user32 is not None:
        return True
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.WinDLL("user32")
    _gdi32 = ctypes.WinDLL("gdi32")
    _kernel32 = ctypes.WinDLL("kernel32")

    # 设置函数返回类型
    _user32.GetSystemMetrics.restype = wintypes.INT
    _user32.GetSystemMetrics.argtypes = [wintypes.INT]
    _user32.GetDC.restype = wintypes.HDC
    _user32.GetDC.argtypes = [wintypes.HWND]
    _user32.ReleaseDC.restype = wintypes.INT
    _user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    _user32.ShowWindow.restype = wintypes.BOOL
    _user32.ShowWindow.argtypes = [wintypes.HWND, wintypes.INT]
    _kernel32.GetConsoleWindow.restype = wintypes.HWND

    _gdi32.CreateCompatibleDC.restype = wintypes.HDC
    _gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    _gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    _gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, wintypes.INT, wintypes.INT]
    _gdi32.SelectObject.restype = wintypes.HGDIOBJ
    _gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    _gdi32.BitBlt.restype = wintypes.BOOL
    _gdi32.BitBlt.argtypes = [wintypes.HDC, wintypes.INT, wintypes.INT,
                              wintypes.INT, wintypes.INT, wintypes.HDC,
                              wintypes.INT, wintypes.INT, wintypes.DWORD]
    _gdi32.GetDIBits.restype = wintypes.INT
    _gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT,
                                 wintypes.UINT, ctypes.c_void_p,
                                 ctypes.c_void_p, wintypes.UINT]
    _gdi32.DeleteObject.restype = wintypes.BOOL
    _gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    _gdi32.DeleteDC.restype = wintypes.BOOL
    _gdi32.DeleteDC.argtypes = [wintypes.HDC]
    return True


# ═══════════════════════════════════════════════════════════════
# 纯 Python 工具函数
# ═══════════════════════════════════════════════════════════════

class _BitWriter:
    """位写入器 — 用于 GIF LZW 压缩的变长位编码"""

    def __init__(self):
        self._bits = 0
        self._count = 0
        self._data = bytearray()

    def write(self, value, n_bits):
        """写入 n_bits 位"""
        self._bits |= (value & ((1 << n_bits) - 1)) << self._count
        self._count += n_bits
        while self._count >= 8:
            self._data.append(self._bits & 0xFF)
            self._bits >>= 8
            self._count -= 8

    def flush(self):
        """刷新剩余位, 返回字节"""
        if self._count > 0:
            self._data.append(self._bits & 0xFF)
            self._bits = 0
            self._count = 0
        return bytes(self._data)


def _lzw_compress(indices, min_code_size):
    """LZW 压缩 — 纯手写 GIF LZW 编码器

    Args:
        indices: 像素颜色索引列表 (bytes 或 bytearray)
        min_code_size: 最小代码位数 (256 色 = 8)

    Returns:
        LZW 压缩后的字节 (含子块分割)
    """
    if not indices:
        return b"\x00"

    clear_code = 1 << min_code_size
    eoi_code = clear_code + 1

    # 初始化码表
    code_table = {}
    for i in range(clear_code):
        code_table[bytes([i])] = i
    next_code = eoi_code + 1
    code_size = min_code_size + 1

    writer = _BitWriter()
    writer.write(clear_code, code_size)

    buffer = bytes([indices[0]])
    for i in range(1, len(indices)):
        k = bytes([indices[i]])
        new_buf = buffer + k
        if new_buf in code_table:
            buffer = new_buf
        else:
            writer.write(code_table[buffer], code_size)
            if next_code < 4096:
                code_table[new_buf] = next_code
                next_code += 1
                # 代码位数增长
                if next_code > (1 << code_size) and code_size < 12:
                    code_size += 1
            else:
                # 码表满, 发清除码
                writer.write(clear_code, code_size)
                code_table = {}
                for j in range(clear_code):
                    code_table[bytes([j])] = j
                next_code = eoi_code + 1
                code_size = min_code_size + 1
            buffer = k

    writer.write(code_table[buffer], code_size)
    writer.write(eoi_code, code_size)

    raw = writer.flush()

    # 分割成最大 255 字节的子块
    out = bytearray()
    pos = 0
    while pos < len(raw):
        chunk = raw[pos:pos + 255]
        out.append(len(chunk))
        out.extend(chunk)
        pos += 255
    out.append(0)  # 块结束标记
    return bytes(out)


def _quantize_332(bgr_data, width, height):
    """3-3-2 颜色量化 — 纯手写

    把 BGR 24-bit 数据量化为 256 色索引 (3位R + 3位G + 2位B)
    返回: (索引字节, 256色调色板 RGB)

    速度快: 每个像素只需位运算

    输入: 紧凑 BGR 数据 (无行对齐填充), 底部优先
    """
    # 构建 3-3-2 调色板 (RGB)
    palette = bytearray()
    for i in range(256):
        r = ((i >> 5) & 0x07) * 36
        g = ((i >> 2) & 0x07) * 36
        b = (i & 0x03) * 85
        palette.extend([r, g, b])
    palette = bytes(palette)

    # 量化每个像素: BGR → 索引 (紧凑数据, 无行填充)
    indices = bytearray(width * height)
    row_bytes = width * 3
    for y in range(height):
        row_off = y * row_bytes
        dst_off = y * width
        for x in range(width):
            src_idx = row_off + x * 3
            b = bgr_data[src_idx]
            g = bgr_data[src_idx + 1]
            r = bgr_data[src_idx + 2]
            # 3-3-2 量化
            r_idx = (r >> 5) & 0x07
            g_idx = (g >> 5) & 0x07
            b_idx = (b >> 6) & 0x03
            indices[dst_off + x] = (r_idx << 5) | (g_idx << 2) | b_idx

    return bytes(indices), palette


def _downscale_bgr(data, src_w, src_h, dst_w, dst_h):
    """最近邻降采样 BGR 数据 (含行对齐)"""
    import array
    src_row = (src_w * 3 + 3) & ~3  # 源行步长 (4字节对齐)
    dst_row = dst_w * 3
    result = array.array("B", [0] * (dst_row * dst_h))

    x_ratio = src_w / dst_w
    y_ratio = src_h / dst_h

    for dy in range(dst_h):
        sy = int(dy * y_ratio)
        src_off = sy * src_row
        dst_off = dy * dst_row
        for dx in range(dst_w):
            sx = int(dx * x_ratio)
            si = src_off + sx * 3
            di = dst_off + dx * 3
            result[di] = data[si]
            result[di + 1] = data[si + 1]
            result[di + 2] = data[si + 2]

    return bytes(result)


def _strip_bmp_padding(data, width, height, bpp=24):
    """去掉 BMP 行对齐填充, 返回紧凑数据"""
    row_padded = (width * (bpp // 8) + 3) & ~3
    row_tight = width * (bpp // 8)
    if row_padded == row_tight:
        return data  # 无需处理
    result = bytearray()
    for y in range(height):
        off = y * row_padded
        result.extend(data[off:off + row_tight])
    return bytes(result)


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
        self._fps = fps
        self._fps = max(1, fps)
        self._frame_count = 0
        self._frame_offsets = []  # (offset, size) 相对于 movi 数据起始
        self._movi_start = 0
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
        fp.write(struct.pack("<I", 0))  # 占位, close 时回写
        fp.write(b"AVI ")

        # ─── LIST hdrl ───
        fp.write(b"LIST")
        fp.write(struct.pack("<I", 0))  # 占位
        fp.write(b"hdrl")
        hdrl_start = fp.tell() - 4  # "hdrl" 开始位置

        # ─── avih (主头, 56 字节) ───
        avih_data = struct.pack("<IIIIIIIIIIIIII",
            us_per_frame,    # dwMicroSecPerFrame
            0,               # dwMaxBytesPerSec (占位)
            0,               # dwPaddingGranularity
            0x10,            # dwFlags = AVIF_HASINDEX
            0,               # dwTotalFrames (占位, close 回写)
            0,               # dwInitialFrames
            1,               # dwStreams
            0,               # dwSuggestedBufferSize (占位)
            w, h,            # dwWidth, dwHeight
            0, 0, 0, 0       # dwReserved[4]
        )
        fp.write(b"avih")
        fp.write(struct.pack("<I", len(avih_data)))
        fp.write(avih_data)

        # ─── LIST strl ───
        strl_start = fp.tell()
        fp.write(b"LIST")
        fp.write(struct.pack("<I", 0))  # 占位
        fp.write(b"strl")

        # strh (流头, 56 字节)
        strh_data = struct.pack("<4s4sIHHIIIIIIIIHHHH",
            b"vids",        # fccType
            b"DIB ",        # fccHandler (无压缩)
            0,              # dwFlags
            0,              # wPriority
            0,              # wLanguage
            0,              # dwInitialFrames
            1,              # dwScale
            fps,            # dwRate
            0,              # dwStart
            0,              # dwLength (占位, close 回写)
            0,              # dwSuggestedBufferSize (占位)
            0xFFFFFFFF,     # dwQuality (-1)
            0,              # dwSampleSize
            0, 0,           # rcFrame left, top
            w, h            # rcFrame right, bottom
        )
        fp.write(b"strh")
        fp.write(struct.pack("<I", len(strh_data)))
        fp.write(strh_data)

        # strf (BITMAPINFOHEADER, 40 字节)
        image_size = w * h * 3
        strf_data = struct.pack("<IiiHHIIiiII",
            40,             # biSize
            w,              # biWidth
            h,              # biHeight (正=底部优先)
            1,              # biPlanes
            24,             # biBitCount
            _BI_RGB,        # biCompression
            image_size,     # biSizeImage
            0,              # biXPelsPerMeter
            0,              # biYPelsPerMeter
            0,              # biClrUsed
            0               # biClrImportant
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
        fp.seek(hdrl_start - 4)  # 回到 hdrl LIST size 位置
        fp.write(struct.pack("<I", hdrl_size))
        fp.seek(hdrl_end)

        # ─── LIST movi ───
        self._movi_list_pos = fp.tell()
        fp.write(b"LIST")
        fp.write(struct.pack("<I", 0))  # 占位
        fp.write(b"movi")
        self._movi_data_start = fp.tell()  # movi 数据起始 (用于 idx1 偏移)

    def add_frame(self, bgr_data):
        """添加一帧 (24-bit BGR, 底部优先, 无行填充)"""
        fp = self._fp
        # 帧数据需要 2 字节对齐
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
        idx1_start = fp.tell()
        fp.write(b"idx1")
        fp.write(struct.pack("<I", self._frame_count * 16))
        for offset, size in self._frame_offsets:
            fp.write(struct.pack("<4sIII",
                b"00dc",        # ckid
                0x10,           # dwFlags = AVIIF_KEYFRAME
                offset,         # dwOffset (相对 movi 数据起始)
                size            # dwSize
            ))

        file_end = fp.tell()

        # ─── 回写 movi LIST 大小 ───
        movi_size = movi_end - self._movi_data_start
        fp.seek(self._movi_list_pos + 4)
        fp.write(struct.pack("<I", movi_size))

        # ─── 回写 RIFF 总大小 ───
        riff_size = file_end - 8
        fp.seek(4)
        fp.write(struct.pack("<I", riff_size))

        # ─── 回写 avih 中的 dwTotalFrames 和 dwSuggestedBufferSize ───
        # avih 位置: RIFF(12) + LIST hdrl 头(12) + "avih" 标签(4) + size(4) = 32
        # dwTotalFrames 在 avih 数据偏移 16 (第5个 DWORD)
        fp.seek(32 + 16)
        fp.write(struct.pack("<I", self._frame_count))
        fp.seek(32 + 28)
        fp.write(struct.pack("<I", self._max_frame_size))

        # ─── 回写 strh 中的 dwLength 和 dwSuggestedBufferSize ───
        # strh 在 avih 之后: 32 + 56 + 8 = 96, 然后 LIST strl 头 12, "strh" 标签 4, size 4
        # strh 数据偏移: 96 + 12 + 8 = 116
        # dwLength 在 strh 数据偏移 32 (第8个 DWORD, 跳过 fccType+fccHandler=8, dwFlags=4, wPriority+wLanguage=4, dwInitialFrames=4, dwScale=4, dwRate=4 = 28, 然后 dwStart=4 → 32)
        # 等等, 让我重新算: strh 格式是 4s4sIHHIIIIIIIHHHH
        # fccType(4) + fccHandler(4) + dwFlags(4) + wPriority(2) + wLanguage(2) + dwInitialFrames(4) + dwScale(4) + dwRate(4) + dwStart(4) + dwLength(4)
        # dwLength 偏移 = 4+4+4+2+2+4+4+4+4 = 32
        # strh 数据起始 = 32(avih chunk) + 56(avih data) + 8(avih chunk header=tag+size) = 不对
        # 让我重新计算:
        # RIFF header: 12 bytes (RIFF + size + AVI )
        # LIST hdrl header: 12 bytes (LIST + size + hdrl)
        # avih chunk: 8 (tag + size) + 56 (data) = 64 bytes
        # LIST strl header: 12 bytes (LIST + size + strl)
        # strh chunk: 8 (tag + size) + 56 (data) = 64 bytes
        # strh data 起始 = 12 + 12 + 64 + 12 + 8 = 108
        # dwLength offset in strh data = 32
        # 所以 dwLength 文件位置 = 108 + 32 = 140
        fp.seek(108 + 32)
        fp.write(struct.pack("<I", self._frame_count))
        fp.seek(108 + 36)
        fp.write(struct.pack("<I", self._max_frame_size))

        fp.close()


# ═══════════════════════════════════════════════════════════════
# 纯 Python GIF 动画编码器 (GIF89a + LZW)
# ═══════════════════════════════════════════════════════════════

class _GIFWriter:
    """GIF 动画写入器 — 纯手写 GIF89a

    256 色 (3-3-2 量化), LZW 压缩, 动画循环
    """

    def __init__(self, path, width, height, fps):
        self._path = path
        self._width = width
        self._height = height
        self._delay = max(2, 100 // fps)  # 延时 (1/100秒)
        self._frame_count = 0
        self._fp = open(path, "wb")
        self._write_header()

    def _write_header(self):
        """写 GIF 头 + 全局调色板 + 动画扩展"""
        fp = self._fp
        w, h = self._width, self._height

        # GIF 头
        fp.write(b"GIF89a")

        # 逻辑屏幕描述 (7 bytes)
        # 宽度, 高度, 全局颜色表标志(1) + 颜色分辨率(3) + 排序(1) + 表大小(3)
        fp.write(struct.pack("<HH", w, h))
        # GCT flag=1, color resolution=7 (8 bits), sort=0, GCT size=7 (256 colors)
        fp.write(struct.pack("B", 0xF7))
        fp.write(struct.pack("B", 0))  # 背景色索引
        fp.write(struct.pack("B", 0))  # 像素宽高比

        # 全局颜色表 (256 色 × 3 bytes)
        for i in range(256):
            r = ((i >> 5) & 0x07) * 36
            g = ((i >> 2) & 0x07) * 36
            b = (i & 0x03) * 85
            fp.write(struct.pack("BBB", r, g, b))

        # 动画循环扩展 (NETSCAPE 2.0)
        fp.write(b"\x21\xFF\x0B")
        fp.write(b"NETSCAPE2.0")
        fp.write(struct.pack("B", 3))   # 子块大小
        fp.write(struct.pack("B", 1))   # 循环标识
        fp.write(struct.pack("<H", 0))  # 循环次数 (0=无限)
        fp.write(struct.pack("B", 0))   # 块结束

    def add_frame(self, bgr_data):
        """添加一帧 (24-bit 紧凑 BGR, 底部优先, 无行对齐填充)"""
        fp = self._fp
        w, h = self._width, self._height

        # 量化为 256 色索引 (3-3-2)
        indices, _ = _quantize_332(bgr_data, w, h)

        # GIF 图像是顶部优先, 需要翻转行序
        # indices 是按 BGR 数据顺序的 (底部优先), 需要翻转为顶部优先
        flipped = bytearray(len(indices))
        for y in range(h):
            src_off = y * w
            dst_off = (h - 1 - y) * w
            flipped[dst_off:dst_off + w] = indices[src_off:src_off + w]
        indices = bytes(flipped)

        # 图形控制扩展 (延时 + 透明)
        fp.write(b"\x21\xF9\x04")
        fp.write(struct.pack("B", 0))  # 打包: 透明=0
        fp.write(struct.pack("<H", self._delay))
        fp.write(struct.pack("B", 0))  # 透明色索引
        fp.write(struct.pack("B", 0))  # 块结束

        # 图像描述
        fp.write(b"\x2C")  # 图像分隔符
        fp.write(struct.pack("<HH", 0, 0))    # 左, 上
        fp.write(struct.pack("<HH", w, h))    # 宽, 高
        fp.write(struct.pack("B", 0))  # 局部颜色表标志=0

        # LZW 压缩
        min_code_size = 8  # 256 色
        fp.write(struct.pack("B", min_code_size))
        compressed = _lzw_compress(indices, min_code_size)
        fp.write(compressed)

        self._frame_count += 1

    def close(self):
        """写 GIF 结尾, 关闭文件"""
        self._fp.write(b"\x3B")  # GIF 结尾
        self._fp.close()


# ═══════════════════════════════════════════════════════════════
# 屏幕截图器 (Win32 GDI via ctypes)
# ═══════════════════════════════════════════════════════════════

class _ScreenCapturer:
    """屏幕截图器 — 用 Win32 GDI (ctypes) 截取桌面

    零第三方依赖, 纯 ctypes 调系统 API
    仅支持 Windows
    """

    def __init__(self):
        if not _init_win32():
            raise RuntimeError("录屏仅支持 Windows (Win32 GDI)")

        import ctypes
        from ctypes import wintypes

        # 获取屏幕分辨率
        self._width = _user32.GetSystemMetrics(0)  # SM_CXSCREEN
        self._height = _user32.GetSystemMetrics(1)  # SM_CYSCREEN

        # 创建 BITMAPINFOHEADER
        class _BMPHeader(ctypes.Structure):
            _fields_ = [
                ("biSize", wintypes.DWORD),
                ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD),
            ]

        self._bmi = _BMPHeader()
        self._bmi.biSize = ctypes.sizeof(_BMPHeader)
        self._bmi.biWidth = self._width
        self._bmi.biHeight = self._height  # 正=底部优先
        self._bmi.biPlanes = 1
        self._bmi.biBitCount = 24  # BGR
        self._bmi.biCompression = _BI_RGB

        # 行对齐步长
        self._row_padded = (self._width * 3 + 3) & ~3
        self._buf_size = self._row_padded * self._height
        self._buffer = (ctypes.c_ubyte * self._buf_size)()

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def capture(self):
        """截取当前屏幕, 返回 BGR 24-bit 字节 (底部优先, 含行对齐)"""
        import ctypes

        hdc_desktop = _user32.GetDC(0)
        hdc_mem = _gdi32.CreateCompatibleDC(hdc_desktop)
        hbitmap = _gdi32.CreateCompatibleBitmap(hdc_desktop, self._width, self._height)
        old_obj = _gdi32.SelectObject(hdc_mem, hbitmap)

        # BitBlt: 桌面 → 内存 DC
        _gdi32.BitBlt(hdc_mem, 0, 0, self._width, self._height,
                      hdc_desktop, 0, 0, _SRCCOPY | _CAPTUREBLT)

        # GetDIBits: 位图 → 字节缓冲
        _gdi32.GetDIBits(hdc_mem, hbitmap, 0, self._height,
                         self._buffer, ctypes.byref(self._bmi), _DIB_RGB_COLORS)

        # 清理
        _gdi32.SelectObject(hdc_mem, old_obj)
        _gdi32.DeleteObject(hbitmap)
        _gdi32.DeleteDC(hdc_mem)
        _user32.ReleaseDC(0, hdc_desktop)

        return bytes(self._buffer)


# ═══════════════════════════════════════════════════════════════
# 控制台隐藏 / 恢复
# ═══════════════════════════════════════════════════════════════

def _hide_console():
    """隐藏控制台窗口 (仅 Windows)"""
    if not _init_win32():
        return
    hwnd = _kernel32.GetConsoleWindow()
    if hwnd:
        _user32.ShowWindow(hwnd, _SW_HIDE)


def _show_console():
    """恢复控制台窗口 (仅 Windows)"""
    if not _init_win32():
        return
    hwnd = _kernel32.GetConsoleWindow()
    if hwnd:
        _user32.ShowWindow(hwnd, _SW_SHOW)


# ═══════════════════════════════════════════════════════════════
# ffmpeg 检测和转码
# ═══════════════════════════════════════════════════════════════

def _find_ffmpeg():
    """检测系统是否安装了 ffmpeg"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _convert_with_ffmpeg(input_path, output_path, fmt_info):
    """用 ffmpeg 把 AVI 转为目标格式"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", fmt_info["codec"],
    ] + fmt_info.get("extra", []) + [
        "-an",  # 无音频
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return result.returncode == 0


# ═══════════════════════════════════════════════════════════════
# 主模块: _ScreenRecordModule
# ═══════════════════════════════════════════════════════════════

class _ScreenRecordModule:
    """PyMsi.record — 📹 录屏模块 (纯自研, 1.5.3 新增)

    纯手搓的屏幕录制:
        - Win32 GDI 截屏 (ctypes)
        - 纯 Python AVI 编码器
        - 纯 Python GIF 动画编码器 (LZW 压缩)
        - 30+ 输出格式 (ffmpeg 转码)
        - 自动隐藏控制台, 后台静默录制
        - 默认 D:/Videos, 录完输出路径

    用法:
        # 一键录屏
        PM.record()

        # 自定义
        PM.record(duration=60, resolution="4K", fmt="mp4")

        # 分步
        PM.record.duration = 60
        PM.record.format = "gif"
        PM.record.start()

        # 查看格式
        PM.record.formats()

        # 输出路径
        print(PM.record.output)

        # 别名: PM.rec / PM.capture / PM.录屏 / PM.录像
    """

    def __init__(self):
        self.duration = _DEFAULT_DURATION
        self.resolution = _DEFAULT_RESOLUTION
        self.format = _DEFAULT_FORMAT
        self.output_dir = _DEFAULT_OUTPUT_DIR
        self.fps = _DEFAULT_FPS
        self._output_path = None
        self._status = "idle"  # idle / recording / done
        self._stop_flag = False

    def __repr__(self):
        return (f"<PyMsi.record [录屏] duration={self.duration}s "
                f"resolution={self.resolution} format={self.format} "
                f"output_dir={self.output_dir}>")

    # ─── 核心方法 ──────────────────────────────────────

    def __call__(self, duration=None, resolution=None, fmt=None,
                 output_dir=None, fps=None):
        """一键录屏 — 配置参数并立即开始录制

        Args:
            duration: int          录屏时长 (秒), 默认 60
            resolution: str        清晰度 "4K"/"1080p"/"720p"/"native" 等, 默认 "4K"
            fmt: str               输出格式 "avi"/"gif"/"mp4" 等, 默认 "avi"
            output_dir: str        输出目录, 默认 "D:/Videos"
            fps: int (可选)        帧率, 不传则按分辨率自动选择

        Returns:
            str                    输出文件路径

        用法:
            PM.record()                                   # 全默认: 1min, 4K, AVI, D:/Videos
            PM.record(duration=30, fmt="gif")             # 30秒 GIF
            PM.record(duration=60, fmt="mp4", resolution="1080p")  # 1分钟 1080p MP4
        """
        if duration is not None:
            self.duration = duration
        if resolution is not None:
            self.resolution = resolution
        if fmt is not None:
            self.format = fmt
        if output_dir is not None:
            self.output_dir = output_dir
        if fps is not None:
            self.fps = fps

        return self.start()

    def start(self, duration=None, resolution=None, fmt=None,
              output_dir=None, fps=None):
        """开始录屏 (隐藏控制台, 录制, 恢复控制台, 输出路径)

        不传参数则用当前配置 (self.duration / self.resolution / ...)
        """
        # 更新配置
        if duration is not None:
            self.duration = duration
        if resolution is not None:
            self.resolution = resolution
        if fmt is not None:
            self.format = fmt
        if output_dir is not None:
            self.output_dir = output_dir
        if fps is not None:
            self.fps = fps

        # 平台检查
        if not _is_windows:
            raise RuntimeError(
                "录屏仅支持 Windows (Win32 GDI 截屏)\n"
                "Linux/macOS 请使用其他截屏方案"
            )

        # 格式检查
        fmt_lower = self.format.lower()
        if fmt_lower not in _ALL_FORMATS:
            raise ValueError(
                f"不支持的格式: {self.format}\n"
                f"支持 {len(_ALL_FORMATS)} 种格式, 用 PM.record.formats() 查看列表"
            )

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = self._get_extension(fmt_lower)
        filename = f"PyMsi_Record_{timestamp}.{ext}"
        output_path = os.path.join(self.output_dir, filename)

        # 确定截屏分辨率
        capturer = _ScreenCapturer()
        screen_w, screen_h = capturer.width, capturer.height

        # 根据清晰度设置限制
        max_w, max_h = _RESOLUTIONS.get(self.resolution, (0, 0))
        if max_w > 0 and (screen_w > max_w or screen_h > max_h):
            # 屏幕超过目标分辨率, 需要降采样
            cap_w, cap_h = screen_w, screen_h  # 截屏仍用原始分辨率
            need_downscale = True
            target_w = min(screen_w, max_w)
            target_h = min(screen_h, max_h)
        else:
            cap_w, cap_h = screen_w, screen_h
            need_downscale = False
            target_w, target_h = screen_w, screen_h

        # 确定帧率
        if self.fps != _DEFAULT_FPS or self.fps is None:
            # 用户显式设了 fps
            record_fps = self.fps if self.fps else _FPS_MAP.get(self.resolution, 24)
        else:
            record_fps = _FPS_MAP.get(self.resolution, 24)

        # GIF 特殊处理: 限制分辨率和帧率
        is_gif = (fmt_lower == "gif")
        is_pure = (_ALL_FORMATS.get(fmt_lower, ("", "unknown"))[1] == "pure")
        is_bmp_seq = (fmt_lower == "bmp")

        if is_gif:
            if target_w > _GIF_MAX_WIDTH or target_h > _GIF_MAX_HEIGHT:
                need_downscale = True
                # 等比降采样
                ratio = min(_GIF_MAX_WIDTH / target_w, _GIF_MAX_HEIGHT / target_h)
                target_w = int(target_w * ratio)
                target_h = int(target_h * ratio)
            record_fps = _GIF_FPS

        # 确定录制方式
        if is_pure:
            # 纯自研格式
            if is_gif:
                self._record_gif(capturer, output_path, target_w, target_h,
                                 need_downscale, record_fps)
            elif is_bmp_seq:
                self._record_bmp_seq(capturer, output_path, target_w, target_h,
                                     need_downscale, record_fps)
            else:
                # AVI
                self._record_avi(capturer, output_path, target_w, target_h,
                                 need_downscale, record_fps)
        else:
            # ffmpeg 格式: 先录 AVI, 再转码
            temp_avi = os.path.join(self.output_dir, f"_temp_{timestamp}.avi")
            self._record_avi(capturer, temp_avi, target_w, target_h,
                             need_downscale, record_fps)

            # 转码
            fmt_info = _FFMPEG_FORMATS[fmt_lower]
            if not _find_ffmpeg():
                # 没有 ffmpeg, 保留 AVI
                print(f"[PyMsi.record] 未检测到 ffmpeg, 保留 AVI 格式: {temp_avi}")
                output_path = temp_avi
            else:
                print(f"[PyMsi.record] 正在用 ffmpeg 转码为 {fmt_lower}...")
                success = _convert_with_ffmpeg(temp_avi, output_path, fmt_info)
                if success:
                    try:
                        os.remove(temp_avi)
                    except OSError:
                        pass
                else:
                    print(f"[PyMsi.record] 转码失败, 保留 AVI: {temp_avi}")
                    output_path = temp_avi

        self._output_path = output_path
        self._status = "done"
        print(f"[PyMsi.record] 录屏完成: {output_path}")
        return output_path

    def stop(self):
        """停止录屏 (提前结束)"""
        self._stop_flag = True

    # ─── 录制方法 ──────────────────────────────────────

    def _record_avi(self, capturer, output_path, target_w, target_h,
                    need_downscale, fps):
        """录制为 AVI (流式写入, 内存友好)"""
        self._status = "recording"
        self._stop_flag = False

        # 隐藏控制台
        _hide_console()

        writer = _AVIWriter(output_path, target_w, target_h, fps)
        start_time = time.time()
        frame_interval = 1.0 / fps

        try:
            while not self._stop_flag:
                elapsed = time.time() - start_time
                if elapsed >= self.duration:
                    break

                frame_data = capturer.capture()

                if need_downscale:
                    frame_data = _downscale_bgr(
                        frame_data, capturer.width, capturer.height,
                        target_w, target_h
                    )
                else:
                    # 去掉行对齐
                    frame_data = _strip_bmp_padding(
                        frame_data, capturer.width, capturer.height
                    )

                writer.add_frame(frame_data)

                # 控制帧率
                expected = (writer._frame_count) * frame_interval
                now = time.time() - start_time
                if now < expected:
                    time.sleep(expected - now)
        finally:
            writer.close()
            _show_console()

    def _record_gif(self, capturer, output_path, target_w, target_h,
                    need_downscale, fps):
        """录制为 GIF 动画 (先截帧到内存, 再编码)"""
        self._status = "recording"
        self._stop_flag = False

        # 隐藏控制台
        _hide_console()

        # 截取所有帧到内存 (GIF 分辨率小, 内存可控)
        frames = []
        start_time = time.time()
        frame_interval = 1.0 / fps

        try:
            while not self._stop_flag:
                elapsed = time.time() - start_time
                if elapsed >= self.duration:
                    break

                frame_data = capturer.capture()

                if need_downscale:
                    frame_data = _downscale_bgr(
                        frame_data, capturer.width, capturer.height,
                        target_w, target_h
                    )
                else:
                    frame_data = _strip_bmp_padding(
                        frame_data, capturer.width, capturer.height
                    )

                frames.append(frame_data)

                # 控制帧率
                expected = len(frames) * frame_interval
                now = time.time() - start_time
                if now < expected:
                    time.sleep(expected - now)

            # 编码 GIF
            writer = _GIFWriter(output_path, target_w, target_h, fps)
            for frame_data in frames:
                writer.add_frame(frame_data)
            writer.close()
        finally:
            _show_console()

    def _record_bmp_seq(self, capturer, output_path, target_w, target_h,
                        need_downscale, fps):
        """录制为 BMP 帧序列 (每帧一个 BMP 文件)"""
        self._status = "recording"
        self._stop_flag = False

        # 输出目录 (把 output_path 当目录)
        seq_dir = output_path.rsplit(".", 1)[0] + "_bmp"
        os.makedirs(seq_dir, exist_ok=True)

        # 隐藏控制台
        _hide_console()

        start_time = time.time()
        frame_interval = 1.0 / fps
        frame_idx = 0

        try:
            while not self._stop_flag:
                elapsed = time.time() - start_time
                if elapsed >= self.duration:
                    break

                frame_data = capturer.capture()

                if need_downscale:
                    frame_data = _downscale_bgr(
                        frame_data, capturer.width, capturer.height,
                        target_w, target_h
                    )
                else:
                    frame_data = _strip_bmp_padding(
                        frame_data, capturer.width, capturer.height
                    )

                # 写 BMP 文件
                bmp_path = os.path.join(seq_dir, f"frame_{frame_idx:06d}.bmp")
                self._write_bmp(bmp_path, frame_data, target_w, target_h)
                frame_idx += 1

                # 控制帧率
                expected = frame_idx * frame_interval
                now = time.time() - start_time
                if now < expected:
                    time.sleep(expected - now)
        finally:
            _show_console()

        # 把目录路径存为输出
        self._bmp_seq_dir = seq_dir

    @staticmethod
    def _write_bmp(path, bgr_data, width, height):
        """写 24-bit BMP 文件"""
        row_padded = (width * 3 + 3) & ~3
        padding = row_padded - width * 3
        image_size = row_padded * height
        file_size = 54 + image_size

        with open(path, "wb") as fp:
            # BMP 文件头 (14 bytes)
            fp.write(b"BM")
            fp.write(struct.pack("<I", file_size))
            fp.write(struct.pack("<HH", 0, 0))
            fp.write(struct.pack("<I", 54))
            # DIB 头 (40 bytes)
            fp.write(struct.pack("<I", 40))
            fp.write(struct.pack("<i", width))
            fp.write(struct.pack("<i", height))
            fp.write(struct.pack("<HH", 1, 24))
            fp.write(struct.pack("<I", 0))  # BI_RGB
            fp.write(struct.pack("<I", image_size))
            fp.write(struct.pack("<i", 0))
            fp.write(struct.pack("<i", 0))
            fp.write(struct.pack("<I", 0))
            fp.write(struct.pack("<I", 0))
            # 像素数据 (BGR, 底部优先)
            # bgr_data 是无行对齐的, 需要加填充
            for y in range(height):
                off = y * width * 3
                fp.write(bgr_data[off:off + width * 3])
                if padding:
                    fp.write(b"\x00" * padding)

    # ─── 辅助方法 ──────────────────────────────────────

    def _get_extension(self, fmt_lower):
        """获取格式对应的文件扩展名"""
        if fmt_lower in _PURE_FORMATS:
            if fmt_lower == "bmp":
                return "bmp"  # 实际是目录
            return fmt_lower
        if fmt_lower in _FFMPEG_FORMATS:
            return _FFMPEG_FORMATS[fmt_lower]["ext"]
        return fmt_lower

    def formats(self):
        """打印全部支持的 30+ 输出格式"""
        print(f"\n[PyMsi.record] 支持 {len(_ALL_FORMATS)} 种输出格式:\n")
        print("─── 纯自研格式 (不依赖 ffmpeg) ───")
        for name, (desc, kind) in sorted(_PURE_FORMATS.items()):
            print(f"  {name:12s}  {desc}")
        print("\n─── ffmpeg 转码格式 (需要安装 ffmpeg) ───")
        for name, info in sorted(_FFMPEG_FORMATS.items()):
            desc = f"{info['codec']} (ffmpeg 转码)"
            print(f"  {name:12s}  {desc}")
        print(f"\n共 {len(_ALL_FORMATS)} 种格式")
        print("用法: PM.record(fmt='mp4')  或  PM.record.format = 'gif'")
        has_ffmpeg = _find_ffmpeg()
        print(f"ffmpeg: {'已安装' if has_ffmpeg else '未安装 (纯自研格式仍可用)'}")

    # ─── 属性 (只读变量) ──────────────────────────────

    @property
    def output(self):
        """上次录屏的输出文件路径 (只读)"""
        path = getattr(self, "_bmp_seq_dir", None) or self._output_path
        return path

    @property
    def status(self):
        """当前状态: idle / recording / done (只读)"""
        return self._status

    @property
    def input(self):
        """上次录屏的输出路径 (output 别名)"""
        return self.output

    @property
    def result(self):
        """上次录屏的输出路径 (output 别名)"""
        return self.output

    @property
    def path(self):
        """上次录屏的输出路径 (output 别名)"""
        return self.output

    @property
    def file(self):
        """上次录屏的输出路径 (output 别名)"""
        return self.output

    # ─── 别名方法 ──────────────────────────────────────

    def record(self, *args, **kwargs):
        """别名: PM.record.record() == PM.record()"""
        return self.__call__(*args, **kwargs)

    def capture(self, *args, **kwargs):
        """别名: PM.record.capture() == PM.record()"""
        return self.__call__(*args, **kwargs)

    def rec(self, *args, **kwargs):
        """别名: PM.record.rec() == PM.record()"""
        return self.__call__(*args, **kwargs)

    def screen(self, *args, **kwargs):
        """别名: PM.record.screen() == PM.record()"""
        return self.__call__(*args, **kwargs)

    def screencast(self, *args, **kwargs):
        """别名: PM.record.screencast() == PM.record()"""
        return self.__call__(*args, **kwargs)

    def screenrecord(self, *args, **kwargs):
        """别名: PM.record.screenrecord() == PM.record()"""
        return self.__call__(*args, **kwargs)

    def start_recording(self, *args, **kwargs):
        """别名: PM.record.start_recording() == PM.record.start()"""
        return self.start(*args, **kwargs)

    def begin(self, *args, **kwargs):
        """别名: PM.record.begin() == PM.record.start()"""
        return self.start(*args, **kwargs)

    def go(self, *args, **kwargs):
        """别名: PM.record.go() == PM.record.start()"""
        return self.start(*args, **kwargs)

    def run(self, *args, **kwargs):
        """别名: PM.record.run() == PM.record.start()"""
        return self.start(*args, **kwargs)

    def list(self):
        """别名: PM.record.list() == PM.record.formats()"""
        return self.formats()

    def ls(self):
        """别名: PM.record.ls() == PM.record.formats()"""
        return self.formats()

    def help(self):
        """打印帮助"""
        print(self.__doc__)
        self.formats()
