"""
math.py — 数学教育模块 (v1.6.0 Education Plus)

专为程序员设计的数学教学工具:
  1. 代数 — 方程求解、因式分解、函数图像
  2. 几何 — 面积体积计算、三角函数
  3. 微积分 — 导数、积分入门
  4. 线性代数 — 向量、矩阵运算 (程序员必备)
  5. 概率统计 — 概率、期望、分布
  6. 数论 — 质数、最大公约数、模运算 (密码学基础)

每个概念都用编程类比来解释, 附带互动教程和计算器!

用法:
  import PyMsi as PM
  PM.math.algebra()          # 代数教程
  PM.math.geometry()         # 几何教程
  PM.math.calculus()         # 微积分教程
  PM.math.linear_algebra()   # 线性代数教程
  PM.math.probability()      # 概率统计教程
  PM.math.number_theory()    # 数论教程

  # 直接计算
  PM.math.quadratic(1, -5, 6)      # 解二次方程
  PM.math.dot_product([1,2,3], [4,5,6])  # 点积
  PM.math.gcd(48, 36)               # 最大公约数
  PM.math.factorial(5)              # 阶乘
  PM.math.matrix_mult([[1,2],[3,4]], [[5,6],[7,8]])  # 矩阵乘法
"""

import os
import json
import math


# ═══════════════════════════════════════════════════════════════
# 1. 代数教程
# ═══════════════════════════════════════════════════════════════

def generate_algebra_tutorial(output_path="math_algebra_tutorial.py"):
    """生成代数互动教程"""
    output_path = os.path.abspath(output_path)

    content = '''#!/usr/bin/env python3
"""
代数互动教程 — 由 PyMsi.math 生成
用编程思维理解代数!

用法: python math_algebra_tutorial.py
"""

import time
import sys
import math

def typewriter(text, delay=0.02):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\\n")

def section(title):
    print(f"\\n{'═' * 60}")
    print(f"  📐 {title}")
    print(f"{'═' * 60}")

def main():
    print("\\n" + "=" * 60)
    print("  📐 代数互动教程")
    print("  用编程思维理解代数!")
    print("=" * 60)

    # 1. 一次方程
    section("1. 一次方程 (ax + b = 0)")
    typewriter("一次方程就像找变量的值 — 就像debug找bug")
    typewriter("ax + b = 0 → x = -b/a")
    typewriter("\\n💡 程序员类比: 就像解一个只有一个未知数的方程,")
    typewriter("   就像函数 f(x) = ax + b 找零点")
    print()

    # 2. 二次方程
    section("2. 二次方程 (ax² + bx + c = 0)")
    typewriter("求根公式: x = (-b ± √(b²-4ac)) / 2a")
    typewriter("判别式 Δ = b² - 4ac:")
    print("   • Δ > 0: 两个不同实根 (函数与x轴两个交点)")
    print("   • Δ = 0: 一个重根 (函数与x轴相切)")
    print("   • Δ < 0: 无实根 (函数与x轴不相交)")
    typewriter("\\n💡 程序员类比: 二次函数就像抛物线,")
    typewriter("   就像程序的性能曲线, 有最小值或最大值")
    print()

    # 3. 方程组
    section("3. 二元一次方程组")
    typewriter("就像两个约束条件同时满足 —")
    typewriter("类似if-else的双重条件判断")
    typewriter("\\n例:")
    print("   2x + y = 7")
    print("   x - y = 2")
    typewriter("\\n解法: 代入法 / 消元法 — 就像变量替换重构")
    print()

    # 4. 因式分解
    section("4. 因式分解")
    typewriter("把多项式拆成乘积形式 — 就像代码重构!")
    typewriter("把复杂表达式拆成简单因子的乘积")
    typewriter("\\n常用公式:")
    print("   • a² - b² = (a+b)(a-b)       — 平方差")
    print("   • a² + 2ab + b² = (a+b)²     — 完全平方")
    print("   • a² - 2ab + b² = (a-b)²     — 完全平方差")
    print("   • x² + (a+b)x + ab = (x+a)(x+b)  — 十字相乘")
    typewriter("\\n💡 程序员类比: 因式分解就像把一个大函数拆成")
    typewriter("   多个小函数的组合, 便于理解和计算")
    print()

    # 5. 函数
    section("5. 函数与图像")
    typewriter("函数就是映射: f(x) = y — 输入x, 输出y")
    typewriter("就像程序的函数: 输入参数, 返回结果!")
    typewriter("\\n常见函数类型:")
    print("   • 一次函数: y = kx + b  (直线)")
    print("   • 二次函数: y = ax² + bx + c  (抛物线)")
    print("   • 指数函数: y = a^x  (指数增长/衰减)")
    print("   • 对数函数: y = log_a(x)  (指数的逆运算)")
    print("   • 三角函数: y = sin(x), cos(x), tan(x)")
    typewriter("\\n💡 程序员类比: 函数图像就是函数的可视化,")
    typewriter("   就像用图表监控程序的性能变化")
    print()

    # 6. 指数与对数
    section("6. 指数与对数")
    typewriter("指数: a^b = c  →  对数: log_a(c) = b")
    typewriter("它们互为逆运算, 就像加密和解密!")
    print()
    print("   指数性质:")
    print("     • a^m × a^n = a^(m+n)    — 指数相加")
    print("     • a^m / a^n = a^(m-n)    — 指数相减")
    print("     • (a^m)^n = a^(m×n)      — 指数相乘")
    print()
    print("   对数性质:")
    print("     • log(ab) = log(a) + log(b)  — 乘变加")
    print("     • log(a/b) = log(a) - log(b)  — 除变减")
    print("     • log(a^b) = b × log(a)      — 指数变系数")
    typewriter("\\n💡 程序员类比: 对数就是把乘法变成加法,")
    typewriter("   就像MapReduce — 先拆分计算再合并结果")
    print()

    # 小测验
    section("小测验")
    score = 0

    print("1. 方程 2x + 6 = 0 的解是?")
    print("   A) x = 3   B) x = -3   C) x = 6   D) x = -6")
    if input("答案: ").strip().upper() == "B":
        print("✅ 正确!")
        score += 1
    else:
        print("❌ 错误! 答案是 B (x = -3)")

    print("\\n2. 二次方程 x² - 5x + 6 = 0 的两个根是?")
    print("   A) 1和6   B) 2和3   C) -2和-3   D) 1和5")
    if input("答案: ").strip().upper() == "B":
        print("✅ 正确! (因式分解: (x-2)(x-3)=0)")
        score += 1
    else:
        print("❌ 错误! 答案是 B (2和3)")

    print("\\n3. log2(8) = ?")
    print("   A) 2   B) 3   C) 4   D) 8")
    if input("答案: ").strip().upper() == "B":
        print("✅ 正确! (2³ = 8)")
        score += 1
    else:
        print("❌ 错误! 答案是 B (3)")

    print(f"\\n成绩: {score}/3")
    if score == 3:
        print("🏆 全对! 代数大师!")
    elif score >= 2:
        print("👍 不错! 代数入门成功!")
    else:
        print("😅 加油! 多看看公式就记住了~")

    print("\\n" + "=" * 60)
    print("代数教程结束! 记住: 代数就是解方程, 就像debug找变量值")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[math] 代数教程已生成: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 2. 几何教程
# ═══════════════════════════════════════════════════════════════

def generate_geometry_tutorial(output_path="math_geometry_tutorial.py"):
    """生成几何互动教程"""
    output_path = os.path.abspath(output_path)

    content = '''#!/usr/bin/env python3
