"""PyMsi 文件串模块 — 像毛线球一样把文件串在一起

把文件一个一个挂在线上面，揉成一个毛线球，变成一个文件。
类似支链蛋白：每个文件是一个"节点"，串在一条链上。

用法:
    import PyMsi as PM

    # 串文件 — 把多个文件揉成一个毛线球
    PM.filechain("a.txt", "b.png", "c.py")           # → 生成 output.yarn
    PM.filechain.to("我的球.yarn", "a.txt", "b.png")  # → 指定输出名

    # 看毛线球里有什么
    PM.filechain.list("我的球.yarn")                   # → 列出所有文件

    # 拆毛线球 — 把文件抽出来
    PM.filechain.un("我的球.yarn")                     # → 全部解出到当前目录
    PM.filechain.un("我的球.yarn", "a.txt")            # → 只解指定文件
    PM.filechain.un("我的球.yarn", output="./out")     # → 解到指定目录

    # 合并毛线球 — 两个球揉成一个
    PM.filechain.merge("a.yarn", "b.yarn", "merged.yarn")
"""

import os
import struct
import sys

# ─── 常量 ───────────────────────────────────────────────
_MAGIC = b"PYMSIYRN"         # 8 字节魔数
_VERSION = 1                  # 格式版本
_HEADER_FMT = "<8sII"         # magic + version + file_count
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)  # 16
_INDEX_ENTRY_FMT = "<H"       # filename_len
_INDEX_ENTRY_FIXED = struct.calcsize(_INDEX_ENTRY_FMT)  # 2
_OFFSET_FMT = "<QQ"           # data_offset + data_size
_OFFSET_SIZE = struct.calcsize(_OFFSET_FMT)  # 16


# ─── 内部工具 ────────────────────────────────────────────

def _read_header(fp):
    """读取并验证文件头，返回 file_count"""
    data = fp.read(_HEADER_SIZE)
    if len(data) < _HEADER_SIZE:
        raise ValueError("文件太小，不是有效的毛线球")
    magic, version, count = struct.unpack(_HEADER_FMT, data)
    if magic != _MAGIC:
        raise ValueError(f"魔数不匹配: 不是 PyMsi 毛线球文件 (got {magic!r})")
    if version != _VERSION:
        print(f"[PyMsi.filechain] 警告: 版本 {version} (当前 {_VERSION})，尝试兼容读取")
    return count


def _read_index(fp):
    """读取索引区，返回 [(filename, data_offset, data_size), ...]"""
    count = _read_header(fp)
    entries = []
    for _ in range(count):
        # 读取文件名长度
        name_len_data = fp.read(_INDEX_ENTRY_FIXED)
        if len(name_len_data) < _INDEX_ENTRY_FIXED:
            break
        name_len = struct.unpack(_INDEX_ENTRY_FMT, name_len_data)[0]

        # 读取文件名
        filename = fp.read(name_len).decode("utf-8")

        # 读取偏移和大小
        off_data = fp.read(_OFFSET_SIZE)
        if len(off_data) < _OFFSET_SIZE:
            break
        data_offset, data_size = struct.unpack(_OFFSET_FMT, off_data)

        entries.append((filename, data_offset, data_size))
    return entries


def _write_file(fp, filename, data):
    """写入单个文件的索引条目 + 数据"""
    name_bytes = filename.encode("utf-8")
    fp.write(struct.pack(_INDEX_ENTRY_FMT, len(name_bytes)))
    fp.write(name_bytes)
    fp.write(struct.pack(_OFFSET_FMT, 0, len(data)))  # offset 稍后修正
    return len(data)


def _list_chain(chain_path):
    """列出毛线球中的所有文件"""
    with open(chain_path, "rb") as f:
        entries = _read_index(f)
    return entries


# ─── 公开模块 ────────────────────────────────────────────

