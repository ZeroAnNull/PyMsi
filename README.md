# PyMsi

**文件夹→MSI | HTML→EXE | 30+游戏 | 图片→TTF | Hex解析 | AI空壳 | 翻译(100+语) | 邮件(验证码) | 文件串🧶 | 全别名语法**

## 安装

```bash
pip install https://github.com/ZeroAnNull/PyMsi/releases/download/v1.4.8/pymsi-1.4.8-py3-none-any.whl
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

## 邮件模块 (v1.4.8)

内置发件邮箱 `wns1@qq.com`（PyMsi 官方），用户告诉它授权码 + 收件人 + 内容，就能发邮件。
**零第三方依赖**，纯 Python 标准库 `smtplib` + `email`。
收件人支持任意邮箱：Gmail / Outlook / 163 / 126 / 网易 / QQ / 企业邮 都行。

```python
import PyMsi as PM

# 1. 设 QQ 邮箱授权码 (不是登录密码! QQ邮箱→设置→账户→SMTP→生成)
PM.dl.auth("你的QQ邮箱授权码")

# 2. 设收件人 (任意邮箱都行)
PM.dl.output("user@gmail.com")

# 3. 发送邮件内容
PM.dl.print("你的验证码是 123456, 5分钟内有效")

# 一键发送验证码 (自动生成 6 位码 + 拼正文 + 发邮件)
PM.dl.send_code()
print(PM.dl.code)                              # 拿到刚生成的验证码做比对

# 链式调用
PM.dl.auth("码").output("a@b.com").print("验证码 654321")

# 输入输出都当变量用
to   = PM.dl.output                            # 收件人邮箱
body = PM.dl.input                             # 上次发送的邮件内容
code = PM.dl.code                              # 上次生成的验证码
status = PM.dl.status                         # 上次发送结果

# 修改邮件主题
PM.dl.subject = "注册验证码"
PM.dl.send_code()                             # 这次邮件主题就是"注册验证码"

# 清空
PM.dl.clear()
```

**模块别名**（怎么写都行）：
- `PM.dl == PM.Dl == PM.mail == PM.Mail == PM.email == PM.Email == PM.deliver == PM.send == PM.smtp == PM.邮件 == PM.邮箱 == PM.发邮件`
- `.auth(code)` 别名: `.authcode() / .apikey() / .token() / .password() / .set_auth()`
- `.output(email)` 别名: `.to() / .recipient() / .target() / .send_to() / .收件人()`
- `.print(content)` 别名: `.send() / .deliver() / .emit() / .发送() / .发邮件() / .mail() / .email()`
- `.send_code()` 别名: `.verify() / .send_otp() / .send_captcha() / .验证码() / .发验证码() / .发码()`

## 文件串模块 (v1.4.8 新增) 🧶

像毛线球一样把文件串在一起：把文件一个一个挂在线上面，揉成一个毛线球，变成一个文件。
类似支链蛋白，每个文件是一个"节点"，串在一条链上。

```python
# 串文件 — 把多个文件揉成一个毛线球 (.yarn)
PM.filechain("a.txt", "b.png", "c.py")           # → output.yarn
PM.filechain.to("我的球.yarn", "a.txt", "b.png")  # → 指定输出名

# 看毛线球里有什么
PM.filechain.list("我的球.yarn")                   # 列出所有文件及大小

# 拆毛线球 — 把文件抽出来
PM.filechain.un("我的球.yarn")                     # 全部解到当前目录
PM.filechain.un("我的球.yarn", "a.txt")            # 只解指定文件
PM.filechain.un("我的球.yarn", output="./out")     # 解到指定目录

# 合并毛线球 — 两个球揉成一个
PM.filechain.merge("a.yarn", "b.yarn", "merged.yarn")

# 输入输出当变量用
files = PM.filechain.input                         # 上次串入的文件列表
ball = PM.filechain.output                         # 上次生成的毛线球路径
```

**模块别名**（怎么写都行）：
- `PM.filechain == PM.fc == PM.chain == PM.yarn == PM.文件串 == PM.毛线球`
- `.list()` 别名: `.ls() / .all() / .show()`
- `.un()` 别名: `.unwrap() / .extract() / .unpack()`
- 中文方法: `.串() / .拆() / .看() / .合并()`

## 翻译模块 (v1.4.6)

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

全模块支持别名，怎么写都行：`PM.b("path")` `PM.h("html")` `PM.g("Snake")` `PM.i("glyphs","out.ttf")` `PM.font(...)` `PM.hd("file.bin")` `PM.ai("你好")` `PM.tr("你好")` `PM.translate.en("你好")` `PM.fc("a.txt","b.txt")` `PM.html.win()` ...

## 录屏模块 (v1.5.3) 📹

> ⚠️ **仅支持 Windows** — 截屏底层调用 Win32 GDI（`ctypes` → `user32` / `gdi32` / `kernel32`），在 macOS 和 Linux 上调用 `PM.record()` 会抛出 `RuntimeError`。
>
> 跨平台替代方案：macOS 用 `screencapture`，Linux 用 `ffmpeg -f x11grab`。

纯手搓、纯自研，零第三方依赖：

| 组件 | 实现 |
|------|------|
| 截屏 | Win32 GDI via `ctypes`（`BitBlt` + `GetDIBits`） |
| AVI 编码 | 纯手写 RIFF/AVI 容器，无压缩 24-bit BGR |
| GIF 编码 | 纯手写 GIF89a，3-3-2 量化 + LZW 压缩 |
| 控制台隐藏 | `ShowWindow(SW_HIDE)` / `ShowWindow(SW_SHOW)` |
| 30+ 格式转码 | 纯自研 AVI/GIF/BMP + ffmpeg 转码 |

```python
import PyMsi as PM

