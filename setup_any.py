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
    version="1.5.0",
    description="文件夹→MSI | HTML→EXE(Electron) | 30+游戏 | 图片→TTF | Hex解析 | AI空壳 | 翻译(100+语) | 邮件 | 文件串🧶 | 🔐KeyKey加密 | 🔒独家加密(通用Python版) — 脚本式API，大量别名",
    author="PyMsi",
    packages=find_packages(),
    python_requires=">=3.7",
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
