"""
PyMsi.image — 图片处理模块
  · PM.image.ttf()  — 一组图片文件夹 → TTF 字体文件 (位图字形)

支持格式: .png .jpg .jpeg .bmp .ico .gif
GIF 自动拆帧，每帧作为一个独立字形。

实现思路:
  1. 使用 PIL (Pillow) 解码各格式图片 (未装时给出明确提示)
  2. 将每个 PNG 字形直接嵌入到 OpenType `sbix` 表 (Apple/Google 均支持)
     同时提供 `glyf` 占位矢量轮廓，保证字体在所有系统可正常加载
  3. 其余表 (cmap / hmtx / name / head / OS/2 等) 按 TrueType 规范构造
     全部纯 Python 构造，零 C 扩展依赖 (除 PIL 仅用于图片解码)
"""

import os
import io
import re
import struct
import zlib
import tempfile


# ═══════════════════════════════════════════════════════════════
# TTF 写出工具: 表构建 + 字体拼装
# 纯 Python，无依赖，使用标准 TrueType/OpenType 结构
# ═══════════════════════════════════════════════════════════════

def _u16(v): return struct.pack(">H", v & 0xFFFF)
def _i16(v):
    v = v & 0xFFFF
    if v >= 0x8000:
        v -= 0x10000
    return struct.pack(">h", v)
def _u32(v): return struct.pack(">I", v & 0xFFFFFFFF)
def _i32(v):
    v = v & 0xFFFFFFFF
    if v >= 0x80000000:
        v -= 0x100000000
    return struct.pack(">i", v)
def _tag(t): return t.encode("ascii")            # 4 字节表标签


def _calc_checksum(data):
    """TrueType 表 checksum，按 4 字节大端字求和"""
    if len(data) % 4 != 0:
        data = data + b"\x00" * (4 - len(data) % 4)
    s = 0
    for i in range(0, len(data), 4):
        s = (s + struct.unpack(">I", data[i:i+4])[0]) & 0xFFFFFFFF
    return s


def _build_name_table(font_family, font_subfamily="Regular",
                      full_name=None, postscript_name=None, version="1.0"):
    """
    构建 name 表 (0x0001 格式)，中英文通用，写 3 种平台/编码
    """
    if full_name is None:
        full_name = font_family + " " + font_subfamily
    if postscript_name is None:
        postscript_name = re.sub(r"[^A-Za-z0-9-]", "", font_family) + "-" + font_subfamily

    recs = []
    storage = b""

    # nameID:  1 Family, 2 Subfamily, 3 Unique, 4 Full, 5 Version, 6 PostScript
    entries = [
        (1, font_family),
        (2, font_subfamily),
        (3, font_family + ";" + version + ";" + postscript_name),
        (4, full_name),
        (5, "Version " + version),
        (6, postscript_name),
    ]

    # Platform 1 (Macintosh), Encoding 0, Lang 0 (English)
    plat_enc_lang_list = [(1, 0, 0), (3, 1, 0x0409)]  # Mac Roman + Win Unicode US
    for pid, eid, lid in plat_enc_lang_list:
        for name_id, text in entries:
            if pid == 1:
                raw = text.encode("mac_roman", errors="replace")
            else:
                raw = text.encode("utf-16-be", errors="replace")
            offset = len(storage)
            storage += raw
            recs.append(struct.pack(">HHHHHH", pid, eid, lid,
                                    name_id, len(raw), offset))

    header = struct.pack(">HHH", 0, len(recs), 6 + len(recs) * 12)
    return header + b"".join(recs) + storage