"""
几何互动教程 — 由 PyMsi.math 生成
用编程思维理解几何!

用法: python math_geometry_tutorial.py
"""

import time
import sys
import math

def typewriter(text, delay=0.02):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\\n")

def section(title):
    print(f"\\n{'═' * 60}")
    print(f"  📏 {title}")
    print(f"{'═' * 60}")

def main():
    print("\\n" + "=" * 60)
    print("  📏 几何互动教程")
    print("  用编程思维理解几何!")
    print("=" * 60)

    # 1. 平面图形
    section("1. 平面图形面积与周长")
    print()
    print("   图形        面积公式            周长公式")
    print("   ────────────────────────────────────────")
    print("   正方形      S = a²              C = 4a")
    print("   长方形      S = a×b             C = 2(a+b)")
    print("   三角形      S = ½×底×高         C = a+b+c")
    print("   平行四边形   S = 底×高           C = 2(a+b)")
    print("   梯形        S = ½×(上底+下底)×高  C = 四边之和")
    print("   圆          S = πr²             C = 2πr")
    typewriter("\\n💡 程序员类比: 面积就像2D数组的元素总数,")
    typewriter("   周长就像遍历边界的步数")
    print()

    # 2. 立体图形
    section("2. 立体图形体积与表面积")
    print()
    print("   图形        体积公式            表面积公式")
    print("   ────────────────────────────────────────")
    print("   正方体      V = a³              S = 6a²")
    print("   长方体      V = a×b×c           S = 2(ab+bc+ac)")
    print("   圆柱        V = πr²h            S = 2πr² + 2πrh")
    print("   圆锥        V = ⅓πr²h           S = πr² + πrl")
    print("   球          V = ⁴⁄₃πr³          S = 4πr²")
    typewriter("\\n💡 程序员类比: 体积就像3D数组的元素总数,")
    typewriter("   表面积就像遍历最外层元素的数量")
    print()

    # 3. 勾股定理
    section("3. 勾股定理")
    typewriter("直角三角形: a² + b² = c² (c是斜边)")
    typewriter("\\n经典勾股数(整数解):")
    print("   • 3, 4, 5    (3² + 4² = 9 + 16 = 25 = 5²)")
    print("   • 5, 12, 13  (5² + 12² = 25 + 144 = 169 = 13²)")
    print("   • 8, 15, 17  (8² + 15² = 64 + 225 = 289 = 17²)")
    typewriter("\\n💡 程序员类比: 勾股定理就像两点间距离公式,")
    typewriter("   在2D坐标系中, 两点距离 = √((x2-x1)² + (y2-y1)²)")
    print()

    # 4. 三角函数
    section("4. 三角函数入门")
    typewriter("在直角三角形中:")
    print("   sin(θ) = 对边 / 斜边    (正弦)")
    print("   cos(θ) = 邻边 / 斜边    (余弦)")
    print("   tan(θ) = 对边 / 邻边    (正切)")
    typewriter("\\n记忆口诀: 正弦对, 余弦邻, 正切对比邻")
    typewriter("\\n💡 程序员类比: 三角函数就像坐标变换函数,")
    typewriter("   把角度映射成比例 — 就像归一化函数")
    print()

    # 5. 特殊角
    section("5. 特殊角的三角函数值")
    print()
    print("   角度    0°    30°      45°      60°      90°")
    print("   ───────────────────────────────────────────")
    print("   sin    0     ½       √2/2     √3/2     1")
    print("   cos    1    √3/2     √2/2      ½       0")
    print("   tan    0    √3/3      1       √3       ∞")
    typewriter("\\n💡 记忆技巧: sin从0到1递增, cos从1到0递减,")
    typewriter("   sin和cos的平方和永远等于1 (sin² + cos² = 1)")
    print()

    # 小测验
    section("小测验")
    score = 0

    print("1. 半径为 r 的圆的面积公式是?")
    print("   A) 2πr   B) πr²   C) 2πr²   D) πr")
    if input("答案: ").strip().upper() == "B":
        print("✅ 正确!")
        score += 1
    else:
        print("❌ 错误! 答案是 B (πr²)")

    print("\\n2. 勾股定理中, 直角边3和4, 斜边是?")
    print("   A) 5   B) 6   C) 7   D) 12")
    if input("答案: ").strip().upper() == "A":
        print("✅ 正确! 3² + 4² = 9 + 16 = 25 = 5²")
        score += 1
    else:
        print("❌ 错误! 答案是 A (5)")

    print("\\n3. sin(30°) = ?")
    print("   A) 0   B) ½   C) √2/2   D) 1")
    if input("答案: ").strip().upper() == "B":
        print("✅ 正确!")
        score += 1
    else:
        print("❌ 错误! 答案是 B (½)")

    print(f"\\n成绩: {score}/3")
    if score == 3:
        print("🏆 全对! 几何小能手!")
    elif score >= 2:
        print("👍 不错! 几何入门成功!")
    else:
        print("😅 加油! 多背公式就记住了~")

    print("\\n" + "=" * 60)
    print("几何教程结束! 记住: 几何就是空间的数学, 就像UI布局")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[math] 几何教程已生成: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 3. 微积分教程
