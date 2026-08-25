"""PyMsi 翻译模块 — 独立翻译器

默认走 LibreTranslate API (100+ 种语言), 输出自动 print 写死, 输入输出都当变量用。
零第三方依赖, 全部用 urllib + json, 捕获所有异常保证不报错。

用法:
    import PyMsi as PM

    # 最简单: 中文 → 英文 (默认)
    PM.translate("你好")

    # 指定目标语言 (英语/俄语/法语/韩语/日语...)
    PM.translate.to("你好", "en")       # → Hello
    PM.translate.to("你好", "ru")       # → Привет
    PM.translate.to("你好", "fr")       # → Bonjour
    PM.translate.to("你好", "ko")       # → 안녕하세요
    PM.translate.to("你好", "ja")       # → こんにちは
    PM.translate.to("你好", "de")       # → Hallo
    # ... 100+ 种语言都行

    # 输入输出当变量
    q = PM.translate.input             # 上次输入的原文
    a = PM.translate.output            # 翻译结果
    src = PM.translate.source_lang     # 源语言
    tgt = PM.translate.target_lang     # 目标语言

    # 换翻译服务器 (自己部署 LibreTranslate / 其他兼容 API)
    PM.translate.url = "https://translate.argosopentech.com"
"""

import json
import urllib.request
import urllib.error
import urllib.parse
import ssl