def _build_cmap_table(chars):
    """
    构建 cmap 表 — 包含:
      · Format 0 (字节编码, Mac)
      · Format 4 (UCS-2 段映射, 平台 3 Windows)
      · Format 12 (UCS-4 段映射, 支持非 BMP)
    """
    cps = sorted({ord(c) for c in chars if c != "\0"})
    if not cps:
        cps = [0x0020]  # 至少有一个空格

    # ---- Format 0 (字节, Mac) ----
    f0_map = bytearray(256)
    gid_for = {cp: i + 1 for i, cp in enumerate(cps)}  # gid 0 = .notdef
    for cp in cps:
        if cp < 256:
            f0_map[cp] = gid_for[cp] & 0xFF
    fmt0 = struct.pack(">HHH", 0, 262, 0) + bytes(f0_map)

    # ---- Format 4 (UCS-2 段式) ----
    cps_16 = [c for c in cps if c <= 0xFFFF]
    if not cps_16:
        cps_16 = [0x0020]

    # 简单拆成一段 (start = min, end = max)，中间未出现的 = 0
    start_code = min(cps_16)
    end_code = max(cps_16)
    segs = [(start_code, end_code)]

    seg_count = len(segs)
    search_range = 2 * (1 << (seg_count.bit_length() - 1))
    entry_selector = seg_count.bit_length() - 1
    range_shift = seg_count * 2 - search_range

    end_codes = b"".join(_u16(e) for s, e in segs) + _u16(0xFFFF)
    reserved = _u16(0)
    start_codes = b"".join(_u16(s) for s, e in segs) + _u16(0xFFFF)

    # id_delta:  让 gid = cp + id_delta (段内连续的情况下)
    # 这里简单：构造 idRangeOffset + 显式 glyphIdArray
    id_deltas = b""
    id_range_offsets = b""
    glyph_id_array = b""
    arr_offset = 2  # 本字节点末尾段的相对位置 (预留)

    glyph_arr = []
    for seg_idx, (s, e) in enumerate(segs):
        delta_offset = 0
        id_deltas += _u16(0)
        # range offset: 指向 glyphIdArray 对应位置
        pos = (seg_count - seg_idx) * 2 + delta_offset
        id_range_offsets += _u16(pos)
        for cp in range(s, e + 1):
            glyph_arr.append(gid_for.get(cp, 0))

    glyph_id_array = b"".join(_u16(g) for g in glyph_arr)

    length = 14 + (seg_count + 1) * 2 * 3 + seg_count * 2 * 2 + len(glyph_id_array)
    fmt4 = struct.pack(">HHHHHHH", 4, length, 0, seg_count * 2,
                       search_range, entry_selector, range_shift)
    fmt4 += end_codes + reserved + start_codes + id_deltas + id_range_offsets + glyph_id_array

    # ---- Format 12 (UCS-4) ----
    # 每个 glyph 单独一条 group (允许不连续；也可以合并段)
    groups = []
    for cp in cps:
        groups.append((cp, cp, gid_for[cp]))
    n_groups = len(groups)
    fmt12_len = 16 + n_groups * 12
    fmt12 = struct.pack(">HHIII", 12, 0, fmt12_len, 0, n_groups)
    for sg, eg, sgid in groups:
        fmt12 += struct.pack(">III", sg, eg, sgid)

    # 汇总到 cmap 头
    tables_data = []
    tables_data.append((1, 0, 0, fmt0))   # Mac / Roman / Format 0
    tables_data.append((3, 1, 0, fmt4))   # Win / Unicode BMP / Format 4
    tables_data.append((3, 10, 0, fmt12)) # Win / Unicode Full / Format 12

    encoding_records = b""
    body = b""
    off = 4 + len(tables_data) * 8
    for pid, eid, lid, body_data in tables_data:
        encoding_records += struct.pack(">HHI", pid, eid, off)
        off += len(body_data)
        body += body_data

    header = struct.pack(">HI", 0, len(tables_data))
    return header + encoding_records + body


def _build_head_table(units_per_em, index_to_loc_format=0, created=0, modified=0):
    """head 表 (54 字节固定结构)"""
    flags = 0x0003  # baseline=0, lsb=0 (默认)
    data = b""
    data += struct.pack(">HH", 1, 0)                 # version 1.0
    data += struct.pack(">HH", 1, 0)                 # fontRevision 1.0
    data += _u32(0x00000000)                         # checksumAdjustment (后补)
    data += _u32(0x5F0F3CF5)                         # magicNumber
    data += _u16(flags)
    data += _u16(units_per_em)
    data += _i32(created) + _i32(modified)
    data += _i16(0) + _i16(units_per_em)             # xMin yMin → 后面跟 max
    data += _i16(units_per_em) + _i16(0)             # xMax yMax
    data += _u16(0)                                   # macStyle
    data += _u16(8)                                   # lowestRecPPEM
    data += _i16(2)                                   # directionHint (mixed)
    data += _i16(index_to_loc_format)                 # indexToLocFormat
    data += _i16(0)                                   # glyphDataFormat
    return data


def _build_hhea_table(num_h_metrics, ascent, descent, linegap):
    data = b""
    data += struct.pack(">HH", 1, 0)                 # version
    data += _i16(ascent) + _i16(descent) + _i16(linegap)
    data += _u16(ascent)                              # advanceWidthMax
    data += _i16(0)                                   # minLeftSideBearing
    data += _i16(0)                                   # minRightSideBearing
    data += _i16(ascent)                              # xMaxExtent
    data += _i16(1) + _i16(0) + _i16(0)              # caretSlopeRise/Run/Offset
    data += b"\x00" * 8                               # reserved
    data += _i16(0)                                   # metricDataFormat
    data += _u16(num_h_metrics)
    return data


def _build_maxp_table(num_glyphs):
    data = struct.pack(">HH", 0, 1)  # version 0.5
    data += _u16(num_glyphs)
    return data


def _build_hmtx_table(advance_widths, lsbs):
    data = b""
    for aw, lsb in zip(advance_widths, lsbs):
        data += _u16(aw) + _i16(lsb)
    return data