# ═══════════════════════════════════════════════════════════════

def generate_calculus_tutorial(output_path="math_calculus_tutorial.py"):
    """生成微积分互动教程"""
    output_path = os.path.abspath(output_path)

    content = '''#!/usr/bin/env python3
"""
微积分入门教程 — 由 PyMsi.math 生成
用编程思维理解微积分!

用法: python math_calculus_tutorial.py
"""

import time
import sys

def typewriter(text, delay=0.02):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\\n")

def section(title):
    print(f"\\n{'═' * 60}")
    print(f"  📈 {title}")
    print(f"{'═' * 60}")

def main():
    print("\\n" + "=" * 60)
    print("  📈 微积分入门教程")
    print("  用编程思维理解微积分!")
    print("=" * 60)

    # 1. 导数
    section("1. 导数 — 变化率")
    typewriter("导数就是函数在某一点的变化率 —")
    typewriter("就像程序的性能监控: 每秒处理多少请求")
    typewriter("\\n数学定义: f'(x) = lim(Δx→0) [f(x+Δx) - f(x)] / Δx")
    typewriter("\\n💡 程序员类比:")
    print("   • 位移的导数 = 速度 (位置变化率)")
    print("   • 速度的导数 = 加速度 (速度变化率)")
    print("   • 就像: 数据量的导数 = 吞吐量 (QPS)")
    print()

    typewriter("常用导数公式:")
    print("   • (C)' = 0           常数的导数是0")
    print("   • (x^n)' = n·x^(n-1)  幂函数")
    print("   • (sin x)' = cos x    正弦")
    print("   • (cos x)' = -sin x   余弦")
    print("   • (e^x)' = e^x        指数函数(自己的导数)")
    print("   • (ln x)' = 1/x       自然对数")
    print()

    # 2. 导数的应用
    section("2. 导数的应用 — 找极值")
    typewriter("导数为0的点 = 函数的极值点 (极大或极小)")
    typewriter("就像程序找最优参数 — 损失函数最小化!")
    typewriter("\\n步骤:")
    print("   1. 求导: f'(x)")
    print("   2. 令 f'(x) = 0, 解出临界点")
    print("   3. 二阶导数判断极大/极小")
    typewriter("\\n💡 程序员类比: 梯度下降法就是利用导数找最小值,")
    typewriter("   机器学习的核心就是这个!")
    print()

    # 3. 积分
    section("3. 积分 — 累加求和")
    typewriter("积分就是把无数个小面积加起来 —")
    typewriter("就像程序里的 sum() 函数, 只不过是无限细分")
    typewriter("\\n定积分: ∫[a→b] f(x) dx = F(b) - F(a)")
    typewriter("(F是f的原函数, 即 F'(x) = f(x))")
    typewriter("\\n💡 程序员类比:")
    print("   • 速度积分 = 位移 (每个瞬间速度×时间加起来)")
    print("   • 就像: 吞吐量积分 = 总数据量")
    print("   • 积分就像 for 循环累加, 只不过步长趋近于0")
    print()

    # 4. 微积分基本定理
    section("4. 微积分基本定理")
    typewriter("导数和积分互为逆运算!")
    typewriter("就像编码和解码, 加密和解密!")
    typewriter("\\n∫[a→b] f'(x) dx = f(b) - f(a)")
    typewriter("\\n💡 理解: 把变化率累加起来 = 总变化量")
    typewriter("   就像: 把每秒请求数加起来 = 总请求数")
    print()

    # 5. 常用积分
    section("5. 常用积分公式")
    print("   • ∫ x^n dx = x^(n+1)/(n+1) + C    (n≠-1)")
    print("   • ∫ 1/x dx = ln|x| + C")
    print("   • ∫ e^x dx = e^x + C")
    print("   • ∫ sin x dx = -cos x + C")
    print("   • ∫ cos x dx = sin x + C")
    print("   • ∫ k dx = kx + C                 (常数)")
    print()
    typewriter("💡 技巧: 积分就是导数反过来, 记住导数就记住积分了!")
    print()

    # 小测验
    section("小测验")
    score = 0

    print("1. f(x) = x³ 的导数是?")
    print("   A) x²   B) 3x²   C) 3x   D) x³")
    if input("答案: ").strip().upper() == "B":
        print("✅ 正确! (x^n)' = n·x^(n-1) = 3x²")
        score += 1
    else:
        print("❌ 错误! 答案是 B (3x²)")

    print("\\n2. ∫ 2x dx = ?")
    print("   A) x² + C   B) 2x² + C   C) x + C   D) 2 + C")
    if input("答案: ").strip().upper() == "A":
        print("✅ 正确! 积分是导数的逆运算, (x²)' = 2x")
        score += 1
    else:
        print("❌ 错误! 答案是 A (x² + C)")

    print("\\n3. 导数为0的点是函数的什么点?")
    print("   A) 零点   B) 极值点   C) 拐点   D) 起点")
    if input("答案: ").strip().upper() == "B":
        print("✅ 正确! 导数为0 = 变化率为0 = 极值点")
        score += 1
    else:
        print("❌ 错误! 答案是 B (极值点)")

    print(f"\\n成绩: {score}/3")
    if score == 3:
        print("🏆 全对! 微积分入门成功!")
    elif score >= 2:
        print("👍 不错! 继续加油!")
    else:
        print("😅 没关系, 微积分本来就难, 多看看就懂了~")

    print("\\n" + "=" * 60)
    print("微积分教程结束! 记住: 导数=变化率, 积分=累加和")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[math] 微积分教程已生成: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 4. 线性代数教程
# ═══════════════════════════════════════════════════════════════

def generate_linear_algebra_tutorial(output_path="math_linalg_tutorial.py"):
    """生成线性代数互动教程"""
    output_path = os.path.abspath(output_path)

    content = '''#!/usr/bin/env python3