# ─── 常用语言别名表 (code ← 中文/英文/日文/韩文/俄文/法文 名字都能写) ───
_LANG_ALIASES = {
    # 中文
    "中文": "zh", "简体": "zh", "简体中文": "zh-Hans", "zh-cn": "zh-Hans", "zh-hans": "zh-Hans", "cn": "zh-Hans",
    "繁体": "zh-Hant", "繁體": "zh-Hant", "繁体中文": "zh-Hant", "zh-tw": "zh-Hant", "zh-hant": "zh-Hant", "tw": "zh-Hant", "hk": "zh-Hant",
    # 英语
    "英文": "en", "英语": "en", "美语": "en", "美语英文": "en", "english": "en", "eng": "en",
    # 俄语
    "俄语": "ru", "俄文": "ru", "russian": "ru", "русский": "ru", "ру": "ru",
    # 法语
    "法语": "fr", "法文": "fr", "french": "fr", "français": "fr", "francais": "fr",
    # 韩语
    "韩语": "ko", "韩文": "ko", "朝鲜语": "ko", "korean": "ko", "한국어": "ko",
    # 日语
    "日语": "ja", "日文": "ja", "japanese": "ja", "日本語": "ja", "jp": "ja",
    # 德语
    "德语": "de", "德文": "de", "german": "de", "deutsch": "de",
    # 西班牙语
    "西班牙语": "es", "西语": "es", "西文": "es", "spanish": "es", "español": "es", "espaniol": "es",
    # 葡萄牙语
    "葡萄牙语": "pt", "葡语": "pt", "portuguese": "pt", "português": "pt",
    "巴西葡语": "pt-BR", "巴西葡萄牙语": "pt-BR", "pt-br": "pt-BR",
    # 意大利语
    "意大利语": "it", "意语": "it", "意文": "it", "italian": "it", "italiano": "it",
    # 阿拉伯语
    "阿拉伯语": "ar", "阿语": "ar", "arabic": "ar", "العربية": "ar",
    # 印地语
    "印地语": "hi", "hindi": "hi",
    # 泰语
    "泰语": "th", "thai": "th", "ไทย": "th",
    # 越南语
    "越南语": "vi", "越语": "vi", "vietnamese": "vi", "tiếng việt": "vi",
    # 土耳其语
    "土耳其语": "tr", "turkish": "tr", "türkçe": "tr",
    # 波兰语
    "波兰语": "pl", "polish": "pl", "polski": "pl",
    # 印尼语
    "印尼语": "id", "indonesian": "id", "bahasa": "id",
    # 荷兰语
    "荷兰语": "nl", "dutch": "nl", "nederlands": "nl",
    # 瑞典语
    "瑞典语": "sv", "swedish": "sv", "svenska": "sv",
    # 挪威语
    "挪威语": "nb", "norwegian": "nb", "norsk": "nb",
    # 丹麦语
    "丹麦语": "da", "danish": "da", "dansk": "da",
    # 芬兰语
    "芬兰语": "fi", "finnish": "fi", "suomi": "fi",
    # 希腊语
    "希腊语": "el", "greek": "el", "ελληνικά": "el",
    # 捷克语
    "捷克语": "cs", "czech": "cs", "čeština": "cs",
    # 罗马尼亚语
    "罗马尼亚语": "ro", "romanian": "ro", "română": "ro",
    # 匈牙利语
    "匈牙利语": "hu", "hungarian": "hu", "magyar": "hu",
    # 乌克兰语
    "乌克兰语": "uk", "ukrainian": "uk", "українська": "uk",
    # 保加利亚语
    "保加利亚语": "bg", "bulgarian": "bg", "български": "bg",
    # 克罗地亚语
    "克罗地亚语": "hr", "croatian": "hr", "hrvatski": "hr",
    # 斯洛伐克语
    "斯洛伐克语": "sk", "slovak": "sk", "slovenčina": "sk",
    # 塞尔维亚语
    "塞尔维亚语": "sr", "serbian": "sr", "српски": "sr",
    # 斯洛文尼亚语
    "斯洛文尼亚语": "sl", "slovenian": "sl", "slovenščina": "sl",
    # 立陶宛语
    "立陶宛语": "lt", "lithuanian": "lt", "lietuvių": "lt",
    # 拉脱维亚语
    "拉脱维亚语": "lv", "latvian": "lv", "latviešu": "lv",
    # 爱沙尼亚语
    "爱沙尼亚语": "et", "estonian": "et", "eesti": "et",
    # 波斯语
    "波斯语": "fa", "persian": "fa", "فارسی": "fa",
    # 希伯来语
    "希伯来语": "he", "hebrew": "he", "עברית": "he",
    # 乌尔都语
    "乌尔都语": "ur", "urdu": "ur", "اردو": "ur",
    # 孟加拉语
    "孟加拉语": "bn", "bengali": "bn", "বাংলা": "bn",
    # 斯瓦希里语
    "斯瓦希里语": "sw", "swahili": "sw", "kiswahili": "sw",
    # 阿尔巴尼亚语
    "阿尔巴尼亚语": "sq", "albanian": "sq", "shqip": "sq",
    # 巴斯克语
    "巴斯克语": "eu", "basque": "eu", "euskara": "eu",
    # 加泰罗尼亚语
    "加泰罗尼亚语": "ca", "catalan": "ca", "català": "ca",
    # 世界语
    "世界语": "eo", "esperanto": "eo",
    # 加利西亚语
    "加利西亚语": "gl", "galician": "gl", "galego": "gl",
    # 爱尔兰语
    "爱尔兰语": "ga", "irish": "ga", "gaeilge": "ga",
    # 冰岛语
    "冰岛语": "is", "icelandic": "is", "íslenska": "is",
    # 吉尔吉斯语
    "吉尔吉斯语": "ky", "kyrgyz": "ky", "кыргызча": "ky",
    # 马来语
    "马来语": "ms", "malay": "ms", "bahasa melayu": "ms",
    # 他加禄语 / 菲律宾语
    "菲律宾语": "tl", "他加禄语": "tl", "tagalog": "tl", "filipino": "tl",
    # 阿塞拜疆语
    "阿塞拜疆语": "az", "azerbaijani": "az", "azərbaycan": "az",
    # 自动检测
    "自动": "auto", "auto": "auto", "检测": "auto", "自动检测": "auto",
}


def _resolve_lang(name):
    """把各种语言名 (中/英/日/韩/代码) 解析成 LibreTranslate code"""
    if not name:
        return "auto"
    if not isinstance(name, str):
        name = str(name)
    s = name.strip().lower()
    # 先查别名表 (区分大小写的原始输入也匹配一次)
    if name in _LANG_ALIASES:
        return _LANG_ALIASES[name]
    if s in _LANG_ALIASES:
        return _LANG_ALIASES[s]
    # 大小写不敏感查 key
    for k, v in _LANG_ALIASES.items():
        if k.lower() == s:
            return v
    # 已经是 code 了 (2-6 位字母含横杠)
    return s