def _build_os2_table(codepage=0x00000001 | 0x00000002,  # ANSI + OEM
                     us_weight_class=400):               # Regular
    """OS/2 表 Version 3 (最小合法字段集)"""
    data = b""
    data += _u16(3)                                      # version
    data += _i16(0)                                      # xAvgCharWidth
    data += _u16(us_weight_class)                        # usWeightClass
    data += _u16(5)                                      # usWidthClass (Medium)
    data += _u16(0)                                      # fsType (Installable)
    data += _i16(0) * 14                                 # ySubscriptX/Y/... ySuperscript... yStrikeout...
    data += _i16(0)                                      # sFamilyClass
    data += b"\x00" * 10                                 # panose
    data += _u32(0) + _u32(0) + _u32(0) + _u32(0)       # ulUnicodeRange 1-4
    data += b"\x00" * 4                                  # achVendID
    data += _u16(0x0040)                                 # fsSelection (Regular)
    data += _u16(0x0020) + _u16(0x007E)                 # usFirst/LastCharIndex
    data += _i16(0) + _i16(0) + _i16(0)                  # sTypo Ascender/Descender/LineGap
    data += _u16(0) + _u16(0)                            # usWin Ascent/Descent
    data += _u32(0) + _u32(0)                            # ulCodePageRange 1-2
    data += codepage.to_bytes(8, "big", signed=False)[:8] if False else _u32(codepage & 0xFFFFFFFF) + _u32(0)
    return data


def _build_post_table(glyph_names):
    """post 表 Version 3.0 (不存名称，最小合法)"""
    data = b""
    data += struct.pack(">HH", 3, 0)                    # version 3.0
    data += _i16(0)                                     # italicAngle
    data += _i16(0) + _i16(0)                           # underlinePosition/Thickness
    data += _u32(0)                                     # isFixedPitch
    data += _u32(0) * 4                                 # min/maxMemType1/42
    return data


