"""
bio.py — 生物教育模块 (v1.5.9 Education Edition)

专为程序员设计的生物学教学工具:
  1. 细胞结构 — 生成 Python 文件, 运行后在终端输出互动式教程
  2. 蛋白质系统 — 生成蛋白质文件, 可被酶催化/加热变性
  3. 酶系统 — 酶文件可催化对应蛋白质, 加热失活

用法:
  import PyMsi as PM
  PM.bio.cell()                    # 生成细胞结构教程
  PM.bio.protein("hemoglobin")     # 生成血红蛋白文件
  PM.bio.enzyme("pepsin")          # 生成胃蛋白酶文件
  PM.bio.denature("hemoglobin.protein", temp=70)  # 加热变性
  PM.bio.catalyze("pepsin.enzyme", "casein.protein")  # 酶催化
"""

import os
import json
import random


# ═══════════════════════════════════════════════════════════════
# 数据库: 细胞结构
# ═══════════════════════════════════════════════════════════════

CELL_STRUCTURE = {
    "cell_membrane": {
        "name": "细胞膜",
        "english": "Cell Membrane",
        "function": "控制物质进出, 保护细胞内部环境",
        "analogy": "像程序里的防火墙, 只允许特定端口(IP/端口)的连接通过",
        "components": ["磷脂双分子层", "蛋白质通道", "糖蛋白"],
        "key_concept": "选择透过性 — 不是什么都能进来的, 就像 API 需要认证"
    },
    "cytoplasm": {
        "name": "细胞质",
        "english": "Cytoplasm",
        "function": "细胞内各种反应的场所, 悬浮细胞器",
        "analogy": "像程序的运行时环境(Runtime), 所有代码都在这里执行",
        "components": ["细胞质基质", "各种细胞器"],
        "key_concept": "一切生命活动的基础 — 没有它细胞就是个空壳"
    },
    "nucleus": {
        "name": "细胞核",
        "english": "Nucleus",
        "function": "储存遗传信息(DNA), 控制细胞活动",
        "analogy": "像程序的 main() 函数 + 配置文件, 控制一切运行",
        "components": ["核膜", "核仁", "染色质(DNA+组蛋白)", "核液"],
        "key_concept": "DNA 就是源代码, 细胞核就是存放源码的仓库"
    },
    "mitochondria": {
        "name": "线粒体",
        "english": "Mitochondria",
        "function": "细胞的有氧呼吸场所, 产生 ATP(能量)",
        "analogy": "像程序的电源/电池模块, 为整个系统供能",
        "components": ["外膜", "内膜(嵴)", "基质", "线粒体DNA"],
        "key_concept": "ATP = 能量的货币单位, 就像程序的电费"
    },
    "ribosome": {
        "name": "核糖体",
        "english": "Ribosome",
        "function": "合成蛋白质的工厂, 按 mRNA 指令翻译",
        "analogy": "像编译器(Compiler), 把 mRNA(中间代码)翻译成蛋白质(可执行文件)",
        "components": ["大亚基", "小亚基", "rRNA"],
        "key_concept": "翻译过程: mRNA → 蛋白质, 就像编译: 源码 → 二进制"
    },
    "endoplasmic_reticulum": {
        "name": "内质网",
        "english": "Endoplasmic Reticulum (ER)",
        "function": "蛋白质合成(粗面)和脂质合成(光面)的场所",
        "analogy": "像程序的后台任务队列, 分两类任务: 粗面ER(蛋白质)和光面ER(脂质)",
        "components": ["粗面内质网(有核糖体)", "光面内质网(无核糖体)"],
        "key_concept": "粗面有核糖体=生产线, 光面=脂质合成线"
    },
    "golgi_apparatus": {
        "name": "高尔基体",
        "english": "Golgi Apparatus",
        "function": "加工、分类、包装蛋白质, 运送到目的地",
        "analogy": "像程序的 CI/CD 管道, 加工打包后分发到各个部署目标",
        "components": ["顺面(接收)", "中间囊", "反面(输出)"],
        "key_concept": "蛋白质的物流中心 — 收货、加工、打包、发货"
    },
    "lysosome": {
        "name": "溶酶体",
        "english": "Lysosome",
        "function": "分解衰老细胞器和外来物质, 含多种水解酶",
        "analogy": "像程序的垃圾回收器(GC), 自动清理不需要的对象",
        "components": ["酸性水解酶", "膜"],
        "key_concept": "细胞内的回收站 — 什么东西不要了就丢进去分解"
    },
    "chloroplast": {
        "name": "叶绿体",
        "english": "Chloroplast",
        "function": "植物细胞特有, 进行光合作用, 把光能转为化学能",
        "analogy": "像太阳能充电板, 把光能转成电能(ATP)储存起来",
        "components": ["外膜", "内膜", "基质", "类囊体", "叶绿素"],
        "key_concept": "光合作用: 光能 + CO2 + H2O → 葡萄糖 + O2"
    },
    "vacuole": {
        "name": "液泡",
        "english": "Vacuole",
        "function": "储存水分、营养物质和废物, 维持细胞渗透压",
        "analogy": "像程序的缓存(Cache)/临时存储区",
        "components": ["液泡膜", "细胞液"],
        "key_concept": "大液泡让植物细胞保持膨胀, 就像内存让程序跑得快"
    },
    "cell_wall": {
        "name": "细胞壁",
        "english": "Cell Wall",
        "function": "植物/真菌/细菌特有, 提供结构支撑和保护",
        "analogy": "像程序的容器(Docker), 给细胞一个固定的运行边界",
        "components": ["纤维素(植物)", "肽聚糖(细菌)", "几丁质(真菌)"],
        "key_concept": "不是所有细胞都有 — 动物细胞没有细胞壁"
    }
}


