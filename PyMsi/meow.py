"""PyMsi.meow — 🐱 .meow 文件打包/解包模块 (1.5.4 新增)

把多个文件"揉成"一个 .meow 文件, 同时吐出 address.json
address.json 存着每个文件的数字地址 (标准格式: 154.04.1.1:数字地址)
解包时提供 address.json 所在目录, 自动从 .meow 提取所有文件到 D:/Dist

.meow 文件格式 (纯自研):
    ┌───────────────────────────────────────┐
    │ Magic: "MEOW" (4 bytes)              │
    │ Version: uint32 LE (4 bytes)          │
    │ File count: uint32 LE (4 bytes)       │
    ├───────────────────────────────────────┤
    │ 文件数据区 (连续存储):                │
    │   [file 1 raw data]                   │
    │   [file 2 raw data]                   │
    │   ...                                 │
    ├───────────────────────────────────────┤
    │ 索引表 (在文件末尾):                  │
    │   每个文件条目:                       │
    │     address_id: uint32 LE (4 bytes)   │
    │     offset:     uint64 LE (8 bytes)   │
    │     size:       uint64 LE (8 bytes)   │
    │     name_len:   uint16 LE (2 bytes)    │
    │     name:       bytes (name_len)      │
    └───────────────────────────────────────┘

用法:
    import PyMsi as PM

    # ── 打包: 把文件揉成 .meow ──
    PM.meow.disteow(["a.txt", "b.png", "c.pdf"])
    # → 生成 D:/Meow/output.meow + D:/Meow/address.json

    # 自定义输出
    PM.meow.disteow(["a.txt", "b.png"], output="E:/test/data.meow")

    # 直接在脚本里写文件列表
    PM.meow.disteow([
        "C:/file1.txt",
        "C:/file2.png",
        "C:/file3.pdf",
    ])

    # ── 解包: 从 .meow 取出所有文件 ──
    PM.meow.undisteow("D:/Meow/")    # 提供 address.json 所在目录
    # → 读取 address.json → 找到 .meow → 提取所有文件到 D:/Dist

    # 别名: PM.cat / PM.meow / PM.揉 / PM.猫
"""

import os
import json
import struct
import hashlib

# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════

_MEOW_MAGIC = b"MEOW"
_MEOW_VERSION = 1
_ADDRESS_PREFIX = "154.04.1.1"  # 标准地址前缀
_DEFAULT_OUTPUT_DIR = "D:/Meow"
_DEFAULT_DIST_DIR = "D:/Dist"
_ADDRESS_JSON_NAME = "address.json"
_DEFAULT_MEOW_NAME = "output.meow"

# 索引条目结构: address_id(I) + offset(Q) + size(Q) + name_len(H) + name
_INDEX_ENTRY_FMT = "<IQQH"  # 不含 name 部分
_INDEX_ENTRY_SIZE = struct.calcsize(_INDEX_ENTRY_FMT)  # 22 bytes


def _make_address(file_id):
    """生成标准地址: 154.04.1.1:00000001"""
    return f"{_ADDRESS_PREFIX}:{file_id:08d}"


def _make_file_id(address):
    """从地址中提取数字地址 (文件ID)"""
    parts = address.split(":")
    if len(parts) != 2:
        raise ValueError(f"无效的地址格式: {address} (标准格式: {_ADDRESS_PREFIX}:数字地址)")
    return int(parts[1])


# ═══════════════════════════════════════════════════════════════
# .meow 打包器
# ═══════════════════════════════════════════════════════════════

