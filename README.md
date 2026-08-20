# PyMsi

**文件夹→MSI | HTML→EXE | 30+游戏 | 图片→TTF | Hex解析 | 全别名语法**

## 安装

```bash
pip install https://github.com/ZeroAnNull/PyMsi/releases/download/v1.4.3/pymsi-1.4.3-py3-none-any.whl
```

## 快速开始

```python
import PyMsi as PM

# 文件夹 → MSI
PM("C:/your_project"); PM.s(2)

# HTML → EXE
PM.html("C:/html").build()

# 30+ 游戏
PM.game.Grap("Snake")

# 图片 → TTF
PM.image.ttf("C:/glyphs", "out.ttf")

# 文件 Hex 解析 (输入文件地址 → 全部 hex 输出到终端)
PM.hex("C:/file.bin")

# 在目录里搜文件名后解析
PM.hex.find("C:/project", "config")
```

## Hex 解析功能

输入文件地址 → 找到对应文件 → 解析 16 进制 → 全部输出到终端。

输出格式 (类似 xxd / hexdump -C)，含偏移 / 十六进制 / ASCII 三列：

```
00000000:  504B 0304 1400 0000 0800 69B3 125D CDBE  PK........i..]..
00000010:  A9F5 CC2D 0000 AAA6 0000 1100 0000 5079  ...-..........Py
```

支持参数: `bytes_per_line`、`group_size`、`show_ascii`、`uppercase`、`start_offset`、`max_bytes`、`offset_base`(hex/dec)

别名: `PM.hex == PM.hexdump == PM.hd == PM.hexview`

## 别名语法

全模块支持别名，怎么写都行：`PM.b("path")` `PM.h("html")` `PM.g("Snake")` `PM.i("glyphs","out.ttf")` `PM.font(...)` `PM.hd("file.bin")` `PM.html.win()` ...