# ═══════════════════════════════════════════════════════════════
# 数据库: 蛋白质
# ═══════════════════════════════════════════════════════════════

PROTEINS = {
    "trypsin": {
        "name": "胰蛋白",
        "english": "Trypsin",
        "type": "消化酶",
        "function": "在胰腺分泌, 分解食物中的蛋白质为小肽和氨基酸",
        "denature_temp": 55,
        "optimal_temp": 37,
        "optimal_ph": 8.0,
        "structure": "球状蛋白, 由二硫键稳定的三级结构",
        "fun_fact": "胰蛋白在胰腺里是'胰蛋白酶原'(没活性的前体), 到了小肠才被激活 — 就像未编译的源代码"
    },
    "keratin": {
        "name": "角蛋白",
        "english": "Keratin",
        "type": "结构蛋白",
        "function": "构成毛发、指甲、皮肤角质层的主要蛋白",
        "denature_temp": 140,
        "optimal_temp": None,
        "optimal_ph": None,
        "structure": "纤维状蛋白, 大量二硫键, 极其稳定",
        "fun_fact": "角蛋白的二硫键比普通蛋白质多得多, 所以头发很难被拉断 — 也很难被烫直(需要打断二硫键)"
    },
    "casein": {
        "name": "酪蛋白",
        "english": "Casein",
        "type": "储存蛋白",
        "function": "牛奶中的主要蛋白质, 为幼崽提供氨基酸和钙",
        "denature_temp": 80,
        "optimal_temp": 37,
        "optimal_ph": 4.6,
        "structure": "磷蛋白, 含磷酸基团, 可结合钙离子",
        "fun_fact": "酸奶就是因为乳酸菌产酸让酪蛋白在 pH 4.6 变性凝固形成的"
    },
    "hemoglobin": {
        "name": "血红蛋白",
        "english": "Hemoglobin",
        "type": "运输蛋白",
        "function": "在红细胞中运输氧气和二氧化碳",
        "denature_temp": 65,
        "optimal_temp": 37,
        "optimal_ph": 7.4,
        "structure": "4个亚基(2个alpha+2个beta), 每个含一个血红素基团(铁离子)",
        "fun_fact": "血红蛋白有4个氧结合位点, 结合氧时有协同效应 — 就像多线程并发, 一个结合了其他的亲和力也会变"
    },
    "albumin": {
        "name": "血清蛋白",
        "english": "Serum Albumin",
        "type": "运输蛋白",
        "function": "血液中含量最多的蛋白, 维持渗透压, 运输脂肪酸等",
        "denature_temp": 60,
        "optimal_temp": 37,
        "optimal_ph": 7.4,
        "structure": "球状蛋白, 心形结构, 有多个疏水结合口袋",
        "fun_fact": "血清蛋白是血液中的'快递车', 什么脂溶性物质都能搭载 — 就像一个通用 API 接口"
    },
    "ferritin": {
        "name": "储存蛋白",
        "english": "Ferritin",
        "type": "储存蛋白",
        "function": "储存铁离子, 防止铁过载中毒",
        "denature_temp": 75,
        "optimal_temp": 37,
        "optimal_ph": 7.4,
        "structure": "球形壳状蛋白, 内部空腔可存4500个铁原子",
        "fun_fact": "铁蛋白就像程序的缓存池 — 当铁多的时候存起来, 缺铁的时候释放"
    },
    "collagen": {
        "name": "胶原蛋白",
        "english": "Collagen",
        "type": "结构蛋白",
        "function": "构成皮肤、骨骼、肌腱、血管的主要结构蛋白",
        "denature_temp": 60,
        "optimal_temp": 37,
        "optimal_ph": 7.4,
        "structure": "三股螺旋, 由甘氨酸-脯氨酸-羟脯氨酸重复序列构成",
        "fun_fact": "胶原蛋白变性后就是明胶 — 你吃的果冻就是变性后的胶原蛋白"
    },
    "myosin": {
        "name": "肌球蛋白",
        "english": "Myosin",
        "type": "运动蛋白",
        "function": "肌肉收缩的主要蛋白, 与肌动蛋白协同产生运动",
        "denature_temp": 50,
        "optimal_temp": 37,
        "optimal_ph": 7.0,
        "structure": "双头结构, 有ATP酶活性, 长尾可形成粗丝",
        "fun_fact": "肌球蛋白像两个'小手'抓住肌动蛋白丝往前走, 消耗ATP — 就像程序里的工作线程在消费消息队列"
    },
    "membrane_protein": {
        "name": "膜蛋白",
        "english": "Membrane Protein",
        "type": "功能蛋白",
        "function": "镶嵌在细胞膜中, 负责信号传递、物质运输、能量转换",
        "denature_temp": 70,
        "optimal_temp": 37,
        "optimal_ph": 7.4,
        "structure": "疏水跨膜区(通常alpha螺旋), 亲水胞内/外区",
        "fun_fact": "膜蛋白就像服务器的端口监听程序, 负责接收外部信号并传递到细胞内部"
    },
    "histone": {
        "name": "组蛋白",
        "english": "Histone",
        "type": "结构蛋白",
        "function": "与DNA结合形成核小体, 帮助DNA压缩染色质",
        "denature_temp": 85,
        "optimal_temp": 37,
        "optimal_ph": 7.4,
        "structure": "八聚体核心(H2A/H2B/H3/H4各两个), DNA缠绕其上",
        "fun_fact": "组蛋白就像代码的缩进格式化 — 没有它DNA就是一团乱码, 有了它才能整齐地折叠"
    }
}


