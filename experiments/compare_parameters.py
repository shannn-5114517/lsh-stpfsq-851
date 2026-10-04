# -*- coding: utf-8 -*-
"""对照实验：分别改变 VDD / λ / R_d，看谁在起作用"""
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

RG1, RG2 = 60.0, 40.0
K, VTH = 0.8e-3, 1.0


def run(VDD, LAM, RD_K):
    """给定 VDD / λ / R_d，返回 (VG, VOV, I_D, V_DS, 工作区, gm, |Av|)"""
    VG = VDD * RG2 / (RG1 + RG2)
    VOV = VG - VTH
    rd = RD_K * 1000

    c = Circuit('nmos')
    c.model('NMOD', 'NMOS', LEVEL=1, VTO=VTH, KP=K, LAMBDA=LAM,
            W=1 @u_um, L=1 @u_um)
    c.V('DD', 'vdd', c.gnd, VDD @u_V)
    c.V('bias', 'g', c.gnd, VG @u_V)
    c.R('d', 'vdd', 'd', RD_K @u_kOhm)
    c.MOSFET('1', 'd', 'g', c.gnd, c.gnd, model='NMOD')
    o = c.simulator(temperature=25, nominal_temperature=25).operating_point()
    vds = val(o['d'])
    idd = (VDD - vds) / rd

    region = '饱和区' if (idd > 1e-9 and vds > VOV) else ('线性区' if idd > 1e-9 else '截止')

    # 固定 V_DS 测 gm
    if idd > 1e-9 and vds > VOV:
        def id_at(vg):
            cc = Circuit('gm')
            cc.model('NMOD', 'NMOS', LEVEL=1, VTO=VTH, KP=K, LAMBDA=LAM,
                     W=1 @u_um, L=1 @u_um)
            cc.V('DS', 'd', cc.gnd, vds @u_V)
            cc.V('G', 'g', cc.gnd, vg @u_V)
            cc.MOSFET('1', 'd', 'g', cc.gnd, cc.gnd, model='NMOD')
            oo = cc.simulator(temperature=25, nominal_temperature=25).operating_point()
            return abs(val(oo.branches['vds']))
        dv = 0.05
        gm = (id_at(VG + dv) - id_at(VG - dv)) / (2 * dv)
        if LAM > 0:
            ro = 1 / (LAM * idd)
            av = gm * (rd * ro) / (rd + ro)
        else:
            av = gm * rd
    else:
        gm, av = 0.0, 0.0

    return VG, VOV, idd * 1000, vds, region, gm * 1000, av


print("=" * 84)
print("  对照实验：一次只改一个参数，看每个参数各起什么作用")
print("=" * 84)

# ══════════ 表 1：固定 R_d = 2 kΩ，分别改 VDD 和 λ ══════════
print()
print("【表 1】固定 R_d = 2 kΩ，分别改变 VDD 和 λ")
print()
print(f"  {'情况':<22} {'VDD':>5} {'λ':>7} {'V_G':>7} {'V_ov':>7} {'I_D(mA)':>9} "
      f"{'V_DS(V)':>9} {'工作区':>8} {'|Av|':>8}")
print("  " + "-" * 82)

cases = [
    ('① 原始（参考基准）',      5.0, 0.02),
    ('② 只改 VDD → 8 V',        8.0, 0.02),
    ('③ 只改 λ → 0',            5.0, 0.0),
    ('④ 两个都改（你这次的）',   8.0, 0.0),
]
for name, vdd, lam in cases:
    VG, VOV, idd, vds, region, gm, av = run(vdd, lam, 2.0)
    print(f"  {name:<20} {vdd:>5.0f} {lam:>7.2f} {VG:>7.2f} {VOV:>7.2f} {idd:>9.4f} "
          f"{vds:>9.4f} {region:>8} {av:>8.4f}")

# ══════════ 表 2：R_d 扫描对比 ══════════
print()
print("【表 2】R_d 扫描：不同参数组合下，临界点挪到哪了")
print()
print(f"  {'R_d(kΩ)':>8} │ {'①原始 VDD=5,λ=0.02':>26} │ {'②VDD=8':>20} │ {'③λ=0':>20}")
print(f"  {'':>8} │ {'V_DS':>10} {'工作区':>13} │ {'V_DS':>9} {'工作区':>9} │ {'V_DS':>9} {'工作区':>9}")
print("  " + "-" * 84)

for rd_k in [1, 2, 3, 5, 8, 10, 12, 15]:
    a = run(5.0, 0.02, rd_k)
    b = run(8.0, 0.02, rd_k)
    c = run(5.0, 0.0, rd_k)
    print(f"  {rd_k:>8.1f} │ {a[3]:>10.4f} {a[4]:>13} │ {b[3]:>9.4f} {b[4]:>9} │ {c[3]:>9.4f} {c[4]:>9}")

# ══════════ 表 3：临界 R_d 对比 ══════════
print()
print("【表 3】临界 R_d（V_DS 刚好跌到 V_ov 的那个点）")
print()
print(f"  {'参数组合':<28} {'V_G(V)':>8} {'V_ov(V)':>9} {'I_D(mA)':>10} {'可用余量(V)':>12} {'临界 R_d(kΩ)':>14}")
print("  " + "-" * 84)

for name, vdd, lam in cases:
    VG = vdd * RG2 / (RG1 + RG2)
    VOV = VG - VTH
    a = 0.5 * K * VOV ** 2
    id_at_boundary = a * (1 + lam * VOV)
    rd_crit = (vdd - VOV) / id_at_boundary / 1000
    print(f"  {name:<26} {VG:>8.2f} {VOV:>9.2f} {id_at_boundary*1000:>10.4f} "
          f"{vdd-VOV:>12.2f} {rd_crit:>14.2f}")

print()
print("=" * 84)
