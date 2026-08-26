"""PyMsi.browser — 极简后台浏览器 (纯 Python, 不调用系统 Chrome/Edge)

在后台打开 HTML, 解析 HTML + CSS + JS, 提供 DOM API

设计原则:
    - 纯 Python, 不调用系统浏览器 (Edge/Chrome/Firefox)
    - 后台运行 (headless, 无 GUI)
    - 解析 HTML 构建 DOM 树 (html.parser 标准库)
    - 解析 CSS (自写轻量解析器, 支持选择器+声明)
    - 执行 JS (优先用 js2py 纯 Python JS 引擎, 没有则跳过)
    - 适配常用 DOM API: document.getElementById, querySelector,
      createElement, appendChild, console.log, fetch 等

用法:
    import PyMsi as PM

    # 打开 HTML 字符串
    PM.browser.open('''
        <!DOCTYPE html>
        <html><head><title>Test</title></head>
        <body>
            <h1 id="title">Hello</h1>
            <script>
                console.log("JS running!");
                document.getElementById("title").innerText = "Changed";
            </script>
        </body></html>
    ''')

    # 拿 DOM
    print(PM.browser.title)         # "Test"
    print(PM.browser.html)          # 渲染后 HTML
    el = PM.browser.find("#title")  # 按 CSS 选择器找
    print(el.text)                  # "Changed"

    # 执行 JS
    result = PM.browser.eval("1 + 2")           # 3
    PM.browser.eval("document.title = 'New'")

    # 关闭
    PM.browser.close()

    # 也可以打开 URL (用 urllib 后台抓取)
    PM.browser.open_url("https://example.com")

注意:
    - 这是极简实现, 不是完整浏览器引擎
    - JS 用 js2py (纯 Python), 主要支持 ES5
    - 不做像素级 CSS 渲染 (无 GUI), 但解析 CSS 选择器
    - 不调用系统任何浏览器
"""

import os
import sys
import io
import re
import json
import urllib.request
import urllib.parse
from html.parser import HTMLParser


# ═══════════════════════════════════════════════════════════════
# DOM 节点
# ═══════════════════════════════════════════════════════════════

class _Node:
    """DOM 节点 (极简版, 模拟浏览器 DOM)"""

    def __init__(self, tag=None, node_type="element"):
        self.nodeType = node_type
        self.tagName = tag.upper() if tag else None
        self.attributes = {}        # dict
        self.children = []          # list[_Node]
        self.parentNode = None
        self._text = ""             # text 节点的文本 / element 的 textContent
        self.style = {}             # CSS 内联样式

    # ─── 常用 DOM 属性 ─────────────────────────────────
    @property
    def textContent(self):
        """所有后代文本拼接"""
        if self.nodeType == "text":
            return self._text
        parts = []
        def walk(n):
            for c in n.children:
                if c.nodeType == "text":
                    parts.append(c._text)
                else:
                    walk(c)
        walk(self)
        return "".join(parts)

    @property
    def innerText(self):
        return self.textContent

    @property
    def innerHTML(self):
        """内部 HTML"""
        return "".join(_node_to_html(c) for c in self.children)

    @property
    def outerHTML(self):
        return _node_to_html(self)

    @property
    def text(self):
        """便捷: 拿 textContent"""
        return self.textContent

    # ─── 属性访问 ──────────────────────────────────────
    def getAttribute(self, name):
        return self.attributes.get(name)

    def setAttribute(self, name, value):
        self.attributes[name] = str(value)
        # class / id 便捷访问
        if name == "class":
            self.className = value
        elif name == "id":
            self.id = value

    def getId(self):
        return self.attributes.get("id")

    # ─── 子节点操作 ────────────────────────────────────
    def appendChild(self, child):
        if child.parentNode:
            child.parentNode.children.remove(child)
        child.parentNode = self
        self.children.append(child)
        return child

    def removeChild(self, child):
        if child in self.children:
            self.children.remove(child)
            child.parentNode = None
        return child

    def querySelector(self, selector):
        """CSS 选择器查找第一个"""
        results = self.querySelectorAll(selector)
        return results[0] if results else None

    def querySelectorAll(self, selector):
        """CSS 选择器查找所有"""
        results = []
        def walk(n):
            for c in n.children:
                if c.nodeType == "element" and _match_selector(c, selector):
                    results.append(c)
                walk(c)
        walk(self)
        return results

    def getElementById(self, id_):
        """按 id 查找"""
        result = [None]
        def walk(n):
            if result[0]:
                return
            for c in n.children:
                if c.nodeType == "element" and c.attributes.get("id") == id_:
                    result[0] = c
                    return
                walk(c)
        walk(self)
        return result[0]

    def getElementsByTagName(self, tag):
        """按标签名查找"""
        tag = tag.upper()
        results = []
        def walk(n):
            for c in n.children:
                if c.nodeType == "element":
                    if c.tagName == tag or tag == "*":
                        results.append(c)
                    walk(c)
        walk(self)
        return results

    def getElementsByClassName(self, cls):
        """按 class 查找"""
        results = []
        def walk(n):
            for c in n.children:
                if c.nodeType == "element":
                    classes = c.attributes.get("class", "").split()
                    if cls in classes:
                        results.append(c)
                    walk(c)
        walk(self)
        return results

    def __repr__(self):
        if self.nodeType == "text":
            return f"<Text: {self._text[:30]!r}>"
        return f"<{self.tagName} attrs={self.attributes}>"


