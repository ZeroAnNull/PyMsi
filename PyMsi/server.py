"""PyMsi.server — 极简 Web 服务器 (类 Flask/Django, 纯标准库)

用极简语法写一个完整的服务器: 启动 / 路由 / 静态文件 / 关闭

零第三方依赖, 全部用 Python 自带的 http.server + threading

用法:
    import PyMsi as PM

    # ─── 方式一: 极简链式 ───
    PM.server.port(8080).route("/").serve("<h1>Hello</h1>").start()
    # → 浏览器访问 http://localhost:8080/ 看到 Hello
    PM.server.stop()

    # ─── 方式二: 类 Flask 装饰器 ───
    @PM.server.app.route("/")
    def home():
        return "<h1>Home</h1>"

    @PM.server.app.route("/api")
    def api():
        return '{"ok": true}'

    PM.server.run(8080)   # 阻塞运行
    PM.server.stop()       # 另一线程关闭

    # ─── 方式三: 静态文件 ───
    PM.server.static("/", "./public")   # 把 ./public 目录映射到 /
    PM.server.start(8080)

    # ─── 链式 + 多路由 ───
    PM.server.port(9000) \\
        .route("/", "<h1>首页</h1>") \\
        .route("/about", "<h1>关于</h1>") \\
        .route("/api", lambda: '{"code": 200}') \\
        .start()

特性:
    - 链式 API
    - 类 Flask 装饰器 (@app.route)
    - 静态文件服务
    - 后台线程运行 (start 非阻塞, run 阻塞)
    - 优雅关闭
    - 自动 JSON 头 (返回 dict 时)
    - 支持 GET/POST/PUT/DELETE
"""

import os
import sys
import json
import threading
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs


# ═══════════════════════════════════════════════════════════════
# Flask 风格的 App 对象 (装饰器路由)
# ═══════════════════════════════════════════════════════════════

class _FlaskApp:
    """类 Flask 的应用对象, 用 @app.route 装饰器注册路由

    用法:
        @PM.server.app.route("/")
        def home():
            return "<h1>Hi</h1>"
    """

    def __init__(self, server_module):
        self._server_module = server_module
        self._routes = {}   # (method, path) -> handler

    def route(self, path, methods=None):
        """装饰器: 注册路由

        Args:
            path:    URL 路径, 如 "/" 或 "/api"
            methods: 允许的 HTTP 方法列表, 默认 ["GET"]
        """
        if methods is None:
            methods = ["GET"]
        if isinstance(methods, str):
            methods = [methods]

        def decorator(func):
            for m in methods:
                self._routes[(m.upper(), path)] = func
                # 同步到 server module 的路由表
                self._server_module._routes[(m.upper(), path)] = func
            return func
        return decorator

    def get(self, path):
        """快捷: @app.get("/")"""
        return self.route(path, ["GET"])

    def post(self, path):
        """快捷: @app.post("/")"""
        return self.route(path, ["POST"])

    def put(self, path):
        return self.route(path, ["PUT"])

    def delete(self, path):
        return self.route(path, ["DELETE"])


# ═══════════════════════════════════════════════════════════════
# 请求处理器
# ═══════════════════════════════════════════════════════════════

