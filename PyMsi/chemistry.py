"""
chemistry.py — 化学教育模块 (v1.6.0 Education Plus)

专为程序员设计的化学教学工具:
  1. 元素周期表 — 20个常见元素, 用编程类比讲解
  2. 化学反应模拟 — 酸碱中和、氧化还原等
  3. 分子结构 — 常见分子, 用数据结构类比
  4. 溶液浓度计算 — 摩尔浓度、pH值
  5. 化学方程式配平

用法:
  import PyMsi as PM
  PM.chem.element()          # 元素周期表教程
  PM.chem.reaction()         # 化学反应模拟器
  PM.chem.molecule()         # 分子结构教程
  PM.chem.solution()         # 溶液计算
  PM.chem.balance("H2+O2=H2O")  # 配平化学方程式
"""

import os
import json
import random


# ═══════════════════════════════════════════════════════════════
# 数据库: 常见元素 (20个)
# ═══════════════════════════════════════════════════════════════

ELEMENTS = {
    "H": {
        "name": "氢", "atomic_number": 1, "symbol": "H",
        "mass": 1.008, "group": "非金属", "period": 1,
        "electrons": "1s1", "valence": 1,
        "analogy": "像程序里的 '基本单元' — 最轻的元素, 宇宙中最丰富",
        "fun_fact": "氢是宇宙中含量最多的元素, 占所有物质的75% — 就像代码里的注释, 到处都是"
    },
    "He": {
        "name": "氦", "atomic_number": 2, "symbol": "He",
        "mass": 4.003, "group": "稀有气体", "period": 1,
        "electrons": "1s2", "valence": 0,
        "analogy": "像程序里的 '惰性函数' — 完全不参与反应, 稳定到爆炸",
        "fun_fact": "氦是最难液化的气体, 也是唯一不能在常压下固化的元素 — 就像永远不崩溃的程序"
    },
    "Li": {
        "name": "锂", "atomic_number": 3, "symbol": "Li",
        "mass": 6.941, "group": "碱金属", "period": 2,
        "electrons": "1s2 2s1", "valence": 1,
        "analogy": "像程序里的 '单例模式' — 最外层只有1个电子, 随时准备丢出去",
        "fun_fact": "锂电池的核心材料, 因为锂很轻且能储存很多能量 — 就像轻量级数据库"
    },
    "C": {
        "name": "碳", "atomic_number": 6, "symbol": "C",
        "mass": 12.01, "group": "非金属", "period": 2,
        "electrons": "1s2 2s2 2p2", "valence": 4,
        "analogy": "像程序里的 '基类/接口' — 能和几乎所有元素结合, 是有机化学的核心",
        "fun_fact": "碳能形成的化合物比所有其他元素加起来还多 — 就像Python的类继承, 能派生出无限多子类"
    },
    "N": {
        "name": "氮", "atomic_number": 7, "symbol": "N",
        "mass": 14.01, "group": "非金属", "period": 2,
        "electrons": "1s2 2s2 2p3", "valence": 3,
        "analogy": "像程序里的 '惰性加载' — 占空气78%但通常不参与反应",
        "fun_fact": "氮气在空气中占78%, 但大部分生物不能直接利用 — 就像占内存但不用的后台程序"
    },
    "O": {
        "name": "氧", "atomic_number": 8, "symbol": "O",
        "mass": 16.00, "group": "非金属", "period": 2,
        "electrons": "1s2 2s2 2p4", "valence": 2,
        "analogy": "像程序里的 '主进程' — 生命必需, 参与绝大多数反应",
        "fun_fact": "氧气占空气21%, 但如果浓度太高会中毒 — 就像CPU占用率太高会过热"
    },
    "F": {
        "name": "氟", "atomic_number": 9, "symbol": "F",
        "mass": 19.00, "group": "卤素", "period": 2,
        "electrons": "1s2 2s2 2p5", "valence": 1,
        "analogy": "像程序里的 '激进优化器' — 反应性极强, 什么都要抢电子",
        "fun_fact": "氟是电负性最强的元素, 几乎能和所有元素反应 — 就像全局正则替换, 什么都匹配"
    },
    "Na": {
        "name": "钠", "atomic_number": 11, "symbol": "Na",
        "mass": 22.99, "group": "碱金属", "period": 3,
        "electrons": "1s2 2s2 2p6 3s1", "valence": 1,
        "analogy": "像程序里的 '急性子线程' — 最外层1个电子, 碰到水就炸",
        "fun_fact": "钠和水反应会爆炸并产生氢气 — 就像空指针异常, 一碰就崩"
    },
    "Mg": {
        "name": "镁", "atomic_number": 12, "symbol": "Mg",
        "mass": 24.31, "group": "碱土金属", "period": 3,
        "electrons": "1s2 2s2 2p6 3s2", "valence": 2,
        "analogy": "像程序里的 '双线程工作' — 最外层2个电子, 反应性也很强",
        "fun_fact": "镁燃烧发出耀眼的白光 — 以前的闪光灯就是用镁粉做的"
    },
    "Al": {
        "name": "铝", "atomic_number": 13, "symbol": "Al",
        "mass": 26.98, "group": "金属", "period": 3,
        "electrons": "1s2 2s2 2p6 3s2 3p1", "valence": 3,
        "analogy": "像程序里的 '轻量级框架' — 轻但强度高, 用途广泛",
        "fun_fact": "铝是地壳中含量最多的金属, 但提炼出来曾经比金还贵 — 就像开源前的商业软件"
    },
    "Si": {
        "name": "硅", "atomic_number": 14, "symbol": "Si",
        "mass": 28.09, "group": "类金属", "period": 3,
        "electrons": "1s2 2s2 2p6 3s2 3p2", "valence": 4,
        "analogy": "像程序里的 '半导体芯片' — 硅是计算机的基础材料",
        "fun_fact": "硅是半导体工业的核心, 没有硅就没有计算机 — 硅就是程序员的'碳基生命'对应物"
    },
    "P": {
        "name": "磷", "atomic_number": 15, "symbol": "P",
        "mass": 30.97, "group": "非金属", "period": 3,
        "electrons": "1s2 2s2 2p6 3s2 3p3", "valence": 3,
        "analogy": "像程序里的 '能量单元' — ATP的核心, 生命能量的载体",
        "fun_fact": "白磷在空气中会自燃 — 就像没有边界检查的数组, 随时溢出"
    },
    "S": {
        "name": "硫", "atomic_number": 16, "symbol": "S",
        "mass": 32.07, "group": "非金属", "period": 3,
        "electrons": "1s2 2s2 2p6 3s2 3p4", "valence": 2,
        "analogy": "像程序里的 '臭代码' — 硫化物都很臭, 但其实很有用",
        "fun_fact": "臭鸡蛋味就是硫化氢 — 就像代码里的臭味, 虽然难闻但能提醒你有问题"
    },
    "Cl": {
        "name": "氯", "atomic_number": 17, "symbol": "Cl",
        "mass": 35.45, "group": "卤素", "period": 3,
        "electrons": "1s2 2s2 2p6 3s2 3p5", "valence": 1,
        "analogy": "像程序里的 '杀毒软件' — 能杀菌消毒, 但也有毒性",
        "fun_fact": "氯气在一战中被用作化学武器, 但现在用来消毒自来水 — 剂量决定毒性, 就像递归深度决定栈溢出"
    },
    "K": {
        "name": "钾", "atomic_number": 19, "symbol": "K",
        "mass": 39.10, "group": "碱金属", "period": 4,
        "electrons": "1s2 2s2 2p6 3s2 3p6 4s1", "valence": 1,
        "analogy": "像程序里的 '越界访问' — 比钠还活泼, 遇水反应更剧烈",
        "fun_fact": "钾和水反应比钠还猛, 会产生紫色火焰 — 就像越界后直接段错误"
    },
    "Ca": {
        "name": "钙", "atomic_number": 20, "symbol": "Ca",
        "mass": 40.08, "group": "碱土金属", "period": 4,
        "electrons": "1s2 2s2 2p6 3s2 3p6 4s2", "valence": 2,
        "analogy": "像程序里的 '结构体/骨架' — 构成骨骼和牙齿的主要成分",
        "fun_fact": "人体中99%的钙都在骨骼和牙齿里 — 就像数据结构, 支撑起整个身体"
    },
    "Fe": {
        "name": "铁", "atomic_number": 26, "symbol": "Fe",
        "mass": 55.85, "group": "过渡金属", "period": 4,
        "electrons": "1s2 2s2 2p6 3s2 3p6 4s2 3d6", "valence": "2,3",
        "analogy": "像程序里的 '核心引擎' — 血红蛋白的核心, 也是工业文明的基础",
        "fun_fact": "地球核心主要是铁镍合金 — 整个地球就是个大铁球, 就像服务器的金属机箱"
    },
    "Cu": {
        "name": "铜", "atomic_number": 29, "symbol": "Cu",
        "mass": 63.55, "group": "过渡金属", "period": 4,
        "electrons": "1s2 2s2 2p6 3s2 3p6 4s1 3d10", "valence": "1,2",
        "analogy": "像程序里的 '高速总线' — 导电性仅次于银, 电线的主要材料",
        "fun_fact": "铜的导电性仅次于银, 但便宜多了 — 就像性价比最高的云服务器"
    },
    "Zn": {
        "name": "锌", "atomic_number": 30, "symbol": "Zn",
        "mass": 65.38, "group": "过渡金属", "period": 4,
        "electrons": "1s2 2s2 2p6 3s2 3p6 4s2 3d10", "valence": 2,
        "analogy": "像程序里的 '防腐层' — 镀锌防止铁生锈",
        "fun_fact": "锌是人体必需的微量元素, 缺锌会影响免疫力 — 就像缺少防火墙的服务器"
    },
    "Ag": {
        "name": "银", "atomic_number": 47, "symbol": "Ag",
        "mass": 107.87, "group": "过渡金属", "period": 5,
        "electrons": "[Kr] 4d10 5s1", "valence": 1,
        "analogy": "像程序里的 '顶级配置' — 导电性最好的金属, 但贵",
        "fun_fact": "银是导电性和导热性最好的金属 — 就像顶配CPU, 性能拉满但价格也拉满"
    }
}


