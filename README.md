# PyMsi

**文件夹→MSI | HTML→EXE | 30+游戏 | 图片→TTF | Hex解析 | AI空壳 | 全别名语法**

## 安装

```bash
pip install https://github.com/ZeroAnNull/PyMsi/releases/download/v1.4.5/pymsi-1.4.5-py3-none-any.whl
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

# AI 空壳 (设 key + 官网后问问题, 输出自动 print)
PM.ai.key = "sk-xxx"
PM.ai.url = "https://api.openai.com"
PM.ai.imput("你好")
```

## AI 空壳功能

本质上是个空壳: 告诉它 API Key 和 AI API 官网, 就能问 AI 问题。
输出在库里直接 print 写死, 不用自己写 print 加双引号。
**输入和输出都能当变量用**, 方便在源代码里继续处理。

```python
PM.ai.key = "sk-xxxxxxxx"                  # 1. 设 API Key
PM.ai.url = "https://api.openai.com"       # 2. 设 AI API 官网 (OpenAI 兼容接口都行)
PM.ai.imput("你好, 你是谁?")                # 3. 问问题 → 终端自动输出回答

# 输入和输出都能当变量用
q = PM.ai.input                            # 上次问的问题
a = PM.ai.output                           # AI 的回答
print(q, "->", a)

PM.ai.model = "deepseek-chat"               # 换模型
PM.ai.clear()                               # 清空对话历史 + 输入 + 输出
```

兼容 OpenAI 接口的服务都行: OpenAI / DeepSeek / Moonshot / 通义千问 / 智谱 等。

别名:
- `PM.ai == PM.AI == PM.gpt == PM.llm == PM.chatbot`
- `PM.ai.imput / ask / chat / question / send / say / talk / q` 都是同一方法
- `PM.ai.input / Input / prompt / question_text` 都是输入别名
- `PM.ai.output / Output / answer / result` 都是输出别名

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

全模块支持别名，怎么写都行：`PM.b("path")` `PM.h("html")` `PM.g("Snake")` `PM.i("glyphs","out.ttf")` `PM.font(...)` `PM.hd("file.bin")` `PM.ai("你好")` `PM.html.win()` ...