"""
线性代数入门教程 — 由 PyMsi.math 生成
程序员必备! AI/图形学/数据科学的基础!

用法: python math_linalg_tutorial.py
"""

import time
import sys

def typewriter(text, delay=0.02):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\\n")

def section(title):
    print(f"\\n{'═' * 60}")
    print(f"  🔢 {title}")
    print(f"{'═' * 60}")

def main():
    print("\\n" + "=" * 60)
    print("  🔢 线性代数入门教程")
    print("  程序员必备! AI/图形学/数据科学的基础!")
    print("=" * 60)

    # 1. 向量
    section("1. 向量 — 有序的数列表")
    typewriter("向量就是一维数组 / list / array!")
    typewriter("\\nv = [v1, v2, ..., vn]  (n维向量)")
    print()
    print("   例: v = [1, 2, 3]  (三维向量)")
    print()

    typewriter("向量运算:")
    print("   • 加法: [a1,a2] + [b1,b2] = [a1+b1, a2+b2]")
    print("   • 数乘: k × [a1,a2] = [k·a1, k·a2]")
    print("   • 点积: a·b = a1×b1 + a2×b2 + ... + an×bn")
    print("   • 模长: |v| = √(v1² + v2² + ... + vn²)")
    typewriter("\\n💡 程序员类比:")
    print("   • 向量就像 Python 的 list")
    print("   • 向量加法就像 zip + map(sum)")
    print("   • 点积就像权重加权和 (加权平均的基础)")
    print()

    # 2. 点积的意义
    section("2. 点积的几何意义")
    typewriter("a·b = |a| × |b| × cos(θ)  (θ是夹角)")
    print()
    print("   • 点积 > 0: 夹角 < 90° (方向相近)")
    print("   • 点积 = 0: 夹角 = 90° (正交/垂直)")
    print("   • 点积 < 0: 夹角 > 90° (方向相反)")
    typewriter("\\n💡 应用场景:")
    print("   • 相似度计算 (推荐系统、NLP)")
    print("   • 光照计算 (图形学)")
    print("   • 投影计算")
    print()

    # 3. 矩阵
    section("3. 矩阵 — 二维数组")
    typewriter("矩阵就是二维数组! 行 × 列")
    print()
    print("   例: A = [[1, 2, 3],")
    print("              [4, 5, 6]]    (2×3矩阵)")
    print()

    typewriter("矩阵运算:")
    print("   • 加法: 对应元素相加 (同型矩阵)")
    print("   • 数乘: 每个元素 × k")
    print("   • 乘法: A(m×n) × B(n×p) = C(m×p)")
    print("     C[i][j] = A第i行 · B第j列 (点积!)")
    typewriter("\\n💡 程序员类比:")
    print("   • 矩阵就像二维数组 / 嵌套list")
    print("   • 矩阵乘法就像三层for循环")
    print("   • 矩阵可以表示线性变换 (旋转、缩放、平移)")
    print()

    # 4. 矩阵的意义
    section("4. 矩阵 = 线性变换")
    typewriter("矩阵可以看作一个函数: 输入向量, 输出向量")
    typewriter("y = A·x  (x是输入向量, A是变换矩阵, y是输出)")
    typewriter("\\n常见变换:")
    print("   • 旋转矩阵: 把向量旋转θ角")
    print("   • 缩放矩阵: 沿x/y轴缩放")
    print("   • 投影矩阵: 投影到某条线/面")
    print("   • 剪切矩阵: 平行四边形变形")
    typewriter("\\n💡 应用: 计算机图形学、3D游戏、AI神经网络")
    print()

    # 5. 行列式与逆矩阵
    section("5. 行列式与逆矩阵")
    typewriter("行列式 det(A): 矩阵变换的'面积缩放因子'")
    print("   • det > 0: 保持方向")
    print("   • det < 0: 翻转方向 (镜像)")
    print("   • det = 0: 降维了 (不可逆!)")
    print()
    typewriter("逆矩阵 A⁻¹: 矩阵的逆操作, 就像反函数")
    print("   A × A⁻¹ = I  (单位矩阵, 就像数字1)")
    print("   只有 det(A) ≠ 0 时才有逆矩阵")
    typewriter("\\n💡 程序员类比: 逆矩阵就像反序列化/解密,")
    typewriter("   能把变换后的向量还原回去")
    print()

    # 6. 特征值与特征向量
    section("6. 特征值与特征向量 (选学)")
    typewriter("A·v = λ·v  (v是特征向量, λ是特征值)")
    typewriter("矩阵A作用在v上, 只改变长度不改变方向!")
    typewriter("\\n💡 应用:")
    print("   • PCA主成分分析 (数据降维)")
    print("   • Google PageRank")
    print("   • 图像处理压缩")
    print("   • 量子力学")
    typewriter("\\n程序员类比: 特征向量就是矩阵的'主轴方向',")
    typewriter("   就像数据的主要变化方向")
    print()

    # 小测验
    section("小测验")
    score = 0

    print("1. 向量 [1,2,3] · [4,5,6] 的点积是?")
    print("   A) 32   B) 24   C) 21   D) 15")
    if input("答案: ").strip().upper() == "A":
        print("✅ 正确! 1×4 + 2×5 + 3×6 = 4+10+18 = 32")
        score += 1
    else:
        print("❌ 错误! 答案是 A (32)")

    print("\\n2. 2×3矩阵 乘以 3×4矩阵, 结果是?")
    print("   A) 2×4矩阵   B) 3×3矩阵   C) 2×3矩阵   D) 4×2矩阵")
    if input("答案: ").strip().upper() == "A":
        print("✅ 正确! m×n × n×p = m×p")
        score += 1
    else:
        print("❌ 错误! 答案是 A (2×4矩阵)")

    print("\\n3. 行列式为0的矩阵意味着?")
    print("   A) 矩阵可逆   B) 矩阵降维/不可逆   C) 矩阵是单位矩阵   D) 矩阵是0矩阵")
    if input("答案: ").strip().upper() == "B":
        print("✅ 正确! det=0 说明变换后维度降低, 不可逆")
        score += 1
    else:
        print("❌ 错误! 答案是 B (降维/不可逆)")

    print(f"\\n成绩: {score}/3")
    if score == 3:
        print("🏆 全对! 线性代数入门成功!")
    elif score >= 2:
        print("👍 不错! AI的数学基础你有了!")
    else:
        print("😅 没关系, 线性代数需要多练~")

    print("\\n" + "=" * 60)
    print("线性代数教程结束! 记住: 向量=数组, 矩阵=2D数组+变换")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[math] 线性代数教程已生成: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 5. 概率统计教程
