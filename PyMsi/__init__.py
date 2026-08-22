"""
PyMsi - 把任意文件夹打包成 MSI 安装包
========================================
用法:
    import PyMsi as PM
    PM("C:/你要构建的目录")   # 指定源文件夹
    PM.s(2)                    # 选择模式: 0=选错了, 1=普通模式, 2=极速模式

运行脚本即自动构建 MSI。
"""

import os
import sys
import shutil
import uuid
import struct
import hashlib
import tempfile
from datetime import datetime


# ─── README ─────────────────────────────────────────────

_README = r"""
╔══════════════════════════════════════════════════════════════╗
║                    PyMsi  v1.4.5                            ║
║ 文件夹→MSI | HTML→EXE | 30+游戏 | 图片→TTF | Hex解析 | AI空壳 ║
╚══════════════════════════════════════════════════════════════╝

【安装】
    pip install pymsi-1.4.5-py3-none-any.whl

【快速开始】

    import PyMsi as PM

    # ─── 方式一：文件夹 → MSI 安装包 ───
    PM("C:/你的项目文件夹")
    PM.s(2)   # 2=极速模式(推荐)  1=普通模式  0=取消
    # ↑ 等价写法 (alias 任意选):
    #   PM.build("C:/你的项目文件夹")
    #   PM.b("C:/你的项目文件夹")
    #   PM.msi("C:/你的项目文件夹")
    #   PM.pack("C:/你的项目文件夹")
    #   PM.make("C:/你的项目文件夹")
    #   PM.s(2) 的别名:  PM.mode(2)  PM.m(2)

    # ─── 方式二：HTML → EXE 桌面应用 (Electron) ───
    PM.html("C:/你的HTML项目")
    PM.html.build()                         # 构建 EXE
    PM.html.sandbox(True)                   # 开启沙箱模式
    PM.html.icon("C:/图标.ico")             # 自定义图标
    PM.html.platform("win32-x64")           # 指定目标平台
    PM.html.title("我的应用")               # 窗口标题
    PM.html.size(1280, 720)                # 窗口大小
    # ↑ 等价写法:
    #   PM.h("C:/html")        PM.web("C:/html")   PM.app("C:/html")
    #   PM.html.run()  .make()  .go()  .exe()     别名全部 == .build()
    #   PM.html.secure()  .safe()                == .sandbox(True)
    #   PM.html.name("标题")                      == .title
    #   PM.html.resize(w,h)                       == .size
    #   PM.html.win()  .windows()  .mac()  .linux()  快捷指定平台

    # ─── 方式三：两行代码，30+ 游戏即开即玩！ ───
    PM.game.Grap("Snake")          # 贪吃蛇
    PM.game.Grap("Tetris")         # 俄罗斯方块
    PM.game.Grap("2048")           # 2048
    PM.game.Grap("FlappyBird")     # 飞扬的小鸟
    PM.game.list()                  # 列出全部 30 款游戏
    # ↑ 等价写法:
    #   PM.g("贪吃蛇")              PM.games("贪吃蛇")
    #   PM.play("贪吃蛇")           PM.game.start / run / open / play("Snake")
    #   PM.game.ls()                PM.game.all()   == .list()

    # ─── 方式四：图片文件夹 → 字体 TTF ───
    # 命名规则: A.png B.png 0.png 等，文件名=字符
    PM.image.ttf("C:/glyph_folder", "我的字体.ttf")
    # 或者给一个映射字典
    PM.image.ttf("C:/glyphs", "out.ttf", mapping={"letter_a.png":"a", "letter_b.png":"b"})
    # ↑ 等价写法:
    #   PM.font(...)   PM.fonts(...)   PM.ttf(...)
    #   PM.img(...)    PM.i(...)       PM.pic(...)    直接调用也行
    #   PM.image(folder, out)                          直接调用也行
    #   PM.image.to_font / to_ttf / build_font / make_font (folder, out)
    #   PM.image.ttf.build / make / run / go / generate / create 都是同方法

    # ─── 方式五：输入文件地址 → 解析 Hex 全部输出到终端 ───
    PM.hex("C:/some/file.bin")                      # 直接 dump 全部 hex
    PM.hex.find("C:/my_project", "config.dat")       # 目录里搜文件名后解析
    PM.hex.dump("C:/file.bin", bytes_per_line=16,
                start_offset=0, max_bytes=512)       # 带参数
    # ↑ 等价写法:
    #   PM.hexdump(...)  PM.hd(...)   PM.hexview(...)
    #   PM.hex(...)       短调用也行
    #   PM.hex.find / search / locate (目录, 文件名)
    #   PM.hex.dump / view / show / print / parse / read (path, ...)

    # ─── 方式六：AI 空壳 — 设 key + 官网后问问题 ───
    PM.ai.key = "sk-xxxxxxxx"                       # 1. 设 API Key
    PM.ai.url = "https://api.openai.com"            # 2. 设 AI API 官网
    PM.ai.imput("你好, 你是谁?")                     # 3. 问问题 (输出自动 print)
    # ↑ 等价写法:
    #   PM.ai("你好")            直接调用也行
    #   PM.ai.ask / chat / question / send / say / talk  都是 imput 别名
    #   PM.AI / PM.gpt / PM.llm / PM.chatbot 都是 ai 别名
    #   q = PM.ai.input          输入当变量用 (上次问的问题)
    #   a = PM.ai.output         输出当变量用 (AI 的回答)
    #   PM.ai.model = "deepseek-chat"   换模型 (OpenAI 兼容接口都行)

────────────────────────────────────────────────────────────
【API 完整参考】

  PM(path)                    设置要打包的源文件夹
    path: str                 文件夹路径

  PM.s(mode)                  选择模式并构建 MSI
    mode: int                 0=取消  1=普通(压缩)  2=极速(推荐)
    返回: str                生成的 .msi 文件路径

  PM.html(path)               设置 HTML 源目录 (重置所有参数)
    path: str                 HTML 项目目录路径

  PM.html.build(output=None)  开始构建 EXE
    output: str (可选)        输出路径，默认 dist/{目录名}.exe
    返回: str                生成的 .exe 文件路径

  PM.html.sandbox(enabled)    沙箱模式开关
    enabled: bool             True=加沙箱  False=不加(默认)

  PM.html.icon(path)          自定义图标
    path: str                 .ico 文件路径

  PM.html.platform(target)    指定目标平台 (默认自动检测)
    target: str               win32-x64 / linux-x64 / darwin-x64

  PM.html.title(text)         窗口标题
    text: str

  PM.html.size(w, h)          窗口大小 (默认 1024x768)
    w: int, h: int

  PM.readme                   打印此帮助文档

  PM.game.Grap(name)          启动内置游戏模板
    name: str                 游戏名称 (英文或中文)
    例如: "Snake", "Tetris", "2048", "贪吃蛇"

  PM.game.list()              列出全部 30 款内置游戏

  PM.game(name)               快捷调用：同 PM.game.Grap(name)

  PM.image.ttf(folder, out, mapping=None, font_name="PyMsiFont")
                              图片 → TTF 字体 (纯 Python，零外部依赖)
    folder: str               包含 png/jpg/bmp/ico/gif 的文件夹
    out: str                  输出 .ttf 文件路径
    mapping: dict (可选)      {"文件名.png": "字符"}，不传则按文件名猜
    font_name: str            字体内部名称
    支持格式: .png .jpg .jpeg .bmp .ico .gif
    GIF 特殊: 自动拆帧，每帧作为一个独立字形

  PM.image.ttf.help()         查看详细教程与示例

  PM.hex(path)                输入文件地址 → 解析 Hex 全部输出到终端
    path: str                 文件路径 (展开 ~ 和环境变量)
    bytes_per_line: int       每行字节数 (默认 16)
    group_size: int           每组字节数 (默认 2), 0=不分组
    show_ascii: bool          显示右侧 ASCII 列 (默认 True)
    uppercase: bool           hex 大写 (默认 True)
    start_offset: int         起始字节偏移 (默认 0)
    max_bytes: int            最多读取字节数 (默认 None=全部; >64MB 自动截断)
    offset_base: str          偏移进制 'hex'/'dec' (默认 'hex')
    返回: int                 成功返回解析的字节数, 失败返回 None

  PM.hex.find(directory, name)  在目录中递归搜索文件名后解析
    directory: str            搜索起始目录
    name: str                 文件名 (大小写不敏感包含匹配)
    其余参数同 PM.hex()

  PM.hex == PM.hexdump == PM.hd == PM.hexview
  PM.hex.find / search / locate   都是同一方法
  PM.hex.dump / view / show / print / parse / read  都是同一方法

  PM.ai.key = key              设 API Key (必填)
  PM.ai.url = url              设 AI API 官网 (必填, OpenAI 兼容接口)
  PM.ai.imput(question)        问 AI 问题, 输出自动 print 到终端
  PM.ai.input                  AI 的输入 (只读变量, 调用 imput 后更新)
  PM.ai.output                 AI 的输出 (只读变量, 调用 imput 后更新)
  PM.ai.model = name           换模型 (默认 gpt-3.5-turbo)
  PM.ai.clear()                清空对话历史 + 输入 + 输出

  PM.ai == PM.AI == PM.gpt == PM.llm == PM.chatbot
  PM.ai.imput / ask / chat / question / send / say / talk / q  都是同一方法
  PM.ai.input / Input / prompt / question_text  都是输入别名
  PM.ai.output / Output / answer / result       都是输出别名

────────────────────────────────────────────────────────────
【图片 → 字体 TTF 用法示例】

  方式一：按文件名识别 (最简单)
  把每个字形图片命名为对应的字符:
    A.png B.png C.png ...      大写字母
    a.png b.png c.png ...      小写字母
    0.png 1.png ... 9.png      数字
    U+4E2D.png 或 0x4E2D.png   Unicode 方式表示中文 "中"
    我.png 你.png 他.png       中文直接命名 (UTF-8 文件系统)

  方式二：提供映射字典
    mapping = {"glyph01.png": "A", "glyph02.png": "中"}
    PM.image.ttf("C:/glyphs", "我的字体.ttf", mapping=mapping)

  方式三：GIF 动画逐帧转字形
    frames.gif 会被拆成 帧1→A 帧2→B 帧3→C...
    (可用 start_char="A" 指定起始字符)

────────────────────────────────────────────────────────────
【文件 Hex 解析用法示例】

  方式一：直接给文件路径
    PM.hex("C:/data/file.bin")
    # → 终端输出类似 xxd 的 hex dump, 含偏移/十六进制/ASCII

  方式二：在目录里搜索文件名
    PM.hex.find("C:/my_project", "config")  # 匹配所有含 config 的文件

  方式三：控制输出格式
    PM.hex("C:/file.bin", bytes_per_line=8, uppercase=False)
    PM.hex("C:/file.bin", start_offset=1024, max_bytes=256)
    PM.hex("C:/file.bin", group_size=0, show_ascii=False)

────────────────────────────────────────────────────────────
【内置游戏列表 (30款)】

  贪吃蛇 Snake        俄罗斯方块 Tetris    扫雷 Minesweeper
  2048                打砖块 Breakout      弹球 Pong
  太空射击 SpaceInvaders  五子棋 Gomoku    井字棋 TicTacToe
  记忆翻牌 Memory     飞扬的小鸟 FlappyBird  吃豆人 PacMan
  数独 Sudoku         颜色记忆 SimonSays   消消乐 Match3
  跳一跳 DoodleJump   乒乓球 PingPong      打地鼠 WhackMole
  滑块拼图 SlidingPuzzle  迷宫 Maze        四子棋 ConnectFour
  弹球打砖 BrickBreaker  双人贪吃蛇 Snake2P  反应测试 ReactionTest
  打字速度 TypingTest  点击器 Clicker      大炮射击 Cannon
  15拼图 Fifteen      算术挑战 MathQuiz    翻牌配对 CardMatch

────────────────────────────────────────────────────────────
【模式说明】

  模式 0 — 选错了，无事发生
  模式 1 — 普通模式，完整构建，压缩率高，适合正式发布
  模式 2 — 极速模式，跳过压缩，构建极快，适合调试

────────────────────────────────────────────────────────────
【沙箱模式说明】

  不加沙箱 (sandbox=False, 默认):
    • 启用 nodeIntegration，可访问 Node.js API
    • 可通过 window.pymsi 访问 fs/path/os/child_process
    • 适合需要完整系统访问的桌面应用

  加沙箱 (sandbox=True):
    • 启用 contextIsolation，禁用 nodeIntegration
    • 注入 CSP 头限制网络和文件访问
    • 适合展示型 HTML 应用，更安全

────────────────────────────────────────────────────────────
【Electron 运行时】

  首次构建时自动下载 Electron v43.4.0 到:
    ~/.pymsi/electron/{version}/{platform}/

  支持平台:
    • win32-x64    (Windows 64位)
    • linux-x64    (Linux 64位)
    • darwin-x64   (macOS Intel)
    • darwin-arm64 (macOS Apple Silicon)

  生成的文件结构:
    {app_name}_app/
    ├── {app_name}.exe     ← 主程序
    ├── resources/
    │   └── app/
    │       ├── main.js        ← Electron 主进程
    │       ├── preload.js     ← 预加载脚本
    │       ├── package.json
    │       └── index.html     ← 你的 HTML 文件
    └── ...（Electron 运行时文件）

────────────────────────────────────────────────────────────
【完整示例】

  import PyMsi as PM

  # 示例 1：把 Python 项目打包成 MSI 安装包
  PM("C:/my_python_project")
  PM.s(2)
  # → 生成 C:/my_python_project.msi

  # 示例 2：把 HTML 项目打包成 Windows 桌面应用
  PM.html("C:/my_website")
  PM.html.title("我的网站")
  PM.html.sandbox(True)
  PM.html.icon("C:/icon.ico")
  PM.html.build()
  # → 生成 C:/my_website/dist/my_website_app/my_website.exe

  # 示例 3：跨平台构建 (Linux 上构建 Windows EXE)
  PM.html("C:/my_website")
  PM.html.platform("win32-x64")
  PM.html.build("C:/output/my_website.exe")
  # → 生成 C:/output/my_website_app/my_website.exe

────────────────────────────────────────────────────────────
【依赖】

  • Python >= 3.7
  • Electron 43.4.0 (首次自动下载，约 140MB)
  • 无需 Node.js 安装

────────────────────────────────────────────────────────────
【License】 MIT
"""


