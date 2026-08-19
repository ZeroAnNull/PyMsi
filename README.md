# PyMsi

**文件夹→MSI | HTML→EXE | 30+游戏 | 图片→TTF | 全别名语法**

## 安装

```bash
pip install https://github.com/ZeroAnNull/PyMsi/releases/download/v1.4.1/pymsi-1.4.1-py3-none-any.whl
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
```

## 别名语法

全模块支持别名，怎么写都行：`PM.b("path")` `PM.h("html")` `PM.g("Snake")` `PM.i("glyphs","out.ttf")` `PM.font(...)` `PM.html.win()` ...