# ═══════════════════════════════════════════════════════════════

def generate_probability_tutorial(output_path="math_prob_tutorial.py"):
    """生成概率统计互动教程"""
    output_path = os.path.abspath(output_path)

    content = '''#!/usr/bin/env python3
"""
概率统计入门教程 — 由 PyMsi.math 生成
数据科学、AI、AB测试的基础!

用法: python math_prob_tutorial.py
"""

import time
import sys
import random

def typewriter(text, delay=0.02):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\\n")

def section(title):
    print(f"\\n{'═' * 60}")
    print(f"  🎲 {title}")
    print(f"{'═' * 60}")

def main():
    print("\\n" + "=" * 60)
    print("  🎲 概率统计入门教程")
    print("  数据科学、AI、AB测试的基础!")
    print("=" * 60)

    # 1. 基本概念
    section("1. 基本概念")
    print("   • 样本空间: 所有可能结果的集合 (Ω)")
    print("   • 事件: 样本空间的子集 (A)")
    print("   • 概率: P(A) = 事件A发生的可能 / 总可能")
    print("   • 0 ≤ P(A) ≤ 1  (概率在0到1之间)")
    typewriter("\\n💡 程序员类比: 概率就像分支的权重,")
    typewriter("   所有分支的概率加起来等于1 (100%)")
    print()

    # 2. 古典概型
    section("2. 古典概型")
    typewriter("所有结果等可能: P(A) = |A| / |Ω|")
    print()
    print("   例1: 抛硬币, 正面朝上的概率 = 1/2 = 0.5")
    print("   例2: 掷骰子, 点数>4的概率 = 2/6 = 1/3")
    print("   例3: 抽牌, 抽到红桃的概率 = 13/52 = 1/4")
    print()

    # 3. 条件概率
    section("3. 条件概率与贝叶斯")
    typewriter("P(A|B) = P(A∩B) / P(B)")
    typewriter("在B发生的条件下, A发生的概率")
    print()
    typewriter("贝叶斯公式:")
    print("   P(A|B) = P(B|A) × P(A) / P(B)")
    typewriter("\\n💡 这是AI/机器学习的核心公式之一!")
    typewriter("   朴素贝叶斯分类器就是基于这个")
    typewriter("   就像: 看到症状 → 推断病因的概率")
    print()

    # 4. 期望与方差
    section("4. 期望与方差")
    typewriter("期望 E(X): 随机变量的平均值 (加权平均)")
    print("   E(X) = Σ xi × P(X=xi)")
    typewriter("\\n方差 Var(X): 数据的离散/波动程度")
    print("   Var(X) = E[(X-E(X))²]")
    typewriter("\\n标准差 σ = √Var(X)  (和原数据同单位)")
    typewriter("\\n💡 程序员类比:")
    print("   • 期望 = 平均响应时间")
    print("   • 方差 = 响应时间的波动大小")
    print("   • 标准差大 = 性能不稳定")
    print()

    # 5. 常见分布
    section("5. 常见概率分布")
    print("   🎯 二项分布 B(n,p): n次独立试验, 成功k次的概率")
    print("      例: 抛10次硬币, 5次正面的概率")
    print()
    print("   🎲 均匀分布 U(a,b): 区间内每个值概率相等")
    print("      例: 掷骰子, 随机数生成")
    print()
    print("   🔔 正态分布 N(μ,σ²): 钟形曲线, 自然界最常见")
    print("      例: 身高、智商、测量误差")
    print("      68-95-99.7法则: ±1σ占68%, ±2σ占95%, ±3σ占99.7%")
    print()
    print("   ⏱️  泊松分布 P(λ): 单位时间内事件发生次数")
    print("      例: 网站访问量、客服接到的电话数")
    typewriter("\\n💡 应用: AB测试、统计显著性检验都基于这些分布")
    print()

    # 6. 大数定律
    section("6. 大数定律 & 中心极限定理")
    typewriter("大数定律: 样本量越大, 样本均值越接近真实期望")
    typewriter("就像测试用例越多, 平均性能越接近真实性能")
    print()
    typewriter("中心极限定理: 大量独立随机变量的和趋近正态分布")
    typewriter("不管原来是什么分布, 加起来都变正态!")
    typewriter("\\n💡 这就是为什么正态分布无处不在 —")
    typewriter("   也解释了为什么AB测试需要足够大的样本量")
    print()

    # 小测验
    section("小测验")
    score = 0

    print("1. 掷一个骰子, 点数为偶数的概率是?")
    print("   A) 1/6   B) 1/3   C) 1/2   D) 2/3")
    if input("答案: ").strip().upper() == "C":
        print("✅ 正确! 偶数有2,4,6共3个, 3/6 = 1/2")
        score += 1
    else:
        print("❌ 错误! 答案是 C (1/2)")

    print("\\n2. 正态分布中, ±2σ 范围内的数据占比约为?")
    print("   A) 68%   B) 95%   C) 99.7%   D) 50%")
    if input("答案: ").strip().upper() == "B":
        print("✅ 正确! 68-95-99.7法则: ±2σ ≈ 95%")
        score += 1
    else:
        print("❌ 错误! 答案是 B (95%)")

    print("\\n3. 贝叶斯公式的作用是?")
    print("   A) 计算期望   B) 计算方差")
    print("   C) 由结果反推原因的概率   D) 生成随机数")
    if input("答案: ").strip().upper() == "C":
        print("✅ 正确! 贝叶斯就是'由果推因'")
        score += 1
    else:
        print("❌ 错误! 答案是 C")

    print(f"\\n成绩: {score}/3")
    if score == 3:
        print("🏆 全对! 统计入门成功!")
    elif score >= 2:
        print("👍 不错! 数据科学的基础你有了!")
    else:
        print("😅 加油! 概率统计需要多练~")

    print("\\n" + "=" * 60)
    print("概率统计教程结束! 记住: 概率=可能性, 统计=从数据找规律")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[math] 概率统计教程已生成: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 6. 数论教程
# ═══════════════════════════════════════════════════════════════

def generate_number_theory_tutorial(output_path="math_number_theory_tutorial.py"):
    """生成数论互动教程"""
    output_path = os.path.abspath(output_path)

    content = '''#!/usr/bin/env python3