# ═══════════════════════════════════════════════════════════════
# 数据库: 酶 (与蛋白质对应)
# ═══════════════════════════════════════════════════════════════

ENZYMES = {
    "trypsin_enzyme": {
        "name": "胰蛋白酶",
        "english": "Trypsin Enzyme",
        "target_protein": "casein",
        "target_name": "酪蛋白",
        "function": "催化水解蛋白质中的赖氨酸和精氨酸的肽键",
        "optimal_temp": 37,
        "optimal_ph": 8.0,
        "inactivation_temp": 55,
        "mechanism": "专一性切割碱性氨基酸的肽键, 产物为小肽和氨基酸",
        "analogy": "就像正则表达式的精确匹配 — 只在特定位置(Lys/Arg后面)切割"
    },
    "pepsin": {
        "name": "胃蛋白酶",
        "english": "Pepsin",
        "target_protein": "casein",
        "target_name": "酪蛋白",
        "function": "在胃中酸性环境下分解蛋白质",
        "optimal_temp": 37,
        "optimal_ph": 2.0,
        "inactivation_temp": 70,
        "mechanism": "酸性条件下催化水解芳香族氨基酸的肽键",
        "analogy": "像在极端环境(酸性=低pH)下才能运行的脚本 — 换个环境就不工作了"
    },
    "pepsin_for_collagen": {
        "name": "胃蛋白酶(胶原)",
        "english": "Pepsin (Collagen)",
        "target_protein": "collagen",
        "target_name": "胶原蛋白",
        "function": "可以部分水解胶原蛋白的三股螺旋",
        "optimal_temp": 37,
        "optimal_ph": 2.0,
        "inactivation_temp": 70,
        "mechanism": "在酸性条件下切割胶原蛋白的肽键, 但三股螺旋部分抵抗",
        "analogy": "像对压缩文件做部分解压 — 只能解开一部分, 核心结构还在"
    },
    "amylase": {
        "name": "淀粉酶",
        "english": "Amylase",
        "target_protein": None,
        "target_name": "淀粉(非蛋白质)",
        "function": "催化水解淀粉中的糖苷键, 产生麦芽糖和葡萄糖",
        "optimal_temp": 37,
        "optimal_ph": 6.8,
        "inactivation_temp": 65,
        "mechanism": "切割淀粉(alpha-1,4糖苷键), 不是蛋白质而是糖类",
        "analogy": "像字符串分割函数 split() — 把长链淀粉切成小段糖"
    },
    "protease_k": {
        "name": "蛋白酶K",
        "english": "Proteinase K",
        "target_protein": "keratin",
        "target_name": "角蛋白",
        "function": "强力蛋白酶, 能分解角蛋白等难降解蛋白",
        "optimal_temp": 50,
        "optimal_ph": 7.5,
        "inactivation_temp": 100,
        "mechanism": "广谱切割, 在高温下仍保持活性, 能破坏二硫键稳定蛋白",
        "analogy": "像万能调试器 — 几乎什么蛋白质都能拆, 而且耐高温"
    },
    "thrombin": {
        "name": "凝血酶",
        "english": "Thrombin",
        "target_protein": "fibrinogen",
        "target_name": "纤维蛋白原(血液蛋白)",
        "function": "将纤维蛋白原转化为纤维蛋白, 形成血凝块",
        "optimal_temp": 37,
        "optimal_ph": 7.4,
        "inactivation_temp": 50,
        "mechanism": "精确切割纤维蛋白原的特定肽键, 暴露聚合位点",
        "analogy": "像触发器(trigger) — 一旦激活就启动级联反应(凝血级联)"
    },
    "helicase_like": {
        "name": "解旋酶(类)",
        "english": "Helicase-like",
        "target_protein": "histone",
        "target_name": "组蛋白",
        "function": "在DNA复制时帮助解开组蛋白-DNA复合体",
        "optimal_temp": 37,
        "optimal_ph": 7.4,
        "inactivation_temp": 50,
        "mechanism": "消耗ATP, 沿DNA移动, 推开组蛋白让DNA解旋",
        "analogy": "像代码格式化工具 — 把紧凑折叠的DNA展开, 方便复制和转录"
    },
    "atpase": {
        "name": "ATP酶",
        "english": "ATPase",
        "target_protein": "myosin",
        "target_name": "肌球蛋白",
        "function": "肌球蛋白本身就含ATP酶活性, 水解ATP产生运动力",
        "optimal_temp": 37,
        "optimal_ph": 7.0,
        "inactivation_temp": 50,
        "mechanism": "ATP结合→水解→构象变化→动力产生→ADP释放, 循环往复",
        "analogy": "像程序的事件循环(Event Loop) — 每次ATP水解就是一个tick, 推动肌肉收缩"
    }
}


