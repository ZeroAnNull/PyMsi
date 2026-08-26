"""纯 Python 通用 wheel 打包配置 (不编 Cython 扩展)

用法:
    python3 setup_any.py bdist_wheel

生成 py3-none-any.whl, 所有平台 (Win/Mac/Linux) 都能装
- 不含编译的 .so/.pyd (避免平台依赖)
- 含 _excl_cipher.pyx 源代码 (用户可自行 cythonize 加速)
- 运行时自动用纯 Python 回退 (Python 内置 int 任意精度, 等价 GMP)

这是给 Windows/macOS 等没有 C 加速 wheel 平台的通用版。
"""
from setuptools import setup, find_packages

setup(
    name="PyMsi",
    version="1.5.2",
    description="文件夹→MSI | HTML→EXE | 30+游戏 | 图片→TTF | Hex | AI | 翻译 | 邮件 | 文件串🧶 | 🔐KeyKey | 🔒独家加密 | 🌐服务器 | 🌍浏览器 | 📦Shrink-Zeta(.㠖) — 脚本式API",
    author="PyMsi",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        # 浏览器 JS 引擎 (QuickJS 绑定, PyPI 有各平台 wheel)
        # 不可用时浏览器自动降级为只解析 HTML/CSS, 不执行 JS
        "dukpy>=0.6",
    ],
    # 不编 C 扩展 → py3-none-any (所有平台通用)
    # 独家加密运行时自动用纯 Python 回退 (Python 内置 int 任意精度)
    package_data={"PyMsi": ["_excl_cipher.pyx"]},  # 随附 Cython 源码
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Cython",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Software Distribution",
        "License :: OSI Approved :: MIT License",
    ],
)