class _PyMsiRequestHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器, 从 server_module 拿路由表"""

    # 静默日志 (不要刷屏)
    def log_message(self, fmt, *args):
        pass

    def _handle(self, method):
        sm = self.server._pmsi_module   # _ServerModule 引用
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 找路由
        key = (method, path)
        handler = sm._routes.get(key)
        if handler is None:
            # 找 method=ANY 的通配路由
            handler = sm._routes.get(("ANY", path))
        if handler is None:
            # 静态文件
            if sm._static_dir and sm._static_prefix:
                if path.startswith(sm._static_prefix):
                    self._serve_static(path, sm)
                    return
            self._send(404, "Not Found", "text/plain")
            return

        # 调 handler
        try:
            # POST/PUT 读 body
            body = None
            if method in ("POST", "PUT", "PATCH"):
                length = int(self.headers.get("Content-Length", 0))
                if length > 0:
                    body = self.rfile.read(length).decode("utf-8", "replace")

            # 构造 request 上下文
            ctx = {
                "method": method,
                "path": path,
                "query": query,
                "headers": dict(self.headers),
                "body": body,
            }

            # handler 可以是 str (直接返回) 或 callable
            if callable(handler):
                result = handler(ctx)
            else:
                result = handler

            # 处理返回值
            if isinstance(result, dict):
                # dict → JSON
                self._send(200, json.dumps(result, ensure_ascii=False),
                           "application/json; charset=utf-8")
            elif isinstance(result, tuple) and len(result) >= 2:
                # (status, body) 或 (status, body, content_type)
                status, rbody = result[0], result[1]
                ctype = result[2] if len(result) > 2 else "text/html; charset=utf-8"
                self._send(status, rbody, ctype)
            elif result is None:
                self._send(204, "", "text/plain")
            else:
                # str → HTML
                self._send(200, str(result), "text/html; charset=utf-8")
        except Exception as e:
            self._send(500, f"Internal Server Error: {e}", "text/plain")

    def _send(self, status, body, content_type):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Server", "PyMsi/1.5.1")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, path, sm):
        """静态文件服务"""
        # 去掉 prefix, 拼到 static_dir
        rel = path[len(sm._static_prefix):]
        if rel.startswith("/"):
            rel = rel[1:]
        # 防目录穿越
        rel = rel.replace("..", "").lstrip("/")
        if not rel:
            rel = "index.html"
        filepath = os.path.join(sm._static_dir, rel)
        if not os.path.isfile(filepath):
            self._send(404, "Not Found", "text/plain")
            return
        ctype, _ = mimetypes.guess_type(filepath)
        if ctype is None:
            ctype = "application/octet-stream"
        with open(filepath, "rb") as f:
            data = f.read()
        self._send(200, data, ctype)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_DELETE(self):
        self._handle("DELETE")


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """多线程 HTTP 服务器 (每个请求一个线程, 不阻塞)"""
    daemon_threads = True
    allow_reuse_address = True   # 避免端口 TIME_WAIT 占用


# ═══════════════════════════════════════════════════════════════
# Server 模块
# ═══════════════════════════════════════════════════════════════

class _ServerModule:
    """PyMsi.server — 极简 Web 服务器"""

    def __init__(self):
        self._port = 8000
        self._host = "0.0.0.0"
        self._routes = {}               # (method, path) -> handler
        self._static_dir = None
        self._static_prefix = "/"
        self._http_server = None
        self._thread = None
        self._running = False
        self.app = _FlaskApp(self)       # Flask 风格 app 对象

    def __repr__(self):
        status = "running" if self._running else "stopped"
        return (f"<PyMsi.server [{status}] port={self._port} "
                f"routes={len(self._routes)} | server.port(8080).route('/').serve('Hi').start()>")

    # ─── 配置 (链式) ─────────────────────────────────────
    def port(self, p):
        """设置端口 (链式)"""
        self._port = int(p)
        return self

    def host(self, h):
        """设置绑定地址 (链式)"""
        self._host = h
        return self

    # ─── 路由注册 (链式) ─────────────────────────────────
    def route(self, path, methods=None):
        """链式路由: PM.server.route("/").serve("Hi")

        - route("/").serve("Hi")              → 链式 GET
        - route("/api", "POST").serve("x")    → 链式指定 method
        - route("/", methods=["GET","POST"])   → 装饰器
        """
        # methods 是字符串 → 当成单个 method, 链式
        if isinstance(methods, str):
            self._current_path = path
            self._current_methods = [methods.upper()]
            return self
        # methods 是列表 → 装饰器模式
        if isinstance(methods, list):
            def decorator(func):
                for m in methods:
                    self._routes[(m.upper(), path)] = func
                return func
            return decorator
        # methods=None → 链式默认 GET
        self._current_path = path
        self._current_methods = ["GET"]
        return self

    def get(self, path):
        self._current_path = path
        self._current_methods = ["GET"]
        return self

    def post(self, path):
        self._current_path = path
        self._current_methods = ["POST"]
        return self

    def serve(self, content):
        """给当前 route 设置静态响应内容 (链式)"""
        path = getattr(self, "_current_path", "/")
        for m in getattr(self, "_current_methods", ["GET"]):
            self._routes[(m, path)] = content
        return self

    def handler(self, func):
        """给当前 route 设置处理函数 (链式)"""
        path = getattr(self, "_current_path", "/")
        for m in getattr(self, "_current_methods", ["GET"]):
            self._routes[(m, path)] = func
        return self

    def static(self, prefix, directory):
        """静态文件服务

        Args:
            prefix:   URL 前缀, 如 "/" 或 "/static"
            directory: 本地目录
        """
        self._static_prefix = prefix.rstrip("/") or "/"
        self._static_dir = os.path.abspath(directory)
        return self

    # ─── 启动 / 停止 ─────────────────────────────────────
    def start(self, port=None):
        """后台启动服务器 (非阻塞)

        Args:
            port: 可选, 指定端口 (覆盖之前设的)
        """
        if port is not None:
            self._port = int(port)
        if self._running:
            print(f"[PyMsi.server] 已经在运行 (port {self._port})")
            return self

        self._http_server = _ThreadingHTTPServer(
            (self._host, self._port), _PyMsiRequestHandler
        )
        self._http_server._pmsi_module = self   # 让 handler 拿到路由表
        self._thread = threading.Thread(
            target=self._http_server.serve_forever,
            daemon=True
        )
        self._thread.start()
        self._running = True

        print("=" * 56)
        print(f"  PyMsi.server 启动 ✓")
        print(f"  地址: http://{self._host if self._host != '0.0.0.0' else 'localhost'}:{self._port}")
        print(f"  路由: {len(self._routes)} 个")
        for (m, p) in sorted(self._routes.keys()):
            print(f"    {m:6s} {p}")
        if self._static_dir:
            print(f"  静态: {self._static_prefix} → {self._static_dir}")
        print(f"  关闭: PM.server.stop()")
        print("=" * 56)
        return self

    def run(self, port=None):
        """前台运行 (阻塞, Ctrl+C 退出)"""
        if port is not None:
            self._port = int(port)
        if self._running:
            print(f"[PyMsi.server] 已经在运行")
            return
        self._http_server = _ThreadingHTTPServer(
            (self._host, self._port), _PyMsiRequestHandler
        )
        self._http_server._pmsi_module = self
        self._running = True
        print(f"[PyMsi.server] 运行在 http://localhost:{self._port} (Ctrl+C 退出)")
        try:
            self._http_server.serve_forever()
        except KeyboardInterrupt:
            print("\n[PyMsi.server] 收到 Ctrl+C, 关闭...")
            self.stop()

    def stop(self):
        """停止服务器"""
        if not self._running:
            print("[PyMsi.server] 未在运行")
            return self
        if self._http_server:
            self._http_server.shutdown()
            self._http_server.server_close()
        self._running = False
        print(f"[PyMsi.server] 已停止 (port {self._port})")
        return self

    # ─── 状态 ────────────────────────────────────────────
    @property
    def running(self):
        return self._running

    @property
    def info(self):
        """显示服务器信息"""
        print("=" * 56)
        print(f"  PyMsi.server")
        print("=" * 56)
        print(f"  状态   : {'运行中' if self._running else '已停止'}")
        print(f"  地址   : {self._host}:{self._port}")
        print(f"  路由数 : {len(self._routes)}")
        for (m, p) in sorted(self._routes.keys()):
            print(f"    {m:6s} {p}")
        if self._static_dir:
            print(f"  静态   : {self._static_prefix} → {self._static_dir}")
        print("-" * 56)
        print("  PM.server.port(8080).route('/').serve('Hi').start()")
        print("  PM.server.stop()")
        print("=" * 56)
        return self