class _MeowPacker:
    """.meow 文件打包器 — 把多个文件揉进一个 .meow"""

    def __init__(self, output_path):
        self._output_path = output_path
        self._files = []  # [(file_id, original_path, data)]
        self._file_counter = 0

    def add_file(self, file_path):
        """添加一个文件到打包列表"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        self._file_counter += 1
        file_id = self._file_counter
        original_name = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            data = f.read()

        self._files.append((file_id, original_name, file_path, data))
        return _make_address(file_id)

    def write(self):
        """写入 .meow 文件, 返回 address.json 数据"""
        output_dir = os.path.dirname(self._output_path) or "."
        os.makedirs(output_dir, exist_ok=True)

        file_count = len(self._files)
        index_entries = []  # [(file_id, offset, size, name_bytes)]

        with open(self._output_path, "wb") as f:
            # ── 头部 (12 bytes) ──
            f.write(_MEOW_MAGIC)
            f.write(struct.pack("<I", _MEOW_VERSION))
            f.write(struct.pack("<I", file_count))

            # ── 文件数据区 ──
            for file_id, name, path, data in self._files:
                offset = f.tell()
                f.write(data)
                index_entries.append((file_id, offset, len(data), name.encode("utf-8")))

            # ── 索引表 ──
            index_offset = f.tell()
            for file_id, offset, size, name_bytes in index_entries:
                f.write(struct.pack(_INDEX_ENTRY_FMT, file_id, offset, size, len(name_bytes)))
                f.write(name_bytes)

        # ── 生成 address.json ──
        address_data = {
            "format": "meow",
            "version": _MEOW_VERSION,
            "meow_file": os.path.basename(self._output_path),
            "meow_path": os.path.abspath(self._output_path),
            "file_count": file_count,
            "index_offset": index_offset,
            "files": {}
        }

        for file_id, name, path, data in self._files:
            address = _make_address(file_id)
            md5 = hashlib.md5(data).hexdigest()
            address_data["files"][address] = {
                "id": file_id,
                "name": name,
                "original_path": os.path.abspath(path),
                "size": len(data),
                "md5": md5
            }

        return address_data


# ═══════════════════════════════════════════════════════════════
# .meow 解包器
# ═══════════════════════════════════════════════════════════════

class _MeowUnpacker:
    """.meow 文件解包器 — 从 address.json 找到 .meow, 提取所有文件"""

    def __init__(self, address_dir):
        """
        Args:
            address_dir: address.json 所在的硬盘目录
        """
        self._address_dir = address_dir
        self._address_path = os.path.join(address_dir, _ADDRESS_JSON_NAME)
        self._address_data = None
        self._meow_path = None

        if not os.path.isfile(self._address_path):
            raise FileNotFoundError(
                f"在目录中找不到 {_ADDRESS_JSON_NAME}: {address_dir}\n"
                f"请提供打包时吐出 address.json 的那个目录"
            )

        with open(self._address_path, "r", encoding="utf-8") as f:
            self._address_data = json.load(f)

        # 找到 .meow 文件 (优先用绝对路径, 其次在 address.json 同目录找)
        meow_path = self._address_data.get("meow_path", "")
        if meow_path and os.path.isfile(meow_path):
            self._meow_path = meow_path
        else:
            meow_name = self._address_data.get("meow_file", _DEFAULT_MEOW_NAME)
            candidate = os.path.join(address_dir, meow_name)
            if os.path.isfile(candidate):
                self._meow_path = candidate
            else:
                raise FileNotFoundError(
                    f"找不到 .meow 文件\n"
                    f"  在 address.json 中记录的路径: {meow_path}\n"
                    f"  在目录中查找: {candidate}\n"
                    f"请确保 .meow 文件和 address.json 在同一目录"
                )

    def list_files(self):
        """列出 .meow 中所有文件的地址和名称"""
        files = self._address_data.get("files", {})
        result = []
        for address, info in sorted(files.items(), key=lambda x: x[1]["id"]):
            result.append({
                "address": address,
                "name": info["name"],
                "size": info["size"],
                "md5": info.get("md5", "")
            })
        return result

    def extract_file(self, address, output_path=None):
        """从 .meow 中提取单个文件

        Args:
            address: 文件地址 (154.04.1.1:00000001)
            output_path: 输出路径, 默认 D:/Dist/原始文件名
        Returns:
            输出文件路径
        """
        files = self._address_data.get("files", {})
        if address not in files:
            raise KeyError(
                f"地址不存在: {address}\n"
                f"可用地址: {list(files.keys())[:5]}..."
            )

        info = files[address]
        file_id = info["id"]
        original_name = info["name"]
        expected_size = info["size"]

        # 从 .meow 文件中按偏移读取
        offset, size = self._find_file_offset(file_id, expected_size)

        if output_path is None:
            os.makedirs(_DEFAULT_DIST_DIR, exist_ok=True)
            output_path = os.path.join(_DEFAULT_DIST_DIR, original_name)

        with open(self._meow_path, "rb") as f:
            f.seek(offset)
            data = f.read(size)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(data)

        return output_path

    def extract_all(self, output_dir=None):
        """从 .meow 中提取所有文件

        Args:
            output_dir: 输出目录, 默认 D:/Dist
        Returns:
            list[dict] — 每个文件的 {address, name, path, size}
        """
        if output_dir is None:
            output_dir = _DEFAULT_DIST_DIR
        os.makedirs(output_dir, exist_ok=True)

        # 读取索引表
        index_map = self._read_index()

        files = self._address_data.get("files", {})
        results = []

        with open(self._meow_path, "rb") as f:
            for address, info in sorted(files.items(), key=lambda x: x[1]["id"]):
                file_id = info["id"]
                original_name = info["name"]

                if file_id not in index_map:
                    raise KeyError(f"文件ID {file_id} 不在 .meow 索引表中")

                offset, size = index_map[file_id]
                f.seek(offset)
                data = f.read(size)

                output_path = os.path.join(output_dir, original_name)
                with open(output_path, "wb") as out:
                    out.write(data)

                results.append({
                    "address": address,
                    "name": original_name,
                    "path": output_path,
                    "size": size
                })

        return results

    def _read_index(self):
        """读取 .meow 索引表, 返回 {file_id: (offset, size)}"""
        index_offset = self._address_data.get("index_offset")
        file_count = self._address_data.get("file_count", 0)

        index_map = {}
        with open(self._meow_path, "rb") as f:
            # 验证魔数
            magic = f.read(4)
            if magic != _MEOW_MAGIC:
                raise ValueError(f"无效的 .meow 文件 (魔数不匹配): {magic}")

            version = struct.unpack("<I", f.read(4))[0]
            count = struct.unpack("<I", f.read(4))[0]

            if index_offset is None:
                # 如果没有存储 index_offset, 需要扫描整个文件
                # 先跳到末尾读取索引 (索引在文件数据之后)
                # 我们需要扫描: 从头部开始, 跳过文件数据
                # 更简单的方法: 从文件末尾倒推
                f.seek(0, 2)
                file_end = f.tell()

                # 索引表大小 = count * (22 + name_len)
                # 但 name_len 可变, 所以从文件末尾往前读
                # 先尝试从 address.json 中的信息构建
                # 如果没有 index_offset, 用 address.json 中的 size 信息
                files = self._address_data.get("files", {})
                offset_acc = 12  # 头部 12 bytes
                for address, info in sorted(files.items(), key=lambda x: x[1]["id"]):
                    index_map[info["id"]] = (offset_acc, info["size"])
                    offset_acc += info["size"]
                return index_map

            # 有 index_offset, 直接读取索引表
            f.seek(index_offset)
            for _ in range(count):
                header = f.read(_INDEX_ENTRY_SIZE)
                if len(header) < _INDEX_ENTRY_SIZE:
                    break
                file_id, offset, size, name_len = struct.unpack(_INDEX_ENTRY_FMT, header)
                name = f.read(name_len).decode("utf-8", errors="replace")
                index_map[file_id] = (offset, size)

        return index_map

    def _find_file_offset(self, file_id, expected_size):
        """找到指定文件在 .meow 中的偏移和大小"""
        index_map = self._read_index()
        if file_id not in index_map:
            raise KeyError(f"文件ID {file_id} 不在 .meow 索引表中")
        return index_map[file_id]


# ═══════════════════════════════════════════════════════════════
# 主模块: _MeowModule
# ═══════════════════════════════════════════════════════════════

class _MeowModule:
    """PyMsi.meow — 🐱 .meow 文件打包/解包模块 (1.5.4 新增)

    把多个文件揉成一个 .meow, 同时吐出 address.json
    address.json 存着每个文件的数字地址 (154.04.1.1:数字地址)
    解包时提供 address.json 所在目录, 提取所有文件到 D:/Dist

    用法:
        # 打包 (揉成 .meow)
        PM.meow.disteow(["a.txt", "b.png", "c.pdf"])
        # → D:/Meow/output.meow + D:/Meow/address.json

        # 自定义输出路径
        PM.meow.disteow(["a.txt", "b.png"], output="E:/test/data.meow")

        # 解包 (从 .meow 取出所有文件)
        PM.meow.undisteow("D:/Meow/")
        # → 读取 address.json → 提取所有文件到 D:/Dist

        # 列出 .meow 中的文件
        PM.meow.list("D:/Meow/")

        # 别名: PM.cat / PM.揉 / PM.猫
    """

    def __init__(self):
        self.output_dir = _DEFAULT_OUTPUT_DIR
        self.dist_dir = _DEFAULT_DIST_DIR

    def __repr__(self):
        return (f"<PyMsi.meow [🐱揉.meow] "
                f"output_dir={self.output_dir} dist_dir={self.dist_dir}>")

    # ─── 打包: disteow ───────────────────────────────────

    def disteow(self, files, output=None):
        """把多个文件揉成一个 .meow

        在脚本里直接写你要揉的文件列表, 它会:
            1. 把所有文件存进一个 .meow 容器
            2. 在输出目录吐出 address.json
            3. address.json 里存着每个文件的数字地址 (154.04.1.1:数字地址)

        Args:
            files: list[str]    要揉的文件路径列表
            output: str        .meow 输出路径, 默认 D:/Meow/output.meow

        Returns:
            dict — {meow_path, address_path, file_count, addresses}

        用法:
            PM.meow.disteow(["a.txt", "b.png", "c.pdf"])
            PM.meow.disteow(["a.txt"], output="E:/test/data.meow")
        """
        if not files:
            raise ValueError("文件列表不能为空")

        if output is None:
            output = os.path.join(self.output_dir, _DEFAULT_MEOW_NAME)

        # 确保输出目录存在
        output_dir = os.path.dirname(output) or "."
        os.makedirs(output_dir, exist_ok=True)

        # 打包
        packer = _MeowPacker(output)
        addresses = []
        for file_path in files:
            addr = packer.add_file(file_path)
            addresses.append(addr)

        address_data = packer.write()

        # 写 address.json
        address_path = os.path.join(output_dir, _ADDRESS_JSON_NAME)
        with open(address_path, "w", encoding="utf-8") as f:
            json.dump(address_data, f, ensure_ascii=False, indent=2)

        result = {
            "meow_path": os.path.abspath(output),
            "address_path": os.path.abspath(address_path),
            "file_count": len(files),
            "addresses": addresses
        }

        print(f"[PyMsi.meow] 揉成 .meow 完成!")
        print(f"  .meow 文件: {result['meow_path']}")
        print(f"  address.json: {result['address_path']}")
        print(f"  文件数量: {result['file_count']}")
        print(f"  数字地址示例: {addresses[0] if addresses else '无'}")

        return result

    # ─── 解包: undisteow ────────────────────────────────

    def undisteow(self, address_dir, output_dir=None):
        """从 .meow 中取出所有文件

        你需要提供打包时吐出的 address.json 所在的硬盘目录
        库会找到 address.json, 根据每个文件的数字地址
        从 .meow 中把每个文件都掏出来, 吐到 D:/Dist

        Args:
            address_dir: str     address.json 所在的硬盘目录
            output_dir: str      输出目录, 默认 D:/Dist

        Returns:
            list[dict] — 每个文件的 {address, name, path, size}

        用法:
            PM.meow.undisteow("D:/Meow/")       # 提取到 D:/Dist
            PM.meow.undisteow("E:/test/", "F:/out")  # 提取到 F:/out
        """
        if output_dir is None:
            output_dir = self.dist_dir

        unpacker = _MeowUnpacker(address_dir)

        # 打印文件列表
        file_list = unpacker.list_files()
        print(f"[PyMsi.meow] 找到 {len(file_list)} 个文件:")
        for item in file_list:
            print(f"  {item['address']}  {item['name']}  ({item['size']} bytes)")

        # 提取所有文件
        results = unpacker.extract_all(output_dir)

        print(f"\n[PyMsi.meow] 解包完成! 提取到: {output_dir}")
        for item in results:
            print(f"  {item['address']}  →  {item['path']}")

        return results

    # ─── 查看文件列表 ────────────────────────────────────

    def list(self, address_dir):
        """列出 .meow 中所有文件 (不提取)

        Args:
            address_dir: str    address.json 所在的硬盘目录

        Returns:
            list[dict] — 每个文件的 {address, name, size, md5}

        用法:
            PM.meow.list("D:/Meow/")
        """
        unpacker = _MeowUnpacker(address_dir)
        file_list = unpacker.list_files()

        print(f"[PyMsi.meow] .meow 中的文件 ({len(file_list)} 个):")
        for item in file_list:
            print(f"  {item['address']}  {item['name']:20s}  {item['size']:>10d} bytes  md5={item['md5'][:8]}...")

        return file_list

    # ─── 提取单个文件 ────────────────────────────────────

    def extract(self, address_dir, address, output_path=None):
        """从 .meow 中提取单个文件

        Args:
            address_dir: str    address.json 所在的硬盘目录
            address: str        文件地址 (154.04.1.1:00000001)
            output_path: str    输出路径, 默认 D:/Dist/原始文件名

        Returns:
            str — 输出文件路径

        用法:
            PM.meow.extract("D:/Meow/", "154.04.1.1:00000001")
        """
        unpacker = _MeowUnpacker(address_dir)
        path = unpacker.extract_file(address, output_path)
        print(f"[PyMsi.meow] 提取: {address} → {path}")
        return path

    # ─── 别名方法 ────────────────────────────────────────

    def pack(self, *args, **kwargs):
        """别名: PM.meow.pack() == PM.meow.disteow()"""
        return self.disteow(*args, **kwargs)

    def unpack(self, *args, **kwargs):
        """别名: PM.meow.unpack() == PM.meow.undisteow()"""
        return self.undisteow(*args, **kwargs)

    def merge(self, *args, **kwargs):
        """别名: PM.meow.merge() == PM.meow.disteow()"""
        return self.disteow(*args, **kwargs)

    def split(self, *args, **kwargs):
        """别名: PM.meow.split() == PM.meow.undisteow()"""
        return self.undisteow(*args, **kwargs)

    def combine(self, *args, **kwargs):
        """别名: PM.meow.combine() == PM.meow.disteow()"""
        return self.disteow(*args, **kwargs)

    def separate(self, *args, **kwargs):
        """别名: PM.meow.separate() == PM.meow.undisteow()"""
        return self.undisteow(*args, **kwargs)

    def 揉(self, *args, **kwargs):
        """别名: PM.meow.揉() == PM.meow.disteow()"""
        return self.disteow(*args, **kwargs)

    def help(self):
        """打印帮助"""
        print(self.__doc__)