# ═══════════════════════════════════════════════════════════════
# 数据库: 常见分子
# ═══════════════════════════════════════════════════════════════

MOLECULES = {
    "H2O": {
        "name": "水", "formula": "H2O",
        "atoms": {"H": 2, "O": 1},
        "bond_type": "极性共价键",
        "shape": "V形(角形)",
        "analogy": "像程序里的 '溶剂/环境' — 大多数反应都在水里进行, 就像大多数代码在操作系统里运行",
        "fun_fact": "水是唯一一种固态密度比液态小的常见物质 — 所以冰浮在水上, 就像注释浮在代码上面"
    },
    "CO2": {
        "name": "二氧化碳", "formula": "CO2",
        "atoms": {"C": 1, "O": 2},
        "bond_type": "极性共价键",
        "shape": "直线形",
        "analogy": "像程序里的 '输出/垃圾' — 呼吸的产物, 多了会导致温室效应",
        "fun_fact": "干冰就是固态二氧化碳, 直接从固体变气体(升华) — 就像内存泄漏, 看不见但一直在增加"
    },
    "NaCl": {
        "name": "氯化钠(食盐)", "formula": "NaCl",
        "atoms": {"Na": 1, "Cl": 1},
        "bond_type": "离子键",
        "shape": "面心立方晶体",
        "analogy": "像程序里的 '配对数据' — 钠丢一个电子给氯, 阴阳离子配对",
        "fun_fact": "食盐是离子晶体, 不是分子 — 就像数组, 每个Na周围有6个Cl, 反之亦然"
    },
    "HCl": {
        "name": "盐酸", "formula": "HCl",
        "atoms": {"H": 1, "Cl": 1},
        "bond_type": "极性共价键",
        "shape": "直线形",
        "analogy": "像程序里的 '强酸处理器' — 胃酸的主要成分, 能分解食物",
        "fun_fact": "浓盐酸在空气中会发烟 — 就像报错信息, 老远就能看到"
    },
    "NaOH": {
        "name": "氢氧化钠(烧碱)", "formula": "NaOH",
        "atoms": {"Na": 1, "O": 1, "H": 1},
        "bond_type": "离子键+共价键",
        "shape": "离子晶体",
        "analogy": "像程序里的 '强碱清理器' — 能溶解油脂, 做肥皂的原料",
        "fun_fact": "氢氧化钠碰到皮肤会滑溜溜的 — 因为它在溶解你的皮肤油脂, 赶紧洗!"
    },
    "CH4": {
        "name": "甲烷", "formula": "CH4",
        "atoms": {"C": 1, "H": 4},
        "bond_type": "非极性共价键",
        "shape": "正四面体",
        "analogy": "像程序里的 '最简结构' — 最简单的有机化合物",
        "fun_fact": "甲烷是天然气的主要成分, 也是温室气体 — 就像基础数据类型, 简单但无处不在"
    },
    "C2H5OH": {
        "name": "乙醇(酒精)", "formula": "C2H5OH",
        "atoms": {"C": 2, "H": 6, "O": 1},
        "bond_type": "共价键",
        "shape": "链状",
        "analogy": "像程序里的 '溶剂/兼容层' — 能溶解很多物质, 也能让大脑'兼容'奇怪的想法",
        "fun_fact": "酒精能和水以任意比例互溶 — 就像动态类型语言, 什么都能混在一起"
    },
    "NH3": {
        "name": "氨", "formula": "NH3",
        "atoms": {"N": 1, "H": 3},
        "bond_type": "极性共价键",
        "shape": "三角锥形",
        "analogy": "像程序里的 '碱性缓冲' — 能接受质子, 是重要的化工原料",
        "fun_fact": "氨有强烈刺激性气味 — 就像debug模式, 一开就知道哪里有问题"
    },
    "H2SO4": {
        "name": "硫酸", "formula": "H2SO4",
        "atoms": {"H": 2, "S": 1, "O": 4},
        "bond_type": "共价键",
        "shape": "四面体",
        "analogy": "像程序里的 '万能工具' — 工业之母, 几乎所有工业都要用",
        "fun_fact": "浓硫酸有脱水性, 能把糖变成黑炭 — 就像格式化硬盘, 数据直接没了"
    },
    "C6H12O6": {
        "name": "葡萄糖", "formula": "C6H12O6",
        "atoms": {"C": 6, "H": 12, "O": 6},
        "bond_type": "共价键",
        "shape": "环状(水溶液中)",
        "analogy": "像程序里的 '能量货币' — 细胞的主要能量来源",
        "fun_fact": "葡萄糖是生命的基本能量单位 — 就像程序的CPU周期, 做什么都要消耗"
    }
}