class _TranslateModule:
    """
    翻译空壳模块 — 默认走 LibreTranslate (100+ 种语言)

    属性:
        url:         LibreTranslate 兼容 API 地址 (可改自建)
        timeout:     请求超时秒数 (默认 60)
        input:       上次翻译的原文 (只读, 变量用)
        output:      上次翻译结果 (只读, 变量用)
        source_lang: 上次的源语言 (只读)
        target_lang: 上次的目标语言 (只读)
    """

    # 默认公开实例池 (逐个 fallback, 防止一个挂了就崩)
    _DEFAULT_ENDPOINTS = [
        "https://libretranslate.com",
        "https://translate.argosopentech.com",
        "https://translate.fortytwo-it.com",
    ]

    def __init__(self):
        self._endpoint_idx = 0       # 当前用的是哪个默认端点
        self.url = ""                # 用户强制指定的 URL (空就走默认池 fallback)
        self.timeout = 60
        self.api_key = ""            # 自建实例如果设了 key 就填这里
        self._input = ""
        self._output = ""
        self._source_lang = "auto"
        self._target_lang = "en"

    # ─── 只读属性 (当变量用) ──────────────────────────────
    @property
    def input(self):
        """上次翻译的原文"""
        return self._input

    @property
    def output(self):
        """上次的翻译结果"""
        return self._output

    @property
    def source_lang(self):
        """上次的源语言 code"""
        return self._source_lang

    @property
    def target_lang(self):
        """上次的目标语言 code"""
        return self._target_lang

    # 输入别名
    @property
    def Input(self): return self._input
    @property
    def text(self): return self._input
    @property
    def original(self): return self._input
    @property
    def source_text(self): return self._input
    @property
    def from_text(self): return self._input

    # 输出别名
    @property
    def Output(self): return self._output
    @property
    def result(self): return self._output
    @property
    def answer(self): return self._output
    @property
    def translated(self): return self._output
    @property
    def translation(self): return self._output

    # 语言别名
    @property
    def src(self): return self._source_lang
    @property
    def tgt(self): return self._target_lang
    @property
    def lang(self): return self._target_lang
    @property
    def to_lang(self): return self._target_lang
    @property
    def from_lang(self): return self._source_lang

    # ─── 快捷目标语言属性 (直接 PM.translate.en("你好") 这样用) ───
    # 常用的几十个直接做方法
    def en(self, text="", source="auto"):
        """中文 → English (英语)"""
        return self.translate(text, target="en", source=source)
    def ru(self, text="", source="auto"):
        """→ Русский (俄语)"""
        return self.translate(text, target="ru", source=source)
    def fr(self, text="", source="auto"):
        """→ Français (法语)"""
        return self.translate(text, target="fr", source=source)
    def ko(self, text="", source="auto"):
        """→ 한국어 (韩语)"""
        return self.translate(text, target="ko", source=source)
    def ja(self, text="", source="auto"):
        """→ 日本語 (日语)"""
        return self.translate(text, target="ja", source=source)
    def de(self, text="", source="auto"):
        """→ Deutsch (德语)"""
        return self.translate(text, target="de", source=source)
    def es(self, text="", source="auto"):
        """→ Español (西语)"""
        return self.translate(text, target="es", source=source)
    def it(self, text="", source="auto"):
        """→ Italiano (意语)"""
        return self.translate(text, target="it", source=source)
    def pt(self, text="", source="auto"):
        """→ Português (葡语)"""
        return self.translate(text, target="pt", source=source)
    def zh(self, text="", source="auto"):
        """→ 中文"""
        return self.translate(text, target="zh-Hans", source=source)
    def ar(self, text="", source="auto"):
        """→ العربية (阿语)"""
        return self.translate(text, target="ar", source=source)
    def hi(self, text="", source="auto"):
        """→ हिन्दी (印地语)"""
        return self.translate(text, target="hi", source=source)
    def th(self, text="", source="auto"):
        """→ ไทย (泰语)"""
        return self.translate(text, target="th", source=source)
    def vi(self, text="", source="auto"):
        """→ Tiếng Việt (越语)"""
        return self.translate(text, target="vi", source=source)
    def tr(self, text="", source="auto"):
        """→ Türkçe (土耳其语)"""
        return self.translate(text, target="tr", source=source)
    def pl(self, text="", source="auto"):
        """→ Polski (波兰语)"""
        return self.translate(text, target="pl", source=source)
    def id(self, text="", source="auto"):
        """→ Bahasa (印尼语)"""
        return self.translate(text, target="id", source=source)
    def nl(self, text="", source="auto"):
        """→ Nederlands (荷兰语)"""
        return self.translate(text, target="nl", source=source)
    def sv(self, text="", source="auto"):
        """→ Svenska (瑞典语)"""
        return self.translate(text, target="sv", source=source)
    def uk(self, text="", source="auto"):
        """→ Українська (乌克兰语)"""
        return self.translate(text, target="uk", source=source)

    # 用中文名也能直接调
    def 英语(self, text="", source="auto"): return self.translate(text, "en", source)
    def 俄语(self, text="", source="auto"): return self.translate(text, "ru", source)
    def 法语(self, text="", source="auto"): return self.translate(text, "fr", source)
    def 韩语(self, text="", source="auto"): return self.translate(text, "ko", source)
    def 日语(self, text="", source="auto"): return self.translate(text, "ja", source)
    def 德语(self, text="", source="auto"): return self.translate(text, "de", source)
    def 西语(self, text="", source="auto"): return self.translate(text, "es", source)
    def 中文(self, text="", source="auto"): return self.translate(text, "zh-Hans", source)
    def 繁体(self, text="", source="auto"): return self.translate(text, "zh-Hant", source)

    # ─── 设 URL / Key ──────────────────────────────────
    def set_url(self, url):
        self.url = url
        return self

    def set_key(self, key):
        self.api_key = key
        return self

    def endpoint(self, url):
        self.url = url
        return self

    def apikey(self, key):
        self.api_key = key
        return self

    # ─── 核心: 翻译 ───────────────────────────────────────
    def to(self, text="", target="en", source="auto"):
        """
        翻译到指定语言 (to 是更直观的名字, 和 translate 等价)

        Args:
            text:   要翻译的文本 (空字符串会弹 input() 交互输入)
            target: 目标语言 code 或名字, 例 "en"/"英语"/"русский"
            source: 源语言 (默认 "auto" 自动检测)
        Returns:
            self (链式调用)
        """
        return self.translate(text, target, source)

    def translate(self, text="", target="en", source="auto"):
        """
        翻译文本 (输出自动 print 到终端, 不用自己加双引号)

        输入会存到 self.input, 输出存到 self.output, 都可当变量用。

        Args:
            text:   要翻译的文本 (空字符串会弹 input() 交互输入)
            target: 目标语言 code 或名字
            source: 源语言 (默认 auto)
        Returns:
            self (链式调用)
        """
        # 空文本 → 交互输入
        if text == "" or text is None:
            try:
                text = input("[PyMsi.translate] 原文: ")
            except EOFError:
                text = ""
        # 非字符串自动转 str
        if not isinstance(text, str):
            text = str(text)

        # 存输入 (无论后续是否报错, 输入都存住)
        self._input = text

        # 解析语言名
        try:
            src_code = _resolve_lang(source)
            tgt_code = _resolve_lang(target)
        except Exception:
            src_code = "auto"
            tgt_code = "en"
        self._source_lang = src_code
        self._target_lang = tgt_code

        # 空文本 → 直接返回空输出
        if not text:
            self._output = ""
            return self

        # 要试的端点列表 (用户指定了 URL 就只用它, 否则走默认池 fallback)
        if self.url and self.url.strip():
            endpoints = [self.url.strip()]
        else:
            # 从上次成功的端点开始, 再绕一圈 fallback
            endpoints = (self._DEFAULT_ENDPOINTS[self._endpoint_idx:] +
                         self._DEFAULT_ENDPOINTS[:self._endpoint_idx])

        last_error = ""
        for idx, ep in enumerate(endpoints):
            base = ep.rstrip("/")
            if "/translate" not in base:
                url = base + "/translate"
            else:
                url = base
            try:
                result = self._post(url, text, src_code, tgt_code)
                if result:
                    # 记住成功的端点, 下次直接用它
                    if not (self.url and self.url.strip()):
                        self._endpoint_idx = (self._endpoint_idx + idx) % len(self._DEFAULT_ENDPOINTS)
                    self._output = result
                    print(result)
                    return self
                else:
                    last_error = "[PyMsi.translate] 翻译返回空结果"
            except Exception as e:
                last_error = "[PyMsi.translate] " + base + " 失败: " + str(e)
                continue

        # 所有端点都挂了 → 输出错误信息 (存到 output 里, 不抛异常)
        self._output = last_error
        print(self._output)
        return self

    def _post(self, url, text, src, tgt):
        """发一次 LibreTranslate POST 请求, 成功返回译文, 失败抛异常让外层 fallback"""
        payload = {
            "q": text,
            "source": src,
            "target": tgt,
            "format": "text",
        }
        if self.api_key:
            payload["api_key"] = self.api_key
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        proxies = {}
        for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            val = __import__("os").environ.get(var)
            if val:
                scheme = "https" if "HTTPS" in var.upper() else "http"
                proxies[scheme] = val

        handlers = [urllib.request.HTTPSHandler(context=ctx)]
        if proxies:
            handlers.insert(0, urllib.request.ProxyHandler(proxies))
        opener = urllib.request.build_opener(*handlers)

        resp = opener.open(req, timeout=self.timeout)
        raw = resp.read().decode("utf-8", errors="replace")
        obj = json.loads(raw)
        if isinstance(obj, dict):
            if "translatedText" in obj:
                return obj["translatedText"]
            if "translation" in obj:
                return obj["translation"]
        return None

    # ─── 别名 (怎么写都行) ─────────────────────────────────
    def 翻译(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def trans(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def tr(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def t(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def do(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def run(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def go(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def make(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def exec(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def convert(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def 转(self, text="", target="en", source="auto"): return self.translate(text, target, source)
    def 翻(self, text="", target="en", source="auto"): return self.translate(text, target, source)

    # ─── 可直接调用: PM.translate("你好") 默认 → 英文 ───
    def __call__(self, text="", target="en", source="auto"):
        return self.translate(text, target, source)

    # ─── 清空 ────────────────────────────────────────────
    def clear(self):
        """清空输入输出缓存"""
        self._input = ""
        self._output = ""
        self._source_lang = "auto"
        self._target_lang = "en"
        return self

    def reset(self):
        return self.clear()

    # ─── 支持的语言列表 ──────────────────────────────────
    def languages(self):
        """打印支持的常用语言及别名 (不请求网络, 纯本地表)"""
        lines = [
            "常用语言 (name/code, 直接写名字或 code 都行):",
            "  中文/zh-Hans  繁体/zh-Hant  英语/en     俄语/ru     法语/fr",
            "  韩语/ko        日语/ja       德语/de     西语/es     意语/it",
            "  葡语/pt        阿语/ar       印地语/hi   泰语/th     越语/vi",
            "  土耳其语/tr    波兰语/pl     印尼语/id   荷兰语/nl   瑞典语/sv",
            "  乌克兰语/uk    希腊语/el     捷克语/cs   挪威语/nb   芬兰语/fi",
            "  丹麦语/da      越南语/vi     阿拉伯语/ar 波斯语/fa   希伯来语/he",
            "  乌尔都语/ur    孟加拉语/bn   斯瓦希里语/sw 阿尔巴尼亚语/sq",
            "  世界语/eo      爱尔兰语/ga   马来语/ms   菲律宾语/tl 阿塞拜疆语/az",
            "  罗马尼亚语/ro  匈牙利语/hu   保加利亚语/bg 克罗地亚语/hr",
            "  立陶宛语/lt    拉脱维亚语/lv  爱沙尼亚语/et 斯洛伐克语/sk",
            "  塞尔维亚语/sr  斯洛文尼亚语/sl 加利西亚语/gl 加泰罗尼亚语/ca",
            "  巴斯克语/eu    吉尔吉斯语/ky",
            "",
            "完整 100+ 语言列表见 LibreTranslate 官方, 直接写 ISO 639-1 code 也行。",
        ]
        msg = "\n".join(lines)
        print(msg)
        self._output = msg
        return self

    def list(self): return self.languages()
    def ls(self): return self.languages()
    def all(self): return self.languages()
    def help(self): return self.languages()
    def langs(self): return self.languages()

    # ─── repr ────────────────────────────────────────────
    def __repr__(self):
        status = []
        status.append("url=" + (self.url if self.url else "默认池(" + str(len(self._DEFAULT_ENDPOINTS)) + "端点)"))
        status.append("timeout=" + str(self.timeout))
        status.append("api_key=" + ("已设" if self.api_key else "未设"))
        io = "有输入输出" if (self._input or self._output) else "无输入输出"
        return ("<PyMsi.translate> " + io +
                " | 直接调用 PM.translate(\"原文\", \"en\")" +
                " | 快捷: PM.translate.en/ru/fr/ko/ja/de/es/it/zh/th/vi...(原文)" +
                " | 变量: .input .output .source_lang .target_lang")