# ─── 常量 ───────────────────────────────────────────────
MODE_DESCRIPTIONS = {
    0: "选错了 — 无事发生，请重新选择模式 (1 或 2)",
    1: "普通模式 — 完整构建，压缩率高，适合发布",
    2: "极速模式 — 跳过压缩，构建极快，适合调试",
}


# ─── OLE Compound File 格式构建器 ────────────────────────
# MSI 文件本质上是 OLE Structured Storage (Compound Document)
# 以下代码在 Windows / Linux 上均可工作，纯 Python 实现


class _OLEWriter:
    """纯 Python 实现的 OLE Compound File 写入器"""

    HEADER_SIZE = 512
    SECTOR_SIZE = 512
    MIN_STREAM_SIZE = 4096  # 小于此值放在 mini stream 中
    MINI_SECTOR_SIZE = 64
    DIFAT_SIZE = 109  # header 中能放的 DIFAT 条目数

    def __init__(self, filepath):
        self._fp = open(filepath, "wb")
        self._fat = []          # FAT 扇区链表
        self._mini_fat = []     # Mini FAT 扇区链表
        self._dir_entries = []  # 目录条目
        self._dir_streams = {}  # name -> (data, is_mini)
        self._next_sector = 0
        self._next_mini_sector = 0
        self._mini_stream_data = b""

    def add_stream(self, name, data):
        is_mini = len(data) < self.MIN_STREAM_SIZE
        self._dir_streams[name] = (data, is_mini)

    def add_storage(self, name):
        self._dir_entries.append(_DirEntry(
            name=name, type=1, sid=-1
        ))

    def close(self):
        self._build()
        self._fp.close()

    def _build(self):
        self._build_directory()
        self._write_body()

    def _build_directory(self):
        # 构建目录树
        entries = []
        # Root Entry
        root = _DirEntry(name="Root Entry", type=1, sid=-1)
        entries.append(root)

        # 为每个流创建目录条目
        for name, (data, is_mini) in self._dir_streams.items():
            entry = _DirEntry(name=name, type=2, sid=-1, size=len(data))
            entries.append(entry)

        # 设置红黑树关系（简化：线性链表）
        for i, entry in enumerate(entries):
            if i > 0:
                entries[i - 1].dir_sibling_right = i - 1 + 2 if i < len(entries) - 1 else -1
            if i == 0:
                entry.dir_child = 1
                entry.dir_root = i
                entry.difat_start = -1
                entry.mini_fat_start = -1

        # 对齐到 128 字节的目录条目
        for entry in entries:
            entry.entry_id = entry.name.encode("utf-16-le")[:64]

        self._dir_entries = entries

    def _write_body(self):
        # 简化版：写入 header + 流数据
        # 先收集所有流数据
        self._write_simple_msi()

    def _write_simple_msi(self):
        """写入简化版 MSI（纯 Python 实现，不依赖 msilib）"""
        # 收集所有需要打包的文件
        streams = {}
        for name, (data, _) in self._dir_streams.items():
            streams[name] = data

        # 计算扇区布局
        # Sector 0: Header
        # Sector 1: FAT
        # Sector 2: Directory (4 entries × 128 bytes = 512 bytes = 1 sector)
        # Sector 3+: Stream data

        num_dir_entries = 1 + len(streams)  # Root + streams
        dir_sectors = max(1, (num_dir_entries * 128 + 511) // 512)

        # 计算流数据起始扇区
        stream_start_sector = 1 + 1 + dir_sectors  # Header + FAT + Directory

        # 为每个流分配扇区
        stream_sectors = {}
        current_sector = stream_start_sector
        for name, data in streams.items():
            num_sectors = (len(data) + 511) // 512
            stream_sectors[name] = (current_sector, len(data))
            current_sector += num_sectors

        total_sectors = current_sector

        # 写入 header（512 字节）
        header = bytearray(512)
        # Magic: D0 CF 11 E0 A1 B1 1A E1
        header[0:8] = bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1])
        # CLSID: MSI database GUID
        # {000C1084-0000-0000-C000-000000000046}
        msi_clsid = bytes([
            0x84, 0x10, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00,
            0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46,
        ])
        header[8:24] = msi_clsid
        # Minor version: 0x003E
        struct.pack_into("<H", header, 24, 0x003E)
        # Major version: 4 (Dex) for MSI
        struct.pack_into("<H", header, 26, 0x0004)
        # Byte order: 0xFFFE = little-endian
        struct.pack_into("<H", header, 28, 0xFFFE)
        # Sector size power: 9 (512) = 2^9 = 512
        struct.pack_into("<H", header, 30, 9)
        # Mini sector size power: 6 (64) = 2^6 = 64
        struct.pack_into("<H", header, 32, 6)
        # Reserved: 6 bytes
        # Number of directory sectors: 0 (means 0 for 512-byte sectors)
        struct.pack_into("<i", header, 40, 0)
        # Number of FAT sectors: 1
        struct.pack_into("<i", header, 44, 1)
        # First directory sector: 2 (sector index 2)
        struct.pack_into("<i", header, 48, 2)
        # Transaction signature number: 0
        # Mini stream cutoff size: 4096
        struct.pack_into("<i", header, 56, 4096)
        # First mini FAT sector: -2 (end of chain, no mini stream)
        struct.pack_into("<i", header, 60, -2)
        # Number of mini FAT sectors: 0
        struct.pack_into("<i", header, 64, 0)
        # First DIFAT sector: -2 (end of chain)
        struct.pack_into("<i", header, 68, -2)
        # Number of DIFAT sectors: 0
        struct.pack_into("<i", header, 72, 0)
        # DIFAT entries: first 109 entries (only first = 1 for FAT sector 1)
        struct.pack_into("<i", header, 76, 1)
        for i in range(1, 109):
            struct.pack_into("<i", header, 76 + i * 4, -1)  # FREE

        self._fp.write(bytes(header))

        # 写入 FAT sector (sector 1)
        fat = bytearray(512)
        # FAT[0]: Free sectors marker
        struct.pack_into("<i", fat, 0, -3)  # 0xFFFFFFFD = FAT sector
        # FAT[1]: end of chain (FAT sector itself)
        struct.pack_into("<i", fat, 4, -2)  # 0xFFFFFFFE = end of chain
        # FAT[2..2+dir_sectors-1]: chain directory sectors
        for d in range(dir_sectors):
            if d < dir_sectors - 1:
                struct.pack_into("<i", fat, (2 + d) * 4, 2 + d + 1)  # point to next
            else:
                struct.pack_into("<i", fat, (2 + d) * 4, -2)  # end of chain
        # FAT[2+dir_sectors+]: end of chain for each stream sector
        for i in range(2 + dir_sectors, total_sectors):
            struct.pack_into("<i", fat, i * 4, -2)  # end of chain
        self._fp.write(bytes(fat))

        # 写入目录 (sector 2+)
        dir_data = bytearray(dir_sectors * 512)
        offset = 0

        # Root Entry (type=5 for root storage)
        root_name = "Root Entry".encode("utf-16-le")
        dir_data[offset:offset + len(root_name)] = root_name
        struct.pack_into("<H", dir_data, offset + 64, len(root_name) + 2)  # name length (bytes, including null)
        dir_data[offset + 66] = 0x05  # type: root storage
        dir_data[offset + 67] = 0x01  # color: black (root is always black)
        struct.pack_into("<i", dir_data, offset + 68, -1)  # left sibling
        struct.pack_into("<i", dir_data, offset + 72, -1)  # right sibling
        struct.pack_into("<i", dir_data, offset + 76, 1)   # child: first stream entry
        # Root CLSID: MSI database GUID
        dir_data[offset + 80:offset + 96] = msi_clsid
        struct.pack_into("<i", dir_data, offset + 96, 0)   # state bits
        struct.pack_into("<Q", dir_data, offset + 100, 0)  # creation time
        struct.pack_into("<Q", dir_data, offset + 108, 0)  # modified time
        struct.pack_into("<i", dir_data, offset + 116, -2)  # start sector: no mini stream
        struct.pack_into("<i", dir_data, offset + 120, 0)  # size low
        struct.pack_into("<i", dir_data, offset + 124, 0)  # size high

        # 为每个流创建目录条目
        for i, (name, data) in enumerate(streams.items()):
            offset = 128 * (i + 1)
            name_bytes = name.encode("utf-16-le")
            # Truncate name to fit (max 32 UTF-16 chars = 64 bytes)
            if len(name_bytes) > 64:
                name_bytes = name_bytes[:64]
            dir_data[offset:offset + len(name_bytes)] = name_bytes
            struct.pack_into("<H", dir_data, offset + 64, len(name_bytes) + 2)  # name length
            dir_data[offset + 66] = 0x02  # type: stream
            dir_data[offset + 67] = 0x00  # color: red
            struct.pack_into("<i", dir_data, offset + 68, -1)  # left sibling
            # Right sibling: point to next stream, or -1 if last
            right_sib = i + 2 if i < len(streams) - 1 else -1
            struct.pack_into("<i", dir_data, offset + 72, right_sib)
            struct.pack_into("<i", dir_data, offset + 76, -1)  # child (none for streams)
            # CLSID: zero
            struct.pack_into("<i", dir_data, offset + 96, 0)   # state bits
            start_sector, size = stream_sectors[name]
            struct.pack_into("<i", dir_data, offset + 116, start_sector)  # start sector
            struct.pack_into("<i", dir_data, offset + 120, size & 0xFFFFFFFF)  # size low
            struct.pack_into("<i", dir_data, offset + 124, (size >> 32) & 0xFFFFFFFF)  # size high

        self._fp.write(bytes(dir_data))

        # 写入流数据
        for name, data in streams.items():
            self._fp.write(data)
            # 填充到 512 对齐
            pad = (512 - (len(data) % 512)) % 512
            if pad:
                self._fp.write(b"\x00" * pad)