# ═══════════════════════════════════════════════════════════════
# 数据库: 化学反应
# ═══════════════════════════════════════════════════════════════

REACTIONS = {
    "acid_base": {
        "name": "酸碱中和反应",
        "equation": "HCl + NaOH → NaCl + H2O",
        "type": "复分解反应",
        "explanation": "酸中的H+和碱中的OH-结合生成水, 剩下的离子组成盐",
        "analogy": "就像两个程序交换变量 — HCl给NaOH一个H+, NaOH回一个OH-, 生成水和盐",
        "phenomenon": "放出热量, 溶液温度升高",
        "demo": True
    },
    "rusting": {
        "name": "铁的生锈",
        "equation": "4Fe + 3O2 + 6H2O → 4Fe(OH)3 → 2Fe2O3·3H2O",
        "type": "氧化还原反应",
        "explanation": "铁在潮湿空气中被氧气氧化, 生成铁锈(水合氧化铁)",
        "analogy": "就像代码没人维护会腐化 — 铁没人保护就会生锈",
        "phenomenon": "铁表面生成红棕色物质, 逐渐剥落",
        "demo": False
    },
    "photosynthesis": {
        "name": "光合作用",
        "equation": "6CO2 + 6H2O →(光/叶绿体) C6H12O6 + 6O2",
        "type": "氧化还原反应(还原CO2)",
        "explanation": "植物利用光能把二氧化碳和水转化为葡萄糖和氧气",
        "analogy": "就像太阳能电池板给电池充电 — 光能变成化学能储存起来",
        "phenomenon": "植物释放氧气, 合成有机物",
        "demo": False
    },
    "combustion_methane": {
        "name": "甲烷燃烧",
        "equation": "CH4 + 2O2 →(点燃) CO2 + 2H2O",
        "type": "氧化还原反应(燃烧)",
        "explanation": "甲烷和氧气反应, 完全燃烧生成二氧化碳和水, 放出大量热",
        "analogy": "就像程序执行完释放资源 — 甲烷的化学能转化为热能释放",
        "phenomenon": "产生蓝色火焰, 放出大量热",
        "demo": False
    },
    "electrolysis_water": {
        "name": "水的电解",
        "equation": "2H2O →(通电) 2H2↑ + O2↑",
        "type": "分解反应",
        "explanation": "通电使水分解为氢气和氧气",
        "analogy": "就像反编译 — 把生成物还原回原始物质",
        "phenomenon": "两极产生气泡, 负极气体是正极的2倍",
        "demo": True
    },
    "metal_acid": {
        "name": "金属与酸反应",
        "equation": "Zn + H2SO4 → ZnSO4 + H2↑",
        "type": "置换反应",
        "explanation": "活泼金属置换出酸中的氢, 生成盐和氢气",
        "analogy": "就像变量替换 — 锌原子替换了氢的位置",
        "phenomenon": "产生气泡(氢气), 金属逐渐溶解",
        "demo": True
    },
    "precipitation": {
        "name": "沉淀反应",
        "equation": "AgNO3 + NaCl → AgCl↓ + NaNO3",
        "type": "复分解反应",
        "explanation": "银离子和氯离子结合生成不溶于水的氯化银沉淀",
        "analogy": "就像两个API返回的数据中找到交集 — Ag+和Cl-碰到一起就'沉淀'出来",
        "phenomenon": "产生白色沉淀",
        "demo": True
    }
}