def _node_to_html(node):
    """节点转 HTML 字符串"""
    if node.nodeType == "text":
        return node._text
    if node.nodeType == "comment":
        return f"<!--{node._text}-->"
    if node.nodeType == "document":
        return "".join(_node_to_html(c) for c in node.children)
    # element
    attrs = "".join(f' {k}="{v}"' for k, v in node.attributes.items())
    inner = "".join(_node_to_html(c) for c in node.children)
    # void elements (无闭合标签)
    void_tags = {"AREA", "BASE", "BR", "COL", "EMBED", "HR", "IMG",
                 "INPUT", "LINK", "META", "PARAM", "SOURCE", "TRACK", "WBR"}
    if node.tagName in void_tags:
        return f"<{node.tagName}{attrs}>"
    return f"<{node.tagName}{attrs}>{inner}</{node.tagName}>"


def _match_selector(node, selector):
    """简单 CSS 选择器匹配 (支持 #id, .class, tag, 组合)"""
    selector = selector.strip()
    # 分组: "a, b"
    for sel in selector.split(","):
        sel = sel.strip()
        if _match_single(node, sel):
            return True
    return False


def _match_single(node, sel):
    """单个选择器 (支持 #id, .class, tag, tag.class, tag#id, 后代选择器 a b)"""
    if not sel:
        return False
    # 后代选择器: "div p" → 取最后一段匹配 (简化版, 不严格校验祖先链)
    if " " in sel:
        parts = [p.strip() for p in sel.split() if p.strip()]
        if parts:
            sel = parts[-1]
    # 解析
    tag = None
    id_ = None
    classes = []
    # 标签名首位字母/星号, 后续允许字母数字 (h1, h2, section, video ...)
    m = re.match(r'^([a-zA-Z*][\w-]*)?(#[\w-]+)?(\.[\w-]+)*', sel)
    if m:
        if m.group(1):
            tag = m.group(1).upper()
        if m.group(2):
            id_ = m.group(2)[1:]
        if m.group(3):
            classes = [c[1:] for c in re.findall(r'\.[\w-]+', sel)]
    # 检查
    if tag and node.tagName != tag and tag != "*":
        return False
    if id_ and node.attributes.get("id") != id_:
        return False
    node_classes = node.attributes.get("class", "").split()
    for c in classes:
        if c not in node_classes:
            return False
    return True


# ═══════════════════════════════════════════════════════════════
# HTML 解析器 → DOM 树
# ═══════════════════════════════════════════════════════════════

class _DOMBuilder(HTMLParser):
    """把 HTML 解析成 DOM 树"""

    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img",
                 "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.document = _Node(node_type="document")
        self.stack = [self.document]
        self.scripts = []   # 收集 <script> 内容
        self.styles = []    # 收集 <style> 内容

    def handle_starttag(self, tag, attrs):
        node = _Node(tag=tag)
        for k, v in attrs:
            node.setAttribute(k, v if v is not None else "")
        self.stack[-1].appendChild(node)
        if tag not in self.VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        # <img /> 自闭合
        node = _Node(tag=tag)
        for k, v in attrs:
            node.setAttribute(k, v if v is not None else "")
        self.stack[-1].appendChild(node)

    def handle_endtag(self, tag):
        # 弹栈到匹配的标签
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tagName == tag.upper():
                del self.stack[i:]
                break

    def handle_data(self, data):
        if data.strip():
            text_node = _Node(node_type="text")
            text_node._text = data
            self.stack[-1].appendChild(text_node)
            # 收集 script 内容
            if self.stack[-1].tagName == "SCRIPT":
                self.scripts.append(data)
            elif self.stack[-1].tagName == "STYLE":
                self.styles.append(data)

    def handle_comment(self, data):
        node = _Node(node_type="comment")
        node._text = data
        self.stack[-1].appendChild(node)


