# -*- coding: utf-8 -*-
"""验证：为什么仿真误差是 0.42% / 0.65% 交替出现"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np

F_START, F_STOP = 10.0, 1e6
PTS_PER_DEC = 60
C = 100e-9

print("=" * 96)
print("  扫频设置的「网格」分析")
print("=" * 96)
print(f"  扫频范围    : {F_START:g} Hz ~ {F_STOP:g} Hz")
print(f"  每十倍频点数: {PTS_PER_DEC}")
print(f"  相邻点频率比: 10^(1/{PTS_PER_DEC}) = {10**(1/PTS_PER_DEC):.6f}  "
      f"（即相邻点差 {(10**(1/PTS_PER_DEC)-1)*100:.3f}%）")
print()
print(f"  → 也就是说：仿真能找到的「−3 dB 点」永远是网格上的某一点，")
print(f"     真实 fc 落在两个网格点之间时，就会有误差。")
print(f"     最大可能误差：{(10**(0.5/PTS_PER_DEC)-1)*100:.3f}%（正好落在两点正中间时）")
print()

print("=" * 96)
print("  逐个算 fc 落在网格的什么位置")
print("=" * 96)
print()
print(f"  {'R (kΩ)':>8} {'真实 fc (Hz)':>14} {'网格位置':>10} {'小数部分':>10} "
      f"{'最近网格点 (Hz)':>16} {'推算误差':>10} {'你实测':>9}")
print("  " + "-" * 92)

measured = {0.1: 0.42, 0.5: 0.65, 1.0: 0.42, 5.0: 0.65, 10.0: 0.42, 50.0: 0.65}

for r_k in [0.1, 0.5, 1, 5, 10, 50]:
    fc = 1 / (2 * np.pi * r_k * 1000 * C)
    dec = np.log10(fc / F_START)          # 距离起点的十倍频程数
    grid = dec * PTS_PER_DEC               # 相当于第几个网格点
    frac = grid - np.floor(grid)           # 小数部分 = 落在格子里的相对位置
    nearest = round(grid)
    fc_grid = F_START * 10 ** (nearest / PTS_PER_DEC)
    err = abs(fc_grid - fc) / fc * 100
    print(f"  {r_k:>8.1f} {fc:>14.1f} {grid:>10.2f} {frac:>10.3f} "
          f"{fc_grid:>16.1f} {err:>9.3f}% {measured[r_k]:>8.2f}%")

print()
print("=" * 96)
print("  结论")
print("=" * 96)
print()
print("  · 0.1 / 1 / 10 kΩ —— 三者相差正好 10 倍（= 整数个十倍频程 = 整数个网格）")
print("    → 在网格上的「相对位置」完全相同（小数部分都是 0.11）")
print("    → 误差也完全相同（0.42%）")
print()
print("  · 0.5 / 5 / 50 kΩ —— 同样相差 10 倍，但位置不同（小数部分 0.17）")
print("    → 误差是另一个固定值（0.65%）")
print()
print("  · 换句话说：**误差跟你取多大的 R 无关，只跟 fc 落在网格的哪个位置有关**")
print()
print("=" * 96)