def _build_glyf_and_loca_table(glyph_render_sizes, units_per_em):
    """
    为每个 glyph 写一个简单的占位矩形轮廓 (1 个 contour)，
    因为 sbix 位图会覆盖它，但 glyf 表必须存在且合法，
    字形尺寸按传入的 (w, h) 比例缩放，保证 hmtx 合理。

    每个 glyph 生成: 移动到(0,0) → 线到(w,0) → 线到(w,h) → 线到(0,h) → 闭合
    """
    glyf_data = b""
    loca_offsets = [0]

    for gw, gh in glyph_render_sizes:
        n_contours = 1
        end_pts = [3]
        # 指令: 空
        instructions = b""
        # 坐标相对编码 (使用第一个绝对，之后相对)
        xs = [0, gw, gw, 0]
        ys = [0, 0, gh, gh]

        flags_list = []
        x_bytes = b""
        y_bytes = b""
        prev_x, prev_y = 0, 0
        for i, (x, y) in enumerate(zip(xs, ys)):
            dx = x - prev_x
            dy = y - prev_y
            flag = 0x01  # on curve
            if -128 <= dx <= 127:
                flag |= 0x02
                x_bytes += struct.pack("B", dx & 0xFF)
            else:
                flag |= 0x10
                x_bytes += _i16(dx)
            if -128 <= dy <= 127:
                flag |= 0x04
                y_bytes += struct.pack("B", dy & 0xFF)
            else:
                flag |= 0x20
                y_bytes += _i16(dy)
            if i == len(xs) - 1:
                pass
            prev_x, prev_y = x, y
            flags_list.append(flag)

        glyf = b""
        glyf += _i16(n_contours)
        glyf += _i16(min(xs)) + _i16(min(ys)) + _i16(max(xs)) + _i16(max(ys))
        if n_contours > 0:
            glyf += b"".join(_u16(ep) for ep in end_pts)
            glyf += _u16(len(instructions)) + instructions
            glyf += bytes(flags_list)
            glyf += x_bytes
            glyf += y_bytes

        # 4 字节对齐
        if len(glyf) % 2 != 0:
            glyf += b"\x00"

        glyf_data += glyf
        # loca v0 (每个条目 offset/2)
        loca_offsets.append(len(glyf_data) // 2)

    return glyf_data, loca_offsets


def _build_loca_table(loca_offsets, is_long=False):
    if is_long:
        return b"".join(_u32(o * 2) for o in loca_offsets)
    else:
        return b"".join(_u16(o) for o in loca_offsets)


def _build_sbix_table(glyph_png_data_list, strikes=(128,)):
    """
    sbix 表 (标准位图表，Apple/macOS/iOS/Chrome 均识别):

    Header:
      uint16 version        = 1
      uint16 flags          = 1 (位图渲染时优先)
      uint32 numStrikes
      uint32 strikeOffset[numStrikes]

    Strike:
      uint16 ppem           字号
      uint16 resolution     72
      uint32 glyphCount     = num_glyphs
      uint32 offsets[glyphCount+1]  (data relative to strike start)
      each glyph data:
        int16 originOffsetX/Y
        uint16 graphicType  'png '
        raw png data bytes
    """
    num_glyphs = len(glyph_png_data_list)
    strikes = list(strikes)
    num_strikes = len(strikes)

    # 为每个 strike 生成内容
    strikes_bytes = []
    strike_offsets_from_header = []

    header_size = 8 + 4 * num_strikes  # 2+2+4 + numStrikes offsets

    cur_off = header_size
    for ppem in strikes:
        strike_offsets_from_header.append(cur_off)

        # offsets 数组大小
        off_array_size = 4 * (num_glyphs + 1)
        data_start_in_strike = 8 + off_array_size  # ppem(2)+res(2)+count(4) + offsets

        # 构造每个 glyph 数据
        glyph_records_bytes = []
        record_offsets = []
        record_ptr = 0
        for gidx in range(num_glyphs):
            png = glyph_png_data_list[gidx]
            record_offsets.append(data_start_in_strike + record_ptr)
            if png:
                rec = _i16(0) + _i16(0) + b"png " + png
            else:
                rec = b""  # 0 长度 = 该 strike 下无位图
            # 4 字节对齐 (每个 glyph 记录可不对齐，sbix 没要求，保险对齐)
            if len(rec) % 4 != 0:
                rec += b"\x00" * (4 - len(rec) % 4)
            glyph_records_bytes.append(rec)
            record_ptr += len(rec)
        record_offsets.append(data_start_in_strike + record_ptr)  # last offset

        strike_bytes = b""
        strike_bytes += _u16(ppem) + _u16(72) + _u32(num_glyphs)
        strike_bytes += b"".join(_u32(o) for o in record_offsets)
        strike_bytes += b"".join(glyph_records_bytes)
        strikes_bytes.append(strike_bytes)
        cur_off += len(strike_bytes)

    data = b""
    data += _u16(1)                  # version
    data += _u16(1)                  # flags: 1 = render sbix above outline
    data += _u32(num_strikes)
    data += b"".join(_u32(o) for o in strike_offsets_from_header)
    data += b"".join(strikes_bytes)
    return data


def _build_font_file(tables):
    """
    tables: [(tag: bytes, data: bytes), ...]
    按 TTF 规范组装，加上 offset table + directory entries + checksumAdjustment
    """
    # 按 tag 排序 (规范要求)
    tables = sorted(tables, key=lambda x: x[0])

    n = len(tables)
    # 选 searchRange 参数
    p2 = 1 << (n.bit_length() - 1) if n > 0 else 1
    search_range = p2 * 16
    entry_selector = n.bit_length() - 1 if n > 0 else 0
    range_shift = n * 16 - search_range

    sfnt_version = 0x00010000  # TrueType
    header = struct.pack(">IHHHH", sfnt_version, n, search_range,
                         entry_selector, range_shift)

    # 每个表需 4 字节对齐
    entry_size = 16  # per table record
    data_start = len(header) + n * entry_size

    entries = b""
    body = b""
    cur_off = data_start
    for tag, data in tables:
        if len(data) % 4 != 0:
            data = data + b"\x00" * (4 - len(data) % 4)
        csum = _calc_checksum(data)
        entries += tag + _u32(csum) + _u32(cur_off) + _u32(len(data))
        # 保证每个表从 4 字节边界开始
        while len(body) % 4 != 0:
            body += b"\x00"
        body += data
        cur_off = data_start + len(body)

    full = header + entries + body
    # 更新 head 表中的 checksumAdjustment = 0xB1B0AFBA - sum(whole font)
    # head 表位置：找到 head 表在 full 中的偏移
    head_tag = b"head"
    pos = None
    cur = len(header)
    for _ in range(n):
        ttag = full[cur:cur+4]
        toff = struct.unpack(">I", full[cur+8:cur+12])[0]
        if ttag == head_tag:
            pos = toff
            break
        cur += 16

    if pos is None:
        return full

    # head 表内 checksumAdjustment 在偏移 8 (version 之后 + fontRevision 之后 = 4+4=8)
    # 先清 0
    adj_off = pos + 8
    full_arr = bytearray(full)
    struct.pack_into(">I", full_arr, adj_off, 0)
    s = 0
    for i in range(0, len(full_arr), 4):
        chunk = bytes(full_arr[i:i+4])
        if len(chunk) < 4:
            chunk = chunk + b"\x00" * (4 - len(chunk))
        s = (s + struct.unpack(">I", chunk)[0]) & 0xFFFFFFFF
    adjustment = (0xB1B0AFBA - s) & 0xFFFFFFFF
    struct.pack_into(">I", full_arr, adj_off, adjustment)
    return bytes(full_arr)


# ═══════════════════════════════════════════════════════════════
# 图片解码 & 字符推断
# ═══════════════════════════════════════════════════════════════

def _try_import_pil():
    try:
        from PIL import Image
        return Image
    except Exception:
        return None


def _decode_image_to_png(file_path):
    """
    读取任意 PIL 支持的图片格式文件,
    输出 (pil_image, png_bytes, width, height)
    """
    Image = _try_import_pil()
    if Image is None:
        raise RuntimeError(
            "[PyMsi.image.ttf] 需要 Pillow 才能解码图片。\n"
            "           请先运行:  pip install pillow\n"
            "           之后再调用 PM.image.ttf(...)"
        )

    im = Image.open(file_path)
    if im.mode not in ("RGBA", "RGB"):
        # ICO 等可能是 P / L 模式，统一转 RGBA
        im = im.convert("RGBA")

    buf = io.BytesIO()
    im.save(buf, format="PNG")
    png = buf.getvalue()
    return im, png, im.size[0], im.size[1]


def _split_gif(file_path):
    """GIF 拆帧，返回 [(frame_idx, pil_image, png_bytes, w, h), ...]"""
    Image = _try_import_pil()
    if Image is None:
        raise RuntimeError("[PyMsi.image.ttf] 需要 Pillow 才能解码 GIF 帧。请 pip install pillow")

    frames = []
    im = Image.open(file_path)
    idx = 0
    try:
        while True:
            frame = im.copy()
            if frame.mode not in ("RGBA", "RGB"):
                frame = frame.convert("RGBA")
            buf = io.BytesIO()
            frame.save(buf, format="PNG")
            frames.append((idx, frame, buf.getvalue(),
                           frame.size[0], frame.size[1]))
            idx += 1
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return frames


def _infer_char_from_filename(filename, fallback_idx=0):
    """
    根据文件名推断该图片对应哪个 Unicode 字符:
      · "A.png"        → 'A'
      · "中.png"       → '中'
      · "U+4E2D.png"   → '中'
      · "0x4E2D.png"   → '中'
      · "U00004E2D.png"→ '中'
      · 其他乱名       → 按 fallback_idx 顺序映射到 A, B, C... Z, a..z, 0..9, U+E000+
    """
    base = os.path.splitext(os.path.basename(filename))[0]
    s = base.strip()

    # U+XXXX / UXXXXXX / 0xXXXX
    m = re.match(r"^(U\+|0x|U)([0-9a-fA-F]{2,8})$", s)
    if m:
        try:
            cp = int(m.group(2), 16)
            if 0 <= cp <= 0x10FFFF:
                return chr(cp)
        except Exception:
            pass

    # 单字符 (ASCII 或任意 UTF-8 单字符)
    if len(s) == 1:
        return s

    # 非 ASCII 中文日文等多字符, 取首个字符
    if len(s) >= 1 and not s[:1].isascii():
        return s[:1]

    # 多字母取首字母大写
    if s and s[0].isalpha():
        return s[0].upper() if len(s) == 1 else s[0].upper()

    # 回退: fallback_idx
    if fallback_idx < 26:
        return chr(ord("A") + fallback_idx)
    if fallback_idx < 52:
        return chr(ord("a") + fallback_idx - 26)
    if fallback_idx < 62:
        return chr(ord("0") + fallback_idx - 52)
    return chr(0xE000 + fallback_idx - 62)


# ═══════════════════════════════════════════════════════════════
# TTF 模块: PM.image.ttf(...)
# ═══════════════════════════════════════════════════════════════

class _TTFBuilder:
    """可调用对象: PM.image.ttf(...) 的处理器"""

    def __repr__(self):
        return "<PyMsi.image.ttf>  图片 → TTF 位图字体 | 运行 .help() 看教程"

    def __call__(self, folder, output_path, mapping=None,
                 font_name="PyMsiFont", family_name=None,
                 start_char="A", units_per_em=1024,
                 strikes=(128, 256)):
        """
        把一个文件夹里的图片变成 TTF 字体文件 (位图字形, sbix 表)

        Args:
            folder:       图片文件夹路径
            output_path:  输出 .ttf 路径
            mapping:      {文件名: 字符} 可选, 不传则按文件名猜
            font_name:    字体内部 PostScript 名 (无空格 ASCII)
            family_name:  字体显示名 (中文 OK)
            start_char:   GIF 拆帧/无有效名字时的起始字符，默认 'A'
            units_per_em: 字体 em 大小，默认 1024
            strikes:      要内嵌的位图字号 (ppem)，默认 (128, 256)
                          字号越大渲染越清晰，但 TTF 体积会更大
        Returns:
            成功时返回 dict: {"output": str, "chars": int, "size": int}
            失败时打印错误返回 None
        """
        if not os.path.isdir(folder):
            print(f"[PyMsi.image.ttf] ✗ 文件夹不存在: {folder}")
            return None

        family_name = family_name or font_name

        # 收集图片文件
        exts = {".png", ".jpg", ".jpeg", ".bmp", ".ico", ".gif"}
        files = sorted([f for f in os.listdir(folder)
                        if os.path.splitext(f)[1].lower() in exts])
        if not files:
            print(f"[PyMsi.image.ttf] ✗ 文件夹里没有找到支持的图片: {exts}")
            return None

        # 解析每个图片 → (char, pil_im, png_bytes, w, h)
        glyphs = []
        fallback_seq = 0

        if mapping is None:
            mapping = {}

        for fname in files:
            fpath = os.path.join(folder, fname)
            ext = os.path.splitext(fname)[1].lower()

            if ext == ".gif":
                # 拆帧: 每帧对应 A, B, C... 或 start_char 开始递增
                frames = _split_gif(fpath)
                for fi, (_, pil_im, png_bytes, w, h) in enumerate(frames):
                    # 映射优先: 比如 "anim.gif" 无单字映射, 用 start_char + fi
                    char_key = f"{fname}#frame{fi}"
                    if char_key in mapping:
                        ch = mapping[char_key]
                    else:
                        start_cp = ord(start_char[0]) if start_char else ord("A")
                        ch = chr(start_cp + fi)
                    glyphs.append({
                        "char": ch, "src": f"[{fname} frame {fi}]",
                        "png": png_bytes, "w": w, "h": h,
                    })
            else:
                # 静态图: 查 mapping → 或按文件名推断
                if fname in mapping:
                    ch = mapping[fname]
                else:
                    ch = _infer_char_from_filename(fname, fallback_seq)
                    fallback_seq += 1

                _, png_bytes, w, h = _decode_image_to_png(fpath)
                glyphs.append({
                    "char": ch, "src": f"[{fname}]",
                    "png": png_bytes, "w": w, "h": h,
                })

        # 去重: 同一字符多次出现的保留最后一张
        dedup = {}
        for g in glyphs:
            dedup[g["char"]] = g
        glyphs = list(dedup.values())
        if not glyphs:
            print("[PyMsi.image.ttf] ✗ 没有有效字形")
            return None

        # 保证 .notdef + 空格 至少存在
        def ensure(ch):
            if ch not in dedup:
                # 生成 1x1 透明 PNG
                Image = _try_import_pil()
                if Image is None:
                    return
                buf = io.BytesIO()
                Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(buf, format="PNG")
                glyphs.append({"char": ch, "src": f"<auto {repr(ch)}>",
                               "png": buf.getvalue(), "w": 1, "h": 1})
        ensure(" ")

        # 重排序: 先 .notdef (用空格代替, gid=0)，再按字符 cp 升序
        ordered = sorted(glyphs, key=lambda g: ord(g["char"]))
        # 保证 gid 0 永远合法 (使用空格)
        # 如果空格不在首位，把它挪到最前面
        space_idx = None
        for i, g in enumerate(ordered):
            if g["char"] == " ":
                space_idx = i
                break
        if space_idx is not None:
            ordered.insert(0, ordered.pop(space_idx))

        chars = [g["char"] for g in ordered]
        pngs = [g["png"] for g in ordered]
        sizes = [(g["w"], g["h"]) for g in ordered]

        # 统一: 把各 strike 的 PNG 缩放成对应尺寸 (按用户给的 strikes ppem)
        # 这里为简化体积，提供原图用于最大 strike，较小的重新 downsample
        # strikes 越大，字形越清晰，但文件越大
        # 我们对每个 glyph, 每个 strike 生成相应 PNG 列表
        def resize_png(png_bytes, target_side):
            """等比缩放到最长边 <= target_side 并保存 PNG"""
            Image = _try_import_pil()
            if Image is None:
                return png_bytes  # 没 PIL 就原封不动
            im = Image.open(io.BytesIO(png_bytes))
            w, h = im.size
            scale = min(target_side / max(w, 1), target_side / max(h, 1), 1.0)
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
            if (nw, nh) == (w, h):
                return png_bytes
            resized = im.resize((nw, nh), Image.LANCZOS)
            if resized.mode not in ("RGBA", "RGB"):
                resized = resized.convert("RGBA")
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            return buf.getvalue()

        strikes = tuple(sorted(set(int(s) for s in strikes if s > 0)))
        if not strikes:
            strikes = (128,)

        strike_pngs = {}  # strike_ppem -> [png per glyph]
        for strike in strikes:
            per_glyph = []
            for g in ordered:
                per_glyph.append(resize_png(g["png"], strike))
            strike_pngs[strike] = per_glyph

        # 计算每个 glyph 在 units_per_em 下的 advanceWidth + 占位轮廓尺寸
        # 让最高 glyph.height = units_per_em * 0.8 (留出一点行间距)
        max_h = max(g["h"] for g in ordered) or 1
        scale = (units_per_em * 0.8) / max_h
        render_sizes = []
        advance_widths = []
        lsbs = []
        for g in ordered:
            gw = max(1, int(g["w"] * scale))
            gh = max(1, int(g["h"] * scale))
            render_sizes.append((gw, gh))
            advance_widths.append(gw + max(1, int(0.08 * units_per_em)))
            lsbs.append(0)

        num_glyphs = len(ordered)

        # ---- 构建各表 ----
        head = _build_head_table(units_per_em, index_to_loc_format=0)
        hhea = _build_hhea_table(num_glyphs,
                                 ascent=int(units_per_em * 0.85),
                                 descent=-int(units_per_em * 0.2),
                                 linegap=int(units_per_em * 0.1))
        maxp = _build_maxp_table(num_glyphs)
        os2 = _build_os2_table()
        post = _build_post_table([None] * num_glyphs)
        cmap = _build_cmap_table(chars)
        name = _build_name_table(family_name, font_subfamily="Regular",
                                 full_name=family_name,
                                 version="1.0")
        hmtx = _build_hmtx_table(advance_widths, lsbs)

        glyf_data, loca_offsets = _build_glyf_and_loca_table(render_sizes, units_per_em)
        loca = _build_loca_table(loca_offsets, is_long=False)

        # sbix: 为每个 strike 提供位图
        # sbix 的 glyph_png_data_list 顺序对应 gid
        # 我们把最大 strike 提供所有；其他 strike 用下采样版
        # sbix API 需要 per-strike；我们合并为一张表：
        sbix_strikes = list(strikes)
        # 每个 glyph 对应所有 strike，组装到一个结构:
        # strike_pngs 里已有每个 strike 的 png 列表 → 传进去统一合并
        # 为简单用 _build_sbix_table 单 strike 多次调用再手动合并太麻烦；
        # 直接修改 _build_sbix_table 为支持每个 strike 单独 PNG 列表
        sbix = _build_sbix_table_multi(strike_pngs)

        tables = [
            (b"cmap", cmap),
            (b"head", head),
            (b"hhea", hhea),
            (b"hmtx", hmtx),
            (b"maxp", maxp),
            (b"name", name),
            (b"OS/2", os2),
            (b"post", post),
            (b"glyf", glyf_data),
            (b"loca", loca),
            (b"sbix", sbix),
        ]

        out_bytes = _build_font_file(tables)
        with open(output_path, "wb") as f:
            f.write(out_bytes)

        chars_list_str = ", ".join(
            f"'{c}'" if c.isprintable() and ord(c) < 128 else f"U+{ord(c):04X}"
            for c in chars[:12]
        )
        if len(chars) > 12:
            chars_list_str += f" ... +{len(chars)-12} 个"

        print(f"[PyMsi.image.ttf] ✓ 字体已生成 -> {output_path}")
        print(f"                  字符数: {len(chars)}  字节: {len(out_bytes):,}")
        print(f"                  字符: {chars_list_str}")

        return {"output": os.path.abspath(output_path),
                "chars": len(chars),
                "size": len(out_bytes)}

    # ─── TTF 模块方法别名 ───
    def build(self, folder, output_path, mapping=None,
              font_name="PyMsiFont", family_name=None,
              start_char="A", units_per_em=1024, strikes=(128, 256)):
        """别名: PM.image.ttf.build(...) = 直接调用 PM.image.ttf(...)"""
        return self.__call__(folder, output_path, mapping=mapping,
                             font_name=font_name, family_name=family_name,
                             start_char=start_char, units_per_em=units_per_em,
                             strikes=strikes)

    def make(self, *a, **kw):
        """别名: PM.image.ttf.make(...)"""
        return self.__call__(*a, **kw)

    def run(self, *a, **kw):
        """别名"""
        return self.__call__(*a, **kw)

    def go(self, *a, **kw):
        """别名"""
        return self.__call__(*a, **kw)

    def generate(self, *a, **kw):
        """别名: PM.image.ttf.generate(...)"""
        return self.__call__(*a, **kw)

    def create(self, *a, **kw):
        """别名"""
        return self.__call__(*a, **kw)

    def man(self):
        """别名: PM.image.ttf.man() = .help()"""
        self.help()

    def doc(self):
        """别名: PM.image.ttf.doc() = .help()"""
        self.help()

    def guide(self):
        """别名"""
        self.help()

    # ─── 帮助文档 ───
    def help(self):
        print("=" * 62)
        print("  PyMsi.image.ttf — 图片 → TTF 位图字体 (使用指南)")
        print("=" * 62)
        print()
        print("【前置: 装 Pillow (第一次)】")
        print("    pip install pillow")
        print("    (PyMsi 本体不强制依赖，只在调用 image.ttf 时需要)")
        print()
        print("【方式一：最简单的命名法】")
        print("  把每个字形图片命名为对应的字符，放同一个文件夹:")
        print()
        print("    C:/myglyphs/")
        print("      ├─ A.png              ← 字符 'A'")
        print("      ├─ B.png")
        print("      ├─ a.png              ← 字符 'a'")
        print("      ├─ 0.png ... 9.png    ← 数字")
        print("      ├─ 中.png             ← 中文 '中'")
        print("      └─ U+4E2D.png         ← 也支持 Unicode 编号")
        print()
        print("  然后一行代码生成:")
        print('    import PyMsi as PM')
        print('    PM.image.ttf("C:/myglyphs", "我的字体.ttf")')
        print()
        print("【方式二：自定义 mapping 字典】")
        print("    mapping = {")
        print('        "glyph_001.png": "A",')
        print('        "glyph_002.png": "中",')
        print('        "glyph_003.png": "😀",')
        print("    }")
        print('    PM.image.ttf("C:/glyphs", "my.ttf", mapping=mapping)')
        print()
        print("【方式三：GIF 拆帧 → 多字形】")
        print("  把动画 GIF 放到文件夹，每帧按顺序对应一个字符:")
        print("    frames.gif (共 26 帧) → A B C ... Z")
        print('    PM.image.ttf("C:/gif_folder", "out.ttf")')
        print("    默认从 A 开始，要改起点:")
        print('    PM.image.ttf("C:/gf", "o.ttf", start_char="0")   # 从 0 开始')
        print()
        print("【支持的图片格式】")
        print("  .png .jpg .jpeg .bmp .ico .gif  (GIF 拆帧处理)")
        print()
        print("【技术细节】")
        print("  每个图片作为位图字形嵌入 TTF 的 sbix 表；")
        print("  同时会自动生成占位矢量轮廓 (glyf) 以便任何软件都能加载；")
        print("  默认内嵌 128px 和 256px 两种分辨率 (strikes)。")
        print()
        print("【自定义 strikes 让字更大/更小】")
        print('    PM.image.ttf("in", "out.ttf", strikes=(64, 128, 512))')
        print("=" * 62)


# ═══════════════════════════════════════════════════════════════
# sbix 表构建: 支持每个 strike 独立 PNG 列表
# ═══════════════════════════════════════════════════════════════

def _build_sbix_table_multi(strike_pngs):
    """
    strike_pngs: { ppem: [png_bytes_per_glyph, ...], ... }
    """
    if not strike_pngs:
        return _build_sbix_table([])

    ppems = sorted(strike_pngs.keys())
    num_strikes = len(ppems)

    sample = strike_pngs[ppems[0]]
    num_glyphs = len(sample)

    header_size = 8 + 4 * num_strikes
    strikes_bytes_list = []
    strike_offsets = []

    cur_off = header_size
    for ppem in ppems:
        strike_offsets.append(cur_off)
        pngs = strike_pngs[ppem]

        off_array_size = 4 * (num_glyphs + 1)
        data_start = 8 + off_array_size

        record_offsets = []
        records = b""
        rec_ptr = 0
        for idx in range(num_glyphs):
            record_offsets.append(data_start + rec_ptr)
            png = pngs[idx] if idx < len(pngs) else None
            if png:
                rec = _i16(0) + _i16(0) + b"png " + png
            else:
                rec = b""
            if len(rec) % 4 != 0:
                rec += b"\x00" * (4 - len(rec) % 4)
            records += rec
            rec_ptr += len(rec)
        record_offsets.append(data_start + rec_ptr)  # 末尾哨兵

        strike_bytes = _u16(ppem) + _u16(72) + _u32(num_glyphs)
        strike_bytes += b"".join(_u32(o) for o in record_offsets)
        strike_bytes += records
        strikes_bytes_list.append(strike_bytes)
        cur_off += len(strike_bytes)

    data = _u16(1) + _u16(1) + _u32(num_strikes)
    data += b"".join(_u32(o) for o in strike_offsets)
    data += b"".join(strikes_bytes_list)
    return data


# ═══════════════════════════════════════════════════════════════
# 顶层 image 模块: PM.image.ttf 指向 _TTFBuilder 实例
# ═══════════════════════════════════════════════════════════════

class _ImageModule:
    """
    PyMsi.image — 图片处理模块
      PM.image.ttf(...) — 图片文件夹 → TTF 字体
    """
    def __init__(self):
        self._ttf = _TTFBuilder()

    def __repr__(self):
        return "<PyMsi.image>  功能: .ttf(图片文件夹, 输出.ttf)"

    def __call__(self, folder, output_path, **kwargs):
        """PM.image(folder, out.ttf) 短调用 = PM.image.ttf(...)"""
        return self._ttf(folder, output_path, **kwargs)

    @property
    def ttf(self):
        """返回可调用的 _TTFBuilder 实例，支持:
            PM.image.ttf(folder, out.ttf)
            PM.image.ttf.help()
        """
        return self._ttf

    # ─── Image 模块别名 ───
    @property
    def font(self):
        """别名: PM.image.font(...) = PM.image.ttf(...)"""
        return self._ttf

    @property
    def fonts(self):
        """别名"""
        return self._ttf

    @property
    def otf(self):
        """别名 (实际输出仍为 TTF)"""
        return self._ttf

    def make_font(self, folder, output_path, **kw):
        """别名"""
        return self._ttf(folder, output_path, **kw)

    def build_font(self, folder, output_path, **kw):
        """别名"""
        return self._ttf(folder, output_path, **kw)

    def to_font(self, folder, output_path, **kw):
        """别名"""
        return self._ttf(folder, output_path, **kw)

    def to_ttf(self, folder, output_path, **kw):
        """别名"""
        return self._ttf(folder, output_path, **kw)