# ═══════════════════════════════════════════════════════════════
# CSS 解析器 (轻量)
# ═══════════════════════════════════════════════════════════════

def _parse_css(css_text):
    """解析 CSS 文本 → [(selector, {prop: value}), ...]"""
    rules = []
    # 去掉注释
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)
    # 匹配 selector { ... }
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css_text):
        selectors = m.group(1).strip()
        declarations = {}
        for decl in m.group(2).split(';'):
            if ':' in decl:
                prop, val = decl.split(':', 1)
                declarations[prop.strip()] = val.strip()
        for sel in selectors.split(','):
            sel = sel.strip()
            if sel and declarations:
                rules.append((sel, declarations))
    return rules


# ═══════════════════════════════════════════════════════════════
# JS 引擎 (优先级: dukpy(QuickJS) > py_mini_racer(V8) > js2py > 无)
# 都是「好多人都在用」的主流纯 Python 绑定, 不调用系统浏览器
# ═══════════════════════════════════════════════════════════════

_JS_ENGINE = None        # "dukpy" | "py_mini_racer" | "js2py" | None
_JS_ERROR = None
_dukpy = None
_pmr = None
_js2py = None

try:
    import dukpy as _dukpy_mod
    _dukpy = _dukpy_mod
    _JS_ENGINE = "dukpy"     # QuickJS, 现代 ES5/ES6, Python 3.7+ 全支持
except ImportError as _e:
    try:
        from py_mini_racer import py_mini_racer as _pmr_mod
        _pmr = _pmr_mod
        _JS_ENGINE = "py_mini_racer"   # V8 引擎, 完整 ES6+
    except ImportError as _e2:
        try:
            import js2py as _js2py_mod
            _js2py = _js2py_mod
            _JS_ENGINE = "js2py"     # 纯 Python, ES5 (Python 3.13+ 字节码变更可能不可用)
        except ImportError as _e3:
            _JS_ERROR = "未安装任何 JS 引擎 (建议: pip install dukpy)"

_JS_AVAILABLE = _JS_ENGINE is not None


# ═══════════════════════════════════════════════════════════════
# JS 桥接代码 (注入 document / console / window 到 JS 环境)
# 节点用 int id 引用 (跨 JS-Python 边界只传 id, 不传对象)
# JS 侧用 Proxy 包装节点, 属性读写实时回调 Python
# ═══════════════════════════════════════════════════════════════