"""
数论入门教程 — 由 PyMsi.math 生成
密码学、算法竞赛的基础!

用法: python math_number_theory_tutorial.py
"""

import time
import sys
import math

def typewriter(text, delay=0.02):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\\n")

def section(title):
    print(f"\\n{'═' * 60}")
    print(f"  🔐 {title}")
    print(f"{'═' * 60}")

def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

def main():
    print("\\n" + "=" * 60)
    print("  🔐 数论入门教程")
    print("  密码学、算法竞赛的基础!")
    print("=" * 60)

    # 1. 质数
    section("1. 质数 (素数)")
    typewriter("质数: 大于1的自然数, 只能被1和自己整除")
    print("   前10个质数: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29")
    print("   注意: 1不是质数! 2是唯一的偶质数!")
    typewriter("\\n💡 程序员类比: 质数就像不可再分的'原子类型',")
    typewriter("   其他数都可以分解成质数的乘积")
    print()

    # 2. 质因数分解
    section("2. 质因数分解")
    typewriter("每个合数都可以唯一分解为质数的乘积")
    typewriter("(算术基本定理)")
    print()
    print("   例:")
    print("     12 = 2 × 2 × 3 = 2² × 3")
    print("     100 = 2 × 2 × 5 × 5 = 2² × 5²")
    print("     2024 = 2 × 2 × 2 × 11 × 23 = 2³ × 11 × 23")
    typewriter("\\n💡 这是RSA加密的基础 — 大数分解很难!")
    typewriter("   就像: 两个大质数相乘很容易,")
    typewriter("   但从乘积反推两个质数却极难")
    print()

    # 3. GCD & LCM
    section("3. 最大公约数 (GCD) & 最小公倍数 (LCM)")
    typewriter("GCD(a,b): 能同时整除a和b的最大数")
    typewriter("LCM(a,b): 能同时被a和b整除的最小数")
    print()
    print("   关系: GCD(a,b) × LCM(a,b) = a × b")
    print()
    typewriter("欧几里得算法 (求GCD):")
    print("   gcd(a, b) = gcd(b, a mod b)")
    print("   直到 b = 0, a就是答案")
    print()
    print("   例: gcd(48, 36)")
    print("   = gcd(36, 48%36=12)")
    print("   = gcd(12, 36%12=0)")
    print("   = 12  ✅")
    typewriter("\\n💡 程序员类比: GCD就像找两个数组的最大公共子数组")
    print()

    # 4. 模运算
    section("4. 模运算")
    typewriter("a mod b = a除以b的余数  (就是 % 运算符!)")
    print()
    print("   例: 7 mod 3 = 1, 10 mod 4 = 2")
    print()
    typewriter("模运算性质:")
    print("   • (a + b) mod m = [(a mod m) + (b mod m)] mod m")
    print("   • (a × b) mod m = [(a mod m) × (b mod m)] mod m")
    print("   • a^b mod m = ((a mod m)^b) mod m")
    typewriter("\\n💡 这就是为什么加密可以用模运算 —")
    typewriter("   可以先取模再运算, 防止数字太大溢出")
    print()

    # 5. 快速幂
    section("5. 快速幂算法")
    typewriter("计算 a^b mod m, b很大时用快速幂 (O(log b))")
    print()
    print("   原理: 把指数拆成二进制, 平方累积")
    print("   例: 3^13 mod 100")
    print("   13 = 1101₂ = 8 + 4 + 1")
    print("   3^1 = 3 mod 100")
    print("   3^2 = 9 mod 100")
    print("   3^4 = 81 mod 100")
    print("   3^8 = 81² = 6561 = 61 mod 100")
    print("   3^13 = 3^8 × 3^4 × 3^1 = 61 × 81 × 3 = 14823 = 23 mod 100")
    typewriter("\\n💡 这是RSA加密的核心算法之一!")
    print()

    # 6. 费马小定理 & RSA
    section("6. 费马小定理与RSA简介")
    typewriter("费马小定理: 如果p是质数, a不是p的倍数, 则:")
    print("   a^(p-1) ≡ 1 (mod p)")
    print()
    typewriter("RSA加密的基本思想:")
    print("   1. 选两个大质数 p, q")
    print("   2. n = p×q, φ(n) = (p-1)(q-1)")
    print("   3. 选e与φ(n)互质 (公钥)")
    print("   4. 找d使 e×d ≡ 1 (mod φ(n)) (私钥)")
    print("   5. 加密: c = m^e mod n")
    print("   6. 解密: m = c^d mod n")
    typewriter("\\n💡 安全性基于: 大数分解很难!")
    typewriter("   知道n=pq但不知道p,q就解不开")
    print()

    # 小测验
    section("小测验")
    score = 0

    print("1. 下列哪个数是质数?")
    print("   A) 1   B) 9   C) 15   D) 17")
    if input("答案: ").strip().upper() == "D":
        print("✅ 正确! 17只能被1和17整除")
        score += 1
    else:
        print("❌ 错误! 答案是 D (17)")

    print("\\n2. gcd(24, 18) = ?")
    print("   A) 2   B) 3   C) 6   D) 12")
    if input("答案: ").strip().upper() == "C":
        print("✅ 正确! gcd(24,18) = gcd(18,6) = gcd(6,0) = 6")
        score += 1
    else:
        print("❌ 错误! 答案是 C (6)")

    print("\\n3. 7 mod 3 = ?")
    print("   A) 0   B) 1   C) 2   D) 3")
    if input("答案: ").strip().upper() == "B":
        print("✅ 正确! 7 ÷ 3 = 2 余 1")
        score += 1
    else:
        print("❌ 错误! 答案是 B (1)")

    print(f"\\n成绩: {score}/3")
    if score == 3:
        print("🏆 全对! 数论入门成功! 可以学密码学了!")
    elif score >= 2:
        print("👍 不错! 密码学的基础你有了!")
    else:
        print("😅 加油! 数论需要多做题~")

    print("\\n" + "=" * 60)
    print("数论教程结束! 记住: 质数是原子, 模运算是加密的基础")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[math] 数论教程已生成: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 7. 直接计算函数