# ═══════════════════════════════════════════════════════════════
# 1. 细胞结构教程生成器
# ═══════════════════════════════════════════════════════════════

def generate_cell_tutorial(output_path="cell_tutorial.py"):
    """生成一个互动式细胞结构教程 Python 文件

    运行生成的文件后, 会在终端逐步输出各种细胞结构的教程,
    用程序员能听懂的类比来讲解。

    Args:
        output_path: str  输出文件路径

    Returns:
        str  生成的文件路径
    """
    output_path = os.path.abspath(output_path)

    content = '''#!/usr/bin/env python3
"""
细胞结构互动教程 — 由 PyMsi.bio 生成
运行后会逐步输出各种细胞结构的讲解, 用程序员的思维理解生物!

用法: python cell_tutorial.py
"""

import time
import sys

CELL_DATA = ''' + json.dumps(CELL_STRUCTURE, ensure_ascii=False, indent=2) + '''

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║          🔬 欢迎来到细胞结构互动教程 🔬                       ║
║                                                              ║
║  本教程专为程序员设计, 用你熟悉的概念来讲解生物学!              ║
║  每个细胞结构都会用编程类比来解释, 保证你能看懂!               ║
╚══════════════════════════════════════════════════════════════╝
"""

def typewriter(text, delay=0.02):
    \"\"\"打字机效果输出\"\"\"
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\\n")

def section_break():
    print("\\n" + "=" * 60 + "\\n")

def teach_structure(key, data):
    \"\"\"讲解一个细胞结构\"\"\"
    print(f"\\n{'─' * 50}")
    typewriter(f"📋 {data['name']} ({data['english']})")
    print(f"{'─' * 50}")

    typewriter(f"\\n📝 功能: {data['function']}")
    time.sleep(0.3)

    typewriter(f"\\n💡 程序员类比: {data['analogy']}")
    time.sleep(0.3)

    typewriter(f"\\n🔧 组成成分:")
    for comp in data['components']:
        print(f"   • {comp}")
    time.sleep(0.3)

    typewriter(f"\\n⭐ 核心概念: {data['key_concept']}")
    time.sleep(0.5)

    input("\\n按回车继续...")
    print()

def quiz():
    \"\"\"课后小测验\"\"\"
    section_break()
    typewriter("📝 课后小测验!")
    typewriter("下面有3道题, 看看你学会了没有~\\n")

    questions = [
        {
            "q": "细胞膜的作用相当于程序里的什么?",
            "options": ["A) 数据库", "B) 防火墙", "C) 编译器", "D) 回收站"],
            "answer": "B"
        },
        {
            "q": "核糖体的功能类似于程序里的什么?",
            "options": ["A) 编译器", "B) 垃圾回收器", "C) 缓存", "D) 容器"],
            "answer": "A"
        },
        {
            "q": "溶酶体相当于程序里的什么?",
            "options": ["A) 电源", "B) 日志系统", "C) 垃圾回收器", "D) API接口"],
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
        print("🏆 全对! 你已经入门细胞生物学了!")
    elif score >= 2:
        print("👍 不错! 再看看教程就完全掌握了!")
    else:
        print("😅 加油! 多看几遍类比就懂了~")

def main():
    print(BANNER)
    time.sleep(0.5)
    typewriter("这个教程会带你了解细胞的11个核心结构...")
    typewriter("每个结构都会用程序员的思维来解释, 保证你能看懂!\\n")
    time.sleep(0.5)

    input("准备好了吗? 按回车开始! 🚀")

    for key, data in CELL_DATA.items():
        teach_structure(key, data)

    section_break()
    typewriter("🎉 恭喜! 你已经了解了细胞的所有核心结构!")
    typewriter("记住: 细胞就是一个精密的生物计算机!")
    typewriter("  • 细胞核 = 源码仓库 (DNA)")
    typewriter("  • 核糖体 = 编译器 (翻译蛋白质)")
    typewriter("  • 线粒体 = 电源 (产生ATP)")
    typewriter("  • 细胞膜 = 防火墙 (控制进出)")
    typewriter("  • 溶酶体 = 垃圾回收器 (分解废物)")

    quiz()

    print("\\n" + "=" * 60)
    print("教程结束! 感谢使用 PyMsi.bio 教育版!")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[bio] 细胞结构教程已生成: {output_path}")
    print(f"[bio] 运行方式: python {os.path.basename(output_path)}")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 2. 蛋白质文件生成器
# ═══════════════════════════════════════════════════════════════

def generate_protein_file(protein_name, output_dir="."):
    """生成蛋白质文件 (.protein)

    Args:
        protein_name: str  蛋白质名称 (如 "hemoglobin", "trypsin")
        output_dir: str   输出目录

    Returns:
        str  生成的文件路径
    """
    protein_name = protein_name.lower().strip()

    # 支持中英文
    name_map = {
        "胰蛋白": "trypsin", "角蛋白": "keratin", "酪蛋白": "casein",
        "血红蛋白": "hemoglobin", "血清蛋白": "albumin", "储存蛋白": "ferritin",
        "胶原蛋白": "collagen", "肌球蛋白": "myosin", "膜蛋白": "membrane_protein",
        "组蛋白": "histone"
    }
    if protein_name in name_map:
        protein_name = name_map[protein_name]

    if protein_name not in PROTEINS:
        available = ", ".join(PROTEINS.keys())
        raise ValueError(f"未知蛋白质: {protein_name}\\n可用: {available}")

    data = PROTEINS[protein_name]
    filename = f"{protein_name}.protein"
    filepath = os.path.join(output_dir, filename)

    file_content = {
        "__file_type__": "PyMsi Bio Protein File",
        "__version__": "1.5.9",
        "__protein_id__": protein_name,
        "__name__": data["name"],
        "__english__": data["english"],
        "__type__": data["type"],
        "__function__": data["function"],
        "__structure__": data["structure"],
        "__denature_temp__": data["denature_temp"],
        "__optimal_temp__": data["optimal_temp"],
        "__optimal_ph__": data["optimal_ph"],
        "__fun_fact__": data["fun_fact"],
        "__status__": "native",
        "__integrity__": 100,
        "__temperature__": data["optimal_temp"] if data["optimal_temp"] else 25,
        "__ph__": data["optimal_ph"] if data["optimal_ph"] else 7.0
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(file_content, f, ensure_ascii=False, indent=2)

    print(f"[bio] 蛋白质文件已生成: {filepath}")
    print(f"[bio] 蛋白质: {data['name']} ({data['english']})")
    print(f"[bio] 类型: {data['type']}")
    print(f"[bio] 变性温度: {data['denature_temp']}°C")
    return filepath


# ═══════════════════════════════════════════════════════════════
# 3. 酶文件生成器
# ═══════════════════════════════════════════════════════════════

def generate_enzyme_file(enzyme_name, output_dir="."):
    """生成酶文件 (.enzyme)

    Args:
        enzyme_name: str  酶名称 (如 "pepsin", "trypsin_enzyme")
        output_dir: str   输出目录

    Returns:
        str  生成的文件路径
    """
    enzyme_name = enzyme_name.lower().strip()

    # 支持中文
    name_map = {
        "胰蛋白酶": "trypsin_enzyme", "胃蛋白酶": "pepsin",
        "淀粉酶": "amylase", "蛋白酶k": "protease_k",
        "蛋白酶K": "protease_k", "凝血酶": "thrombin",
        "解旋酶": "helicase_like", "atp酶": "atpase"
    }
    if enzyme_name in name_map:
        enzyme_name = name_map[enzyme_name]

    if enzyme_name not in ENZYMES:
        available = ", ".join(ENZYMES.keys())
        raise ValueError(f"未知酶: {enzyme_name}\\n可用: {available}")

    data = ENZYMES[enzyme_name]
    filename = f"{enzyme_name}.enzyme"
    filepath = os.path.join(output_dir, filename)

    file_content = {
        "__file_type__": "PyMsi Bio Enzyme File",
        "__version__": "1.5.9",
        "__enzyme_id__": enzyme_name,
        "__name__": data["name"],
        "__english__": data["english"],
        "__target_protein__": data["target_protein"],
        "__target_name__": data["target_name"],
        "__function__": data["function"],
        "__mechanism__": data["mechanism"],
        "__analogy__": data["analogy"],
        "__optimal_temp__": data["optimal_temp"],
        "__optimal_ph__": data["optimal_ph"],
        "__inactivation_temp__": data["inactivation_temp"],
        "__status__": "active",
        "__activity__": 100,
        "__temperature__": data["optimal_temp"],
        "__ph__": data["optimal_ph"]
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(file_content, f, ensure_ascii=False, indent=2)

    print(f"[bio] 酶文件已生成: {filepath}")
    print(f"[bio] 酶: {data['name']} ({data['english']})")
    print(f"[bio] 目标蛋白: {data['target_name']}")
    print(f"[bio] 失活温度: {data['inactivation_temp']}°C")
    return filepath


# ═══════════════════════════════════════════════════════════════
# 4. 加热变性
# ═══════════════════════════════════════════════════════════════

def denature_protein(protein_file, temp=100, output_file=None):
    """加热蛋白质使其变性

    Args:
        protein_file: str  蛋白质文件路径
        temp: float        加热温度 (°C)
        output_file: str   输出文件路径 (默认覆盖原文件)

    Returns:
        str  变性后的文件路径
    """
    protein_file = os.path.abspath(protein_file)

    if not os.path.exists(protein_file):
        raise FileNotFoundError(f"蛋白质文件不存在: {protein_file}")

    with open(protein_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if data.get("__file_type__") != "PyMsi Bio Protein File":
        raise ValueError(f"不是有效的蛋白质文件: {protein_file}")

    denature_temp = data.get("__denature_temp__", 60)
    name = data.get("__name__", "未知蛋白")
    integrity = data.get("__integrity__", 100)

    if output_file is None:
        output_file = protein_file

    if temp >= denature_temp:
        # 变性!
        data["__status__"] = "denatured"
        data["__integrity__"] = 0
        data["__temperature__"] = temp
        data["__denatured__"] = True
        data["__denature_message__"] = (
            f"蛋白质 '{name}' 在 {temp}°C 下变性! "
            f"(变性温度: {denature_temp}°C) "
            f"空间结构被破坏, 生物活性丧失, 不可逆!"
        )
    else:
        # 未变性
        data["__temperature__"] = temp
        integrity_loss = max(0, int((temp / denature_temp) * 30))
        data["__integrity__"] = max(0, integrity - integrity_loss)
        if data["__integrity__"] < 50:
            data["__status__"] = "stressed"
        data["__denature_message__"] = (
            f"蛋白质 '{name}' 在 {temp}°C 下保持稳定 "
            f"(变性温度: {denature_temp}°C, 完整性: {data['__integrity__']}%)"
        )

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[bio] 加热结果: {data['__denature_message__']}")
    return output_file


# ═══════════════════════════════════════════════════════════════
# 5. 酶催化反应
# ═══════════════════════════════════════════════════════════════

def catalyze_reaction(enzyme_file, protein_file, output_file=None):
    """酶催化蛋白质反应

    Args:
        enzyme_file: str    酶文件路径
        protein_file: str   蛋白质文件路径
        output_file: str    输出文件路径 (默认覆盖蛋白质文件)

    Returns:
        str  反应后的文件路径
    """
    enzyme_file = os.path.abspath(enzyme_file)
    protein_file = os.path.abspath(protein_file)

    if not os.path.exists(enzyme_file):
        raise FileNotFoundError(f"酶文件不存在: {enzyme_file}")
    if not os.path.exists(protein_file):
        raise FileNotFoundError(f"蛋白质文件不存在: {protein_file}")

    with open(enzyme_file, 'r', encoding='utf-8') as f:
        enz = json.load(f)
    with open(protein_file, 'r', encoding='utf-8') as f:
        prot = json.load(f)

    if enz.get("__file_type__") != "PyMsi Bio Enzyme File":
        raise ValueError(f"不是有效的酶文件: {enzyme_file}")
    if prot.get("__file_type__") != "PyMsi Bio Protein File":
        raise ValueError(f"不是有效的蛋白质文件: {protein_file}")

    enz_status = enz.get("__status__", "active")
    prot_status = prot.get("__status__", "native")
    target = enz.get("__target_protein__")
    prot_id = prot.get("__protein_id__")

    if output_file is None:
        output_file = protein_file

    enz_name = enz.get("__name__", "未知酶")
    prot_name = prot.get("__name__", "未知蛋白")
    enz_temp = enz.get("__temperature__", 25)
    enz_ph = enz.get("__ph__", 7.0)
    enz_inact_temp = enz.get("__inactivation_temp__", 50)
    enz_opt_temp = enz.get("__optimal_temp__", 37)
    enz_opt_ph = enz.get("__optimal_ph__", 7.0)

    # 检查酶是否失活
    if enz_status == "denatured" or enz_temp >= enz_inact_temp:
        result_msg = (
            f"酶 '{enz_name}' 已失活 (温度 {enz_temp}°C >= 失活温度 {enz_inact_temp}°C), "
            f"无法催化反应! 请生成新的酶文件."
        )
        print(f"[bio] ⚠️ {result_msg}")
        prot["__last_catalysis__"] = result_msg
    elif prot_status == "denatured":
        result_msg = (
            f"蛋白质 '{prot_name}' 已变性, 无法被酶催化! "
            f"变性蛋白已被破坏, 酶无底物可作用."
        )
        print(f"[bio] ⚠️ {result_msg}")
        prot["__last_catalysis__"] = result_msg
    elif target and prot_id and target != prot_id:
        result_msg = (
            f"酶 '{enz_name}' 的目标蛋白是 '{enz.get('__target_name__', target)}', "
            f"但提供的蛋白质是 '{prot_name}'. 底物不匹配, 无法催化!"
        )
        print(f"[bio] ⚠️ {result_msg}")
        prot["__last_catalysis__"] = result_msg
    else:
        # 催化成功!
        temp_efficiency = max(0, 1 - abs(enz_temp - enz_opt_temp) / enz_opt_temp)
        ph_efficiency = max(0, 1 - abs(enz_ph - enz_opt_ph) / max(enz_opt_ph, 0.1))
        efficiency = int(temp_efficiency * ph_efficiency * 100)

        prot["__status__"] = "catalyzed"
        prot["__integrity__"] = max(0, prot.get("__integrity__", 100) - efficiency // 2)
        prot["__last_catalysis__"] = (
            f"酶 '{enz_name}' 成功催化蛋白质 '{prot_name}'! "
            f"催化效率: {efficiency}% (温度效率: {int(temp_efficiency*100)}%, "
            f"pH效率: {int(ph_efficiency*100)}%). "
            f"蛋白质被分解, 完整性降至 {prot['__integrity__']}%. "
            f"机制: {enz.get('__mechanism__', '未知')}"
        )
        print(f"[bio] ✅ {prot['__last_catalysis__']}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prot, f, ensure_ascii=False, indent=2)

    return output_file


# ═══════════════════════════════════════════════════════════════
# 6. 模块包装类
# ═══════════════════════════════════════════════════════════════

class _BioModule:
    """PyMsi.bio — 🧬 生物教育模块 (1.5.9 Education Edition)

    专为程序员设计的生物学教学工具:

    1. 细胞结构 — 生成互动式教程 Python 文件
    2. 蛋白质系统 — 10种蛋白质, 可加热变性
    3. 酶系统 — 8种酶, 可催化对应蛋白质

    用法:
        # 生成细胞结构教程
        PM.bio.cell()
        PM.bio.cell(output="my_tutorial.py")

        # 生成蛋白质文件
        PM.bio.protein("hemoglobin")
        PM.bio.protein("血红蛋白")  # 支持中文

        # 生成酶文件
        PM.bio.enzyme("pepsin")
        PM.bio.enzyme("胃蛋白酶")

        # 加热变性
        PM.bio.denature("hemoglobin.protein", temp=70)
        PM.bio.heat("casein.protein", temp=100)  # 别名

        # 酶催化反应
        PM.bio.catalyze("pepsin.enzyme", "casein.protein")
        PM.bio.react("pepsin.enzyme", "casein.protein")  # 别名

        # 查看可用蛋白质/酶
        PM.bio.list_proteins()
        PM.bio.list_enzymes()
    """

    def __init__(self):
        self.output_dir = "."

    def __repr__(self):
        return "<PyMsi.bio [生物教育模块] v1.5.9 Education Edition>"

    def __call__(self, action="cell", **kwargs):
        """快捷调用: PM.bio("cell"), PM.bio("protein", name="hemoglobin")"""
        if action == "cell":
            return self.cell(**kwargs)
        elif action == "protein":
            return self.protein(kwargs.get("name", "hemoglobin"))
        elif action == "enzyme":
            return self.enzyme(kwargs.get("name", "pepsin"))
        elif action == "list":
            self.list_all()
        else:
            print(f"未知操作: {action}")
            print("可用: cell, protein, enzyme, list")

    def cell(self, output=None):
        """生成细胞结构互动教程 Python 文件"""
        if output is None:
            output = "cell_tutorial.py"
        return generate_cell_tutorial(output)

    def protein(self, name):
        """生成蛋白质文件"""
        return generate_protein_file(name, self.output_dir)

    def enzyme(self, name):
        """生成酶文件"""
        return generate_enzyme_file(name, self.output_dir)

    def denature(self, protein_file, temp=100, output_file=None):
        """加热蛋白质使其变性"""
        return denature_protein(protein_file, temp, output_file)

    def heat(self, protein_file, temp=100, output_file=None):
        """别名: 加热蛋白质"""
        return self.denature(protein_file, temp, output_file)

    def catalyze(self, enzyme_file, protein_file, output_file=None):
        """酶催化蛋白质反应"""
        return catalyze_reaction(enzyme_file, protein_file, output_file)

    def react(self, enzyme_file, protein_file, output_file=None):
        """别名: 酶催化反应"""
        return self.catalyze(enzyme_file, protein_file, output_file)

    def list_proteins(self):
        """列出所有可用蛋白质"""
        print("\n🧬 可用蛋白质列表:")
        print("─" * 50)
        for key, data in PROTEINS.items():
            print(f"  {key:20s} | {data['name']} ({data['english']})")
            print(f"  {'':20s} | 类型: {data['type']}, 变性温度: {data['denature_temp']}°C")
            print()

    def list_enzymes(self):
        """列出所有可用酶"""
        print("\n⚗️ 可用酶列表:")
        print("─" * 50)
        for key, data in ENZYMES.items():
            target = data.get("target_name", "无")
            print(f"  {key:25s} | {data['name']} ({data['english']})")
            print(f"  {'':25s} | 目标: {target}, 失活温度: {data['inactivation_temp']}°C")
            print()

    def list_all(self):
        """列出所有可用蛋白质和酶"""
        self.list_proteins()
        self.list_enzymes()
        print("💡 提示: PM.bio.protein('hemoglobin') 生成蛋白质文件")
        print("💡       PM.bio.enzyme('pepsin') 生成酶文件")
        print("💡       PM.bio.denature('hemoglobin.protein', temp=70) 加热变性")
        print("💡       PM.bio.catalyze('pepsin.enzyme', 'casein.protein') 酶催化")