# ═══════════════════════════════════════════════════════════════
# 1. 元素周期表教程生成器
# ═══════════════════════════════════════════════════════════════

def generate_element_tutorial(output_path="chem_element_tutorial.py"):
    """生成元素周期表互动教程 Python 文件"""
    output_path = os.path.abspath(output_path)

    content = '''#!/usr/bin/env python3
"""
化学元素周期表互动教程 — 由 PyMsi.chem 生成
用程序员的思维来理解化学元素!

用法: python chem_element_tutorial.py
"""

import time
import sys
import random

ELEMENTS = ''' + json.dumps(ELEMENTS, ensure_ascii=False, indent=2) + '''

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║          ⚗️  化学元素周期表互动教程 ⚗️                        ║
║                                                              ║
║  用程序员的思维理解化学元素 — 每个元素都有编程类比!            ║
║  20个常见元素, 从氢到银, 让你一次搞懂!                        ║
╚══════════════════════════════════════════════════════════════╝
"""

def typewriter(text, delay=0.02):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\\n")

def teach_element(symbol, data):
    print(f"\\n{'═' * 50}")
    typewriter(f"⚛️  {data['name']} ({data['symbol']}) — 原子序数 {data['atomic_number']}")
    print(f"{'═' * 50}")

    typewriter(f"\\n📊 基本信息:")
    print(f"   • 原子质量: {data['mass']} u")
    print(f"   • 元素类别: {data['group']}")
    print(f"   • 周期: 第{data['period']}周期")
    print(f"   • 价电子数: {data['valence']}")
    print(f"   • 电子排布: {data['electrons']}")
    time.sleep(0.3)

    typewriter(f"\\n💡 程序员类比: {data['analogy']}")
    time.sleep(0.5)

    typewriter(f"\\n🌟 趣味知识: {data['fun_fact']}")
    time.sleep(0.5)

    input("\\n按回车继续...")

def quiz():
    print("\\n" + "=" * 60)
    typewriter("📝 课后小测验! 看看你记住了多少~\\n")

    questions = [
        {
            "q": "哪个元素是宇宙中含量最多的?",
            "options": ["A) 氧", "B) 碳", "C) 氢", "D) 氦"],
            "answer": "C"
        },
        {
            "q": "哪个元素是计算机芯片的主要材料?",
            "options": ["A) 铁", "B) 硅", "C) 铝", "D) 铜"],
            "answer": "B"
        },
        {
            "q": "导电性最好的金属是?",
            "options": ["A) 铜", "B) 金", "C) 铝", "D) 银"],
            "answer": "D"
        },
        {
            "q": "氯化钠(食盐)是什么键?",
            "options": ["A) 共价键", "B) 离子键", "C) 金属键", "D) 氢键"],
            "answer": "B"
        },
        {
            "q": "哪个元素遇水反应最剧烈?",
            "options": ["A) 钠", "B) 镁", "C) 钾", "D) 钙"],
            "answer": "C"
        }
    ]

    score = 0
    for i, item in enumerate(questions):
        print(f"\\n第{i+1}题: {item['q']}")
        for opt in item['options']:
            print(f"   {opt}")
        ans = input("你的答案: ").strip().upper()
        if ans == item['answer']:
            print("✅ 正确!")
            score += 1
        else:
            print(f"❌ 错误! 答案是 {item['answer']}")

    print(f"\\n成绩: {score}/{len(questions)}")
    if score == len(questions):
        print("🏆 全对! 你是化学天才!")
    elif score >= len(questions) * 0.6:
        print("👍 不错! 化学入门成功!")
    else:
        print("😅 加油! 再看一遍教程吧~")

def main():
    print(BANNER)
    time.sleep(0.5)
    typewriter("这个教程会带你认识20个常见化学元素...")
    typewriter("每个元素都有程序员能听懂的类比!\\n")
    time.sleep(0.5)

    choice = input("按回车按顺序学习, 输入 'random' 随机学习: ").strip().lower()
    print()

    symbols = list(ELEMENTS.keys())
    if choice == "random":
        random.shuffle(symbols)

    for sym in symbols:
        teach_element(sym, ELEMENTS[sym])

    print("\\n" + "=" * 60)
    typewriter("🎉 恭喜! 你已经认识了20个常见元素!")
    typewriter("记住: 化学元素就像编程的基本类型 — 不同的组合产生无限可能!")
    print("=" * 60)

    quiz()

if __name__ == "__main__":
    main()
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[chem] 元素教程已生成: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 2. 分子结构教程生成器
# ═══════════════════════════════════════════════════════════════

def generate_molecule_tutorial(output_path="chem_molecule_tutorial.py"):
    """生成分子结构互动教程 Python 文件"""
    output_path = os.path.abspath(output_path)

    content = '''#!/usr/bin/env python3
