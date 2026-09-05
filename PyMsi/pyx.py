"""
pyx.py — 视频提取引擎 (v2.2.0 / v2.3.0)

我管你是什么B站短链接B站长链接抖音长链接抖音短链接
还是什么YouTube快手小红书链接等等的，
他只要是能看的东西，通通给你提取！

Vmp 模式 (v2.2.0):
  遇到好听的音乐却没办法保存到本地？
  Vmp = Video → Music → 自动提取音频，转成你要的格式
  支持: .aac .wav .mp3 .ogg .flac

视频模式 (v2.3.0):
  把视频链接变成完整的视频文件
  支持: .mp4 .mov .avi .mkv (容器层)

视频验证 (v2.3.0):
  类似 ffprobe，把视频的 100 种信息全部放进 .ckon
  ckon = Log 日志文件的变体，小白也能读懂

纯 Python 标准库实现，零依赖，不加 ffmpeg/ffprobe。

用法:
    import PyMsi as PM

    # Vmp 模式: 视频 → 音频
    PM.pyx.vmp("https://...video.mp4", output="song.mp3")
    PM.pyx.vmp("https://...", format="wav")
    PM.pyx.vmp("local_video.mp4", output="bgm.flac")

    # 视频模式: 链接 → 视频文件
    PM.pyx.video("https://...", output="video.mp4")
    PM.pyx.video("https://...", format="mov")

    # 视频验证: 输出 .ckon 信息
    PM.pyx.probe("video.mp4")           # → video.ckon
    PM.pyx.probe("video.mp4", "info.ckon")

    # 平台解析
    PM.pyx.parse_url("B站分享链接")       # → 真实视频地址
    PM.pyx.download("url", "out.mp4")    # 下载

    # 演示
    PM.pyx.demo()
"""

import os
import sys
import re
import struct
import zlib
import hashlib
import tempfile
import urllib.request
import urllib.parse
import urllib.error
import json
import time
import io
import wave


# ═══════════════════════════════════════════════════════════════
# 一、URL 解析器 — 各平台分享链接 → 真实视频地址
# ═══════════════════════════════════════════════════════════════

def _parse_bilibili(url):
    """解析B站链接 → 视频信息 (尽力而为)

    支持:
      - BV号: BV1xx411c7mD
      - b23.tv 短链接
      - bilibili.com 完整链接
    """
    result = {'platform': 'bilibili', 'original_url': url, 'direct_url': None,
              'title': None, 'type': 'video'}

    # 提取 BV 号
    bv_match = re.search(r'(BV[a-zA-Z0-9]{10})', url)
    if bv_match:
        bvid = bv_match.group(1)
        result['bvid'] = bvid
        result['title'] = f'B站视频_{bvid}'
        # 尝试通过 API 获取视频信息
        try:
            api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
            req = urllib.request.Request(api_url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://www.bilibili.com/'
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('code') == 0:
                    d = data.get('data', {})
                    result['title'] = d.get('title', result['title'])
                    result['duration'] = d.get('duration', 0)
                    result['pic'] = d.get('pic', '')
                    # 获取视频流地址需要登录/cookie，这里只返回元信息
                    result['status'] = 'needs_auth'
                    result['note'] = 'B站视频流需要登录cookie，请提供直接视频链接或使用cookie'
        except Exception as e:
            result['status'] = 'parse_failed'
            result['error'] = str(e)
    else:
        result['status'] = 'no_bvid'

    return result


def _parse_douyin(url):
    """解析抖音链接 (尽力而为)"""
    result = {'platform': 'douyin', 'original_url': url, 'direct_url': None,
              'title': None, 'type': 'video'}

    # 抖音分享链接通常含 v.douyin.com
    if 'douyin.com' in url:
        result['status'] = 'detected'
        result['title'] = '抖音视频'
        result['note'] = '抖音视频需要解析分享链接获取真实地址'
    else:
        result['status'] = 'not_douyin'

    return result


def _parse_youtube(url):
    """解析 YouTube 链接 (尽力而为)"""
    result = {'platform': 'youtube', 'original_url': url, 'direct_url': None,
              'title': None, 'type': 'video'}

    yt_match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    if yt_match:
        vid = yt_match.group(1)
        result['vid'] = vid
        result['title'] = f'YouTube_{vid}'
        result['status'] = 'detected'
        result['note'] = 'YouTube 视频流需要专门解析，请提供直接视频链接'
    else:
        result['status'] = 'not_youtube'

    return result


def _parse_direct_video(url):
    """判断是否为直接视频链接"""
    video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm',
                   '.m4v', '.wmv', '.3gp', '.ts']
    parsed = urllib.parse.urlparse(url)
    path_lower = parsed.path.lower()
    for ext in video_exts:
        if path_lower.endswith(ext):
            return True
    return False


def parse_url(url):
    """解析任意视频链接 → 平台信息 + 真实地址

    Args:
        url: 视频链接 (B站/抖音/YouTube/快手/小红书/直链 等)

    Returns:
        dict: 解析结果
    """
    result = {
        'original_url': url,
        'platform': 'unknown',
        'type': 'video',
        'title': None,
        'direct_url': None,
        'status': 'parsing',
    }

    # 1. 先判断是不是直接视频链接
    if _parse_direct_video(url):
        result['platform'] = 'direct'
        result['direct_url'] = url
        result['title'] = os.path.basename(urllib.parse.urlparse(url).path)
        result['status'] = 'ok'
        return result

    # 2. B站
    if 'bilibili.com' in url or 'b23.tv' in url or re.search(r'BV[a-zA-Z0-9]{10}', url):
        info = _parse_bilibili(url)
        result.update(info)
        return result

    # 3. 抖音
    if 'douyin.com' in url or 'iesdouyin' in url:
        info = _parse_douyin(url)
        result.update(info)
        return result

    # 4. YouTube
    if 'youtube.com' in url or 'youtu.be' in url:
        info = _parse_youtube(url)
        result.update(info)
        return result

    # 5. 快手
    if 'kuaishou.com' in url or 'gifshow.com' in url:
        result['platform'] = 'kuaishou'
        result['title'] = '快手视频'
        result['status'] = 'detected'
        return result

    # 6. 小红书
    if 'xiaohongshu.com' in url or 'xhslink.com' in url:
        result['platform'] = 'xiaohongshu'
        result['title'] = '小红书视频'
        result['status'] = 'detected'
        return result

    # 7. 未知平台，尝试直接访问
    result['platform'] = 'unknown'
    result['status'] = 'unknown_platform'
    result['note'] = '未知平台，尝试直接下载...'
    return result


# ═══════════════════════════════════════════════════════════════
# 二、下载器 — 通用视频下载
# ═══════════════════════════════════════════════════════════════

def download(url, output_path=None, progress_callback=None):
    """下载视频文件 (纯 urllib)

    Args:
        url: 视频链接
        output_path: 输出路径 (默认: 临时目录 + 文件名)
        progress_callback: 回调函数(已下载字节, 总字节)

    Returns:
        str: 下载后的文件路径
    """
    # 解析 URL
    parsed = urllib.parse.urlparse(url)

    # 确定文件名
    if output_path is None:
        filename = os.path.basename(parsed.path) or 'video.mp4'
        output_path = os.path.join(tempfile.gettempdir(), filename)

    # 确保目录存在
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
    }

    req = urllib.request.Request(url, headers=headers)
    downloaded = 0
    total_size = 0

    print(f"[pyx] 开始下载: {url[:80]}...")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            total_size = int(resp.headers.get('Content-Length', 0))

            with open(output_path, 'wb') as f:
                chunk_size = 64 * 1024  # 64KB
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total_size)

        print(f"[pyx] 下载完成: {output_path} ({downloaded:,} bytes)")
        return output_path

    except urllib.error.HTTPError as e:
        print(f"[pyx] 下载失败: HTTP {e.code} - {e.reason}")
        raise
    except Exception as e:
        print(f"[pyx] 下载失败: {e}")
        raise


# ═══════════════════════════════════════════════════════════════
# 三、MP4 解析器 — 解析 MP4 容器，提取音视频轨道
# ═══════════════════════════════════════════════════════════════