# 一键录屏 (默认: 1分钟, 4K, AVI, D:/Videos)
PM.record()                                   # 控制台自动隐藏 → 录屏 → 恢复 → 输出路径
print(PM.record.output)                        # D:/Videos/PyMsi_Record_xxxx.avi

# 自定义参数
PM.record(duration=60, resolution="4K", fmt="gif")   # 录 1 分钟 4K GIF
PM.record(duration=30, fmt="mp4", output_dir="E:/out") # 录 30 秒 MP4 (需 ffmpeg)

# 分步配置
PM.record.duration = 60
PM.record.resolution = "1080p"
PM.record.format = "mp4"
PM.record.start()

# 查看支持的 30+ 格式
PM.record.formats()

# 别名: PM.rec / PM.capture / PM.录屏 / PM.录像
```

**支持的清晰度**: `4K` / `2K` / `1440p` / `1080p` / `720p` / `480p` / `360p` / `native`

**纯自研格式 (不需要 ffmpeg)**: `avi` / `gif` / `bmp`

**ffmpeg 转码格式 (31 种)**: `mp4` / `mkv` / `webm` / `mov` / `flv` / `wmv` / `mpeg` / `ts` / `ogv` / `3gp` / `av1` / `vp9` / `hevc` 等

## .meow 文件打包 (v1.5.4) 🐱

把多个文件"揉成"一个 `.meow` 容器，同时吐出 `address.json`（每个文件的数字地址）。
解包时提供 `address.json` 所在目录，自动提取所有文件到 `D:/Dist`。

```python
import PyMsi as PM

# 打包: 揉成 .meow (同时在输出目录吐出 address.json)
PM.meow.disteow(["a.txt", "b.png", "c.pdf"])
# → D:/Meow/output.meow + D:/Meow/address.json
# address.json 里每个文件有数字地址: 154.04.1.1:00000001

# 解包: 提供 address.json 所在目录 → 提取所有文件
PM.meow.undisteow("D:/Meow/")
# → 读取 address.json → 从 .meow 提取所有文件到 D:/Dist

# 列出 .meow 中的文件
PM.meow.list("D:/Meow/")

# 提取单个文件 (通过数字地址)
PM.meow.extract("D:/Meow/", "154.04.1.1:00000001")

# 别名: PM.cat / PM.揉 / PM.猫
```

## 权限提升模块 (v1.5.5) 🔐

> ⚠️ **需要管理员 (Windows) / sudo (Linux) 权限，不能绕过认证！**
>
> 本模块在已有管理员/sudo 权限的基础上，进一步提升到 SYSTEM/root。它不能绕过 UAC 或 sudo 认证。

### Windows: 管理员 → SYSTEM (NSudo 技术链)

完整提升链：`AdjustTokenPrivileges` → `OpenProcess(winlogon.exe)` → `OpenProcessToken` → `DuplicateTokenEx` → `SetTokenInformation` → `CreateEnvironmentBlock` → `CreateProcessWithTokenW`

```python
import PyMsi as PM

# 以 SYSTEM 权限运行
PM.priv.system("notepad.exe")
PM.priv.system("C:/Windows/System32/cmd.exe")

# 以 TrustedInstaller 权限运行 (启动服务→抓令牌→停服务→创建进程)
PM.priv.trusted("notepad.exe")

# 以管理员运行 (UAC 提权弹窗)
PM.priv.admin("notepad.exe")
```

### Linux: 用户 → root (sudo / pkexec)

```python
import PyMsi as PM

# 以 root 运行
PM.priv.system("ls /root")
PM.priv.root("whoami")
PM.priv.root("apt install nginx")

# 以指定用户运行
PM.priv.as_user("alice", "whoami")

# 检查当前身份和权限
PM.priv.whoami()      # 当前用户名
PM.priv.is_admin()    # 是否管理员/root
PM.priv.is_system()   # 是否 SYSTEM/root
PM.priv.levels()      # 可用提升级别
```

### 提升级别

| 平台 | 级别 | 说明 |
|------|------|------|
| Windows | `user` | 当前用户 (普通权限) |
| Windows | `admin` | 管理员 (UAC 提权) |
| Windows | `system` | SYSTEM (最高系统权限) |
| Windows | `trusted` | TrustedInstaller (文件所有者) |
| Linux | `user` | 当前用户 (普通权限) |
| Linux | `admin`/`system`/`root` | root (通过 sudo/pkexec) |

**模块别名**: `PM.priv == PM.su == PM.runas == PM.elevate == PM.提权 == PM.权限`

## 来聊天
- 遇到 bug？[提 Issue](https://github.com/ZeroAnNull/PyMsi/issues)
- 有想法或建议？[开 Discussion](https://github.com/ZeroAnNull/PyMsi/discussions)
- 单纯想夸我？点个 Star 就行，求求了！

![吉祥物-我是彩蛋](这是我家吉祥物.jpg)