# ═══════════════════════════════════════════════════════════════

def quadratic(a, b, c):
    """解一元二次方程 ax² + bx + c = 0

    Returns:
        list  根的列表 (0个/1个/2个实根)
    """
    delta = b * b - 4 * a * c
    print(f"[math] 方程: {a}x² + {b}x + {c} = 0")
    print(f"[math] 判别式 Δ = {b}² - 4×{a}×{c} = {delta}")

    if delta < 0:
        print(f"[math] Δ < 0, 无实根")
        return []
    elif delta == 0:
        x = -b / (2 * a)
        print(f"[math] Δ = 0, 重根: x = {x}")
        return [x]
    else:
        sqrt_delta = math.sqrt(delta)
        x1 = (-b + sqrt_delta) / (2 * a)
        x2 = (-b - sqrt_delta) / (2 * a)
        print(f"[math] Δ > 0, 两个实根: x1 = {x1}, x2 = {x2}")
        return [x1, x2]


def factorial(n):
    """计算阶乘 n!

    Args:
        n: int  非负整数

    Returns:
        int  n!
    """
    if n < 0:
        raise ValueError("阶乘只定义在非负整数上")
    result = 1
    for i in range(2, n + 1):
        result *= i
    print(f"[math] {n}! = {result}")
    return result


def gcd(a, b):
    """最大公约数 (欧几里得算法)

    Returns:
        int  gcd(a, b)
    """
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    print(f"[math] gcd = {a}")
    return a


def lcm(a, b):
    """最小公倍数

    Returns:
        int  lcm(a, b)
    """
    result = abs(a * b) // gcd(a, b)
    print(f"[math] lcm = {result}")
    return result


def dot_product(v1, v2):
    """向量点积

    Args:
        v1, v2: list  两个向量 (长度必须相同)

    Returns:
        float  点积
    """
    if len(v1) != len(v2):
        raise ValueError("向量长度必须相同")
    result = sum(a * b for a, b in zip(v1, v2))
    print(f"[math] {v1} · {v2} = {result}")
    return result


def vector_magnitude(v):
    """向量模长 (长度)

    Returns:
        float  |v|
    """
    result = math.sqrt(sum(x * x for x in v))
    print(f"[math] |{v}| = {result:.4f}")
    return result


def matrix_add(A, B):
    """矩阵加法

    Returns:
        list  A + B
    """
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError("矩阵维度不同, 不能相加")
    result = [[A[i][j] + B[i][j] for j in range(len(A[0]))]
              for i in range(len(A))]
    print(f"[math] 矩阵加法完成: {len(A)}×{len(A[0])}")
    return result


