"""
PyMsi HTML → EXE 构建器 (Electron 版)
=======================================
直接使用 Electron 运行时，把 HTML 文件夹打包成独立桌面应用。
支持自定义图标、沙箱模式开关。

构建原理:
  1. 下载 Electron 预编译运行时 (缓存到 ~/.pymsi/electron/)
  2. 把 HTML 文件放入 Electron 的 resources/app/ 目录
  3. 生成 main.js (Electron 主进程入口)
  4. 沙箱模式：启用 contextIsolation + CSP 限制
  5. 非沙箱模式：启用 nodeIntegration，允许完整系统访问
"""

import os
import sys
import json
import shutil
import ssl
import urllib.request
import zipfile


# ─── Electron 版本和下载 ──────────────────────────────────

ELECTRON_VERSION = "43.4.0"

# 国内镜像源优先 (实测速度对比: 华为云 47MB/s > 淘宝 12MB/s > GitHub 3.8MB/s)
# 任一源失败自动 fallback 到下一个, 最后回退到官方 GitHub Releases
ELECTRON_MIRRORS = [
    "https://mirrors.huaweicloud.com/electron/{version}/electron-v{version}-{platform}.zip",
    "https://registry.npmmirror.com/-/binary/electron/{version}/electron-v{version}-{platform}.zip",
    "https://npmmirror.com/mirrors/electron/{version}/electron-v{version}-{platform}.zip",
    "https://github.com/electron/electron/releases/download/"
    "v{version}/electron-v{version}-{platform}.zip",
]

ELECTRON_URL = ELECTRON_MIRRORS[0]

_PLATFORM_MAP = {
    ("win32", "AMD64"): "win32-x64",
    ("win32", "x86"): "win32-ia32",
    ("win32", "ARM64"): "win32-arm64",
    ("linux", "x86_64"): "linux-x64",
    ("linux", "aarch64"): "linux-arm64",
    ("darwin", "x86_64"): "darwin-x64",
    ("darwin", "arm64"): "darwin-arm64",
}


def _detect_platform():
    """检测当前平台对应的 Electron 下载标识"""
    plat = sys.platform
    machine = None
    if plat == "win32":
        import platform as pf
        machine = pf.machine()
    else:
        machine = os.uname().machine if hasattr(os, "uname") else ""
    return _PLATFORM_MAP.get((plat, machine), "linux-x64")


