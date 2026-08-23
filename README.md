# PyMsi

**文件夹→MSI | HTML→EXE | 30+游戏 | 图片→TTF | Hex解析 | AI空壳 | 翻译(100+语) | 全别名语法**

## 安装

```bash
pip install https://github.com/ZeroAnNull/PyMsi/releases/download/v1.4.6/pymsi-1.4.6-py3-none-any.whl
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

# 翻译 (100+ 种语言, 默认走 LibreTranslate API, 零依赖)
PM.translate("你好")                           # 中文 → 英文 (默认)
PM.translate.en("你好")                        # → 英语
PM.translate.ru("你好")                        # → 俄语
PM.translate.fr("你好")                        # → 法语
PM.translate.ko("你好")                        # → 韩语
PM.translate.ja("你好")                        # → 日语
PM.translate.de("你好")                        # → 德语
PM.translate.中文("Hello")                     # → 中文
PM.translate.to("你好", "es")                  # → 西语 (任意 code/名字都行)
# 输入输出都能当变量用
q = PM.translate.input                         # 原文
a = PM.translate.output                        # 译文
```

## 翻译模块 (v1.4.6 新增)

默认走 LibreTranslate 公开 API（100+ 种语言），3 个公开实例自动 fallback，单个挂了不会崩。
**零第三方依赖**，urllib + json 搞定。

```python
# 快捷调用: 常用语言直接当方法名
PM.translate.en("你好")      # → Hello (英语)
PM.translate.ru("你好")      # → Привет (俄语)
PM.translate.fr("你好")      # → Bonjour (法语)
PM.translate.ko("你好")      # → 안녕하세요 (韩语)
PM.translate.ja("你好")      # → こんにちは (日语)
PM.translate.de("你好")      # → Hallo (德语)
PM.translate.es("你好")      # → Hola (西语)
PM.translate.it("你好")      # → Ciao (意语)
PM.translate.pt("你好")      # → Olá (葡语)
PM.translate.zh("Hello")     # → 你好 (中文)
PM.translate.ar("你好")      # → مرحبا (阿语)
PM.translate.hi("你好")      # → नमस्ते (印地语)
PM.translate.th("你好")      # → สวัสดี (泰语)
PM.translate.vi("你好")      # → Xin chào (越语)
PM.translate.tr("你好")      # → Merhaba (土耳其语)
PM.translate.pl("你好")      # → Cześć (波兰语)
PM.translate.id("你好")      # → Halo (印尼语)
PM.translate.nl("你好")      # → Hallo (荷兰语)
PM.translate.sv("你好")      # → Hej (瑞典语)
PM.translate.uk("你好")      # → Привіт (乌克兰语)
# ... 50+ 常用语言快捷方法, 其余 50+ 用 PM.translate.to(原文, "code")

# 用中文名也能调快捷方法
PM.translate.英语("你好")
PM.translate.俄语("你好")
PM.translate.法语("你好")
PM.translate.韩语("你好")
PM.translate.日语("你好")
PM.translate.德语("你好")
PM.translate.西语("你好")
PM.translate.中文("Hello")
PM.translate.繁体("你好")

# 通用 to() 方法 (指定 code 或语言名都可)
PM.translate.to("你好", "英语")
PM.translate.to("你好", "en")
PM.translate.to("你好", "русский")
PM.translate.to("Hello", "zh")

# 输入输出当变量用 (全部只读)
q = PM.translate.input         # 别名: Input / text / original / source_text / from_text
a = PM.translate.output        # 别名: Output / result / answer / translated / translation
s = PM.translate.source_lang   # 别名: src / from_lang
t = PM.translate.target_lang   # 别名: tgt / to_lang / lang

# 换翻译服务器 (自建 LibreTranslate / 其他兼容 API)
PM.translate.url = "https://your-libretranslate.example.com"
PM.translate.api_key = "xxxx"  # 自建实例如设了 key 就填

# 看支持的语言 (纯本地, 不请求网络)
PM.translate.languages()

# 清空缓存
PM.translate.clear()
```

**模块别名**（怎么写都行）：
- `PM.translate == PM.Translate == PM.tr == PM.trans == PM.translation == PM.translator == PM.t == PM.翻译 == PM.译`
- `.translate() / to() / 翻译() / trans() / tr() / t() / do() / run() / go() / make() / convert() / 转() / 翻()` 都是同一方法

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

全模块支持别名，怎么写都行：`PM.b("path")` `PM.h("html")` `PM.g("Snake")` `PM.i("glyphs","out.ttf")` `PM.font(...)` `PM.hd("file.bin")` `PM.ai("你好")` `PM.tr("你好")` `PM.translate.en("你好")` `PM.html.win()` ...


















##💬来聊天
- 遇到bug？[提Issue]
- 有想法或建议？[开Discussion]
- 单纯想夸我？ 点个⭐就行，求求了！
！[演示](视频.mp4)