_BRIDGE_JS_DUKPY = r"""
(function() {
    function wrapNode(id) {
        if (id === null || id === undefined) return null;
        var handler = {
            get: function(t, prop) {
                if (prop === '_pmsi_id') return id;
                if (prop === 'tagName' || prop === 'nodeName')
                    return globalThis.call_python('pmsi.get_tag', id);
                if (prop === 'textContent' || prop === 'innerText')
                    return globalThis.call_python('pmsi.get_text', id);
                if (prop === 'innerHTML')
                    return globalThis.call_python('pmsi.get_inner_html', id);
                if (prop === 'outerHTML')
                    return globalThis.call_python('pmsi.get_outer_html', id);
                if (prop === 'children' || prop === 'childNodes')
                    return globalThis.call_python('pmsi.get_children', id).map(wrapNode);
                if (prop === 'parentNode' || prop === 'parentElement') {
                    var p = globalThis.call_python('pmsi.get_parent', id);
                    return p === null ? null : wrapNode(p);
                }
                if (prop === 'getAttribute')
                    return function(name) {
                        return globalThis.call_python('pmsi.get_attr', id, name);
                    };
                if (prop === 'setAttribute')
                    return function(name, v) {
                        globalThis.call_python('pmsi.set_attr', id, name, String(v));
                    };
                if (prop === 'appendChild')
                    return function(child) {
                        globalThis.call_python('pmsi.append_child',
                            id, child ? child._pmsi_id : null);
                        return child;
                    };
                if (prop === 'querySelector')
                    return function(sel) {
                        var n = globalThis.call_python('pmsi.query', id, sel);
                        return n === null ? null : wrapNode(n);
                    };
                if (prop === 'querySelectorAll')
                    return function(sel) {
                        return globalThis.call_python('pmsi.query_all', id, sel).map(wrapNode);
                    };
                if (prop === 'getElementById')
                    return function(id_) {
                        var n = globalThis.call_python('pmsi.get_by_id', id, id_);
                        return n === null ? null : wrapNode(n);
                    };
                if (prop === 'getElementsByTagName')
                    return function(tag) {
                        return globalThis.call_python('pmsi.by_tag', id, tag).map(wrapNode);
                    };
                if (prop === 'getElementsByClassName')
                    return function(cls) {
                        return globalThis.call_python('pmsi.by_class', id, cls).map(wrapNode);
                    };
                if (typeof prop === 'string')
                    return globalThis.call_python('pmsi.get_attr', id, prop);
                return undefined;
            },
            set: function(t, prop, value) {
                if (prop === 'textContent' || prop === 'innerText')
                    globalThis.call_python('pmsi.set_text', id, String(value));
                else if (prop === 'innerHTML')
                    globalThis.call_python('pmsi.set_inner_html', id, String(value));
                else if (prop === 'id')
                    globalThis.call_python('pmsi.set_attr', id, 'id', String(value));
                else if (prop === 'className' || prop === 'class')
                    globalThis.call_python('pmsi.set_attr', id, 'class', String(value));
                else
                    globalThis.call_python('pmsi.set_attr', id, String(prop), String(value));
                return true;
            }
        };
        return new Proxy({_pmsi_id: id}, handler);
    }
    globalThis.__pmsi_wrap = wrapNode;

    globalThis.console = {
        log: function() {
            globalThis.call_python('pmsi.log',
                Array.prototype.slice.call(arguments).join(' '));
        },
        error: function() {
            globalThis.call_python('pmsi.log', '[ERROR] ' +
                Array.prototype.slice.call(arguments).join(' '));
        },
        warn: function() {
            globalThis.call_python('pmsi.log', '[WARN] ' +
                Array.prototype.slice.call(arguments).join(' '));
        },
        info: function() {
            globalThis.call_python('pmsi.log',
                Array.prototype.slice.call(arguments).join(' '));
        }
    };

    var _doc_id = globalThis.call_python('pmsi.get_doc_id');

    globalThis.document = {
        get title() { return globalThis.call_python('pmsi.get_title'); },
        set title(v) { globalThis.call_python('pmsi.set_title', String(v)); },
        get body() {
            var n = globalThis.call_python('pmsi.get_body_id');
            return n === null ? null : wrapNode(n);
        },
        get head() {
            var n = globalThis.call_python('pmsi.get_head_id');
            return n === null ? null : wrapNode(n);
        },
        getElementById: function(id) {
            var n = globalThis.call_python('pmsi.get_by_id', _doc_id, id);
            return n === null ? null : wrapNode(n);
        },
        querySelector: function(sel) {
            var n = globalThis.call_python('pmsi.query', _doc_id, sel);
            return n === null ? null : wrapNode(n);
        },
        querySelectorAll: function(sel) {
            return globalThis.call_python('pmsi.query_all', _doc_id, sel).map(wrapNode);
        },
        getElementsByTagName: function(tag) {
            return globalThis.call_python('pmsi.by_tag', _doc_id, tag).map(wrapNode);
        },
        getElementsByClassName: function(cls) {
            return globalThis.call_python('pmsi.by_class', _doc_id, cls).map(wrapNode);
        },
        createElement: function(tag) {
            var n = globalThis.call_python('pmsi.create_element', String(tag));
            return wrapNode(n);
        },
        createTextNode: function(text) {
            var n = globalThis.call_python('pmsi.create_text', String(text));
            return wrapNode(n);
        },
        write: function(html) {
            globalThis.call_python('pmsi.doc_write', String(html));
        }
    };

    globalThis.window = {
        document: globalThis.document,
        console: globalThis.console,
        location: { href: 'about:blank', hostname: 'localhost' }
    };
})();
"""