"""
分子结构互动教程 — 由 PyMsi.chem 生成
用数据结构的思维理解分子!

用法: python chem_molecule_tutorial.py
"""

import time
import sys

MOLECULES = ''' + json.dumps(MOLECULES, ensure_ascii=False, indent=2) + '''

def typewriter(text, delay=0.02):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\\n")

def teach_molecule(formula, data):
    print(f"\\n{'═' * 50}")
    typewriter(f"🧪 {data['name']} ({data['formula']})")
    print(f"{'═' * 50}")

    typewriter(f"\\n📊 基本信息:")
    print(f"   • 化学键类型: {data['bond_type']}")
    print(f"   • 空间结构: {data['shape']}")
    print(f"   • 组成原子: {', '.join(f'{k}×{v}' for k,v in data['atoms'].items())}")
    time.sleep(0.3)

    typewriter(f"\\n💡 程序员类比: {data['analogy']}")
    time.sleep(0.5)

    typewriter(f"\\n🌟 趣味知识: {data['fun_fact']}")
    time.sleep(0.5)

    input("\\n按回车继续...")

def main():
    print("\\n" + "=" * 60)
    print("  🧬 分子结构互动教程")
    print("  用数据结构的思维理解分子!")
    print("=" * 60)

    for formula, data in MOLECULES.items():
        teach_molecule(formula, data)

    print("\\n" + "=" * 60)
    print("🎉 恭喜! 你已经了解了10种常见分子!")
    print("记住: 分子就像数据结构 — 原子是字段, 化学键是引用关系")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[chem] 分子教程已生成: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 3. 化学反应模拟器
