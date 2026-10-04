# -*- coding: utf-8 -*-
"""λ 三档对比：沟道长度调制对 Q 点和增益的影响"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('MPLCONFIGDIR', os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import PySpice.Logging.Logging as Logging
Logging.setup_logging()
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

def val(x):
    return float(np.asarray(x).flatten()[0])

VDD = 5.0
RG1, RG2 = 60.0, 40.0
K, VTH = 0.8e-3, 1.0
VG = VDD * RG2 / (RG1 + RG2)
VOV = VG - VTH


def measure(lam, rd_k):
    rd = rd_k * 1000
    c = Circuit('n')
    c.model('NMOD', 'NMOS', LEVEL=1, VTO=VTH, KP=K, LAMBDA=lam, W=1 @u_um, L=1 @u_um)
    c.V('DD', 'vdd', c.gnd, VDD @u_V)
    c.V('bias', 'g', c.gnd, VG @u_V)
    c.R('d', 'vdd', 'd', rd_k @u_kOhm)
    c.MOSFET('1', 'd', 'g', c.gnd, c.gnd, model='NMOD')
    o = c.simulator(temperature=25, nominal_temperature=25).operating_point()
    vds = val(o['d'])
    idd = (VDD - vds) / rd

    if idd <= 1e-9 or vds <= VOV:
        return idd * 1000, vds, 0.0, float('inf'), 0.0

    def id_at(vg):
        cc = Circuit('gm')
        cc.model('NMOD', 'NMOS', LEVEL=1, VTO=VTH, KP=K, LAMBDA=lam, W=1 @u_um, L=1 @u_um)
        cc.V('DS', 'd', cc.gnd, vds @u_V)
        cc.V('G', 'g', cc.gnd, vg @u_V)
        cc.MOSFET('1', 'd', 'g', cc.gnd, cc.gnd, model='NMOD')
        oo = cc.simulator(temperature=25, nominal_temperature=25).operating_point()
        return abs(val(oo.branches['vds']))

    dv = 0.02
    gm = (id_at(VG + dv) - id_at(VG - dv)) / (2 * dv)
    ro = 1 / (lam * idd)
    par = (rd * ro) / (rd + ro)
    return idd * 1000, vds, gm * 1000, ro / 1000, gm * par


LAMS = [0.02, 0.1, 0.5]
RDS = [0.5, 1, 2, 4, 6]

print("=" * 92)
print("  λ 三档对比 —— 沟道长度调制到底影响了什么")
print("=" * 92)

for lam in LAMS:
    print()
    print(f"【λ = {lam}】  （λ 越大 → 沟道长度调制越强）")
    print()
    print(f"  {'Rd(kΩ)':>8} {'I_D(mA)':>10} {'V_DS(V)':>9} {'g_m(mA/V)':>11} "
          f"{'r_o(kΩ)':>10} {'Rd∥r_o(kΩ)':>12} {'|A_v|':>9}")
    print("  " + "-" * 88)
    for rd_k in RDS:
        idd, vds, gm, ro, av = measure(lam, rd_k)
        par = (rd_k * ro) / (rd_k + ro) if ro != float('inf') else rd_k
        ro_s = f"{ro:.1f}" if ro != float('inf') else "∞"
        print(f"  {rd_k:>8.1f} {idd:>10.4f} {vds:>9.4f} {gm:>11.4f} "
              f"{ro_s:>10} {par:>12.3f} {av:>9.4f}")

# ---------- 汇总：增益随 λ 的变化 ----------
print()
print("=" * 92)
print("  【关键】增益 |A_v| 随 λ 的变化 —— 注意第 1 行和第 5 行的趋势相反！")
print("=" * 92)
print()
print(f"  {'Rd(kΩ)':>8} │" + "".join(f" {'λ='+str(l):>12} │" for l in LAMS) + "  趋势")
print("  " + "-" * 88)
for rd_k in RDS:
    avs = [measure(l, rd_k)[4] for l in LAMS]
    trend = "⬆ 升" if avs[-1] > avs[0] else "⬇ 降"
    print(f"  {rd_k:>8.1f} │" + "".join(f" {a:>12.4f} │" for a in avs) + f"  {trend}")

# ---------- 解释 ----------
print()
print("=" * 92)
print("  为什么小 R_d 时升、大 R_d 时降？")
print("=" * 92)
print()
for rd_k in [0.5, 6.0]:
    print(f"  【R_d = {rd_k} kΩ】")
    for lam in [0.02, 0.5]:
        idd, vds, gm, ro, av = measure(lam, rd_k)
        par = (rd_k * ro) / (rd_k + ro)
        print(f"    λ={lam:<5} → I_D={idd:.4f} mA,  g_m={gm:.4f} mA/V,  r_o={ro:.1f} kΩ,  "
              f"R_d∥r_o={par:.3f} kΩ,  |A_v|={av:.4f}")
    a1 = measure(0.02, rd_k)[4]
    a2 = measure(0.5, rd_k)[4]
    g1 = measure(0.02, rd_k)[2]; g2 = measure(0.5, rd_k)[2]
    p1 = (rd_k * measure(0.02, rd_k)[3]) / (rd_k + measure(0.02, rd_k)[3])
    p2 = (rd_k * measure(0.5, rd_k)[3]) / (rd_k + measure(0.5, rd_k)[3])
    print(f"    → g_m 变化 {(g2/g1-1)*100:+.1f}%（拉动增益上升）")
    print(f"    → R_d∥r_o 变化 {(p2/p1-1)*100:+.1f}%（拉动增益下降）")
    print(f"    → 净效果 {(a2/a1-1)*100:+.1f}%")
    print()
print("=" * 92)