def matrix_mult(A, B):
    """矩阵乘法

    Args:
        A: list  m×n 矩阵
        B: list  n×p 矩阵

    Returns:
        list  m×p 矩阵
    """
    m, n, p = len(A), len(A[0]), len(B[0])
    if n != len(B):
        raise ValueError(f"矩阵维度不匹配: {m}×{n} 和 {len(B)}×{p}")

    result = [[0] * p for _ in range(m)]
    for i in range(m):
        for j in range(p):
            for k in range(n):
                result[i][j] += A[i][k] * B[k][j]

    print(f"[math] 矩阵乘法完成: {m}×{n} × {n}×{p} = {m}×{p}")
    return result


def is_prime(n):
    """判断是否为质数

    Returns:
        bool
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def prime_factors(n):
    """质因数分解

    Returns:
        dict  {质数: 指数}
    """
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = 1

    expr = " × ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(factors.items()))
    print(f"[math] 质因数分解: {expr}")
    return factors


def fast_pow(a, b, mod=None):
    """快速幂 (模幂)

    Args:
        a: int  底数
        b: int  指数
        mod: int  模数 (可选)

    Returns:
        int  a^b (mod mod)
    """
    result = 1
    base = a
    if mod:
        base %= mod

    while b > 0:
        if b & 1:
            result = (result * base) % mod if mod else result * base
        base = (base * base) % mod if mod else base * base
        b >>= 1

    if mod:
        print(f"[math] {a}^{b if b else 'b'} mod {mod} = {result}")
    else:
        print(f"[math] {a}^{b if b else 'b'} = {result}")
    return result


# ═══════════════════════════════════════════════════════════════
# 8. 模块包装类
# ═══════════════════════════════════════════════════════════════

class _MathModule:
    """PyMsi.math — 🔢 数学教育模块 (v1.6.0 Education Plus)

    专为程序员设计的数学教学工具, 6大分支:

    1. 代数 — 方程、函数、因式分解
    2. 几何 — 面积体积、三角函数、勾股定理
    3. 微积分 — 导数、积分、极值
    4. 线性代数 — 向量、矩阵、特征值 (AI必备)
    5. 概率统计 — 概率分布、期望方差、贝叶斯
    6. 数论 — 质数、GCD、模运算、RSA基础

    用法:
        # 生成教程
        PM.math.algebra()            # 代数教程
        PM.math.geometry()           # 几何教程
        PM.math.calculus()           # 微积分教程
        PM.math.linear_algebra()     # 线性代数教程
        PM.math.probability()        # 概率统计教程
        PM.math.number_theory()      # 数论教程

        # 直接计算
        PM.math.quadratic(1, -5, 6)  # 解二次方程
        PM.math.factorial(5)         # 阶乘
        PM.math.gcd(48, 36)          # 最大公约数
        PM.math.lcm(12, 18)          # 最小公倍数
        PM.math.dot_product([1,2,3], [4,5,6])  # 点积
        PM.math.matrix_mult([[1,2],[3,4]], [[5,6],[7,8]])  # 矩阵乘法
        PM.math.is_prime(17)         # 判断质数
        PM.math.prime_factors(100)   # 质因数分解
        PM.math.fast_pow(3, 13, 100) # 快速幂

        # 别名: PM.maths / PM.数学
    """

    def __init__(self):
        self.output_dir = "."

    def __repr__(self):
        return "<PyMsi.math [数学教育模块] v1.6.0 Education Plus>"

    def algebra(self, output=None):
        """生成代数互动教程"""
        if output is None:
            output = "math_algebra_tutorial.py"
        return generate_algebra_tutorial(output)

    def geometry(self, output=None):
        """生成几何互动教程"""
        if output is None:
            output = "math_geometry_tutorial.py"
        return generate_geometry_tutorial(output)

    def calculus(self, output=None):
        """生成微积分入门教程"""
        if output is None:
            output = "math_calculus_tutorial.py"
        return generate_calculus_tutorial(output)

    def linear_algebra(self, output=None):
        """生成线性代数入门教程"""
        if output is None:
            output = "math_linalg_tutorial.py"
        return generate_linear_algebra_tutorial(output)

    def linalg(self, output=None):
        """别名: linear_algebra"""
        return self.linear_algebra(output)

    def probability(self, output=None):
        """生成概率统计入门教程"""
        if output is None:
            output = "math_prob_tutorial.py"
        return generate_probability_tutorial(output)

    def stats(self, output=None):
        """别名: probability"""
        return self.probability(output)

    def number_theory(self, output=None):
        """生成数论入门教程"""
        if output is None:
            output = "math_number_theory_tutorial.py"
        return generate_number_theory_tutorial(output)

    # 计算函数
    def quadratic(self, a, b, c):
        """解一元二次方程 ax² + bx + c = 0"""
        return quadratic(a, b, c)

    def factorial(self, n):
        """计算阶乘 n!"""
        return factorial(n)

    def gcd(self, a, b):
        """最大公约数"""
        return gcd(a, b)

    def lcm(self, a, b):
        """最小公倍数"""
        return lcm(a, b)

    def dot_product(self, v1, v2):
        """向量点积"""
        return dot_product(v1, v2)

    def dot(self, v1, v2):
        """别名: dot_product"""
        return dot_product(v1, v2)

    def vector_len(self, v):
        """向量模长"""
        return vector_magnitude(v)

    def matrix_mult(self, A, B):
        """矩阵乘法"""
        return matrix_mult(A, B)

    def matmul(self, A, B):
        """别名: matrix_mult"""
        return matrix_mult(A, B)

    def is_prime(self, n):
        """判断是否为质数"""
        result = is_prime(n)
        print(f"[math] {n} {'是质数' if result else '不是质数'}")
        return result

    def prime_factors(self, n):
        """质因数分解"""
        return prime_factors(n)

    def fast_pow(self, a, b, mod=None):
        """快速幂 (模幂)"""
        return fast_pow(a, b, mod)

    def pow_mod(self, a, b, mod):
        """别名: fast_pow (带模)"""
        return fast_pow(a, b, mod)