# ═══════════════════════════════════════════════════════════════

def generate_reaction_simulator(output_path="chem_reaction_sim.py"):
    """生成化学反应模拟器 Python 文件"""
    output_path = os.path.abspath(output_path)

    content = '''#!/usr/bin/env python3
"""
化学反应模拟器 — 由 PyMsi.chem 生成
模拟各种化学反应, 看现象学原理!

用法: python chem_reaction_sim.py
"""

import time
import sys

REACTIONS = ''' + json.dumps(REACTIONS, ensure_ascii=False, indent=2) + '''

def typewriter(text, delay=0.02):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\\n")

def show_reaction(key, data):
    print(f"\\n{'═' * 60}")
    typewriter(f"⚗️  {data['name']}")
    print(f"{'═' * 60}")

    typewriter(f"\\n📝 化学方程式: {data['equation']}")
    typewriter(f"📌 反应类型: {data['type']}")
    time.sleep(0.3)

    typewriter(f"\\n🔬 反应原理: {data['explanation']}")
    time.sleep(0.5)

    typewriter(f"💡 程序员类比: {data['analogy']}")
    time.sleep(0.5)

    typewriter(f"\\n👀 实验现象: {data['phenomenon']}")
    time.sleep(0.5)

    # 模拟动画
    if data['demo']:
        typewriter("\\n🎬 反应模拟:")
        simulate_animation(key)

    input("\\n按回车继续...")

def simulate_animation(key):
    """简单的文本动画模拟反应"""
    if key == "acid_base":
        print("  HCl + NaOH → NaCl + H2O")
        time.sleep(0.5)
        print("  [H+]  +  [OH-]  →  H2O  💧")
        time.sleep(0.5)
        print("  💥 放出热量! 温度升高! 🌡️↑")
    elif key == "electrolysis_water":
        print("  H2O →(通电) H2↑ + O2↑")
        time.sleep(0.5)
        print("  ⚡ 负极: 2H+ + 2e- → H2  💨💨")
        time.sleep(0.3)
        print("  ⚡ 正极: 2O²⁻ - 4e- → O2  💨")
        time.sleep(0.3)
        print("  💡 负极气体体积是正极的2倍!")
    elif key == "metal_acid":
        print("  Zn + H2SO4 → ZnSO4 + H2↑")
        time.sleep(0.5)
        print("  ⚗️  锌粒表面产生气泡... 💨💨💨")
        time.sleep(0.3)
        print("  📉 锌粒逐渐溶解... 变小...")
        time.sleep(0.3)
        print("  🔥 溶液温度升高 (放热反应)")
    elif key == "precipitation":
        print("  AgNO3 + NaCl → AgCl↓ + NaNO3")
        time.sleep(0.5)
        print("  Ag+ + Cl- → AgCl↓  ⬇️⬇️⬇️")
        time.sleep(0.3)
        print("  🤍 产生白色沉淀!")
        time.sleep(0.3)
        print("  (沉淀物沉到试管底部)")

def main():
    print("\\n" + "=" * 60)
    print("  ⚗️  化学反应模拟器")
    print("  7个经典化学反应, 看动画学原理!")
    print("=" * 60)

    for key, data in REACTIONS.items():
        show_reaction(key, data)

    print("\\n" + "=" * 60)
    print("🎉 恭喜! 你已经了解了7个经典化学反应!")
    print("记住: 化学反应就像函数调用 — 输入反应物, 输出产物, 伴随能量变化")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[chem] 反应模拟器已生成: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 4. 溶液浓度计算器
# ═══════════════════════════════════════════════════════════════

def molarity(mass_g, molar_mass, volume_L):
    """计算摩尔浓度 (mol/L)

    Args:
        mass_g: float      溶质质量 (g)
        molar_mass: float  摩尔质量 (g/mol)
        volume_L: float    溶液体积 (L)

    Returns:
        float  摩尔浓度 (mol/L)
    """
    moles = mass_g / molar_mass
    conc = moles / volume_L
    print(f"[chem] 溶质: {mass_g}g ÷ {molar_mass}g/mol = {moles:.3f} mol")
    print(f"[chem] 浓度: {moles:.3f} mol ÷ {volume_L} L = {conc:.3f} mol/L")
    return conc


def ph_from_hplus(hplus_conc):
    """从氢离子浓度计算 pH

    Args:
        hplus_conc: float  H+ 浓度 (mol/L)

    Returns:
        float  pH 值
    """
    import math
    ph = -math.log10(hplus_conc)
    print(f"[chem] [H+] = {hplus_conc} mol/L")
    print(f"[chem] pH = -log10({hplus_conc}) = {ph:.2f}")
    return ph


def ph_from_ohminus(ohminus_conc):
    """从氢氧根离子浓度计算 pH

    Args:
        ohminus_conc: float  OH- 浓度 (mol/L)

    Returns:
        float  pH 值
    """
    import math
    kw = 1.0e-14  # 水的离子积
    hplus = kw / ohminus_conc
    ph = -math.log10(hplus)
    print(f"[chem] [OH-] = {ohminus_conc} mol/L")
    print(f"[chem] [H+] = Kw / [OH-] = 1e-14 / {ohminus_conc} = {hplus:.2e} mol/L")
    print(f"[chem] pH = {ph:.2f}")
    return ph


def solution_calculator():
    """交互式溶液浓度计算器 (终端运行)"""
    import math

    print("\\n" + "=" * 50)
    print("  🧪 溶液浓度计算器")
    print("=" * 50)
    print("  1. 摩尔浓度计算")
    print("  2. pH 计算 (从 H+ 浓度)")
    print("  3. pH 计算 (从 OH- 浓度)")
    print("=" * 50)

    choice = input("选择功能 (1-3): ").strip()

    if choice == "1":
        mass = float(input("溶质质量 (g): "))
        mm = float(input("溶质摩尔质量 (g/mol): "))
        vol = float(input("溶液体积 (L): "))
        molarity(mass, mm, vol)
    elif choice == "2":
        conc = float(input("H+ 浓度 (mol/L): "))
        ph_from_hplus(conc)
    elif choice == "3":
        conc = float(input("OH- 浓度 (mol/L): "))
        ph_from_ohminus(conc)
    else:
        print("无效选择!")


# ═══════════════════════════════════════════════════════════════
# 5. 化学方程式配平 (简单版)
# ═══════════════════════════════════════════════════════════════

def balance_equation(equation):
    """尝试配平简单的化学方程式 (演示用, 支持基础反应)

    Args:
        equation: str  形如 "H2+O2=H2O" 或 "Fe+O2=Fe2O3"

    Returns:
        str  配平后的方程式
    """
    # 简单的解析和配平 (演示用, 支持常见反应)
    if "=" not in equation:
        raise ValueError("方程式需要用 = 分隔反应物和生成物")

    left_str, right_str = equation.split("=", 1)
    left = [x.strip() for x in left_str.split("+")]
    right = [x.strip() for x in right_str.split("+")]

    print(f"[chem] 原方程式: {equation}")
    print(f"[chem] 反应物: {left}")
    print(f"[chem] 生成物: {right}")

    # 内置一些已知配平 (演示用)
    known = {
        "H2+O2=H2O": "2H2 + O2 = 2H2O",
        "Fe+O2=Fe2O3": "4Fe + 3O2 = 2Fe2O3",
        "C+O2=CO2": "C + O2 = CO2",
        "N2+H2=NH3": "N2 + 3H2 = 2NH3",
        "Al+O2=Al2O3": "4Al + 3O2 = 2Al2O3",
        "Mg+O2=MgO": "2Mg + O2 = 2MgO",
        "Na+Cl2=NaCl": "2Na + Cl2 = 2NaCl",
        "HCl+NaOH=NaCl+H2O": "HCl + NaOH = NaCl + H2O",
        "Zn+HCl=ZnCl2+H2": "Zn + 2HCl = ZnCl2 + H2↑",
        "CH4+O2=CO2+H2O": "CH4 + 2O2 = CO2 + 2H2O",
    }

    # 规范化键
    norm_key = equation.replace(" ", "")
    if norm_key in known:
        balanced = known[norm_key]
        print(f"[chem] 配平结果: {balanced}")
        return balanced

    print(f"[chem] ⚠️  这个方程式暂不支持自动配平")
    print(f"[chem] 💡 支持的方程式: H2+O2=H2O, Fe+O2=Fe2O3, C+O2=CO2, N2+H2=NH3, 等")
    return equation


# ═══════════════════════════════════════════════════════════════
# 6. 模块包装类
# ═══════════════════════════════════════════════════════════════

class _ChemistryModule:
    """PyMsi.chem — ⚗️  化学教育模块 (v1.6.0 Education Plus)

    专为程序员设计的化学教学工具:

    1. 元素周期表 — 20个常见元素, 每个都有编程类比
    2. 分子结构 — 10种常见分子, 用数据结构类比
    3. 化学反应 — 7个经典反应, 带动画模拟
    4. 溶液计算 — 摩尔浓度、pH值计算器
    5. 方程式配平 — 简单化学方程式配平

    用法:
        PM.chem.element()          # 元素周期表教程
        PM.chem.molecule()         # 分子结构教程
        PM.chem.reaction()         # 化学反应模拟器
        PM.chem.solution()         # 溶液计算器 (交互式)
        PM.chem.balance("H2+O2=H2O")  # 配平方程式
        PM.chem.molarity(10, 40, 0.5)  # 摩尔浓度计算
        PM.chem.ph(0.001)          # pH计算
        PM.chem.list_elements()    # 列出所有元素
    """

    def __init__(self):
        self.output_dir = "."

    def __repr__(self):
        return "<PyMsi.chem [化学教育模块] v1.6.0 Education Plus>"

    def element(self, output=None):
        """生成元素周期表互动教程"""
        if output is None:
            output = "chem_element_tutorial.py"
        return generate_element_tutorial(output)

    def molecule(self, output=None):
        """生成分子结构互动教程"""
        if output is None:
            output = "chem_molecule_tutorial.py"
        return generate_molecule_tutorial(output)

    def reaction(self, output=None):
        """生成化学反应模拟器"""
        if output is None:
            output = "chem_reaction_sim.py"
        return generate_reaction_simulator(output)

    def solution(self):
        """运行交互式溶液浓度计算器"""
        return solution_calculator()

    def balance(self, equation):
        """配平化学方程式"""
        return balance_equation(equation)

    def molarity(self, mass_g, molar_mass, volume_L):
        """计算摩尔浓度"""
        return molarity(mass_g, molar_mass, volume_L)

    def ph(self, hplus_conc):
        """从 H+ 浓度计算 pH"""
        return ph_from_hplus(hplus_conc)

    def ph_from_oh(self, ohminus_conc):
        """从 OH- 浓度计算 pH"""
        return ph_from_ohminus(ohminus_conc)

    def list_elements(self):
        """列出所有元素"""
        print("\n⚛️  元素列表 (20个常见元素):")
        print("─" * 60)
        for sym, data in ELEMENTS.items():
            print(f"  {sym:4s} {data['name']:4s} | {data['group']:10s} | "
                  f"原子序数 {data['atomic_number']:2d} | 质量 {data['mass']:.2f}")

    def list_molecules(self):
        """列出所有分子"""
        print("\n🧪 分子列表 (10种常见分子):")
        print("─" * 60)
        for formula, data in MOLECULES.items():
            print(f"  {formula:10s} {data['name']} | {data['bond_type']} | {data['shape']}")


# ═══════════════════════════════════════════════════════════════
# 自测
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    generate_element_tutorial('/tmp/test_chem_elem.py')
    generate_molecule_tutorial('/tmp/test_chem_mol.py')
    generate_reaction_simulator('/tmp/test_chem_react.py')

    print()
    print("=== 摩尔浓度测试 ===")
    molarity(10, 40, 0.5)  # 10g NaOH (40g/mol) in 0.5L = 0.5 mol/L

    print()
    print("=== pH 测试 ===")
    ph_from_hplus(0.001)  # pH = 3
    ph_from_ohminus(0.001)  # pH = 11

    print()
    print("=== 配平测试 ===")
    balance_equation("H2+O2=H2O")
    balance_equation("Fe+O2=Fe2O3")

    print()
    print("化学模块测试通过!")
