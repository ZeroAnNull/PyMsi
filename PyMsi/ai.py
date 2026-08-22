"""PyMsi AI 模块 — 空壳 AI 调用器

本质上是一个空壳: 你告诉它 API Key 和 AI API 官网, 就能问 AI 问题。
所有输出在库里直接 print 写死, 不需要自己写 print 加双引号。

用法:
    import PyMsi as PM

    # 1. 告诉它 API Key
    PM.ai.key = "sk-xxxxxxxx"

    # 2. 告诉它 AI API 官网 (OpenAI 兼容的都行: OpenAI/DeepSeek/Moonshot/Qwen...)
    PM.ai.url = "https://api.openai.com"

    # 3. 问 AI 问题 (输出会自动 print 到终端, 不用自己加双引号)
    PM.ai.imput("你好, 你是谁?")

    # 4. 想再拿到原始输出文本也行
    print(PM.ai.output)
"""

import json
import urllib.request
import urllib.error
import ssl


class _AIModule:
    """
    AI 空壳模块

    属性:
        key:  API Key (先设这个)
        url:  AI API 官网 (再设这个, OpenAI 兼容接口)
        model: 模型名 (默认 gpt-3.5-turbo, 可改 deepseek-chat 等)
        output: AI 的输出 (只读, 调用 imput 后更新)
    """

    def __init__(self):
        self.key = ""
        self.url = ""
        self.model = "gpt-3.5-turbo"
        self.timeout = 60
        self._output = ""
        self._history = []

    # ─── 输出 (只读属性) ──────────────────────────────────
    @property
    def output(self):
        """AI 的输出 (调用 imput 后更新)"""
        return self._output

    @property
    def Output(self):
        """别名: AI 的输出 (大写 O)"""
        return self._output

    @property
    def answer(self):
        """别名: AI 的输出"""
        return self._output

    @property
    def result(self):
        """别名: AI 的输出"""
        return self._output

    # ─── 设 API Key 的别名 ────────────────────────────────
    def set_key(self, key):
        """设置 API Key"""
        self.key = key
        return self

    def apikey(self, key):
        """别名: 设置 API Key"""
        self.key = key
        return self

    def token(self, key):
        """别名: 设置 API Key"""
        self.key = key
        return self

    # ─── 设官网 URL 的别名 ─────────────────────────────────
    def set_url(self, url):
        """设置 AI API 官网"""
        self.url = url
        return self

    def base(self, url):
        """别名: 设置 AI API 官网"""
        self.url = url
        return self

    def endpoint(self, url):
        """别名: 设置 AI API 官网"""
        self.url = url
        return self

    def 官网(self, url):
        """别名: 设置 AI API 官网"""
        self.url = url
        return self

    # ─── 核心方法: 问 AI 问题 ──────────────────────────────
    def imput(self, question=""):
        """
        问 AI 问题 (输出会自动 print 到终端, 不用自己加双引号)

        Args:
            question: 要问的问题 (字符串; 不加引号传变量也行)
        Returns:
            self (用于链式调用)
        """
        # 没传问题就用内置 input() 交互读取
        if question == "" or question is None:
            try:
                question = input("[PyMsi.ai] 你: ")
            except EOFError:
                question = ""
        # 非字符串自动转 str (支持 imput(123) 这种不带引号的写法)
        if not isinstance(question, str):
            question = str(question)

        # 校验 key
        if not self.key:
            self._output = "[PyMsi.ai] 错误: 未设置 API Key, 请先 PM.ai.key = 'your-key'"
            print(self._output)
            return self
        # 校验 url
        if not self.url:
            self._output = "[PyMsi.ai] 错误: 未设置 AI API 官网, 请先 PM.ai.url = 'https://api.openai.com'"
            print(self._output)
            return self

        # 拼接 chat completions 端点 (OpenAI 兼容)
        base = self.url.rstrip("/")
        if "/chat/completions" in base:
            endpoint = base
        elif base.endswith("/v1"):
            endpoint = base + "/chat/completions"
        else:
            endpoint = base + "/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": self._history + [{"role": "user", "content": question}],
            "stream": False,
        }
        headers = {
            "Authorization": "Bearer " + self.key,
            "Content-Type": "application/json",
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # 配置代理 (有就用, 没有直连)
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

        try:
            resp = opener.open(req, timeout=self.timeout)
            raw = resp.read().decode("utf-8")
            result = json.loads(raw)
            answer = result["choices"][0]["message"]["content"]
            self._output = answer
            # 记录上下文, 支持多轮对话
            self._history.append({"role": "user", "content": question})
            self._history.append({"role": "assistant", "content": answer})
            # 库里直接写死 print, 不用用户自己加双引号
            print(answer)
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            self._output = "[PyMsi.ai] HTTP 错误 " + str(e.code) + ": " + body
            print(self._output)
        except urllib.error.URLError as e:
            self._output = "[PyMsi.ai] 网络错误: " + str(e.reason)
            print(self._output)
        except Exception as e:
            self._output = "[PyMsi.ai] 请求失败: " + str(e)
            print(self._output)
        return self

    # ─── imput 的别名 (怎么写都行) ─────────────────────────
    def ask(self, question=""):
        return self.imput(question)

    def chat(self, question=""):
        return self.imput(question)

    def question(self, question=""):
        return self.imput(question)

    def send(self, question=""):
        return self.imput(question)

    def say(self, question=""):
        return self.imput(question)

    def talk(self, question=""):
        return self.imput(question)

    def q(self, question=""):
        return self.imput(question)

    # ─── 可调用: PM.ai("问题") 直接问 ─────────────────────
    def __call__(self, question=""):
        return self.imput(question)

    # ─── 清空对话历史 ──────────────────────────────────────
    def clear(self):
        """清空对话历史"""
        self._history = []
        self._output = ""
        return self

    def reset(self):
        """别名: 清空对话历史"""
        return self.clear()

    def __repr__(self):
        status = []
        status.append("key=" + ("已设" if self.key else "未设"))
        status.append("url=" + ("已设" if self.url else "未设"))
        return ("<PyMsi.ai> 空壳 AI | " + ", ".join(status) +
                " | ai.key='...' ai.url='...' ai.imput('问题') | print(ai.output)")
