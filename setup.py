from setuptools import setup, find_packages, Extension
import sys

# 独家加密 C 扩展 (GMP 大整数)
# 跨平台编译: Linux(.so) / Windows(.pyd) / macOS(.dylib)
# 用户装 wheel 即用, 无需编译器
if sys.platform == "win32":
    # MSVC: /O2 优化, /W3 警告, 抑制不安全警告
    extra_args = ["/O2", "/W3"]
    # Windows 上 GMP 库叫 gmp (vcpkg) 或 libgmp-10
    libs = ["gmp"]
else:
    # GCC/Clang (Linux/macOS)
    extra_args = ["-O2", "-Wall"]
    libs = ["gmp"]

excl_cipher_ext = Extension(
    "PyMsi._excl_cipher",
    sources=["PyMsi/_excl_cipher.c"],
    libraries=libs,
    extra_compile_args=extra_args,
)

setup(
    name="PyMsi",
    version="1.5.0",
    description="文件夹→MSI | HTML→EXE(Electron) | 30+游戏 | 图片→TTF | Hex解析 | AI空壳 | 翻译(100+语) | 邮件 | 文件串🧶 | 🔐KeyKey加密 | 🔒独家加密(C/GMP) — 脚本式API，大量别名",
    author="PyMsi",
    packages=find_packages(),
    python_requires=">=3.7",
    ext_modules=[excl_cipher_ext],
    # 把 C 源代码也打进 wheel (完整源代码公开发布)
    package_data={"PyMsi": ["_excl_cipher.c"]},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Software Distribution",
        "License :: OSI Approved :: MIT License",
    ],
)