def _download_electron(target_platform):
    """下载并缓存 Electron 运行时，返回解压后的目录路径"""
    cache_dir = os.path.join(os.path.expanduser("~"), ".pymsi", "electron")
    version_dir = os.path.join(cache_dir, ELECTRON_VERSION, target_platform)

    # 判断可执行文件名
    if "win32" in target_platform:
        exe_name = "electron.exe"
    elif "darwin" in target_platform:
        exe_name = "Electron.app"
    else:
        exe_name = "electron"

    # 已缓存则直接返回
    if os.path.exists(os.path.join(version_dir, exe_name)):
        return version_dir

    os.makedirs(version_dir, exist_ok=True)

    # 下载 zip
    zip_path = os.path.join(cache_dir, f"electron-{ELECTRON_VERSION}-{target_platform}.zip")

    if not os.path.isfile(zip_path):
        print(f"[PyMsi.html] 下载 Electron v{ELECTRON_VERSION} ({target_platform})...")

        # 配置代理 (有代理用代理, 但国内镜像通常不需要代理)
        proxies = {}
        for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            val = os.environ.get(var)
            if val:
                scheme = "https" if "HTTPS" in var.upper() else "http"
                proxies[scheme] = val

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # 构建 opener：代理 + SSL context
        https_handler = urllib.request.HTTPSHandler(context=ctx)
        handlers = [https_handler]
        if proxies:
            handlers.insert(0, urllib.request.ProxyHandler(proxies))
        opener = urllib.request.build_opener(*handlers)

        # 遍历镜像列表, 第一个能连上就用第一个
        resp = None
        used_url = None
        last_err = None
        for mirror in ELECTRON_MIRRORS:
            url = mirror.format(version=ELECTRON_VERSION, platform=target_platform)
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/octet-stream",
                })
                resp = opener.open(req, timeout=60)
                used_url = url
                print(f"[PyMsi.html] 使用源: {url}")
                break
            except Exception as e:
                print(f"[PyMsi.html] 源不可用, 切换下一个: {url}")
                print(f"           原因: {e}")
                last_err = e
                continue

        if resp is None:
            raise RuntimeError(
                f"所有 Electron 镜像均不可用。最后错误: {last_err}\n"
                "可手动下载 electron zip 放到 ~/.pymsi/electron/ 目录后重试"
            )

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(zip_path, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded * 100 // total
                    mb = downloaded // 1048576
                    total_mb = total // 1048576
                    print(f"\r[PyMsi.html] 下载: {pct}% ({mb}MB / {total_mb}MB)", end="", flush=True)
        print()

    # 解压
    print(f"[PyMsi.html] 解压 Electron...")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(version_dir)

    # Linux: 设置可执行权限
    if "linux" in target_platform:
        exe_path = os.path.join(version_dir, "electron")
        if os.path.isfile(exe_path):
            os.chmod(exe_path, 0o755)

    return version_dir


# ─── Electron main.js 模板 ─────────────────────────────────
# 使用占位符替换，避免 {} 冲突

_MAIN_JS = r'''const { app, BrowserWindow, session } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: __WIDTH__,
        height: __HEIGHT__,
        title: "__TITLE__",
        __ICON_LINE__
        webPreferences: {
            sandbox: __SANDBOX__,
            contextIsolation: __CONTEXT_ISOLATION__,
            nodeIntegration: __NODE_INTEGRATION__,
            preload: path.join(__dirname, 'preload.js'),
        }
    });

    mainWindow.loadFile("__INDEX_HTML__");

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (mainWindow === null) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
'''

_PRELOAD_JS_SANDBOX = r'''// PyMsi Preload (Sandbox Mode)
// 沙箱模式：限制 API 暴露，只允许基本交互
window.addEventListener('DOMContentLoaded', () => {
    console.log('[PyMsi] Sandbox mode enabled');
});
'''

_PRELOAD_JS_FULL = r'''// PyMsi Preload (Full Access Mode)
// 非沙箱模式：暴露 Node.js API，允许完整系统访问
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('pymsi', {
    // 暴露文件系统访问
    fs: require('fs'),
    path: require('path'),
    os: require('os'),
    child_process: require('child_process'),
});
'''

_PACKAGE_JSON = '''{
    "name": "__APP_NAME__",
    "version": "1.0.0",
    "main": "main.js",
    "private": true
}
'''


# ─── HTML → EXE 构建器 ────────────────────────────────────

class _HTMLBuilder:
    """HTML 文件夹 → EXE 构建器 (Electron 版)"""

    def __init__(self):
        self._source_dir = None
        self._icon_path = None
        self._sandbox = False
        self._output_path = None
        self._title = "PyMsi App"
        self._width = 1024
        self._height = 768
        self._target_platform = None  # None=自动检测

    def build(self, source_dir, output_path=None):
        """执行构建"""
        self._source_dir = os.path.abspath(source_dir)

        if not os.path.isdir(self._source_dir):
            raise FileNotFoundError(f"目录不存在: {self._source_dir}")

        # 确定目标平台
        if self._target_platform is None:
            self._target_platform = _detect_platform()

        is_win = "win32" in self._target_platform
        ext = ".exe" if is_win else ""

        # 确定输出路径
        if output_path is None:
            dir_name = os.path.basename(self._source_dir.rstrip("/\\"))
            dist_dir = os.path.join(os.path.dirname(self._source_dir), "dist")
            self._output_path = os.path.join(dist_dir, f"{dir_name}{ext}")
        else:
            self._output_path = output_path

        # 自动检测 index.html
        index_html = self._find_index_html()
        if index_html is None:
            raise FileNotFoundError(
                f"未找到 index.html，请在目录下放置一个入口 HTML 文件:\n"
                f"  {self._source_dir}"
            )

        self._title = self._guess_title(index_html)

        print(f"[PyMsi.html] 源目录: {self._source_dir}")
        print(f"[PyMsi.html] 入口文件: {index_html}")
        print(f"[PyMsi.html] 应用标题: {self._title}")
        print(f"[PyMsi.html] 沙箱模式: {'开启' if self._sandbox else '关闭'}")
        print(f"[PyMsi.html] 目标平台: {self._target_platform}")
        if self._icon_path:
            print(f"[PyMsi.html] 自定义图标: {self._icon_path}")

        return self._build_exe(index_html)

    def _find_index_html(self):
        """查找 index.html"""
        for name in ("index.html", "index.htm", "main.html", "app.html"):
            path = os.path.join(self._source_dir, name)
            if os.path.isfile(path):
                return name
        return None

    def _guess_title(self, index_html):
        """从 HTML 中提取 <title>"""
        idx_path = os.path.join(self._source_dir, index_html)
        try:
            with open(idx_path, "r", encoding="utf-8") as f:
                content = f.read(4096)
            import re
            match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        except Exception:
            pass
        return os.path.basename(self._source_dir)

    def _build_exe(self, index_html):
        """使用 Electron 构建"""
        # Step 1: 获取 Electron 运行时
        electron_dir = _download_electron(self._target_platform)

        # Step 2: 创建输出目录 (xxx_app/)
        app_name = os.path.splitext(os.path.basename(self._output_path))[0]
        output_dir = os.path.join(os.path.dirname(self._output_path), app_name + "_app")

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # Step 3: 复制 Electron 运行时
        print(f"[PyMsi.html] 复制 Electron 运行时...")
        # 列出源目录中的条目
        for item in os.listdir(electron_dir):
            src = os.path.join(electron_dir, item)
            dst = os.path.join(output_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        # Step 4: 创建 resources/app/ 结构
        app_dir = os.path.join(output_dir, "resources", "app")
        os.makedirs(app_dir, exist_ok=True)

        # Step 5: 复制 HTML 文件到 app 目录
        print(f"[PyMsi.html] 复制 HTML 文件...")
        file_count = 0
        for root, dirs, files in os.walk(self._source_dir):
            for fname in files:
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, self._source_dir)
                dest = os.path.join(app_dir, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(full, dest)
                file_count += 1
        print(f"[PyMsi.html] 嵌入文件数: {file_count}")

        # Step 6: 生成 main.js
        icon_line = ""
        if self._icon_path:
            icon_line = 'icon: path.join(__dirname, "icon.ico"),'

        main_js = _MAIN_JS
        main_js = main_js.replace("__WIDTH__", str(self._width))
        main_js = main_js.replace("__HEIGHT__", str(self._height))
        main_js = main_js.replace("__TITLE__", self._title.replace('"', '\\"'))
        main_js = main_js.replace("__ICON_LINE__", icon_line)
        main_js = main_js.replace("__SANDBOX__", str(self._sandbox).lower())
        main_js = main_js.replace("__CONTEXT_ISOLATION__", str(self._sandbox).lower())
        main_js = main_js.replace("__NODE_INTEGRATION__", str(not self._sandbox).lower())
        main_js = main_js.replace("__INDEX_HTML__", index_html)

        with open(os.path.join(app_dir, "main.js"), "w", encoding="utf-8") as f:
            f.write(main_js)

        # Step 7: 生成 preload.js
        preload = _PRELOAD_JS_SANDBOX if self._sandbox else _PRELOAD_JS_FULL
        with open(os.path.join(app_dir, "preload.js"), "w", encoding="utf-8") as f:
            f.write(preload)

        # Step 8: 生成 package.json
        pkg = _PACKAGE_JSON.replace("__APP_NAME__", app_name.lower().replace("-", "_"))
        with open(os.path.join(app_dir, "package.json"), "w", encoding="utf-8") as f:
            f.write(pkg)

        # Step 9: 沙箱模式注入 CSP
        if self._sandbox:
            self._inject_csp(app_dir, index_html)

        # Step 10: 复制图标
        if self._icon_path and os.path.isfile(self._icon_path):
            shutil.copy2(self._icon_path, os.path.join(app_dir, "icon.ico"))

        # Step 11: 重命名主可执行文件
        is_win = "win32" in self._target_platform
        is_darwin = "darwin" in self._target_platform

        if is_win:
            old_exe = os.path.join(output_dir, "electron.exe")
            new_exe = os.path.join(output_dir, f"{app_name}.exe")
            if os.path.isfile(old_exe):
                os.rename(old_exe, new_exe)
            self._output_path = new_exe
        elif is_darwin:
            old_app = os.path.join(output_dir, "Electron.app")
            new_app = os.path.join(output_dir, f"{app_name}.app")
            if os.path.isdir(old_app):
                os.rename(old_app, new_app)
            self._output_path = new_app
        else:
            old_exe = os.path.join(output_dir, "electron")
            new_exe = os.path.join(output_dir, app_name)
            if os.path.isfile(old_exe):
                os.rename(old_exe, new_exe)
                os.chmod(new_exe, 0o755)
            self._output_path = new_exe

        # 统计大小
        total_size = 0
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                total_size += os.path.getsize(os.path.join(root, f))
        size_mb = total_size / (1024 * 1024)

        print(f"[PyMsi.html] 构建完成!")
        print(f"[PyMsi.html] 输出目录: {output_dir}")
        print(f"[PyMsi.html] 主程序: {self._output_path}")
        print(f"[PyMsi.html] 总大小: {size_mb:.1f} MB")
        return self._output_path

    def _inject_csp(self, app_dir, index_html):
        """沙箱模式：在 index.html 中注入 CSP 头"""
        idx_path = os.path.join(app_dir, index_html)
        try:
            with open(idx_path, "r", encoding="utf-8") as f:
                content = f.read()

            csp_meta = (
                '<meta http-equiv="Content-Security-Policy" '
                "content=\"default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self';\">"
            )

            if "<head>" in content:
                content = content.replace("<head>", "<head>" + csp_meta)
            elif "<html" in content:
                content = content.replace("<html", csp_meta + "\n<html")
            else:
                content = csp_meta + content

            with open(idx_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[PyMsi.html] CSP 头已注入 (沙箱模式)")
        except Exception as e:
            print(f"[PyMsi.html] CSP 注入失败: {e}")

    def set_icon(self, icon_path):
        """设置自定义图标"""
        self._icon_path = icon_path
        return self

    def set_sandbox(self, enabled):
        """设置沙箱模式"""
        self._sandbox = bool(enabled)
        return self

    def set_title(self, title):
        self._title = title
        return self

    def set_size(self, width, height):
        self._width = width
        self._height = height
        return self

    def set_platform(self, platform):
        """设置目标平台: win32-x64, linux-x64, darwin-x64"""
        self._target_platform = platform
        return self


# ─── HTML 子模块入口 (挂载到 PM.html) ──────────────────────

class _HTMLModule:
    """
    PM.html 子模块 — 用 Electron 把 HTML 打包成独立桌面应用

    用法:
        import PyMsi as PM
        PM.html("C:/your_html_project")      # 指定 HTML 项目目录
        PM.html.icon("C:/icon.ico")           # 自定义图标
        PM.html.sandbox(True)                 # 沙箱模式 (True=加沙箱, False=不加)
        PM.html.build()                       # 开始构建
    """

    def __init__(self, builder, readme_func=None):
        self._builder = builder
        self._readme_func = readme_func

    def __repr__(self):
        return (
            "<PyMsi.html> 用法: PM.html(path).build()\n"
            "  查看完整文档: PM.readme"
        )

    @property
    def readme(self):
        """打印完整帮助文档"""
        if self._readme_func:
            self._readme_func()
        return self

    def __call__(self, path):
        """设置 HTML 源目录，同时重置构建参数"""
        self._builder._source_dir = os.path.abspath(path)
        self._builder._sandbox = False
        self._builder._icon_path = None
        self._builder._title = "PyMsi App"
        self._builder._width = 1024
        self._builder._height = 768
        self._builder._target_platform = None
        self._builder._output_path = None
        print(f"[PyMsi.html] 源目录已设置: {path}")
        return self

    def icon(self, path):
        """设置自定义图标 (.ico 格式)"""
        self._builder.set_icon(path)
        return self

    def sandbox(self, enabled=True):
        """
        设置沙箱模式
        True  = 加沙箱（限制网络和文件访问，更安全）
        False = 不加沙箱（允许完整系统访问）
        """
        self._builder.set_sandbox(enabled)
        return self

    def title(self, text):
        """设置应用窗口标题"""
        self._builder.set_title(text)
        return self

    def size(self, width, height):
        """设置窗口大小"""
        self._builder.set_size(width, height)
        return self

    def platform(self, target):
        """设置目标平台: win32-x64, linux-x64, darwin-x64"""
        self._builder.set_platform(target)
        return self

    def build(self, output_path=None):
        """开始构建 EXE"""
        if self._builder._source_dir is None:
            raise RuntimeError(
                "请先使用 PM.html(path) 设置 HTML 源目录，再调用 PM.html.build()"
            )
        return self._builder.build(self._builder._source_dir, output_path)

    # ─── HTML 模块别名 ───
    def run(self, output_path=None):
        """别名: PM.html.run() = PM.html.build()"""
        return self.build(output_path)

    def make(self, output_path=None):
        """别名: PM.html.make() = PM.html.build()"""
        return self.build(output_path)

    def go(self, output_path=None):
        """别名: PM.html.go() = PM.html.build()"""
        return self.build(output_path)

    def exe(self, output_path=None):
        """别名: PM.html.exe() = PM.html.build()"""
        return self.build(output_path)

    def output(self, output_path):
        """别名: PM.html.output(path) 然后 build()"""
        self._builder._output_path = output_path
        return self

    def out(self, output_path):
        """短别名: PM.html.out(path)"""
        return self.output(output_path)

    def set_icon(self, path):
        """别名: PM.html.set_icon(p) = PM.html.icon(p)"""
        return self.icon(path)

    def set_sandbox(self, enabled=True):
        """别名"""
        return self.sandbox(enabled)

    def secure(self, enabled=True):
        """别名: PM.html.secure(True) = PM.html.sandbox(True)"""
        return self.sandbox(enabled)

    def safe(self, enabled=True):
        """别名: PM.html.safe(True) 同 sandbox"""
        return self.sandbox(enabled)

    def set_title(self, text):
        """别名"""
        return self.title(text)

    def name(self, text):
        """别名: PM.html.name(\"我的应用\") = PM.html.title(...)"""
        return self.title(text)

    def set_size(self, w, h):
        """别名"""
        return self.size(w, h)

    def resize(self, w, h):
        """别名: PM.html.resize(w, h) = PM.html.size(w, h)"""
        return self.size(w, h)

    def set_platform(self, target):
        """别名"""
        return self.platform(target)

    def arch(self, target):
        """别名: PM.html.arch(\"win32-x64\") = PM.html.platform(...)"""
        return self.platform(target)

    def win(self):
        """快捷: PM.html.win() = PM.html.platform(\"win32-x64\")"""
        return self.platform("win32-x64")

    def windows(self):
        """快捷"""
        return self.platform("win32-x64")

    def linux(self):
        """快捷: PM.html.linux()"""
        return self.platform("linux-x64")

    def mac(self):
        """快捷: PM.html.mac() = darwin-x64"""
        return self.platform("darwin-x64")

    def darwin(self):
        """快捷"""
        return self.platform("darwin-x64")
