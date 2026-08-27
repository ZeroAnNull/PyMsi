"""
PyMsi v1.5.3 录屏示例 — 纯手搓、纯自研
========================================

在 Windows 上运行此脚本:
    python 录屏示例.py

它会:
    1. 自动隐藏控制台窗口
    2. 后台静默录屏 1 分钟 (最高 4K)
    3. 录完后恢复控制台
    4. 自动输出录制文件路径 (默认 D:/Videos)

自定义参数:
    python 录屏示例.py          # 默认: 1分钟, 4K, AVI
    python 录屏示例.py gif      # 录制 GIF
    python 录屏示例.py mp4      # 录制 MP4 (需要 ffmpeg)
"""

import sys
import PyMsi as PM

# ─── 在代码里写死的录屏配置 ──────────────────────────
DURATION = 60           # 录屏时长 1 分钟
RESOLUTION = "4K"       # 清晰度 (最高 4K)
OUTPUT_DIR = "D:/Videos"  # 默认输出目录

# 输出格式 (从命令行参数获取, 默认 avi)
fmt = "avi"
if len(sys.argv) > 1:
    fmt = sys.argv[1]

print(f"[PyMsi v1.5.3] 录屏配置:")
print(f"  时长: {DURATION} 秒")
print(f"  清晰度: {RESOLUTION} (最高 4K)")
print(f"  格式: {fmt}")
print(f"  输出目录: {OUTPUT_DIR}")
print(f"  支持格式: 34 种 (含 GIF)")
print()
print(">>> 即将开始录屏, 控制台将自动隐藏...")
print(">>> 录制完成后控制台会自动恢复并输出文件路径")
print()

# ─── 一键录屏 ────────────────────────────────────────
# PM.record() 会:
#   1. 隐藏控制台窗口 (ShowWindow SW_HIDE)
#   2. 用 Win32 GDI 逐帧截屏 (BitBlt + GetDIBits)
#   3. 纯自研 AVI/GIF 编码器写入文件
#   4. (如需 MP4 等) 用 ffmpeg 转码
#   5. 恢复控制台窗口
#   6. 打印输出文件路径
output_path = PM.record(
    duration=DURATION,
    resolution=RESOLUTION,
    fmt=fmt,
    output_dir=OUTPUT_DIR,
)

print()
print(f"[PyMsi v1.5.3] 录屏完成!")
print(f"  文件路径: {output_path}")
print()
print("也可以用变量访问:")
print(f"  PM.record.output  → {PM.record.output}")
print(f"  PM.record.status  → {PM.record.status}")