class _FileChainModule:
    """
    文件串模块 — 像毛线球一样把文件串在一起

    把文件一个一个挂在线上面，揉成一个毛线球 (.yarn)，变成一个文件。
    支持串、拆、看、合并。
    """

    def __init__(self):
        self._last_input = []
        self._last_output = ""

    # ─── 属性 (输入输出当变量用) ──────────────────────────
    @property
    def input(self):
        """上次串入的文件列表"""
        return self._last_input

    @property
    def output(self):
        """上次生成的毛线球路径"""
        return self._last_output

    # ─── 核心方法 ─────────────────────────────────────────

    def __call__(self, *files):
        """
        把文件串成毛线球

        PM.filechain("a.txt", "b.png", "c.py")
        → 生成 "output.yarn"

        Args:
            *files: 要串起来的文件路径列表
        Returns:
            self (链式调用)
        """
        return self.to("output.yarn", *files)

    def to(self, output, *files):
        """
        指定输出名，把文件串成毛线球

        PM.filechain.to("我的球.yarn", "a.txt", "b.png")

        Args:
            output: 输出 .yarn 文件路径
            *files: 要串起来的文件路径列表
        Returns:
            self (链式调用)
        """
        if not files:
            print("[PyMsi.filechain] 没有文件可串，请至少给一个文件路径")
            return self

        print(f"[PyMsi.filechain] 🧶 开始串毛线球...")

        # 预先读取所有文件数据
        file_data = []
        total_size = 0
        for filepath in files:
            if not os.path.isfile(filepath):
                print(f"[PyMsi.filechain] 跳过: {filepath} (不是文件)")
                continue
            with open(filepath, "rb") as f:
                data = f.read()
            basename = os.path.basename(filepath)
            file_data.append((basename, data, filepath))
            total_size += len(data)
            print(f"  ├─ 挂上: {basename} ({len(data):,} 字节)")

        if not file_data:
            print("[PyMsi.filechain] 没有有效文件，无法串球")
            return self

        # 写入 .yarn 文件
        # 格式: Header | Index | Data
        # Index 中的 offset 是相对于数据区起始的偏移
        with open(output, "wb") as f:
            # 写入 header
            f.write(struct.pack(_HEADER_FMT, _MAGIC, _VERSION, len(file_data)))

            # 计算数据区起始偏移: header + index
            # index 大小 = 每个条目: 2 (name_len) + name_bytes + 16 (offset+size)
            index_start = f.tell()
            data_start = index_start
            for basename, data, _ in file_data:
                data_start += _INDEX_ENTRY_FIXED + len(basename.encode("utf-8")) + _OFFSET_SIZE

            # 写入索引 (offset 指向数据区位置)
            current_data_offset = data_start
            for basename, data, _ in file_data:
                name_bytes = basename.encode("utf-8")
                f.write(struct.pack(_INDEX_ENTRY_FMT, len(name_bytes)))
                f.write(name_bytes)
                f.write(struct.pack(_OFFSET_FMT, current_data_offset, len(data)))
                current_data_offset += len(data)

            # 写入数据
            for basename, data, _ in file_data:
                f.write(data)

        size_mb = total_size / (1024 * 1024)
        self._last_input = list(files)
        self._last_output = output
        print(f"  └─ 毛线球完成: {output} ({size_mb:.2f} MB, {len(file_data)} 个文件)")
        return self

    def list(self, chain_path=None):
        """
        列出毛线球里的所有文件

        PM.filechain.list("my.yarn")
        → 打印文件列表

        Args:
            chain_path: .yarn 文件路径，不传则用上次的 output
        Returns:
            self (链式调用)
        """
        path = chain_path or self._last_output
        if not path:
            print("[PyMsi.filechain] 请指定毛线球文件路径")
            return self

        if not os.path.isfile(path):
            print(f"[PyMsi.filechain] 文件不存在: {path}")
            return self

        entries = _list_chain(path)
        total = sum(size for _, _, size in entries)
        print(f"[PyMsi.filechain] 🧶 {path} 包含 {len(entries)} 个文件 ({total:,} 字节):")
        for i, (name, offset, size) in enumerate(entries, 1):
            print(f"  {i:3d}. {name}  ({size:,} 字节)")
        return self

    def un(self, chain_path, target=None, output=None):
        """
        拆毛线球 — 把文件抽出来

        PM.filechain.un("my.yarn")                    # 全部解到当前目录
        PM.filechain.un("my.yarn", "a.txt")           # 只解指定文件
        PM.filechain.un("my.yarn", output="./out")    # 解到指定目录

        Args:
            chain_path: .yarn 文件路径
            target: 要解出的文件名 (str) 或 输出目录 (传 output= 参数)
            output: 输出目录 (与 target 互斥，用这个来指定目录)
        Returns:
            self (链式调用)
        """
        if not os.path.isfile(chain_path):
            print(f"[PyMsi.filechain] 文件不存在: {chain_path}")
            return self

        # 解析参数
        extract_one = None
        out_dir = "."

        if output is not None:
            out_dir = output
        elif target is not None:
            if os.path.isdir(target) or target.endswith("/") or target.endswith("\\"):
                out_dir = target
            elif target and not os.path.sep in target:
                extract_one = target
            else:
                out_dir = os.path.dirname(target) or "."
                extract_one = os.path.basename(target)

        entries = _list_chain(chain_path)

        if extract_one:
            # 只解指定文件
            with open(chain_path, "rb") as f:
                for name, offset, size in entries:
                    if name == extract_one:
                        f.seek(offset)
                        data = f.read(size)
                        os.makedirs(out_dir, exist_ok=True)
                        out_path = os.path.join(out_dir, name)
                        with open(out_path, "wb") as wf:
                            wf.write(data)
                        print(f"[PyMsi.filechain] 抽出: {out_path} ({size:,} 字节)")
                        return self
            print(f"[PyMsi.filechain] 毛线球里没有: {extract_one}")
        else:
            # 全部解出
            os.makedirs(out_dir, exist_ok=True)
            with open(chain_path, "rb") as f:
                for name, offset, size in entries:
                    f.seek(offset)
                    data = f.read(size)
                    out_path = os.path.join(out_dir, name)
                    with open(out_path, "wb") as wf:
                        wf.write(data)
                    print(f"  ├─ 抽出: {out_path} ({size:,} 字节)")
            print(f"[PyMsi.filechain] 全部解开到: {os.path.abspath(out_dir)} ({len(entries)} 个文件)")
        return self

    def merge(self, *chain_paths):
        """
        合并多个毛线球 — 揉成一个

        PM.filechain.merge("a.yarn", "b.yarn", "merged.yarn")

        Args:
            *chain_paths: 最后一个是输出路径，前面的都是输入
        Returns:
            self (链式调用)
        """
        if len(chain_paths) < 2:
            print("[PyMsi.filechain] 至少需要 2 个参数: merge(input1, input2, ..., output)")
            return self

        *inputs, output = chain_paths

        all_entries = []
        for path in inputs:
            if not os.path.isfile(path):
                print(f"[PyMsi.filechain] 跳过不存在: {path}")
                continue
            entries = _list_chain(path)
            for name, offset, size in entries:
                with open(path, "rb") as f:
                    f.seek(offset)
                    data = f.read(size)
                all_entries.append((name, data))

        if not all_entries:
            print("[PyMsi.filechain] 没有有效文件可合并")
            return self

        # 写入合并后的毛线球
        with open(output, "wb") as f:
            f.write(struct.pack(_HEADER_FMT, _MAGIC, _VERSION, len(all_entries)))

            # 计算数据区起始
            data_start = f.tell()
            for name, data in all_entries:
                data_start += _INDEX_ENTRY_FIXED + len(name.encode("utf-8")) + _OFFSET_SIZE

            # 写索引
            current_offset = data_start
            for name, data in all_entries:
                name_bytes = name.encode("utf-8")
                f.write(struct.pack(_INDEX_ENTRY_FMT, len(name_bytes)))
                f.write(name_bytes)
                f.write(struct.pack(_OFFSET_FMT, current_offset, len(data)))
                current_offset += len(data)

            # 写数据
            for name, data in all_entries:
                f.write(data)

        total_size = sum(len(d) for _, d in all_entries)
        print(f"[PyMsi.filechain] 合并完成: {output} ({len(all_entries)} 个文件, {total_size:,} 字节)")
        self._last_output = output
        return self

    # ─── 别名 ─────────────────────────────────────────────
    def ls(self, chain_path=None):
        """别名: PM.filechain.ls() = .list()"""
        return self.list(chain_path)

    def all(self, chain_path=None):
        """别名: PM.filechain.all() = .list()"""
        return self.list(chain_path)

    def show(self, chain_path=None):
        """别名: PM.filechain.show() = .list()"""
        return self.list(chain_path)

    def unwrap(self, chain_path, target=None, output=None):
        """别名: PM.filechain.unwrap() = .un()"""
        return self.un(chain_path, target=target, output=output)

    def extract(self, chain_path, target=None, output=None):
        """别名: PM.filechain.extract() = .un()"""
        return self.un(chain_path, target=target, output=output)

    def unpack(self, chain_path, target=None, output=None):
        """别名: PM.filechain.unpack() = .un()"""
        return self.un(chain_path, target=target, output=output)

    def 串(self, *files):
        """中文: PM.filechain.串("a.txt", "b.png") = PM.filechain(...)"""
        return self.__call__(*files)

    def 拆(self, chain_path, target=None, output=None):
        """中文: PM.filechain.拆("my.yarn") = PM.filechain.un(...)"""
        return self.un(chain_path, target=target, output=output)

    def 看(self, chain_path=None):
        """中文: PM.filechain.看("my.yarn") = PM.filechain.list(...)"""
        return self.list(chain_path)

    def 合并(self, *chain_paths):
        """中文: PM.filechain.合并("a.yarn", "b.yarn", "out.yarn")"""
        return self.merge(*chain_paths)

    def help(self):
        """打印帮助"""
        print(__doc__)
        return self

    def __repr__(self):
        return "<PyMsi.filechain 🧶 文件串/毛线球>"