class _DirEntry:
    __slots__ = ("name", "type", "sid", "size", "entry_id",
                 "dir_child", "dir_sibling_left", "dir_sibling_right",
                 "dir_root", "difat_start", "mini_fat_start")

    def __init__(self, name, type, sid, size=0):
        self.name = name
        self.type = type  # 1=storage, 2=stream, 5=root
        self.sid = sid
        self.size = size
        self.entry_id = b""
        self.dir_child = -1
        self.dir_sibling_left = -1
        self.dir_sibling_right = -1
        self.dir_root = -1
        self.difat_start = -1
        self.mini_fat_start = -1


# ─── MSI 构建器 ──────────────────────────────────────────

class _MSIBuilder:
    """MSI 安装包构建器"""

    def __init__(self):
        self._source_dir = None
        self._mode = None
        self._output_path = None

    def build(self, source_dir, mode, output_path=None):
        self._source_dir = os.path.abspath(source_dir)
        self._mode = mode

        if not os.path.isdir(self._source_dir):
            raise FileNotFoundError(f"目录不存在: {self._source_dir}")

        # 确定输出路径
        if output_path is None:
            dir_name = os.path.basename(self._source_dir.rstrip("/\\"))
            self._output_path = os.path.join(
                os.path.dirname(self._source_dir),
                f"{dir_name}.msi"
            )
        else:
            self._output_path = output_path

        # 收集所有文件
        file_list = self._collect_files()

        # 根据模式构建
        if self._mode == 0:
            print("[PyMsi] 模式 0: 选错了 — 无事发生。")
            print("        请使用 PM.s(1) 普通模式 或 PM.s(2) 极速模式")
            return None

        elif self._mode == 1:
            return self._build_normal(file_list)

        elif self._mode == 2:
            return self._build_fast(file_list)

        else:
            raise ValueError(f"未知模式: {self._mode}，有效值为 0/1/2")

    def _collect_files(self):
        """收集源目录下所有文件"""
        file_list = []
        base = self._source_dir
        for root, dirs, files in os.walk(base):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, base)
                file_list.append((full, rel))
        return file_list

    def _build_normal(self, file_list):
        """普通模式：完整构建 MSI"""
        print(f"[PyMsi] 普通模式构建中...")
        print(f"[PyMsi] 源目录: {self._source_dir}")
        print(f"[PyMsi] 文件数: {len(file_list)}")
        return self._write_msi(file_list, compress=True)

    def _build_fast(self, file_list):
        """极速模式：跳过压缩，快速构建"""
        print(f"[PyMsi] ⚡ 极速模式构建中...")
        print(f"[PyMsi] 源目录: {self._source_dir}")
        print(f"[PyMsi] 文件数: {len(file_list)}")
        return self._write_msi(file_list, compress=False)

    def _write_msi(self, file_list, compress):
        """写入 MSI 文件"""
        try:
            # 先尝试使用 Python 内置的 msilib（Windows）
            return self._write_msi_msilib(file_list, compress)
        except ImportError:
            # 非 Windows 环境，使用纯 Python 实现
            return self._write_msi_pure(file_list, compress)

    def _write_msi_msilib(self, file_list, compress):
        """使用 msilib 构建 MSI (Windows)"""
        import msilib

        product_code = self._generate_product_code()
        db = msilib.init_database(
            self._output_path,
            msilib.schema,
            os.path.basename(self._source_dir),
            product_code,
            "1.0.0.0",
            "PyMsi",
        )

        # 添加 Directory 表
        msilib.add_data(db, "Directory", [
            ("TARGETDIR", "", "SourceDir"),
            ("ProgramFilesFolder", "TARGETDIR", "PFiles"),
            ("INSTALLDIR", "ProgramFilesFolder", f"PyMsi_{os.path.basename(self._source_dir)}"),
        ])

        # 添加 Property 表
        msilib.add_data(db, "Property", [
            ("ProductCode", product_code),
            ("ProductName", os.path.basename(self._source_dir)),
            ("ProductVersion", "1.0.0.0"),
            ("Manufacturer", "PyMsi"),
            ("ARPURLINFOABOUT", "https://github.com/pymsi"),
        ])

        # 添加 Feature 表
        feature_name = "Complete"
        msilib.add_data(db, "Feature", [
            (feature_name, "", "Complete", "", 1, "INSTALLDIR", 0),
        ])

        # 添加 Component 表 + File 表 + FeatureComponents
        # 同时将文件添加到 CAB
        cab = msilib.CAB("PyMsi.cab")
        for i, (full_path, rel_path) in enumerate(file_list, 1):
            comp_id = self._make_guid(rel_path)
            file_name = os.path.basename(rel_path)
            short_name = file_name[:8].upper() if len(file_name) > 8 else file_name.upper()

            msilib.add_data(db, "Component", [
                (comp_id, comp_id, "INSTALLDIR", 2 if compress else 0),
            ])
            msilib.add_data(db, "FeatureComponents", [
                (feature_name, comp_id),
            ])
            msilib.add_data(db, "File", [
                (file_name, comp_id, file_name, len(open(full_path, "rb").read()),
                 "1.0.0.0", "", 8192, i),
            ])

            cab.add_file(full_path)

        # 添加 Media 表
        msilib.add_data(db, "Media", [
            (1, len(file_list), "#PyMsi.cab"),
        ])

        # 添加 InstallExecuteSequence 表
        msilib.add_data(db, "InstallExecuteSequence", [
            ("InstallValidate", "", 1400),
            ("InstallInitialize", "", 1500),
            ("InstallFinalize", "", 6600),
        ])

        cab.commit(db)
        db.Commit()
        print(f"[PyMsi] 构建完成: {self._output_path}")
        return self._output_path

    def _write_msi_pure(self, file_list, compress):
        """纯 Python 实现 MSI 构建（跨平台）"""
        print(f"[PyMsi] 使用纯 Python 模式构建 MSI...")

        # 收集所有文件数据
        total_size = 0
        file_entries = []
        for full_path, rel_path in file_list:
            with open(full_path, "rb") as f:
                data = f.read()
            file_entries.append((rel_path, data))
            total_size += len(data)

        # 构建 MSI 数据库内容
        db_content = self._build_msi_database(file_entries)

        # 创建 OLE compound file
        ole = _OLEWriter(self._output_path)
        ole.add_stream("\x05SummaryInformation", self._build_summary_info())
        ole.add_stream("_\x05DocumentSummaryInformation", self._build_doc_summary())
        ole.add_stream("Data", db_content)
        ole.add_stream("_Streams", self._build_streams(file_entries))
        ole.close()

        size_mb = total_size / (1024 * 1024)
        print(f"[PyMsi] 构建完成: {self._output_path}")
        print(f"[PyMsi] 总大小: {size_mb:.2f} MB")
        return self._output_path

    def _build_msi_database(self, file_entries):
        """构建 MSI 数据库表结构"""
        # 简化的 MSI 数据库
        tables = []

        # _Tables 表
        tables.append(self._make_table("_Tables", ["Name"], [
            ("Property",), ("Directory",), ("Component",),
            ("Feature",), ("FeatureComponents",), ("File",),
            ("Media",), ("InstallExecuteSequence",),
        ]))

        # Property 表
        product_code = self._generate_product_code()
        tables.append(self._make_table("Property", ["Property", "Value"], [
            ("ProductCode", product_code),
            ("ProductName", os.path.basename(self._source_dir)),
            ("ProductVersion", "1.0.0.0"),
            ("Manufacturer", "PyMsi"),
            ("ARPURLINFOABOUT", "https://github.com/pymsi"),
        ]))

        # Directory 表
        tables.append(self._make_table("Directory", ["Directory", "Directory_Parent", "DefaultDir"], [
            ("TARGETDIR", "", "SourceDir"),
            ("ProgramFilesFolder", "TARGETDIR", "PFiles"),
            ("INSTALLDIR", "ProgramFilesFolder", f"PyMsi:{os.path.basename(self._source_dir)}"),
        ]))

        # Component 表
        components = []
        for rel_path, _ in file_entries:
            comp_id = self._make_guid(rel_path)
            components.append((comp_id, comp_id, "INSTALLDIR", rel_path))
        tables.append(self._make_table("Component", ["Component", "ComponentId", "Directory_", "Attributes"], components))

        # Feature 表
        tables.append(self._make_table("Feature", ["Feature", "Feature_Parent", "Title", "Display", "Level", "Directory_", "Attributes"], [
            ("Complete", "", "Complete", "", 1, "INSTALLDIR", 0),
        ]))

        # FeatureComponents 表
        fc = [(comp[0], "Complete") for comp in components]
        tables.append(self._make_table("FeatureComponents", ["Feature_", "Component_"], fc))

        # File 表
        files = []
        for i, (rel_path, data) in enumerate(file_entries):
            comp_id = self._make_guid(rel_path)
            file_name = os.path.basename(rel_path)
            files.append((
                file_name, comp_id, file_name, len(data),
                "1.0.0.0", "", 0, 8192, 1 + i
            ))
        tables.append(self._make_table("File", [
            "File", "Component_", "FileName", "FileSize",
            "Version", "Language", "Attributes", "Sequence"
        ], files))

        # Media 表
        tables.append(self._make_table("Media", ["DiskId", "LastSequence", "Cabinet"], [
            (1, len(file_entries), "#PyMsi.cab"),
        ]))

        # InstallExecuteSequence 表
        tables.append(self._make_table("InstallExecuteSequence", ["Action", "Condition", "Sequence"], [
            ("InstallValidate", "", 1400),
            ("InstallInitialize", "", 1500),
            ("InstallFinalize", "", 6600),
        ]))

        # 序列化所有表
        result = b""
        for table_name, columns, rows in tables:
            result += self._serialize_table(table_name, columns, rows)

        return result

    def _make_table(self, name, columns, rows):
        return (name, columns, rows)

    def _serialize_table(self, name, columns, rows):
        """简单序列化表数据"""
        lines = []
        lines.append(f"[{name}]")
        lines.append("\t".join(columns))
        for row in rows:
            lines.append("\t".join(str(v) for v in row))
        lines.append("")
        return "\n".join(lines).encode("utf-8")

    def _build_summary_info(self):
        """构建 Summary Information 流"""
        # 简化的 Summary Information
        data = bytearray(4096)
        # Property set format
        # 写入基本的摘要信息
        return bytes(data)

    def _build_doc_summary(self):
        """构建 Document Summary Information 流"""
        return b"\x00" * 4096

    def _build_streams(self, file_entries):
        """构建文件流数据"""
        result = b""
        for rel_path, data in file_entries:
            result += struct.pack("<I", len(rel_path.encode("utf-8")))
            result += rel_path.encode("utf-8")
            result += struct.pack("<Q", len(data))
            result += data
        return result

    def _generate_product_code(self):
        """生成产品 GUID"""
        return str(uuid.uuid4()).upper()

    def _make_guid(self, seed):
        """基于种子生成确定性 GUID"""
        h = hashlib.md5(seed.encode("utf-8")).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}".upper()


