from setuptools import setup, find_packages, Extension
import sys

# 独家加密 Cython 扩展
# .pyx 编译成 .so/.pyd (各平台原生, 需要 Cython + C 编译器)
# 运行时无外部依赖 (用 Python int, 不再依赖 libgmp)
try:
    from Cython.Build import cythonize
    cython_exts = cythonize(
        "PyMsi/_excl_cipher.pyx",
        compiler_directives={"language_level": "3"},
    )
except ImportError:
    # 没有 Cython 就不编 C 扩展 (走纯 Python 回退)
    cython_exts = []

# 跨编译器编译选项
if sys.platform == "win32":
    extra_args = ["/O2", "/W3"]
else:
    extra_args = ["-O2", "-Wall"]

for ext in cython_exts:
    ext.extra_compile_args = extra_args

setup(
    name="PyMsi",
    version="1.5.0",
    description="文件夹→MSI | HTML→EXE(Electron) | 30+游戏 | 图片→TTF | Hex解析 | AI空壳 | 翻译(100+语) | 邮件 | 文件串🧶 | 🔐KeyKey加密 | 🔒独家加密(Cython) — 脚本式API，大量别名",
    author="PyMsi",
    packages=find_packages(),
    python_requires=">=3.7",
    ext_modules=cython_exts,
    package_data={"PyMsi": ["_excl_cipher.pyx"]},
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
        "Programming Language :: C",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Software Distribution",
        "License :: OSI Approved :: MIT License",
    ],
)