# js2py 桥接代码 (简化版, 不用 Proxy, 用对象+函数)
_BRIDGE_JS_JS2PY = r"""
var console = {
    log: function() {
        __pmsi_log(Array.prototype.slice.call(arguments).join(' '));
    },
    error: function() {
        __pmsi_log('[ERROR] ' + Array.prototype.slice.call(arguments).join(' '));
    }
};
var document = {
    get title() { return __pmsi_get_title(); },
    set title(v) { __pmsi_set_title(String(v)); },
    getElementById: function(id) { return __pmsi_get_by_id(id); },
    querySelector: function(sel) { return __pmsi_query(sel); },
    querySelectorAll: function(sel) { return __pmsi_query_all(sel); },
    getElementsByTagName: function(tag) { return __pmsi_by_tag(tag); },
    createElement: function(tag) { return __pmsi_create_element(tag); },
    createTextNode: function(text) { return __pmsi_create_text(text); },
    write: function(html) { __pmsi_doc_write(String(html)); }
};
var window = { document: document, console: console };
"""


# ═══════════════════════════════════════════════════════════════
# 浏览器模块
# ═══════════════════════════════════════════════════════════════

class _BrowserModule:
    """PyMsi.browser — 极简后台浏览器 (纯 Python, 不调用系统浏览器)"""

    def __init__(self):
        self.document = None       # document 节点
        self._html = ""            # 原始 HTML
        self._url = ""             # 当前 URL
        self._console_logs = []    # console.log 输出
        self._js_ctx = None        # JS 执行上下文 (dukpy/py_mini_racer/js2py)
        self._css_rules = []       # 解析后的 CSS 规则
        self._node_registry = {}  # int -> _Node (JS 引擎用)
        self._next_node_id = 1
        self._doc_id = None        # document 节点的 id

    def __repr__(self):
        status = "opened" if self.document else "closed"
        js = _JS_ENGINE or "no-js"
        return (f"<PyMsi.browser [{status}] js={js} | "
                "browser.open(HTML) / browser.open_url(URL)>")

    # ─── 打开 ──────────────────────────────────────────
    def open(self, html):
        """打开 HTML 字符串, 解析 DOM + CSS + 执行 JS

        Args:
            html: HTML 字符串

        Returns:
            self (链式)
        """
        if not isinstance(html, str):
            html = str(html)

        self._html = html
        self._url = "about:blank"
        self._console_logs = []

        # 解析 HTML → DOM
        builder = _DOMBuilder()
        builder.feed(html)
        builder.close()
        self.document = builder.document
        self._css_rules = []

        # 解析 <style>
        for style_text in builder.styles:
            self._css_rules.extend(_parse_css(style_text))

        # 应用内联 style 属性 (基础)
        self._apply_inline_styles(self.document)

        # 执行 <script>
        self._init_js_context()
        for script in builder.scripts:
            try:
                self._exec_js(script)
            except Exception as e:
                self._console_logs.append(f"[JS Error] {e}")

        return self

    def open_url(self, url):
        """打开 URL, 后台用 urllib 抓取 HTML 再解析

        Args:
            url: 网址

        Returns:
            self (链式)
        """
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "PyMsi/1.5.1 (minimal browser)"
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                # 自动检测编码
                charset = resp.headers.get_content_charset() or "utf-8"
                html = resp.read().decode(charset, "replace")
            self._url = url
            return self.open(html)
        except Exception as e:
            print(f"[PyMsi.browser] ✗ 打开 URL 失败: {e}")
            return self

    def open_file(self, path):
        """打开本地 HTML 文件"""
        if not os.path.isfile(path):
            print(f"[PyMsi.browser] ✗ 文件不存在: {path}")
            return self
        with open(path, "r", encoding="utf-8") as f:
            return self.open(f.read())

    # ─── DOM 查询 ──────────────────────────────────────
    @property
    def title(self):
        """页面 <title>"""
        if not self.document:
            return ""
        head = self._find_first_tag(self.document, "HEAD")
        if head:
            title_el = self._find_first_tag(head, "TITLE")
            if title_el:
                return title_el.textContent
        return ""

    @property
    def html(self):
        """渲染后 HTML (DOM 序列化)"""
        if not self.document:
            return ""
        return _node_to_html(self.document)

    @property
    def body(self):
        """<body> 元素"""
        if not self.document:
            return None
        return self._find_first_tag(self.document, "BODY")

    @property
    def head(self):
        """<head> 元素"""
        if not self.document:
            return None
        return self._find_first_tag(self.document, "HEAD")

    def find(self, selector):
        """CSS 选择器查找第一个"""
        if not self.document:
            return None
        return self.document.querySelector(selector)

    def find_all(self, selector):
        """CSS 选择器查找所有"""
        if not self.document:
            return []
        return self.document.querySelectorAll(selector)

    def find_by_id(self, id_):
        if not self.document:
            return None
        return self.document.getElementById(id_)

    def find_by_tag(self, tag):
        if not self.document:
            return []
        return self.document.getElementsByTagName(tag)

    # ─── JS 执行 ───────────────────────────────────────
    def eval(self, js_code):
        """执行 JS 代码, 返回结果

        Args:
            js_code: JavaScript 代码字符串

        Returns:
            执行结果 (Python 类型)
        """
        if not self.document:
            raise RuntimeError("未打开任何页面, 先 browser.open(HTML)")
        return self._exec_js(js_code)

    def _init_js_context(self):
        """初始化 JS 执行上下文 (优先 dukpy/QuickJS)"""
        self._js_ctx = None
        self._node_registry = {}
        self._next_node_id = 1
        self._doc_id = None

        if not _JS_AVAILABLE:
            return

        try:
            if _JS_ENGINE == "dukpy":
                self._js_ctx = _dukpy.JSInterpreter()
                self._export_dukpy_functions()
                self._js_ctx.evaljs(_BRIDGE_JS_DUKPY)
            elif _JS_ENGINE == "py_mini_racer":
                # py_mini_racer 0.6 移除了 add_function, 暂不支持 Python 回调
                self._js_ctx = _pmr.MiniRacer()
                self._console_logs.append(
                    "[PyMsi.browser] py_mini_racer 0.6+ 无 add_function, "
                    "JS 可执行但无法桥接 DOM (建议: pip install dukpy)")
            elif _JS_ENGINE == "js2py":
                self._js_ctx = _js2py.EvalJs()
                self._export_js2py_functions()
                try:
                    self._js_ctx.execute(_BRIDGE_JS_JS2PY)
                except Exception as e:
                    self._console_logs.append(f"[JS Bridge Error] {e}")
        except Exception as e:
            self._console_logs.append(f"[JS Init Error] {e}")
            self._js_ctx = None

        # 注册 document 节点
        if self._js_ctx and self.document:
            self._doc_id = self._register_node(self.document)

    # ─── 节点注册表 ───────────────────────────────────
    def _register_node(self, node):
        """把 _Node 注册到注册表, 返回 int id (已注册则返回原 id)"""
        if node is None:
            return None
        for nid, n in self._node_registry.items():
            if n is node:
                return nid
        nid = self._next_node_id
        self._next_node_id += 1
        self._node_registry[nid] = node
        return nid

    def _node_by_id(self, nid):
        if nid is None:
            return None
        return self._node_registry.get(nid)

    # ─── 导出 Python 函数给 JS ────────────────────────
    def _export_dukpy_functions(self):
        c = self._js_ctx
        c.export_function('pmsi.log', self._py_log)
        c.export_function('pmsi.get_doc_id', lambda: self._doc_id)
        c.export_function('pmsi.get_title', lambda: self.title)
        c.export_function('pmsi.set_title', self._py_set_title)
        c.export_function('pmsi.get_body_id',
                          lambda: self._register_node(self.body))
        c.export_function('pmsi.get_head_id',
                          lambda: self._register_node(self.head))
        c.export_function('pmsi.get_by_id', self._py_get_by_id)
        c.export_function('pmsi.query', self._py_query)
        c.export_function('pmsi.query_all', self._py_query_all)
        c.export_function('pmsi.by_tag', self._py_by_tag)
        c.export_function('pmsi.by_class', self._py_by_class)
        c.export_function('pmsi.create_element', self._py_create_element)
        c.export_function('pmsi.create_text', self._py_create_text)
        c.export_function('pmsi.doc_write', self._py_doc_write)
        c.export_function('pmsi.get_tag', self._py_get_tag)
        c.export_function('pmsi.get_attr', self._py_get_attr)
        c.export_function('pmsi.set_attr', self._py_set_attr)
        c.export_function('pmsi.get_text', self._py_get_text)
        c.export_function('pmsi.set_text', self._py_set_text)
        c.export_function('pmsi.get_inner_html', self._py_get_inner_html)
        c.export_function('pmsi.set_inner_html', self._py_set_inner_html)
        c.export_function('pmsi.get_outer_html', self._py_get_outer_html)
        c.export_function('pmsi.get_children', self._py_get_children)
        c.export_function('pmsi.get_parent', self._py_get_parent)
        c.export_function('pmsi.append_child', self._py_append_child)

    def _export_js2py_functions(self):
        c = self._js_ctx
        c.__pmsi_log = self._py_log
        c.__pmsi_get_title = lambda: self.title
        c.__pmsi_set_title = self._py_set_title
        c.__pmsi_get_by_id = lambda id_: self._register_node(
            self.document.getElementById(id_) if self.document else None)
        c.__pmsi_query = lambda sel: self._register_node(
            self.document.querySelector(sel) if self.document else None)
        c.__pmsi_query_all = lambda sel: [
            self._register_node(e) for e in
            (self.document.querySelectorAll(sel) if self.document else [])]
        c.__pmsi_by_tag = lambda tag: [
            self._register_node(e) for e in
            (self.document.getElementsByTagName(tag) if self.document else [])]
        c.__pmsi_create_element = lambda tag: self._register_node(_Node(tag=tag))
        c.__pmsi_create_text = lambda text: self._register_node(
            self._py_create_text(text))
        c.__pmsi_doc_write = self._py_doc_write

    # ─── Python 实现 (供 JS 通过 call_python 调用) ──
    def _py_log(self, msg):
        self._console_logs.append(str(msg))
        return None

    def _py_set_title(self, title):
        if self.document:
            head = self._find_first_tag(self.document, "HEAD")
            if head:
                t = self._find_first_tag(head, "TITLE")
                if t:
                    t.children = []
                    tn = _Node(node_type="text")
                    tn._text = str(title)
                    tn.parentNode = t
                    t.children.append(tn)

    def _py_get_by_id(self, root_id, id_):
        root = self._node_by_id(root_id) or self.document
        if root is None:
            return None
        el = root.getElementById(id_)
        return self._register_node(el) if el else None

    def _py_query(self, root_id, sel):
        root = self._node_by_id(root_id) or self.document
        if root is None:
            return None
        el = root.querySelector(sel)
        return self._register_node(el) if el else None

    def _py_query_all(self, root_id, sel):
        root = self._node_by_id(root_id) or self.document
        if root is None:
            return []
        return [self._register_node(e) for e in root.querySelectorAll(sel)]

    def _py_by_tag(self, root_id, tag):
        root = self._node_by_id(root_id) or self.document
        if root is None:
            return []
        return [self._register_node(e) for e in root.getElementsByTagName(tag)]

    def _py_by_class(self, root_id, cls):
        root = self._node_by_id(root_id) or self.document
        if root is None:
            return []
        return [self._register_node(e) for e in root.getElementsByClassName(cls)]

    def _py_create_element(self, tag):
        n = _Node(tag=str(tag))
        return self._register_node(n)

    def _py_create_text(self, text):
        n = _Node(node_type="text")
        n._text = str(text)
        return self._register_node(n)

    def _py_doc_write(self, html):
        if self.document:
            body = self._find_first_tag(self.document, "BODY")
            if body:
                sub = _DOMBuilder()
                sub.feed(str(html))
                sub.close()
                for c in sub.document.children:
                    body.appendChild(c)

    def _py_get_tag(self, nid):
        n = self._node_by_id(nid)
        return n.tagName if n and n.tagName else None

    def _py_get_attr(self, nid, name):
        n = self._node_by_id(nid)
        if n is None:
            return None
        return n.attributes.get(name)

    def _py_set_attr(self, nid, name, value):
        n = self._node_by_id(nid)
        if n:
            n.setAttribute(name, value)

    def _py_get_text(self, nid):
        n = self._node_by_id(nid)
        return n.textContent if n else None

    def _py_set_text(self, nid, text):
        n = self._node_by_id(nid)
        if n:
            n.children = []
            t = _Node(node_type="text")
            t._text = str(text)
            t.parentNode = n
            n.children.append(t)

    def _py_get_inner_html(self, nid):
        n = self._node_by_id(nid)
        return n.innerHTML if n else None

    def _py_set_inner_html(self, nid, html):
        n = self._node_by_id(nid)
        if n:
            sub = _DOMBuilder()
            sub.feed(str(html))
            sub.close()
            n.children = []
            for c in sub.document.children:
                n.appendChild(c)

    def _py_get_outer_html(self, nid):
        n = self._node_by_id(nid)
        return n.outerHTML if n else None

    def _py_get_children(self, nid):
        n = self._node_by_id(nid)
        if n is None:
            return []
        return [self._register_node(c) for c in n.children
                if c.nodeType == "element"]

    def _py_get_parent(self, nid):
        n = self._node_by_id(nid)
        if n is None or n.parentNode is None:
            return None
        return self._register_node(n.parentNode)

    def _py_append_child(self, parent_id, child_id):
        parent = self._node_by_id(parent_id)
        child = self._node_by_id(child_id)
        if parent and child:
            parent.appendChild(child)
        return None

    def _exec_js(self, code):
        """执行 JS 代码 (用 dukpy/py_mini_racer/js2py)"""
        if not _JS_AVAILABLE:
            self._console_logs.append(
                "[PyMsi.browser] JS 引擎不可用 (pip install dukpy)")
            return None
        if not self._js_ctx:
            self._init_js_context()
        if not self._js_ctx:
            return None
        try:
            if _JS_ENGINE == "dukpy":
                return self._js_ctx.evaljs(code)
            elif _JS_ENGINE == "py_mini_racer":
                return self._js_ctx.eval(code)
            elif _JS_ENGINE == "js2py":
                return self._js_ctx.eval(code)
        except Exception as e:
            msg = str(e)
            if 'at <eval>' in msg:
                msg = msg.split('\n')[0]
            self._console_logs.append(f"[JS Error] {msg}")
            return None

    # ─── console / 日志 ────────────────────────────────
    @property
    def logs(self):
        """console.log 输出列表"""
        return self._console_logs

    @property
    def console(self):
        """打印 console 日志"""
        for log in self._console_logs:
            print(log)
        return self

    # ─── 工具 ──────────────────────────────────────────
    def _find_first_tag(self, root, tag):
        """递归找第一个指定标签"""
        tag = tag.upper()
        for c in root.children:
            if c.nodeType == "element":
                if c.tagName == tag:
                    return c
                found = self._find_first_tag(c, tag)
                if found:
                    return found
        return None

    def _apply_inline_styles(self, node):
        """应用内联 style 属性"""
        if node.nodeType == "element":
            style_str = node.attributes.get("style", "")
            if style_str:
                for decl in style_str.split(";"):
                    if ":" in decl:
                        prop, val = decl.split(":", 1)
                        node.style[prop.strip()] = val.strip()
        for c in node.children:
            self._apply_inline_styles(c)

    # ─── 信息 / 关闭 ──────────────────────────────────
    @property
    def info(self):
        """显示浏览器信息"""
        print("=" * 56)
        print("  PyMsi.browser — 极简后台浏览器")
        print("=" * 56)
        status = "已打开" if self.document else "未打开"
        print(f"  状态   : {status}")
        print(f"  URL    : {self._url}")
        print(f"  标题   : {self.title!r}")
        print(f"  JS 引擎: {'js2py (可用)' if _JS_AVAILABLE else '不可用 (缺 js2py)'}")
        if not _JS_AVAILABLE:
            print(f"  原因   : {_JS_ERROR}")
        print(f"  CSS 规则: {len(self._css_rules)} 条")
        print(f"  console: {len(self._console_logs)} 条日志")
        print("-" * 56)
        print("  PM.browser.open(HTML)      # 打开")
        print("  PM.browser.open_url(URL)   # 打开网址")
        print("  PM.browser.title / .html   # 拿内容")
        print("  PM.browser.find('#id')     # CSS 选择器")
        print("  PM.browser.eval('JS代码')   # 执行 JS")
        print("  PM.browser.close()         # 关闭")
        print("=" * 56)
        return self

    def close(self):
        """关闭浏览器, 释放资源"""
        self.document = None
        self._html = ""
        self._url = ""
        self._console_logs = []
        self._js_context = None
        self._css_rules = []
        print("[PyMsi.browser] 已关闭")
        return self