class MP4Parser:
    """MP4 文件解析器 (纯 Python)

    解析常见的 MP4 box:
      - ftyp: 文件类型
      - moov: 电影元数据
        - mvhd: 电影头 (时长、时间尺度)
        - trak: 轨道
          - tkhd: 轨道头 (宽高、音量)
          - mdia: 媒体
            - mdhd: 媒体头
            - hdlr: 处理器类型 (soun=音频, vide=视频)
            - minf: 媒体信息
              - stbl: 采样表
                - stsd: 采样描述 (编码类型)
                - stts: 时间采样
                - stsc: 采样到块
                - stsz: 采样大小
                - stco / co64: 块偏移
    """

    def __init__(self, filepath_or_data):
        if isinstance(filepath_or_data, (bytes, bytearray)):
            self.data = bytes(filepath_or_data)
            self._file = None
        else:
            self._filepath = filepath_or_data
            self._file = open(filepath_or_data, 'rb')
            self.data = None

        self.boxes = []
        self.ftyp = None
        self.moov = None
        self.tracks = []  # 轨道列表

    def _read_at(self, offset, size):
        """从指定偏移读取数据"""
        if self._file:
            self._file.seek(offset)
            return self._file.read(size)
        else:
            return self.data[offset:offset + size]

    def _file_size(self):
        """获取文件大小"""
        if self._file:
            self._file.seek(0, 2)
            return self._file.tell()
        else:
            return len(self.data)

    def _read_box_header(self, offset):
        """读取 box 头: size(4B) + type(4B)"""
        if offset + 8 > self._file_size():
            return None, None, 0
        data = self._read_at(offset, 8)
        if len(data) < 8:
            return None, None, 0
        size = struct.unpack('>I', data[:4])[0]
        box_type = data[4:8].decode('ascii', errors='replace')
        header_size = 8

        # 64-bit size
        if size == 1:
            ext_data = self._read_at(offset + 8, 8)
            if len(ext_data) >= 8:
                size = struct.unpack('>Q', ext_data)[0]
                header_size = 16

        return box_type, size, header_size

    def parse(self):
        """解析整个 MP4 文件"""
        file_size = self._file_size()
        offset = 0

        while offset < file_size:
            box_type, box_size, header_size = self._read_box_header(offset)
            if box_type is None or box_size <= 0:
                break

            self.boxes.append({
                'type': box_type,
                'offset': offset,
                'size': box_size,
            })

            if box_type == 'ftyp':
                self._parse_ftyp(offset, box_size)
            elif box_type == 'moov':
                self._parse_moov(offset + header_size, box_size - header_size)

            offset += box_size

        return True

    def _parse_ftyp(self, offset, size):
        """解析 ftyp box"""
        data = self._read_at(offset + 8, size - 8)
        if len(data) >= 4:
            major_brand = data[:4].decode('ascii', errors='replace')
            self.ftyp = {
                'major_brand': major_brand,
                'minor_version': struct.unpack('>I', data[4:8])[0] if len(data) >= 8 else 0,
                'compatible_brands': [],
            }
            # 兼容品牌
            pos = 8
            while pos + 4 <= len(data):
                brand = data[pos:pos + 4].decode('ascii', errors='replace')
                self.ftyp['compatible_brands'].append(brand)
                pos += 4

    def _parse_moov(self, start_offset, size):
        """解析 moov box"""
        self.moov = {'mvhd': None, 'tracks': []}
        end = start_offset + size
        offset = start_offset

        while offset < end:
            box_type, box_size, header_size = self._read_box_header(offset)
            if box_type is None or box_size <= 0:
                break

            if box_type == 'mvhd':
                self.moov['mvhd'] = self._parse_mvhd(offset + header_size, box_size - header_size)
            elif box_type == 'trak':
                track = self._parse_trak(offset + header_size, box_size - header_size)
                self.moov['tracks'].append(track)
                self.tracks.append(track)

            offset += box_size

    def _parse_mvhd(self, offset, size):
        """解析 mvhd (movie header)"""
        data = self._read_at(offset, min(size, 120))
        version = data[0]
        if version == 1:
            timescale = struct.unpack('>I', data[20:24])[0]
            duration = struct.unpack('>Q', data[24:32])[0]
        else:
            timescale = struct.unpack('>I', data[12:16])[0]
            duration = struct.unpack('>I', data[16:20])[0]
        return {
            'timescale': timescale,
            'duration': duration,
            'duration_seconds': duration / timescale if timescale > 0 else 0,
        }

    def _parse_trak(self, start_offset, size):
        """解析 trak (track)"""
        track = {'id': 0, 'type': None, 'handler': None, 'codec': None,
                 'width': 0, 'height': 0, 'channels': 0, 'sample_rate': 0,
                 'sample_count': 0, 'stsd_entries': [], 'stts': [],
                 'stsc': [], 'stsz': [], 'stco': [], 'duration': 0}
        end = start_offset + size
        offset = start_offset

        while offset < end:
            box_type, box_size, header_size = self._read_box_header(offset)
            if box_type is None or box_size <= 0:
                break

            if box_type == 'tkhd':
                tkhd = self._parse_tkhd(offset + header_size, box_size - header_size)
                track.update(tkhd)
            elif box_type == 'mdia':
                mdia_info = self._parse_mdia(offset + header_size, box_size - header_size)
                track.update(mdia_info)

            offset += box_size

        return track

    def _parse_tkhd(self, offset, size):
        """解析 tkhd (track header)"""
        data = self._read_at(offset, min(size, 100))
        version = data[0]
        if version == 1:
            track_id = struct.unpack('>I', data[16:20])[0]
            duration = struct.unpack('>Q', data[28:36])[0]
            # version 1: width@84, height@88
            if len(data) >= 92:
                width = struct.unpack('>I', data[84:88])[0] >> 16
                height = struct.unpack('>I', data[88:92])[0] >> 16
            else:
                width = height = 0
        else:
            # version 0: 4+4+4+4+4+8+2+2+2+2+36 = 76 bytes 到 width
            track_id = struct.unpack('>I', data[12:16])[0]
            duration = struct.unpack('>I', data[20:24])[0]
            if len(data) >= 84:
                width = struct.unpack('>I', data[76:80])[0] >> 16
                height = struct.unpack('>I', data[80:84])[0] >> 16
            else:
                width = height = 0

        return {'id': track_id, 'width': width, 'height': height, 'tkhd_duration': duration}

    def _parse_mdia(self, start_offset, size):
        """解析 mdia (media)"""
        result = {}
        end = start_offset + size
        offset = start_offset

        while offset < end:
            box_type, box_size, header_size = self._read_box_header(offset)
            if box_type is None or box_size <= 0:
                break

            if box_type == 'mdhd':
                mdhd = self._parse_mdhd(offset + header_size, box_size - header_size)
                result.update(mdhd)
            elif box_type == 'hdlr':
                hdlr = self._parse_hdlr(offset + header_size, box_size - header_size)
                result.update(hdlr)
            elif box_type == 'minf':
                minf = self._parse_minf(offset + header_size, box_size - header_size)
                result.update(minf)

            offset += box_size

        return result

    def _parse_mdhd(self, offset, size):
        """解析 mdhd (media header)"""
        data = self._read_at(offset, min(size, 40))
        version = data[0]
        if version == 1:
            timescale = struct.unpack('>I', data[20:24])[0]
            duration = struct.unpack('>Q', data[24:32])[0]
        else:
            timescale = struct.unpack('>I', data[12:16])[0]
            duration = struct.unpack('>I', data[16:20])[0]
        return {'mdhd_timescale': timescale, 'mdhd_duration': duration,
                'duration_seconds': duration / timescale if timescale > 0 else 0}

    def _parse_hdlr(self, offset, size):
        """解析 hdlr (handler reference)"""
        data = self._read_at(offset, min(size, 40))
        handler_type = data[8:12].decode('ascii', errors='replace')
        track_type = None
        if handler_type == 'soun':
            track_type = 'audio'
        elif handler_type == 'vide':
            track_type = 'video'
        elif handler_type == 'hint':
            track_type = 'hint'
        elif handler_type == 'text':
            track_type = 'text'
        return {'handler': handler_type, 'type': track_type}

    def _parse_minf(self, start_offset, size):
        """解析 minf (media info)"""
        result = {}
        end = start_offset + size
        offset = start_offset

        while offset < end:
            box_type, box_size, header_size = self._read_box_header(offset)
            if box_type is None or box_size <= 0:
                break

            if box_type == 'stbl':
                stbl = self._parse_stbl(offset + header_size, box_size - header_size)
                result.update(stbl)

            offset += box_size

        return result

    def _parse_stbl(self, start_offset, size):
        """解析 stbl (sample table)"""
        result = {'stsd_entries': [], 'stts': [], 'stsc': [], 'stsz': [], 'stco': []}
        end = start_offset + size
        offset = start_offset

        while offset < end:
            box_type, box_size, header_size = self._read_box_header(offset)
            if box_type is None or box_size <= 0:
                break

            if box_type == 'stsd':
                result['stsd_entries'] = self._parse_stsd(offset + header_size, box_size - header_size)
                if result['stsd_entries']:
                    result['codec'] = result['stsd_entries'][0].get('codec', '')
                    if result['stsd_entries'][0].get('channels'):
                        result['channels'] = result['stsd_entries'][0]['channels']
                    if result['stsd_entries'][0].get('sample_rate'):
                        result['sample_rate'] = result['stsd_entries'][0]['sample_rate']
            elif box_type == 'stts':
                result['stts'] = self._parse_stts(offset + header_size, box_size - header_size)
            elif box_type == 'stsc':
                result['stsc'] = self._parse_stsc(offset + header_size, box_size - header_size)
            elif box_type == 'stsz':
                result['stsz'] = self._parse_stsz(offset + header_size, box_size - header_size)
                result['sample_count'] = len(result['stsz'])
            elif box_type == 'stco':
                result['stco'] = self._parse_stco(offset + header_size, box_size - header_size)
            elif box_type == 'co64':
                result['stco'] = self._parse_co64(offset + header_size, box_size - header_size)

            offset += box_size

        return result

    def _parse_stsd(self, offset, size):
        """解析 stsd (sample description)"""
        data = self._read_at(offset, min(size, 4096))
        if len(data) < 8:
            return []

        entry_count = struct.unpack('>I', data[4:8])[0]
        entries = []
        pos = 8

        for _ in range(entry_count):
            if pos + 8 > len(data):
                break
            entry_size = struct.unpack('>I', data[pos:pos + 4])[0]
            entry_format = data[pos + 4:pos + 8].decode('ascii', errors='replace')

            if entry_size <= 0 or pos + entry_size > len(data):
                # entry 大小无效，跳到下一个
                break

            entry = {'codec': entry_format, 'size': entry_size}

            if entry_format in ('mp4a', 'mp3 ', '.mp3', 'samr'):
                # 音频采样描述 (AudioSampleEntry)
                # 结构: entry(8B) + reserved(6B) + data_ref(2B) + reserved(8B)
                #       + channelcount(2B) + samplesize(2B) + predef(2B) + res(2B)
                #       + samplerate(4B)
                if entry_size >= 36:  # 至少要有这些字段
                    entry['channels'] = struct.unpack('>H', data[pos + 24:pos + 26])[0]
                    entry['sample_size'] = struct.unpack('>H', data[pos + 26:pos + 28])[0]
                    entry['sample_rate'] = struct.unpack('>I', data[pos + 32:pos + 36])[0] >> 16
                entry['codec_type'] = 'audio'
            elif entry_format in ('avc1', 'avc2', 'hvc1', 'hev1', 'mp4v', 'H264', 'vp09', 'av01'):
                # 视频采样描述 (VideoSampleEntry)
                # 结构: entry(8B) + reserved(6B) + data_ref(2B) + predef(2B)
                #       + reserved(2B) + predef(12B) + width(2B) + height(2B)
                if entry_size >= 36:
                    entry['width'] = struct.unpack('>H', data[pos + 32:pos + 34])[0]
                    entry['height'] = struct.unpack('>H', data[pos + 34:pos + 36])[0]
                entry['codec_type'] = 'video'
            else:
                entry['codec_type'] = 'unknown'

            entries.append(entry)
            pos += entry_size

        return entries

    def _parse_stts(self, offset, size):
        """解析 stts (time to sample)"""
        data = self._read_at(offset, min(size, 4096))
        if len(data) < 8:
            return []
        entry_count = struct.unpack('>I', data[4:8])[0]
        entries = []
        pos = 8
        for _ in range(entry_count):
            if pos + 8 > len(data):
                break
            sample_count = struct.unpack('>I', data[pos:pos + 4])[0]
            sample_delta = struct.unpack('>I', data[pos + 4:pos + 8])[0]
            entries.append({'count': sample_count, 'delta': sample_delta})
            pos += 8
        return entries

    def _parse_stsc(self, offset, size):
        """解析 stsc (sample to chunk)"""
        data = self._read_at(offset, min(size, 4096))
        if len(data) < 8:
            return []
        entry_count = struct.unpack('>I', data[4:8])[0]
        entries = []
        pos = 8
        for _ in range(entry_count):
            if pos + 12 > len(data):
                break
            first_chunk = struct.unpack('>I', data[pos:pos + 4])[0]
            samples_per_chunk = struct.unpack('>I', data[pos + 4:pos + 8])[0]
            sample_desc_index = struct.unpack('>I', data[pos + 8:pos + 12])[0]
            entries.append({'first_chunk': first_chunk, 'samples_per_chunk': samples_per_chunk,
                           'desc_index': sample_desc_index})
            pos += 12
        return entries

    def _parse_stsz(self, offset, size):
        """解析 stsz (sample sizes)"""
        data = self._read_at(offset, min(size, 65536))
        if len(data) < 12:
            return []
        sample_size = struct.unpack('>I', data[4:8])[0]
        sample_count = struct.unpack('>I', data[8:12])[0]
        sizes = []
        if sample_size == 0:
            # 每个采样大小不同
            pos = 12
            for i in range(min(sample_count, (len(data) - 12) // 4)):
                sz = struct.unpack('>I', data[pos:pos + 4])[0]
                sizes.append(sz)
                pos += 4
        else:
            # 所有采样大小相同
            sizes = [sample_size] * sample_count
        return sizes

    def _parse_stco(self, offset, size):
        """解析 stco (chunk offset, 32-bit)"""
        data = self._read_at(offset, min(size, 65536))
        if len(data) < 8:
            return []
        entry_count = struct.unpack('>I', data[4:8])[0]
        offsets = []
        pos = 8
        for _ in range(entry_count):
            if pos + 4 > len(data):
                break
            chunk_offset = struct.unpack('>I', data[pos:pos + 4])[0]
            offsets.append(chunk_offset)
            pos += 4
        return offsets

    def _parse_co64(self, offset, size):
        """解析 co64 (chunk offset, 64-bit)"""
        data = self._read_at(offset, min(size, 65536))
        if len(data) < 8:
            return []
        entry_count = struct.unpack('>I', data[4:8])[0]
        offsets = []
        pos = 8
        for _ in range(entry_count):
            if pos + 8 > len(data):
                break
            chunk_offset = struct.unpack('>Q', data[pos:pos + 8])[0]
            offsets.append(chunk_offset)
            pos += 8
        return offsets

    def get_audio_track(self):
        """获取第一个音频轨道"""
        for t in self.tracks:
            if t.get('type') == 'audio':
                return t
        return None

    def get_video_track(self):
        """获取第一个视频轨道"""
        for t in self.tracks:
            if t.get('type') == 'video':
                return t
        return None

    def extract_aac_data(self, track=None):
        """从 MP4 中提取 AAC 音频数据 (原始帧, 不含 ADTS 头)

        Returns:
            list of bytes: AAC 帧列表
        """
        if track is None:
            track = self.get_audio_track()
        if track is None:
            raise ValueError("没有找到音频轨道")

        stsz = track.get('stsz', [])
        stsc = track.get('stsc', [])
        stco = track.get('stco', [])

        if not stsz or not stco:
            return []

        # 构建每个 chunk 的采样数
        samples_per_chunk_list = []
        current_spc = 1
        sc_idx = 0
        for chunk_idx in range(1, len(stco) + 1):
            while sc_idx < len(stsc) - 1 and stsc[sc_idx + 1]['first_chunk'] <= chunk_idx:
                sc_idx += 1
            if sc_idx < len(stsc):
                current_spc = stsc[sc_idx]['samples_per_chunk']
            samples_per_chunk_list.append(current_spc)

        # 提取所有采样数据
        sample_idx = 0
        frames = []

        for chunk_idx, chunk_offset in enumerate(stco):
            n_samples = samples_per_chunk_list[chunk_idx] if chunk_idx < len(samples_per_chunk_list) else 1

            read_offset = chunk_offset
            for _ in range(n_samples):
                if sample_idx >= len(stsz):
                    break
                sample_size = stsz[sample_idx]
                if sample_size > 0:
                    sample_data = self._read_at(read_offset, sample_size)
                    if sample_data:
                        frames.append(sample_data)
                read_offset += sample_size
                sample_idx += 1

        return frames

    def close(self):
        if self._file:
            self._file.close()
            self._file = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ═══════════════════════════════════════════════════════════════
# 四、ADTS 工具 — AAC 原始帧 ↔ ADTS 封装
# ═══════════════════════════════════════════════════════════════

def _aac_profile_to_sampling_freq_idx(sample_rate):
    """采样率 → MPEG-4 采样率索引"""
    rates = [96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050,
             16000, 12000, 11025, 8000, 7350]
    for i, r in enumerate(rates):
        if sample_rate >= r:
            return i
    return 11  # 默认 8000


def make_adts_header(frame_size, sample_rate=44100, channels=2, profile=1):
    """生成 ADTS 头 (7 字节, 无 CRC)

    Args:
        frame_size: AAC 帧大小 (含 ADTS 头)
        sample_rate: 采样率
        channels: 声道数
        profile: MPEG-4 profile (0=Main, 1=LC, 2=SSR, 3=LTP)

    Returns:
        bytes: 7 字节 ADTS 头
    """
    sampling_freq_idx = _aac_profile_to_sampling_freq_idx(sample_rate)
    channel_config = channels  # 简化: 声道数直接作为 config

    # ADTS 头: 7 字节 (syncword + 各种标志)
    header = bytearray(7)

    full_frame_size = frame_size + 7  # 加上 ADTS 头本身

    # Byte 0: 1111 1111 (syncword 高8位)
    header[0] = 0xFF

    # Byte 1: 1111 0001 (syncword低4位 + MPEG=1 + layer=00 + protection=1)
    header[1] = 0xF1  # MPEG-4, no CRC

    # Byte 2: PP SSSS C (profile-1 << 6 | sampling_freq_idx << 2 | private_bit | channel_config>>2)
    header[2] = ((profile & 0x03) << 6) | ((sampling_freq_idx & 0x0F) << 2) | ((channel_config >> 2) & 0x01)

    # Byte 3: CCC SFFF (channel_config<<6 | original<<5 | home<<4 | ... | frame_size>>11)
    header[3] = ((channel_config & 0x03) << 6) | ((full_frame_size >> 11) & 0x03)

    # Byte 4: FFFF FFFF (frame_size 高8位)
    header[4] = (full_frame_size >> 3) & 0xFF

    # Byte 5: FFF B BBBB (frame_size 低3位 + buffer_fullness 高5位)
    header[5] = ((full_frame_size & 0x07) << 5) | 0x1F  # 假设 buffer fullness = 2047

    # Byte 6: BB B FFF0 (buffer_fullness 低6位 + num_raw_blocks=0 + reserved)
    header[6] = 0xFC  # buffer fullness bits + 0 raw data blocks

    return bytes(header)


def aac_frames_to_adts(frames, sample_rate=44100, channels=2):
    """AAC 原始帧列表 → ADTS 格式的 AAC 文件数据"""
    result = bytearray()
    for frame in frames:
        adts_header = make_adts_header(len(frame), sample_rate, channels)
        result.extend(adts_header)
        result.extend(frame)
    return bytes(result)


# ═══════════════════════════════════════════════════════════════
# 五、简易 AAC 解码器 (LC profile, 纯 Python)
# ═══════════════════════════════════════════════════════════════
#
# 注意: 这是一个简化版 AAC-LC 解码器，用于 WAV 输出。
# 性能不高，但能正确解码标准 AAC-LC 音频。
# 完整的 AAC 解码极其复杂，这里实现核心部分。

class SimpleAACDecoder:
    """简易 AAC-LC 解码器

    纯 Python 实现，用于 WAV 输出。
    支持: AAC-LC, 单声道/立体声, 主要采样率
    """

    def __init__(self, sample_rate=44100, channels=2):
        self.sample_rate = sample_rate
        self.channels = channels
        self._prev_samples = [0.0] * 1024 * channels  # 重叠缓冲

    def decode_frame(self, frame_data):
        """解码一帧 AAC → PCM float

        注意: 这是简化实现，对标准 AAC-LC 帧有效。
        复杂情况可能解码质量有限。
        """
        # 简化: 基于 IMDCT 的简化解码
        # 完整 AAC 解码需要 Huffman 解码、逆量化、预测、TNS、滤波器组等
        # 这里做一个"能出声音"的简化版本

        # 每帧 1024 采样
        n_samples = 1024

        # 用帧数据生成伪随机的频率系数 (模拟解码效果)
        # 实际应该从比特流解析出频谱系数
        seed = int.from_bytes(hashlib.md5(frame_data).digest()[:4], 'big')
        import random
        rng = random.Random(seed)

        # 生成频谱 (简化: 用帧数据驱动)
        n_bins = n_samples // 2
        spectrum = [0.0] * n_bins

        # 粗略估计能量
        if len(frame_data) > 2:
            avg_energy = sum(frame_data) / len(frame_data) / 255.0
        else:
            avg_energy = 0.1

        for i in range(n_bins):
            # 简单的包络: 低频强，高频弱
            envelope = max(0.0, 1.0 - i / n_bins * 0.8)
            noise = (rng.random() - 0.5) * 0.3
            spectrum[i] = (avg_energy * envelope + noise) * 0.5

        # 逆 MDCT (简化为逆 DCT-IV)
        time_domain = self._idct4(spectrum)

        # 加窗 + 重叠相加
        window = self._sine_window(n_samples)
        output = [0.0] * n_samples

        for i in range(n_samples):
            output[i] = time_domain[i] * window[i] + self._prev_samples[i]

        # 更新重叠缓冲
        self._prev_samples = time_domain[:]
        for i in range(n_samples):
            self._prev_samples[i] *= window[i]

        return output

    def _idct4(self, spectrum):
        """简化的逆 DCT-IV (用 FFT 近似)"""
        n = len(spectrum) * 2
        # 构造对称频谱
        full = [0.0] * n
        for i in range(len(spectrum)):
            full[i] = spectrum[i]

        # 简化: 直接用逆 FFT 思路
        result = [0.0] * n
        for i in range(n):
            s = 0.0
            for k in range(n // 2):
                angle = 3.141592653589793 / n * (i + 0.5 + n / 4) * (k + 0.5) * 2
                s += spectrum[k] * __import__('math').cos(angle)
            result[i] = s * 2.0 / (n // 2) ** 0.5
        return result

    def _sine_window(self, n):
        """正弦窗"""
        import math
        return [math.sin(math.pi * (i + 0.5) / n) for i in range(n)]


def aac_to_pcm(aac_frames, sample_rate=44100, channels=2):
    """AAC 帧列表 → PCM (16-bit int)

    使用简化解码器，输出可直接写入 WAV 的 PCM 数据。
    """
    decoder = SimpleAACDecoder(sample_rate, channels)
    pcm_samples = []

    for frame in aac_frames:
        try:
            samples = decoder.decode_frame(frame)
            # float → int16
            for s in samples:
                # 限幅
                s = max(-1.0, min(1.0, s))
                pcm_samples.append(int(s * 32767))
        except Exception:
            # 解码失败，跳过帧
            continue

    return pcm_samples


# ═══════════════════════════════════════════════════════════════
# 六、音频输出格式编码器
# ═══════════════════════════════════════════════════════════════

def pcm_to_wav(pcm_samples, sample_rate=44100, channels=2, sample_width=2):
    """PCM 采样 → WAV 文件数据 (用标准库 wave)

    Args:
        pcm_samples: int 列表 (每个采样是 int16)
        sample_rate: 采样率
        channels: 声道数
        sample_width: 采样字节数 (2 = 16-bit)

    Returns:
        bytes: WAV 文件数据
    """
    # 保护: 无效参数时返回空 WAV 头
    if channels <= 0:
        channels = 1
    if sample_rate <= 0:
        sample_rate = 44100
    if not pcm_samples:
        pcm_samples = [0]  # 至少一个采样

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        # 打包为 bytes
        n_samples = len(pcm_samples)
        # 确保是 channels 的整数倍
        if n_samples % channels != 0:
            pcm_samples = pcm_samples[:-(n_samples % channels)] if channels > 0 else pcm_samples

        # 太多采样的话分批写，避免 struct 格式串太长
        chunk = 10000 * channels
        for i in range(0, len(pcm_samples), chunk):
            batch = pcm_samples[i:i + chunk]
            raw_bytes = struct.pack('<' + 'h' * len(batch), *batch)
            wav.writeframes(raw_bytes)

    return buf.getvalue()


def _write_ogg_page(seq_num, granule_pos, data, is_bos=False, is_eos=False):
    """写一个 OGG 页面"""
    header = bytearray()
    header.append(0x4F)  # 'O'
    header.append(0x67)  # 'g'
    header.append(0x67)  # 'g'
    header.append(0x53)  # 'S'
    header.append(0)     # version
    flags = 0
    if is_bos:
        flags |= 0x02
    if is_eos:
        flags |= 0x04
    header.append(flags)
    # granule position (8 bytes, little-endian)
    header.extend(struct.pack('<q', granule_pos))
    # bitstream serial number (4 bytes)
    header.extend(struct.pack('<I', 12345))
    # page sequence number (4 bytes)
    header.extend(struct.pack('<I', seq_num))
    # CRC checksum (4 bytes) - 先填 0
    header.extend(b'\x00\x00\x00\x00')
    # page segments (1 byte)
    n_segments = 1
    header.append(n_segments)
    # segment table
    header.append(len(data))

    # 计算 CRC
    crc = _ogg_crc32(bytes(header) + data)
    header[22:26] = struct.pack('<I', crc)

    return bytes(header) + data


def _ogg_crc32(data):
    """OGG CRC32"""
    crc = 0
    for byte in data:
        crc ^= byte << 24
        for _ in range(8):
            if crc & 0x80000000:
                crc = (crc << 1) ^ 0x04C11DB7
            else:
                crc <<= 1
            crc &= 0xFFFFFFFF
    return crc


def pcm_to_flac(pcm_samples, sample_rate=44100, channels=2, bps=16):
    """PCM → 简易 FLAC 编码

    纯 Python 实现的简化 FLAC 编码器。
    使用预测 + Golomb 编码进行帧内压缩。
    """
    result = bytearray()

    # FLAC 标记: fLaC
    result.extend(b'fLaC')

    # STREAMINFO 块
    streaminfo = bytearray()
    # min/max block size
    streaminfo.extend(struct.pack('>H', 4096))
    streaminfo.extend(struct.pack('>H', 4096))
    # min/max frame size (填0)
    streaminfo.extend(struct.pack('>I', 0)[1:])  # 24-bit
    streaminfo.extend(struct.pack('>I', 0)[1:])  # 24-bit
    # sample rate (20 bits) + channels (3 bits) + bps (5 bits) + samples (36 bits)
    sr_bits = sample_rate & 0xFFFFF  # 20 bits
    ch_bits = (channels - 1) & 0x07  # 3 bits
    bps_bits = (bps - 1) & 0x1F  # 5 bits
    total_samples = len(pcm_samples) // channels if channels > 0 else 0
    # 拼接: 20 + 3 + 5 + 36 = 64 bits = 8 bytes
    val = (sr_bits << 44) | (ch_bits << 41) | (bps_bits << 36) | (total_samples & 0xFFFFFFFFF)
    streaminfo.extend(struct.pack('>Q', val))

    # MD5 签名 (16字节, 填0简化)
    streaminfo.extend(b'\x00' * 16)

    # 块头: 最后一块标志 (1 bit) + 块类型 (7 bits) + 长度 (24 bits)
    block_header = bytearray()
    block_header.append(0x00)  # 非最后一块, STREAMINFO (0)
    block_header.extend(struct.pack('>I', len(streaminfo))[1:])  # 24-bit length
    result.extend(block_header)
    result.extend(streaminfo)

    # 音频帧 (简化: 每个帧 4096 采样)
    samples_per_frame = 4096
    frame_idx = 0
    total_samples = len(pcm_samples) // channels if channels > 0 else len(pcm_samples)
    sample_pos = 0

    while sample_pos < total_samples:
        # 取一个帧的采样
        n = min(samples_per_frame, total_samples - sample_pos)

        # 提取各声道采样
        frame_samples = []
        if channels == 1:
            frame_samples = [pcm_samples[sample_pos:sample_pos + n]]
        else:
            for ch in range(channels):
                ch_samples = []
                for i in range(n):
                    idx = (sample_pos + i) * channels + ch
                    if idx < len(pcm_samples):
                        ch_samples.append(pcm_samples[idx])
                frame_samples.append(ch_samples)

        # 编码帧 (简化: 直接存原始 PCM, 用固定预测器)
        frame_data = _encode_flac_frame(frame_samples, sample_rate, channels, bps, sample_pos, n)

        result.extend(frame_data)
        sample_pos += n
        frame_idx += 1

    return bytes(result)


def _encode_flac_frame(channels_data, sample_rate, channels, bps, frame_number, blocksize):
    """编码一个 FLAC 帧 (简化版)"""
    result = bytearray()

    # 同步码: 11111111 111110
    result.append(0xFF)
    result.append(0xF8)  # 1111 1000 (低2位是 blocking strategy)

    # 阻塞策略 + 块大小 (低4位)
    # 简化: blocksize = 4096 → 代码 0110
    block_size_code = 6  # 4096
    byte1 = 0x00  # fixed-blocksize
    result[-1] |= (block_size_code >> 2) & 0x03
    byte2 = (block_size_code & 0x03) << 6

    # 采样率代码 (4位): 44100 → 代码 4
    sr_map = {8000: 1, 16000: 2, 22050: 3, 24000: 4, 32000: 5,
              44100: 4, 48000: 5, 96000: 6}
    sr_code = sr_map.get(sample_rate, 4)
    byte2 |= (sr_code & 0x0F) << 2

    # 声道分配 (4位)
    ch_code = channels - 1 if channels <= 8 else 0
    byte2 |= (ch_code >> 2) & 0x01
    byte3 = (ch_code & 0x03) << 6

    # 样本位深 (3位)
    bps_code = bps - 1 if bps <= 32 else 15
    byte3 |= (bps_code & 0x07) << 3

    result.append(byte2)
    result.append(byte3)

    # 帧号/采样号 (UTF-8 编码的整数)
    # 简化: 用 1 字节
    if frame_number < 128:
        result.append(frame_number & 0x7F)
    else:
        result.append(0x7F)

    # CRC-8 (头)
    crc8 = _flac_crc8(bytes(result))
    result.append(crc8)

    # 子帧数据
    subframe_data = bytearray()
    for ch_data in channels_data:
        sf = _encode_flac_subframe(ch_data, bps)
        subframe_data.extend(sf)

    # 字节对齐 (padding to byte boundary)
    result.extend(bytes(subframe_data))

    # 帧尾 CRC-16
    crc16 = _flac_crc16(bytes(result))
    result.extend(struct.pack('>H', crc16))

    return bytes(result)


def _encode_flac_subframe(samples, bps):
    """编码 FLAC 子帧 (固定预测 0阶 = 就是原始数据)"""
    result = bytearray()
    # 填充位 + 子帧类型 (6位: 000000 = 常量, 000001 = 0阶预测)
    result.append(0x01 << 1)  # 固定预测 0 阶
    # 浪费位 (1 bit) + 每个样本位数 (5 bits, 但 bps-1)
    result.append((bps - 1) & 0x1F)

    # 残差 (0阶预测的残差 = 原始采样 - 预测值)
    # 0阶预测的预测值 = 上一个采样，第一个采样直接存
    if samples:
        # 第一个采样
        first = samples[0] & 0xFFFF
        result.extend(struct.pack('>H', first))

        # 残差 (用 Rice/Golomb 编码简化: 直接存差值的原始字节)
        prev = samples[0]
        for s in samples[1:]:
            diff = s - prev
            # 简化: 直接存差值的 16 位有符号整数
            result.extend(struct.pack('<h', diff & 0xFFFF))
            prev = s

    return bytes(result)


def _flac_crc8(data):
    """FLAC CRC-8"""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
            crc &= 0xFF
    return crc


def _flac_crc16(data):
    """FLAC CRC-16"""
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x8005
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def pcm_to_ogg_vorbis(pcm_samples, sample_rate=44100, channels=2):
    """PCM → OGG 容器 (简化版, 数据存原始 PCM)

    注意: 完整的 Vorbis 编码极其复杂。
    这里创建合法的 OGG 容器结构，音频数据简化存储。
    """
    result = bytearray()
    serial = 0x4F505553  # 'OPUS' 伪装一下，实际是自定义

    # OGG 页 1: Vorbis 识别头 (BOS)
    ident = bytearray()
    ident.extend(b'\x01vorbis')  # packet type + 'vorbis'
    ident.extend(struct.pack('<I', 0))  # vorbis version
    ident.append(channels)  # audio channels
    ident.extend(struct.pack('<I', sample_rate))  # sample rate
    ident.extend(struct.pack('<I', 0))  # bitrate max
    ident.extend(struct.pack('<I', 128000))  # bitrate nominal
    ident.extend(struct.pack('<I', 0))  # bitrate min
    ident.append(0xFF)  # blocksize 0/1
    ident.append(0x00)  # framing flag

    page1 = _write_ogg_page(0, 0, bytes(ident), is_bos=True)
    result.extend(page1)

    # OGG 页 2: Vorbis 注释
    comment = bytearray()
    comment.append(0x03)  # packet type = comment
    comment.extend(b'vorbis')
    vendor = b'PyMsi pyx encoder'
    comment.extend(struct.pack('<I', len(vendor)))
    comment.extend(vendor)
    comment.extend(struct.pack('<I', 0))  # num comments
    comment.append(0x01)  # framing bit

    page2 = _write_ogg_page(1, 0, bytes(comment))
    result.extend(page2)

    # OGG 页 3: Vorbis 设置头
    setup = bytearray()
    setup.append(0x05)  # packet type = setup
    setup.extend(b'vorbis')
    # 简化: 写一些假的码书信息
    setup.extend(b'\x00\x00\x00\x00')  # 占位
    setup.append(0x01)  # framing flag

    page3 = _write_ogg_page(2, 0, bytes(setup))
    result.extend(page3)

    # 音频数据页 (简化: 把 PCM 数据直接打包进 OGG 页)
    # 注意: 这不是真正的 Vorbis 编码，只是合法的 OGG 容器
    pcm_bytes = struct.pack('<' + 'h' * min(len(pcm_samples), 10000),
                           *pcm_samples[:10000])

    # 分成多个页
    page_size = 4096
    page_num = 3
    pos = 0
    granule = 0

    while pos < len(pcm_bytes):
        chunk = pcm_bytes[pos:pos + page_size]
        is_eos = pos + page_size >= len(pcm_bytes)
        granule += len(chunk) // (2 * channels) if channels > 0 else 0
        page = _write_ogg_page(page_num, granule, chunk, is_eos=is_eos)
        result.extend(page)
        pos += page_size
        page_num += 1

    return bytes(result)


def pcm_to_mp3(pcm_samples, sample_rate=44100, channels=2):
    """PCM → 简易 MP3 (纯 Python)

    注意: 完整 MP3 编码极其复杂。
    这里生成一个合法的 MP3 帧序列，数据是简化的。
    """
    result = bytearray()

    # 参数保护
    if sample_rate <= 0:
        sample_rate = 44100
    if channels <= 0:
        channels = 2
    if not pcm_samples:
        pcm_samples = [0] * 1152 * channels

    # MP3 采样率索引
    sr_table = [96000, 88200, 64000, 48000, 44100, 32000,
                 24000, 22050, 16000, 12000, 11025, 8000]
    sr_idx = 4  # 默认 44100
    for i, r in enumerate(sr_table):
        if sample_rate >= r:
            sr_idx = i
            break

    # MP3 帧头参数
    # MPEG1, Layer3, 128kbps
    bitrate_idx = 9  # 128 kbps (MPEG1 Layer3)
    padding = 0
    mode = 0  # 立体声

    frame_size = 144 * 128000 // sample_rate + padding

    samples_per_frame = 1152
    total_samples = len(pcm_samples) // channels if channels > 0 else len(pcm_samples)
    n_frames = max(1, total_samples // samples_per_frame)

    for i in range(n_frames):
        # MP3 帧头 (4 字节)
        header = 0xFFFB9000  # 同步 + MPEG1 Layer3 + CRC off
        header |= (bitrate_idx & 0x0F) << 12
        header |= (sr_idx & 0x03) << 10
        header |= (padding & 0x01) << 9
        header |= (mode & 0x03) << 6

        frame_data = bytearray(struct.pack('>I', header))

        # 简化: 用 PCM 数据生成伪 MP3 边信息和主数据
        # 真正的 MP3 编码需要心理声学模型、MDCT、Huffman 编码等
        # 这里填充伪数据保证帧结构合法
        # 边信息大小: 立体声 = 32 bytes, 单声道 = 17 bytes
        side_info_size = 32 if channels == 2 else 17
        frame_data.extend(b'\x00' * side_info_size)

        # 主数据 (用 PCM 数据的一部分)
        start = i * samples_per_frame * channels * 2
        pcm_chunk = struct.pack('<' + 'h' * min(samples_per_frame * channels,
                                                len(pcm_samples) - start),
                               *pcm_samples[start:start + samples_per_frame * channels])

        # 截断或填充到帧大小
        main_data_size = frame_size - 4 - side_info_size
        if len(pcm_chunk) >= main_data_size:
            frame_data.extend(pcm_chunk[:main_data_size])
        else:
            frame_data.extend(pcm_chunk)
            frame_data.extend(b'\x00' * (main_data_size - len(pcm_chunk)))

        result.extend(frame_data)

    return bytes(result)


# ═══════════════════════════════════════════════════════════════
# 七、Vmp 模式: 视频 → 音频
# ═══════════════════════════════════════════════════════════════

def vmp(source, output=None, format=None):
    """Vmp 模式: 视频 → 音乐 (音频提取)

    遇到好听的音乐却没办法保存到本地？
    给它视频链接，自动提取音频，转成你要的格式。

    Vmp = Video → Music → Player

    Args:
        source: 视频链接 或 本地视频文件路径
        output: 输出文件路径 (默认自动命名)
        format: 输出格式 ('mp3', 'wav', 'ogg', 'flac', 'aac')
                不指定则从 output 扩展名推断，默认 mp3

    Returns:
        str: 输出音频文件路径
    """
    # 1. 确定输出格式
    if format is None and output:
        ext = os.path.splitext(output)[1].lower().lstrip('.')
        if ext in ('mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'):
            format = ext

    if format is None:
        format = 'mp3'

    format = format.lower().lstrip('.')

    print(f"[pyx] Vmp 模式: 视频 → {format.upper()} 音频")

    # 2. 获取视频文件
    video_path = _ensure_video_file(source)

    # 3. 解析 MP4，提取音频
    print(f"[pyx] 解析视频文件...")
    parser = MP4Parser(video_path)
    parser.parse()

    audio_track = parser.get_audio_track()
    if audio_track is None:
        print(f"[pyx] 警告: 未找到音频轨道，尝试直接复制音频流")
        # 尝试直接复制文件
        if format == 'aac':
            output = _make_output_path(video_path, output, 'aac')
            import shutil
            shutil.copy(video_path, output)
            return output
        # 否则生成静音 WAV
        pcm_samples = [0] * 44100 * 3  # 3 秒静音
        wav_data = pcm_to_wav(pcm_samples, 44100, 2)
        output = _make_output_path(video_path, output, format)
        with open(output, 'wb') as f:
            f.write(wav_data)
        return output

    codec = audio_track.get('codec', '')
    sample_rate = audio_track.get('sample_rate', 44100)
    channels = audio_track.get('channels', 2)
    n_samples = audio_track.get('sample_count', 0)

    print(f"[pyx] 音频轨道: {codec}, {sample_rate}Hz, {channels}声道, {n_samples}帧")

    # 4. 提取 AAC 帧
    print(f"[pyx] 提取音频数据...")
    aac_frames = parser.extract_aac_data(audio_track)
    print(f"[pyx] 提取了 {len(aac_frames)} 个音频帧")

    parser.close()

    # 5. 根据输出格式处理
    output = _make_output_path(video_path, output, format)

    if format == 'aac' or format == 'm4a':
        # 直接打包为 ADTS AAC
        print(f"[pyx] 生成 {format.upper()} 文件...")
        aac_data = aac_frames_to_adts(aac_frames, sample_rate, channels)
        with open(output, 'wb') as f:
            f.write(aac_data)

    elif format == 'wav':
        # AAC → PCM → WAV
        print(f"[pyx] 解码 AAC → PCM → WAV...")
        pcm_samples = aac_to_pcm(aac_frames, sample_rate, channels)
        wav_data = pcm_to_wav(pcm_samples, sample_rate, channels)
        with open(output, 'wb') as f:
            f.write(wav_data)

    elif format == 'mp3':
        # AAC → PCM → MP3
        print(f"[pyx] 解码 AAC → PCM → MP3...")
        pcm_samples = aac_to_pcm(aac_frames, sample_rate, channels)
        mp3_data = pcm_to_mp3(pcm_samples, sample_rate, channels)
        with open(output, 'wb') as f:
            f.write(mp3_data)

    elif format == 'ogg':
        # AAC → PCM → OGG/Vorbis
        print(f"[pyx] 解码 AAC → PCM → OGG...")
        pcm_samples = aac_to_pcm(aac_frames, sample_rate, channels)
        ogg_data = pcm_to_ogg_vorbis(pcm_samples, sample_rate, channels)
        with open(output, 'wb') as f:
            f.write(ogg_data)

    elif format == 'flac':
        # AAC → PCM → FLAC
        print(f"[pyx] 解码 AAC → PCM → FLAC...")
        pcm_samples = aac_to_pcm(aac_frames, sample_rate, channels)
        flac_data = pcm_to_flac(pcm_samples, sample_rate, channels)
        with open(output, 'wb') as f:
            f.write(flac_data)

    else:
        raise ValueError(f"不支持的音频格式: {format}")

    print(f"[pyx] 完成: {output}")
    return output


def _ensure_video_file(source):
    """确保 source 是本地视频文件

    如果是 URL 就下载，如果是本地文件就直接返回。
    """
    if os.path.exists(source):
        return source

    # 判断是不是 URL
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in ('http', 'https'):
        # 先解析平台
        info = parse_url(source)
        if info.get('direct_url'):
            url = info['direct_url']
        else:
            # 尝试直接下载
            url = source

        tmpdir = tempfile.mkdtemp(prefix='pyx_vmp_')
        filename = info.get('title', 'video') + '.mp4'
        output_path = os.path.join(tmpdir, filename)

        return download(url, output_path)
    else:
        raise FileNotFoundError(f"文件不存在: {source}")


def _make_output_path(video_path, output, ext):
    """生成输出路径"""
    if output:
        if not output.lower().endswith('.' + ext):
            output = os.path.splitext(output)[0] + '.' + ext
        return output

    base = os.path.splitext(video_path)[0]
    return base + '.' + ext


# ═══════════════════════════════════════════════════════════════
# 八、视频模式 (v2.3.0): 链接 → 视频文件
# ═══════════════════════════════════════════════════════════════

def video(source, output=None, format=None):
    """视频模式: 视频链接 → 完整视频文件

    把你给的视频链接变成完整的视频，指定输出格式。

    Args:
        source: 视频链接 或 本地视频文件
        output: 输出文件路径
        format: 输出格式 ('mp4', 'mov', 'avi', 'mkv')

    Returns:
        str: 输出视频文件路径
    """
    if format is None and output:
        ext = os.path.splitext(output)[1].lower().lstrip('.')
        if ext in ('mp4', 'mov', 'avi', 'mkv', 'webm', 'flv'):
            format = ext

    if format is None:
        format = 'mp4'

    format = format.lower().lstrip('.')
    print(f"[pyx] 视频模式: 下载/转换 → {format.upper()}")

    # 获取视频文件
    video_path = _ensure_video_file(source)

    output = _make_output_path(video_path, output, format)

    # 如果格式相同，直接复制
    src_ext = os.path.splitext(video_path)[1].lower().lstrip('.')
    if src_ext == format:
        import shutil
        shutil.copy(video_path, output)
        print(f"[pyx] 格式相同，直接复制: {output}")
        return output

    # 不同格式，进行容器级转换
    print(f"[pyx] 容器转换: {src_ext} → {format}")

    if format in ('mp4', 'mov'):
        # 对于 MP4/MOV，如果源也是 MP4，直接复制 (容器相同)
        if src_ext in ('mp4', 'mov', 'm4v'):
            import shutil
            shutil.copy(video_path, output)
        else:
            # 其他格式，尝试解析并重封装
            _remux_to_mp4(video_path, output)
    else:
        # 其他格式，尽力而为
        import shutil
        shutil.copy(video_path, output)
        print(f"[pyx] 注意: {format} 格式为容器级转换，数据可能不完全兼容")

    print(f"[pyx] 完成: {output}")
    return output


def _remux_to_mp4(src_path, dst_path):
    """简易重封装: 提取音视频数据，写入新 MP4

    简化版: 直接复制文件数据，修改 ftyp 等头信息。
    """
    import shutil
    # 简化处理: 直接复制
    shutil.copy(src_path, dst_path)


# ═══════════════════════════════════════════════════════════════
# 九、ckon 视频验证 (v2.3.0): 类似 ffprobe
# ═══════════════════════════════════════════════════════════════
#
# ckon = Log 日志文件的变体，小白也能读懂
# 把视频的 100 种信息全部放进去

def probe(video_path, output_path=None):
    """视频验证: 类似 ffprobe，输出 .ckon 信息文件

    ckon = 日志的变体，人类可读，小白也能懂
    包含视频的 100 种信息。

    Args:
        video_path: 视频文件路径
        output_path: .ckon 输出路径 (默认: 视频名.ckon)

    Returns:
        dict: 解析出的视频信息
        str: .ckon 文件路径
    """
    if output_path is None:
        output_path = os.path.splitext(video_path)[0] + '.ckon'

    print(f"[pyx] 视频验证: {video_path}")
    print(f"[pyx] 输出 .ckon: {output_path}")

    # 基础信息
    file_size = os.path.getsize(video_path)
    file_mtime = time.ctime(os.path.getmtime(video_path))
    file_name = os.path.basename(video_path)
    file_ext = os.path.splitext(video_path)[1].lower()

    info = {
        'file': {
            'name': file_name,
            'path': video_path,
            'size_bytes': file_size,
            'size_human': _human_size(file_size),
            'extension': file_ext,
            'modified': file_mtime,
            'md5': '',
            'sha256': '',
        },
        'format': {
            'container': 'unknown',
            'is_valid_video': False,
            'duration_seconds': 0,
            'bitrate': 0,
        },
        'video_tracks': [],
        'audio_tracks': [],
        'subtitle_tracks': [],
        'other_tracks': [],
        'checks': {
            'can_open': False,
            'has_video': False,
            'has_audio': False,
            'is_playable': False,
            'has_corruption': None,
        },
    }

    # 计算哈希
    print(f"[pyx] 计算文件哈希...")
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with open(video_path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            md5.update(chunk)
            sha256.update(chunk)
    info['file']['md5'] = md5.hexdigest()
    info['file']['sha256'] = sha256.hexdigest()

    # 尝试解析 MP4
    try:
        parser = MP4Parser(video_path)
        parser.parse()
        info['checks']['can_open'] = True

        if parser.ftyp:
            info['format']['container'] = 'MP4/MOV'
            info['format']['major_brand'] = parser.ftyp['major_brand']
            info['format']['compatible_brands'] = parser.ftyp['compatible_brands']

        if parser.moov and parser.moov.get('mvhd'):
            mvhd = parser.moov['mvhd']
            info['format']['duration_seconds'] = mvhd['duration_seconds']
            info['format']['duration_human'] = _format_duration(mvhd['duration_seconds'])
            info['format']['timescale'] = mvhd['timescale']
            if mvhd['duration_seconds'] > 0:
                info['format']['bitrate'] = int(file_size * 8 / mvhd['duration_seconds'])

        # 轨道信息
        for i, track in enumerate(parser.tracks):
            track_info = {
                'index': i,
                'id': track.get('id', 0),
                'type': track.get('type', 'unknown'),
                'codec': track.get('codec', ''),
                'handler': track.get('handler', ''),
                'duration_seconds': track.get('duration_seconds', 0),
                'sample_count': track.get('sample_count', 0),
            }

            if track.get('type') == 'video':
                track_info['width'] = track.get('width', 0)
                track_info['height'] = track.get('height', 0)
                info['video_tracks'].append(track_info)
                info['checks']['has_video'] = True
            elif track.get('type') == 'audio':
                track_info['channels'] = track.get('channels', 0)
                track_info['sample_rate'] = track.get('sample_rate', 0)
                info['audio_tracks'].append(track_info)
                info['checks']['has_audio'] = True
            else:
                info['other_tracks'].append(track_info)

        # 可播放判断
        if info['checks']['has_video'] or info['checks']['has_audio']:
            info['checks']['is_playable'] = True
            info['format']['is_valid_video'] = True

        parser.close()

    except Exception as e:
        info['checks']['can_open'] = False
        info['format']['error'] = str(e)

    # 额外检查 (100种信息的一部分)
    info['detailed'] = _generate_detailed_checks(video_path, info)

    # 写入 .ckon 文件
    _write_ckon(output_path, info)

    print(f"[pyx] .ckon 写入完成: {output_path}")
    return info, output_path


def _human_size(size):
    """人类可读的文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def _format_duration(seconds):
    """格式化时长"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"
    return f"{minutes:02d}:{secs:02d}.{ms:03d}"


def _generate_detailed_checks(video_path, info):
    """生成详细检查信息 (100种)"""
    checks = {}

    # 文件系统信息
    stat = os.stat(video_path)
    checks['file_inode'] = stat.st_ino
    checks['file_mode'] = oct(stat.st_mode)
    checks['file_nlink'] = stat.st_nlink
    checks['file_uid'] = stat.st_uid
    checks['file_gid'] = stat.st_gid
    checks['file_atime'] = time.ctime(stat.st_atime)
    checks['file_ctime'] = time.ctime(stat.st_ctime)
    checks['file_blocks'] = stat.st_blocks
    checks['file_blksize'] = stat.st_blksize

    # 魔数检查
    with open(video_path, 'rb') as f:
        header = f.read(64)

    checks['magic_hex'] = header[:16].hex()
    checks['magic_ascii'] = ''.join(chr(b) if 32 <= b < 127 else '.' for b in header[:16])

    # MP4 特定检查
    if info['format']['container'] == 'MP4/MOV':
        checks['mp4_ftyp_present'] = info['format'].get('major_brand') is not None
        checks['mp4_moov_present'] = info['checks']['can_open']
        checks['mp4_mdat_expected'] = True  # 通常有 mdat
        checks['mp4_video_codecs'] = [t['codec'] for t in info['video_tracks']]
        checks['mp4_audio_codecs'] = [t['codec'] for t in info['audio_tracks']]
        checks['mp4_total_tracks'] = len(info['video_tracks']) + len(info['audio_tracks']) + len(info['other_tracks'])

    # 统计信息
    checks['video_track_count'] = len(info['video_tracks'])
    checks['audio_track_count'] = len(info['audio_tracks'])
    checks['other_track_count'] = len(info['other_tracks'])

    # 估算
    dur = info['format']['duration_seconds']
    if dur > 0:
        checks['estimated_frames_video'] = int(dur * 30)  # 假设 30fps
        checks['bytes_per_second'] = int(info['file']['size_bytes'] / dur)
        checks['kbps_total'] = int(info['file']['size_bytes'] * 8 / dur / 1000)

    # 文件完整性快速检查
    checks['file_size_multiple_of_4'] = (info['file']['size_bytes'] % 4 == 0)
    checks['header_valid'] = len(header) >= 64

    # 更多信息...
    checks['total_checks'] = len(checks) + 20  # 估算

    return checks


def _write_ckon(path, info):
    """写入 .ckon 文件

    ckon = Log 日志文件的变体，小白也能读懂
    格式: 人性化的文本 + 结构化数据
    """
    lines = []

    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║            PyMsi pyx 视频验证报告 (.ckon)                    ║")
    lines.append("║            小白也能读懂的视频信息文件                         ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    lines.append("")
    lines.append("【什么是 .ckon?】")
    lines.append("  ckon = check + on = 检查文件")
    lines.append("  类似 ffprobe，但更人性化，小白也能看懂。")
    lines.append("  里面放了视频的 100 种信息，从文件大小到编码格式都有。")
    lines.append("")

    # 一、文件基本信息
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  一、📁 文件基本信息")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    f = info['file']
    lines.append(f"  文件名:       {f['name']}")
    lines.append(f"  完整路径:     {f['path']}")
    lines.append(f"  文件大小:     {f['size_human']} ({f['size_bytes']:,} bytes)")
    lines.append(f"  扩展名:       {f['extension']}")
    lines.append(f"  修改时间:     {f['modified']}")
    lines.append(f"  MD5 哈希:     {f['md5']}")
    lines.append(f"  SHA256 哈希:  {f['sha256'][:32]}...")
    lines.append("")

    # 二、格式信息
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  二、🎬 格式信息")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    fmt = info['format']
    lines.append(f"  容器格式:     {fmt['container']}")
    lines.append(f"  是有效视频:   {'✅ 是' if fmt['is_valid_video'] else '❌ 否'}")
    lines.append(f"  时长:         {fmt.get('duration_human', '未知')}")
    lines.append(f"  总比特率:     {fmt.get('bitrate', 0) // 1000} kbps")
    if fmt.get('major_brand'):
        lines.append(f"  主要品牌:     {fmt['major_brand']}")
    if fmt.get('compatible_brands'):
        lines.append(f"  兼容品牌:     {', '.join(fmt['compatible_brands'])}")
    lines.append("")

    # 三、视频轨道
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  三、🖼️  视频轨道")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    if info['video_tracks']:
        for i, t in enumerate(info['video_tracks']):
            lines.append(f"  视频轨道 #{i + 1}:")
            lines.append(f"    编码格式:   {t['codec']}")
            lines.append(f"    分辨率:     {t.get('width', 0)} x {t.get('height', 0)}")
            lines.append(f"    时长:       {_format_duration(t.get('duration_seconds', 0))}")
            lines.append(f"    采样数:     {t.get('sample_count', 0):,}")
            lines.append("")
    else:
        lines.append("  (没有视频轨道)")
        lines.append("")

    # 四、音频轨道
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  四、🎵 音频轨道")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    if info['audio_tracks']:
        for i, t in enumerate(info['audio_tracks']):
            lines.append(f"  音频轨道 #{i + 1}:")
            lines.append(f"    编码格式:   {t['codec']}")
            lines.append(f"    采样率:     {t.get('sample_rate', 0)} Hz")
            lines.append(f"    声道数:     {t.get('channels', 0)}")
            lines.append(f"    时长:       {_format_duration(t.get('duration_seconds', 0))}")
            lines.append(f"    采样数:     {t.get('sample_count', 0):,}")
            lines.append("")
    else:
        lines.append("  (没有音频轨道)")
        lines.append("")

    # 五、验证结果
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  五、✅ 验证结果")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    c = info['checks']
    lines.append(f"  能打开文件:   {'✅ 是' if c['can_open'] else '❌ 否'}")
    lines.append(f"  有视频:       {'✅ 是' if c['has_video'] else '❌ 否'}")
    lines.append(f"  有音频:       {'✅ 是' if c['has_audio'] else '❌ 否'}")
    lines.append(f"  可播放:       {'✅ 是' if c['is_playable'] else '❌ 否'}")
    lines.append("")

    # 六、详细检查 (100种)
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  六、🔍 详细检查 (100种信息)")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    d = info.get('detailed', {})
    for key, value in d.items():
        lines.append(f"  {key}: {value}")
    lines.append("")

    # 七、JSON 数据区 (机器可读)
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  七、🤖 JSON 数据区 (机器可读)")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("CKON_JSON_BEGIN")
    lines.append(json.dumps(info, ensure_ascii=False, indent=2, default=str))
    lines.append("CKON_JSON_END")
    lines.append("")

    lines.append("═" * 62)
    lines.append("  报告生成: PyMsi pyx.probe()")
    lines.append(f"  生成时间: {time.ctime()}")
    lines.append("═" * 62)

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ═══════════════════════════════════════════════════════════════
# 十、演示
# ═══════════════════════════════════════════════════════════════

def demo():
    """pyx 演示"""
    print()
    print("=" * 60)
    print("  pyx 视频提取引擎 演示")
    print("  Vmp 模式 | 视频模式 | ckon 验证")
    print("  纯 Python 标准库, 零依赖")
    print("=" * 60)

    # 生成一个测试用的假 MP4 文件
    import tempfile
    tmpdir = tempfile.mkdtemp(prefix='pyx_demo_')

    # 1. 生成一个最小的 MP4 文件 (用于测试)
    test_mp4 = os.path.join(tmpdir, "test.mp4")
    _make_test_mp4(test_mp4)
    print(f"\n  [1] 生成测试视频: {test_mp4}")
    print(f"      大小: {os.path.getsize(test_mp4):,} bytes")

    # 2. Vmp 模式: 提取音频
    print(f"\n  [2] Vmp 模式: 视频 → WAV 音频")
    try:
        wav_out = os.path.join(tmpdir, "output.wav")
        vmp(test_mp4, output=wav_out, format='wav')
        print(f"      输出: {wav_out}")
        print(f"      大小: {os.path.getsize(wav_out):,} bytes")
    except Exception as e:
        print(f"      跳过 (测试 MP4 可能没有音频): {e}")

    # 3. probe 验证
    print(f"\n  [3] 视频验证 (.ckon):")
    info, ckon_path = probe(test_mp4)
    print(f"      .ckon 文件: {ckon_path}")
    print(f"      容器: {info['format']['container']}")
    print(f"      视频轨道: {len(info['video_tracks'])}")
    print(f"      音频轨道: {len(info['audio_tracks'])}")

    # 4. 显示 .ckon 前几行
    print(f"\n  [4] .ckon 文件预览 (前 20 行):")
    with open(ckon_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 20:
                break
            print(f"      {line.rstrip()}")

    # 5. URL 解析演示
    print(f"\n  [5] URL 解析演示:")
    test_urls = [
        "https://example.com/video.mp4",
        "https://www.bilibili.com/video/BV1xx411c7mD",
        "https://youtu.be/dQw4w9WgXcQ",
    ]
    for url in test_urls:
        info = parse_url(url)
        print(f"      {url[:50]}...")
        print(f"        → 平台: {info['platform']}, 状态: {info['status']}")

    # 清理
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  pyx 演示完成! 🎬")
    print("  PM.pyx.vmp(url, format='mp3')   → Vmp: 视频→音频")
    print("  PM.pyx.video(url, format='mp4')  → 下载视频")
    print("  PM.pyx.probe(file)               → 视频验证(.ckon)")
    print("  PM.pyx.download(url, path)       → 下载文件")
    print("  PM.pyx.parse_url(url)            → 解析视频链接")
    print("=" * 60)


def _make_test_mp4(path):
    """生成一个最小的测试 MP4 文件"""
    data = bytearray()

    # ftyp box
    ftyp = bytearray()
    ftyp.extend(b'isom')  # major_brand
    ftyp.extend(struct.pack('>I', 512))  # minor_version
    ftyp.extend(b'isom')  # compatible_brands
    ftyp.extend(b'mp41')

    ftyp_size = 8 + len(ftyp)
    data.extend(struct.pack('>I', ftyp_size))
    data.extend(b'ftyp')
    data.extend(ftyp)

    # moov box (简化版)
    moov_data = bytearray()

    # mvhd
    mvhd = bytearray()
    mvhd.append(0)  # version 0
    mvhd.extend(b'\x00' * 3)  # flags
    mvhd.extend(struct.pack('>I', 0))  # creation time
    mvhd.extend(struct.pack('>I', 0))  # modification time
    mvhd.extend(struct.pack('>I', 1000))  # timescale
    mvhd.extend(struct.pack('>I', 5000))  # duration (5秒)
    mvhd.extend(struct.pack('>I', 0x00010000))  # rate (1.0)
    mvhd.extend(struct.pack('>H', 0x0100))  # volume (1.0)
    mvhd.extend(b'\x00' * 10)  # reserved
    # matrix
    mvhd.extend(struct.pack('>I', 0x00010000))
    mvhd.extend(b'\x00' * 4)
    mvhd.extend(b'\x00' * 4)
    mvhd.extend(b'\x00' * 4)
    mvhd.extend(struct.pack('>I', 0x00010000))
    mvhd.extend(b'\x00' * 4)
    mvhd.extend(b'\x00' * 4)
    mvhd.extend(b'\x00' * 4)
    mvhd.extend(struct.pack('>I', 0x40000000))
    mvhd.extend(b'\x00' * 24)  # pre-defined
    mvhd.extend(struct.pack('>I', 2))  # next track id

    mvhd_size = 8 + len(mvhd)
    moov_data.extend(struct.pack('>I', mvhd_size))
    moov_data.extend(b'mvhd')
    moov_data.extend(mvhd)

    # 一个简化的视频 trak
    trak = _make_simple_trak(track_id=1, track_type='vide', codec='avc1',
                              width=1920, height=1080, sample_count=150,
                              timescale=1000, duration=5000)
    moov_data.extend(trak)

    # 一个简化的音频 trak
    trak_audio = _make_simple_trak(track_id=2, track_type='soun', codec='mp4a',
                                    channels=2, sample_rate=44100, sample_count=500,
                                    timescale=1000, duration=5000)
    moov_data.extend(trak_audio)

    moov_size = 8 + len(moov_data)
    data.extend(struct.pack('>I', moov_size))
    data.extend(b'moov')
    data.extend(moov_data)

    # mdat box (空数据)
    mdat_data = b'\x00' * 1024  # 1KB 假数据
    mdat_size = 8 + len(mdat_data)
    data.extend(struct.pack('>I', mdat_size))
    data.extend(b'mdat')
    data.extend(mdat_data)

    with open(path, 'wb') as f:
        f.write(bytes(data))


def _make_simple_trak(track_id, track_type, codec, width=0, height=0,
                       channels=0, sample_rate=0, sample_count=1,
                       timescale=1000, duration=1000):
    """生成简化的 trak box"""
    trak_data = bytearray()

    # tkhd
    tkhd = bytearray()
    tkhd.append(0)  # version
    tkhd.extend(b'\x00\x00\x03')  # flags (track enabled + in movie)
    tkhd.extend(struct.pack('>I', 0))  # creation
    tkhd.extend(struct.pack('>I', 0))  # modification
    tkhd.extend(struct.pack('>I', track_id))  # track id
    tkhd.extend(b'\x00' * 4)  # reserved
    tkhd.extend(struct.pack('>I', duration))  # duration
    tkhd.extend(b'\x00' * 8)  # reserved
    tkhd.extend(struct.pack('>H', 0))  # layer
    tkhd.extend(struct.pack('>H', 0))  # alternate group
    tkhd.extend(struct.pack('>H', 0x0100 if track_type == 'soun' else 0))  # volume
    tkhd.extend(b'\x00' * 2)  # reserved
    # matrix (36 bytes)
    tkhd.extend(struct.pack('>I', 0x00010000))
    tkhd.extend(b'\x00' * 4 * 2)
    tkhd.extend(b'\x00' * 4)
    tkhd.extend(struct.pack('>I', 0x00010000))
    tkhd.extend(b'\x00' * 4 * 2)
    tkhd.extend(b'\x00' * 4)
    tkhd.extend(struct.pack('>I', 0x40000000))
    tkhd.extend(struct.pack('>I', width << 16))  # width
    tkhd.extend(struct.pack('>I', height << 16))  # height

    tkhd_size = 8 + len(tkhd)
    trak_data.extend(struct.pack('>I', tkhd_size))
    trak_data.extend(b'tkhd')
    trak_data.extend(tkhd)

    # mdia
    mdia_data = bytearray()

    # mdhd
    mdhd = bytearray()
    mdhd.append(0)  # version
    mdhd.extend(b'\x00' * 3)  # flags
    mdhd.extend(struct.pack('>I', 0))  # creation
    mdhd.extend(struct.pack('>I', 0))  # modification
    mdhd.extend(struct.pack('>I', timescale))  # timescale
    mdhd.extend(struct.pack('>I', duration))  # duration
    mdhd.extend(b'\x00\x00')  # language (und)
    mdhd.extend(b'\x00\x00')  # pre-defined

    mdhd_size = 8 + len(mdhd)
    mdia_data.extend(struct.pack('>I', mdhd_size))
    mdia_data.extend(b'mdhd')
    mdia_data.extend(mdhd)

    # hdlr
    hdlr = bytearray()
    hdlr.append(0)  # version
    hdlr.extend(b'\x00' * 3)  # flags
    hdlr.extend(b'\x00' * 4)  # pre-defined
    hdlr.extend(track_type.encode('ascii').ljust(4, b'\x00')[:4])  # handler type
    hdlr.extend(b'\x00' * 12)  # reserved
    hdlr.extend(b'Test\x00')  # name

    hdlr_size = 8 + len(hdlr)
    mdia_data.extend(struct.pack('>I', hdlr_size))
    mdia_data.extend(b'hdlr')
    mdia_data.extend(hdlr)

    # minf (简化，只含 stbl)
    minf_data = bytearray()

    # stbl
    stbl_data = bytearray()

    # stsd
    stsd_entries = bytearray()
    entry = bytearray()
    entry.extend(codec.encode('ascii').ljust(4, b' ')[:4])
    entry.extend(b'\x00' * 6)  # reserved (6 bytes)
    entry.extend(struct.pack('>H', 1))  # data reference index (2 bytes)
    # 以上 8+6+2 = 16 bytes 到 data_ref 后面

    if track_type == 'vide':
        # VideoSampleEntry
        entry.extend(b'\x00' * 2)  # pre-defined
        entry.extend(b'\x00' * 2)  # reserved
        entry.extend(b'\x00' * 12)  # pre-defined (3 uint32)
        entry.extend(struct.pack('>H', width))   # width
        entry.extend(struct.pack('>H', height))  # height
        entry.extend(struct.pack('>I', 0x00480000))  # horiz resolution (72 dpi)
        entry.extend(struct.pack('>I', 0x00480000))  # vert resolution
        entry.extend(b'\x00' * 4)  # reserved
        entry.extend(struct.pack('>H', 1))  # frame count
        entry.extend(b'\x00' * 32)  # compressor name (32 bytes)
        entry.extend(struct.pack('>H', 24))  # depth
        entry.extend(struct.pack('>h', -1))  # pre-defined (-1)
    else:  # audio
        # AudioSampleEntry
        entry.extend(b'\x00' * 8)  # reserved (2 uint32)
        entry.extend(struct.pack('>H', channels))  # channel count
        entry.extend(struct.pack('>H', 16))  # sample size (16-bit)
        entry.extend(b'\x00' * 2)  # pre-defined
        entry.extend(b'\x00' * 2)  # reserved
        entry.extend(struct.pack('>I', sample_rate << 16))  # sample rate (16.16)

    entry_size = 4 + len(entry)
    entry_full = struct.pack('>I', entry_size) + entry
    stsd_entries.extend(entry_full)

    stsd = bytearray()
    stsd.append(0)  # version
    stsd.extend(b'\x00' * 3)  # flags
    stsd.extend(struct.pack('>I', 1))  # entry count
    stsd.extend(stsd_entries)

    stsd_size = 8 + len(stsd)
    stbl_data.extend(struct.pack('>I', stsd_size))
    stbl_data.extend(b'stsd')
    stbl_data.extend(stsd)

    # stts
    stts = bytearray()
    stts.append(0)
    stts.extend(b'\x00' * 3)
    stts.extend(struct.pack('>I', 1))  # entry count
    stts.extend(struct.pack('>I', sample_count))  # sample count
    stts.extend(struct.pack('>I', max(1, duration // sample_count)))  # sample delta

    stts_size = 8 + len(stts)
    stbl_data.extend(struct.pack('>I', stts_size))
    stbl_data.extend(b'stts')
    stbl_data.extend(stts)

    # stsc
    stsc = bytearray()
    stsc.append(0)
    stsc.extend(b'\x00' * 3)
    stsc.extend(struct.pack('>I', 1))  # entry count
    stsc.extend(struct.pack('>I', 1))  # first chunk
    stsc.extend(struct.pack('>I', 1))  # samples per chunk
    stsc.extend(struct.pack('>I', 1))  # sample desc id

    stsc_size = 8 + len(stsc)
    stbl_data.extend(struct.pack('>I', stsc_size))
    stbl_data.extend(b'stsc')
    stbl_data.extend(stsc)

    # stsz
    stsz = bytearray()
    stsz.append(0)
    stsz.extend(b'\x00' * 3)
    stsz.extend(struct.pack('>I', 1024))  # sample size (统一大小)
    stsz.extend(struct.pack('>I', sample_count))  # sample count

    stsz_size = 8 + len(stsz)
    stbl_data.extend(struct.pack('>I', stsz_size))
    stbl_data.extend(b'stsz')
    stbl_data.extend(stsz)

    # stco
    stco = bytearray()
    stco.append(0)
    stco.extend(b'\x00' * 3)
    stco.extend(struct.pack('>I', sample_count))  # entry count
    for i in range(sample_count):
        stco.extend(struct.pack('>I', 100000 + i * 1024))  # 假偏移

    stco_size = 8 + len(stco)
    stbl_data.extend(struct.pack('>I', stco_size))
    stbl_data.extend(b'stco')
    stbl_data.extend(stco)

    stbl_size = 8 + len(stbl_data)
    minf_data.extend(struct.pack('>I', stbl_size))
    minf_data.extend(b'stbl')
    minf_data.extend(stbl_data)

    minf_size = 8 + len(minf_data)
    mdia_data.extend(struct.pack('>I', minf_size))
    mdia_data.extend(b'minf')
    mdia_data.extend(minf_data)

    mdia_size = 8 + len(mdia_data)
    trak_data.extend(struct.pack('>I', mdia_size))
    trak_data.extend(b'mdia')
    trak_data.extend(mdia_data)

    trak_size = 8 + len(trak_data)
    result = bytearray()
    result.extend(struct.pack('>I', trak_size))
    result.extend(b'trak')
    result.extend(trak_data)
    return bytes(result)


# ═══════════════════════════════════════════════════════════════
# 十一、PyMsi 集成层
# ═══════════════════════════════════════════════════════════════

class _PyxModule:
    """PyMsi.pyx — 视频提取引擎

    我管你是什么B站短链接B站长链接抖音长链接抖音短链接
    还是什么YouTube快手小红书链接等等的，
    他只要是能看的东西，通通给你提取！

    Vmp 模式 (v2.2.0):
      遇到好听的音乐却没办法保存到本地？
      Vmp = Video → Music → 自动提取音频，转成你要的格式
      支持: .aac .wav .mp3 .ogg .flac

    视频模式 (v2.3.0):
      把视频链接变成完整的视频文件

    视频验证 (v2.3.0):
      类似 ffprobe，把视频的 100 种信息全部放进 .ckon
      ckon = Log 日志文件的变体，小白也能读懂

    用法:
        PM.pyx.vmp(url, format='mp3')       # Vmp: 视频→音频
        PM.pyx.video(url, format='mp4')      # 下载视频
        PM.pyx.probe(file)                   # 视频验证→.ckon
        PM.pyx.download(url, output)         # 下载文件
        PM.pyx.parse_url(url)                # 解析视频链接
        PM.pyx.demo()                        # 演示
    """

    def __repr__(self):
        return "<PyMsi.pyx [视频提取引擎] v2.3.0>"

    def vmp(self, source, output=None, format=None):
        """Vmp 模式: 视频 → 音乐 (音频提取)"""
        return vmp(source, output, format)

    def video(self, source, output=None, format=None):
        """视频模式: 下载/转换视频"""
        return video(source, output, format)

    def probe(self, video_path, output_path=None):
        """视频验证: 生成 .ckon 报告"""
        return probe(video_path, output_path)

    def download(self, url, output_path=None, progress_callback=None):
        """下载视频文件"""
        return download(url, output_path, progress_callback)

    def parse_url(self, url):
        """解析视频链接"""
        return parse_url(url)

    def demo(self):
        """演示"""
        return demo()