# ─── 公开 API ───────────────────────────────────────────

from .html_builder import _HTMLBuilder, _HTMLModule
from .game import _GameModule, _GAME_NAMES
from .image import _ImageModule
from .hex import _HexModule
from .ai import _AIModule


# ═══════════════════════════════════════════════════════════════
# 主类
# ═══════════════════════════════════════════════════════════════

class _PyMsi:
    """
    PyMsi 主类 — 可调用对象 + .s() 方法 + .html 子模块

    用法:
        # 文件夹 → MSI
        import PyMsi as PM
        PM("C:/your/folder")
        PM.s(2)  # 极速模式构建

        # HTML → EXE (像 Electron 一样)
        PM.html("C:/html_project")
        PM.html.sandbox(True)   # 沙箱模式
        PM.html.icon("C:/icon.ico")
        PM.html.build()
    """

    def __init__(self):
        self._source_dir = None
        self._mode = None
        self._builder = _MSIBuilder()
        self._html_builder = _HTMLBuilder()
        self._html_module = _HTMLModule(self._html_builder, self._print_readme)
        self._game_module = _GameModule()
        self._image_module = _ImageModule()
        self._hex_module = _HexModule()
        self._ai_module = _AIModule()

    def __call__(self, path):
        """
        设置源文件夹路径

        Args:
            path: 要打包成 MSI 的文件夹路径

        Returns:
            self (用于链式调用)
        """
        self._source_dir = path
        print(f"[PyMsi] 源目录已设置: {path}")
        return self

    def s(self, mode):
        """
        选择构建模式并开始构建

        Args:
            mode: 构建模式
                0 = 选错了，不执行任何操作
                1 = 普通模式，完整构建，压缩率高
                2 = 极速模式，跳过压缩，构建极快

        Returns:
            生成的 MSI 文件路径，或 None
        """
        self._mode = mode

        if mode not in MODE_DESCRIPTIONS:
            raise ValueError(f"无效模式: {mode}，有效值: 0, 1, 2")

        desc = MODE_DESCRIPTIONS[mode]
        print(f"[PyMsi] 模式: {mode} - {desc}")

        if mode == 0:
            return None

        if self._source_dir is None:
            raise RuntimeError("请先使用 PM(path) 设置源目录，再调用 PM.s()")

        return self._builder.build(self._source_dir, mode)

    def _print_readme(self):
        """内部方法: 打印 README"""
        print(_README)

    @property
    def readme(self):
        """打印完整的帮助文档"""
        print(_README)
        return self

    # ═══════════════════════════════════════════════════════════
    # 别名 Aliases — 长短名通用，怎么写都行
    # ═══════════════════════════════════════════════════════════

    # PM.build() = PM("path") + PM.s(2) 一步到位
    def build(self, path, mode=2):
        """别名: 一步构建 MSI — PM.build("path") = PM("path"); PM.s(2)"""
        self.__call__(path)
        return self.s(mode)

    def b(self, path, mode=2):
        """短别名: PM.b("path") = PM.build(path, 2)"""
        return self.build(path, mode)

    def mode(self, m):
        """别名: PM.mode(2) = PM.s(2)"""
        return self.s(m)

    def m(self, m):
        """短别名: PM.m(2) = PM.s(2)"""
        return self.s(m)

    # MSI 相关: PM.msi / PM.pack / PM.make
    @property
    def msi(self):
        """别名: PM.msi("path", 2) 一步构建 MSI（callable 属性）"""
        class _MSIAliaser:
            def __init__(self, outer): self._outer = outer
            def __call__(self, path, mode=2):
                self._outer.__call__(path)
                return self._outer.s(mode)
            def __repr__(self):
                return "<PyMsi.msi> alias: PM.msi('path') = PM('path'); PM.s(2)"
        return _MSIAliaser(self)

    @property
    def pack(self):
        """别名: PM.pack(path) = PM.msi(path, 2)"""
        class _PAliaser:
            def __init__(self, outer): self._outer = outer
            def __call__(self, path, mode=2):
                self._outer.__call__(path)
                return self._outer.s(mode)
            def __repr__(self):
                return "<PyMsi.pack> alias"
        return _PAliaser(self)

    @property
    def make(self):
        """别名: PM.make(path, 2) 同 PM.build"""
        class _MAliaser:
            def __init__(self, outer): self._outer = outer
            def __call__(self, path, mode=2):
                self._outer.__call__(path)
                return self._outer.s(mode)
        return _MAliaser(self)

    # help 别名
    def help(self):
        """别名: PM.help() = PM.readme"""
        print(_README)
        return self

    @property
    def doc(self):
        """别名: PM.doc = PM.readme"""
        print(_README)
        return self

    @property
    def man(self):
        """别名: PM.man = PM.readme"""
        print(_README)
        return self

    # ═══════════════════════════════════════════════════════════
    # 子模块短别名
    # ═══════════════════════════════════════════════════════════

    @property
    def h(self):
        """短别名: PM.h = PM.html"""
        return self._html_module

    @property
    def web(self):
        """别名: PM.web = PM.html"""
        return self._html_module

    @property
    def app(self):
        """别名: PM.app = PM.html (把 HTML 做成 app)"""
        return self._html_module

    @property
    def electron(self):
        """别名: PM.electron = PM.html"""
        return self._html_module

    @property
    def g(self):
        """短别名: PM.g = PM.game"""
        return self._game_module

    @property
    def games(self):
        """别名: PM.games = PM.game"""
        return self._game_module

    @property
    def play(self):
        """别名: PM.play("Snake") = PM.game.Grap("Snake")"""
        class _Play:
            def __init__(self, gm): self._g = gm
            def __call__(self, name):
                return self._g.Grap(name)
            def __repr__(self):
                return "<PyMsi.play> alias: PM.play(name) = PM.game.Grap(name)"
            def __getattr__(self, item):
                return getattr(self._g, item)
        return _Play(self._game_module)

    @property
    def img(self):
        """短别名: PM.img = PM.image"""
        return self._image_module

    @property
    def i(self):
        """短别名: PM.i = PM.image"""
        return self._image_module

    @property
    def pic(self):
        """别名: PM.pic = PM.image"""
        return self._image_module

    @property
    def font(self):
        """别名: PM.font(folder, out) = PM.image.ttf(...)"""
        return self._image_module._ttf

    @property
    def fonts(self):
        """别名: PM.fonts = PM.image.ttf"""
        return self._image_module._ttf

    @property
    def ttf(self):
        """别名: PM.ttf(folder, out) = PM.image.ttf(...)"""
        return self._image_module._ttf

    # hex 子模块别名: PM.hexdump / PM.hd / PM.hexview
    @property
    def hexdump(self):
        """别名: PM.hexdump = PM.hex"""
        return self._hex_module

    @property
    def hd(self):
        """短别名: PM.hd = PM.hex"""
        return self._hex_module

    @property
    def hexview(self):
        """别名: PM.hexview = PM.hex"""
        return self._hex_module

    @property
    def html(self):
        """
        HTML → EXE 子模块

        像 Electron 一样把 HTML 文件夹打包成独立 EXE。
        支持自定义图标、沙箱模式开关。

        用法:
            PM.html("C:/html_project")
            PM.html.icon("C:/icon.ico")
            PM.html.sandbox(True)   # 加沙箱
            PM.html.build()
        """
        return self._html_module

    @property
    def game(self):
        """
        内置游戏模板库 (30+ 游戏)

        两行代码即开即玩！

        用法:
            PM.game.Grap("Snake")    # 贪吃蛇
            PM.game.Grap("Tetris")   # 俄罗斯方块
            PM.game.list()            # 列出所有游戏
        """
        return self._game_module

    @property
    def image(self):
        """
        图片处理模块

        当前功能: 图片 → TTF 字体 (纯 Python, 零外部依赖)
          - 支持 png / jpg / jpeg / bmp / ico / gif
          - GIF 自动拆帧，每帧作为一个独立字形
          - 按文件名自动识别对应字符，或提供 mapping 字典

        用法:
            # 方式一：命名 = 字符 (A.png → 'A', 中.png → '中')
            PM.image.ttf("C:/glyph_folder", "out.ttf")

            # 方式二：自定义映射
            PM.image.ttf("C:/glyphs", "out.ttf",
                         mapping={"glyph1.png": "A", "glyph2.png": "中"})

            # 查看完整教程
            PM.image.ttf.help()
        """
        return self._image_module

    @property
    def hex(self):
        """
        文件 Hex 解析子模块

        输入文件地址 → 找到对应文件 → 解析 16 进制 → 全部输出到终端

        用法:
            # 直接给文件路径, 全部 hex 输出到终端
            PM.hex("C:/some/file.bin")

            # 在目录里按文件名搜索, 找到后解析
            PM.hex.find("C:/my_project", "config.dat")

            # 带参数控制输出格式
            PM.hex.dump("C:/file.bin", bytes_per_line=16,
                        start_offset=0, max_bytes=512)

            # PM.hex == PM.hexdump == PM.hd == PM.hexview
        """
        return self._hex_module

    @property
    def ai(self):
        """
        AI 空壳子模块 — 告诉它 API Key + AI API 官网, 就能问 AI 问题

        用法:
            PM.ai.key = "sk-xxx"                      # 1. 设 API Key
            PM.ai.url = "https://api.openai.com"      # 2. 设 AI API 官网
            PM.ai.imput("你好, 你是谁?")               # 3. 问问题 (输出自动 print)

            # PM.ai("问题")  直接问也行
            # print(PM.ai.output)  拿原始输出文本
            # PM.ai.ask / chat / question / send / say  都是 imput 别名
        """
        return self._ai_module

    # ai 子模块别名: PM.AI / PM.gpt / PM.chat / PM.llm
    @property
    def AI(self):
        """别名: PM.AI = PM.ai"""
        return self._ai_module

    @property
    def gpt(self):
        """别名: PM.gpt = PM.ai"""
        return self._ai_module

    @property
    def llm(self):
        """别名: PM.llm = PM.ai"""
        return self._ai_module

    @property
    def chatbot(self):
        """别名: PM.chatbot = PM.ai"""
        return self._ai_module


# ─── 模块替换：把自身变成可调用的 PM 实例 ─────────────────
# 先捕获所有模块属性，再替换 sys.modules
import sys as _sys
_module_file = __file__
_module_path = __path__  # noqa: F821 — 包级别 __path__ 变量
_module_name = __name__
_module_package = __package__

# 导出单例
PM = _PyMsi()

# 把模块自身替换为可调用的 PM 实例
# 这样 import PyMsi as PM 之后 PM(...) 和 PM.s(...) 都可用
_sys.modules[__name__] = PM

# 保留模块属性以便 from PyMsi import ... 和包发现正常工作
PM.__all__ = ["PM"]
PM.__version__ = "1.4.5"
PM.__file__ = _module_file
PM.__path__ = _module_path
PM.__name__ = _module_name
PM.__package__ = _module_package