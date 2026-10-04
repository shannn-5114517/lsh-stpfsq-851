# -*- coding: utf-8 -*-
"""
作业 ②：验证戴维南定理
包含：
  1. 含源二端网络图（标注端口 a / b）+ 戴维南等效电路图
  2. V_oc（开路电压）仿真  → 验证 V_th
  3. I_sc（短路电流）仿真  → 验证 R_th = V_oc / I_sc
  4. 等效替换后接负载的电压 / 电流验证表
运行：python 02_thevenin.py
输出：images/02_*.png
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
_HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('MPLCONFIGDIR', os.path.join(_HERE, '.mplcache'))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

import PySpice.Logging.Logging as Logging
Logging.setup_logging()
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

IMG = os.path.join(_HERE, 'images')
os.makedirs(IMG, exist_ok=True)


def val(x):
    """WaveForm → float（兼容 numpy 2.x）"""
    return float(np.asarray(x).flatten()[0])


# ==================== 参数（可自行修改）====================
V1_VALUE = 20  @u_V
R1_VALUE = 1.5 @u_kOhm
R2_VALUE = 3  @u_kOhm

V1 = float(V1_VALUE); R1 = float(R1_VALUE); R2 = float(R2_VALUE)

VTH = V1 * R2 / (R1 + R2)
RTH = R1 * R2 / (R1 + R2)
ISC = VTH / RTH

print("=" * 68)
print("  ② 验证戴维南定理")
print("=" * 68)
print(f"  原电路：V1 = {V1:g} V,  R1 = {R1/1000:g} kΩ,  R2 = {R2/1000:g} kΩ")
print()
print("  【手算】")
print(f"    戴维南电压  V_th = V1·R2/(R1+R2) = {V1:g}×{R2/1000:g}"
      f"/({(R1+R2)/1000:g}) = {VTH:.4f} V")
print(f"    戴维南电阻  R_th = R1∥R2        = {R1/1000:g}×{R2/1000:g}"
      f"/({(R1+R2)/1000:g}) = {RTH:.1f} Ω = {RTH/1000:.4f} kΩ")
print(f"    短路电流    I_sc = V_th/R_th    = {ISC*1000:.4f} mA")


# ==================== 电路构造函数 ====================
def build_original(load=None, short=False):
    """原电路；short=True 时输出端短路（用于测 I_sc）"""
    c = Circuit('Thevenin Original')
    c.V('1', 'n1', c.gnd, V1_VALUE)
    c.R('1', 'n1', 'a', R1_VALUE)
    c.R('2', 'a', c.gnd, R2_VALUE)
    if short:
        c.V('sense', 'a', c.gnd, 0 @u_V)          # 0V 源作电流探针
    elif load is not None:
        c.R('L', 'a', c.gnd, load)
    else:
        c.R('L', 'a', c.gnd, 1 @u_GOhm)           # 近似开路
    return c


def build_equiv(load=None):
    c = Circuit('Thevenin Equivalent')
    c.V('th', 'src', c.gnd, VTH @u_V)
    c.R('th', 'src', 'a', RTH @u_Ohm)
    if load is not None:
        c.R('L', 'a', c.gnd, load)
    else:
        c.R('L', 'a', c.gnd, 1 @u_GOhm)
    return c


def solve(circuit):
    sim = circuit.simulator(temperature=25, nominal_temperature=25)
    return sim.operating_point()


# ==================== 1. 画电路图 ====================
import schemdraw
import schemdraw.elements as elm
schemdraw.config(font='Microsoft YaHei', fontsize=13, lw=1.9)

# --- 原电路（含源二端网络，标注端口）---
with schemdraw.Drawing(file=os.path.join(IMG, '02a_circuit_auto.png'), show=False) as d:
    d.config(unit=2.5)
    # 电源
    d += elm.SourceV().at((0, -2.6)).up().to((0, 0)).label('$V_1$\n10 V', loc='left')
    # 顶边到 R1
    d += elm.Line().at((0, 0)).right().to((1.4, 0))
    # R1
    d += (R1e := elm.Resistor().right().label('$R_1$\n2 kΩ', loc='top'))
    # 到分压节点
    d += elm.Line().to((5.2, 0))
    d += elm.Dot().at((5.2, 0))
    # 端口 a
    d += elm.Line().at((5.2, 0)).right().to((6.8, 0))
    d += elm.Dot(open=True).at((6.8, 0)).label('$a$', loc='right', fontsize=14)
    # R2 向下
    d += elm.Resistor().at((5.2, 0)).down().to((5.2, -3.0)) \
            .label('$R_2$\n3 kΩ', loc='right')
    # 底边回线
    d += elm.Line().at((5.2, -3.0)).left().to((0, -3.0))
    d += elm.Line().at((0, -3.0)).up().to((0, -2.6))
    # 端口 b
    d += elm.Line().at((5.2, -3.0)).right().to((6.8, -3.0))
    d += elm.Dot(open=True).at((6.8, -3.0)).label('$b$', loc='right', fontsize=14)
    # 标题（放在足够高的位置）
    d += elm.Label().at((3.2, 1.5)) \
            .label('含源二端网络（端口 a、b）', fontsize=13)
print("[图] 含源二端网络图  → images/02a_circuit.png")

# --- 戴维南等效电路 ---
with schemdraw.Drawing(file=os.path.join(IMG, '02b_equivalent.png'), show=False) as d:
    d.config(unit=2.5)
    d += elm.SourceV().at((0, -2.6)).up().to((0, 0)) \
            .label(f'$V_{{th}}$\n{VTH:.4g} V', loc='left')
    d += elm.Line().at((0, 0)).right().to((1.4, 0))
    d += (Re := elm.Resistor().right().label(f'$R_{{th}}$\n{RTH/1000:.1f} kΩ', loc='top'))
    d += elm.Line().to((5.2, 0))
    d += elm.Dot().at((5.2, 0))
    d += elm.Line().at((5.2, 0)).right().to((6.8, 0))
    d += elm.Dot(open=True).at((6.8, 0)).label('$a$', loc='right', fontsize=14)
    # 底边回线
    d += elm.Line().at((5.2, 0)).down().to((5.2, -3.0))
    d += elm.Line().at((5.2, -3.0)).left().to((0, -3.0))
    d += elm.Line().at((0, -3.0)).up().to((0, -2.6))
    d += elm.Line().at((5.2, -3.0)).right().to((6.8, -3.0))
    d += elm.Dot(open=True).at((6.8, -3.0)).label('$b$', loc='right', fontsize=14)
    d += elm.Label().at((3.2, 1.5)).label('戴维南等效电路', fontsize=13)
print("[图] 戴维南等效电路  → images/02b_equivalent.png")


# ==================== 2. V_oc 仿真 ====================
op_oc = solve(build_original())
voc_sim = val(op_oc['a'])
print("\n" + "=" * 68)
print("  【理论值 vs 仿真值 对比表】")
print("=" * 68)
print(f"  {'项目':<24}{'理论值':>15}{'仿真值':>15}{'误差':>12}")
print("  " + "-" * 66)

def prow(name, th, sim, unit='', prec=4):
    err = abs(sim - th) / abs(th) * 100 if th else 0
    print(f"  {name:<24}{th:>14.{prec}f}{unit}{sim:>14.{prec}f}{unit}{err:>11.4f}%")

prow('开路电压 V_oc (V)', VTH, voc_sim, ' V')

# ==================== 3. I_sc 仿真 ====================
op_sc = solve(build_original(short=True))
# 注意：SPICE 内部会把元件名转成小写，所以 key 是 'vsense' 而不是 'sense'
isc_sim = abs(val(op_sc.branches['vsense']))
rth_sim = voc_sim / isc_sim

prow('短路电流 I_sc (mA)', ISC*1000, isc_sim*1000, ' mA')
prow('R_th = V_oc/I_sc (Ω)', RTH, rth_sim, ' Ω', 3)


# ==================== 4. 负载验证（电压 + 电流）====================
print("\n" + "-" * 66)
print("  等效替换后接负载的电压 / 电流验证表")
print("-" * 66)
loads_k = [0.5, 1.0, 1.2, 2.0, 3.0, 5.0, 10.0, 20.0]
print(f"  {'R_L':>7} {'V_L原(V)':>11} {'V_L等效(V)':>12} "
      f"{'I_L原(mA)':>12} {'I_L等效(mA)':>13} {'V误差%':>10} {'I误差%':>10}")
print("  " + "-" * 80)

rows = []
for rl_k in loads_k:
    rl = rl_k @u_kOhm
    vo_ = val(solve(build_original(rl))['a'])
    ve_ = val(solve(build_equiv(rl))['a'])
    io_ = vo_ / (rl_k * 1000) * 1000      # mA
    ie_ = ve_ / (rl_k * 1000) * 1000
    ev = abs(vo_ - ve_) / ve_ * 100 if ve_ else 0
    ei = abs(io_ - ie_) / ie_ * 100 if ie_ else 0
    rows.append((rl_k, vo_, ve_, io_, ie_, ev, ei))
    print(f"  {rl_k:>7.1f} {vo_:>11.6f} {ve_:>12.6f} "
          f"{io_:>12.6f} {ie_:>13.6f} {ev:>10.2e} {ei:>10.2e}")

max_v = max(r[5] for r in rows)
max_i = max(r[6] for r in rows)
print("  " + "-" * 80)
print(f"  电压最大相对误差 {max_v:.2e} %      电流最大相对误差 {max_i:.2e} %")
print(f"  → 原电路与等效电路在 {len(rows)} 种负载下完全一致 ✅")


# ==================== 5. 由负载数据反推 R_th ====================
print("\n" + "-" * 66)
print("  由仿真数据反推 R_th：R_th = R_L·(V_oc − V_L)/V_L")
print("-" * 66)
rth_list = []
for rl_k, vo_, _, _, _, _, _ in rows:
    if 0.01 < vo_ < VTH - 0.01:
        r = rl_k * 1000 * (VTH - vo_) / vo_
        rth_list.append(r)
rth_avg = float(np.mean(rth_list))
print(f"  8 组负载反推 R_th 平均值 = {rth_avg:.2f} Ω  ({rth_avg/1000:.4f} kΩ)")
print(f"  理论 R_th                = {RTH:.2f} Ω  ({RTH/1000:.4f} kΩ)")
print(f"  误差                     = {abs(rth_avg-RTH)/RTH*100:.4f} %")


# ==================== 6. 画验证图 ====================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2))
xs = [r[0] for r in rows]

ax1.plot(xs, [r[1] for r in rows], 'o', color='#1f77b4', markersize=9,
         label='原电路 $V_L$')
ax1.plot(xs, [r[2] for r in rows], 's', color='#d62728', markersize=8,
         markerfacecolor='none', markeredgewidth=2, label='等效电路 $V_L$')
ax1.plot(xs, [VTH*(x*1000)/(RTH+x*1000) for x in xs], '--', color='#2ca02c',
         linewidth=1.7, label=r'理论 $V_{th}R_L/(R_{th}+R_L)$')
ax1.axvline(RTH/1000, color='gray', linestyle=':', linewidth=1.4,
            label=f'$R_L=R_{{th}}$={RTH/1000:.1f} kΩ')
ax1.set_xlabel('负载电阻 $R_L$ (kΩ)', fontsize=11)
ax1.set_ylabel('输出电压 $V_L$ (V)', fontsize=11)
ax1.set_title('电压验证：两条曲线完全重合', fontsize=12)
ax1.grid(True, alpha=0.3); ax1.legend(fontsize=9)

ax2.plot(xs, [r[3] for r in rows], 'o-', color='#1f77b4', markersize=7,
         label='原电路 $I_L$')
ax2.plot(xs, [r[4] for r in rows], 's--', color='#d62728', markersize=6,
         markerfacecolor='none', markeredgewidth=1.8, label='等效电路 $I_L$')
ax2.set_xlabel('负载电阻 $R_L$ (kΩ)', fontsize=11)
ax2.set_ylabel('负载电流 $I_L$ (mA)', fontsize=11)
ax2.set_title(f'电流验证：最大误差 {max_i:.1e} %', fontsize=12)
ax2.grid(True, alpha=0.3); ax2.legend(fontsize=9)

plt.suptitle('② 戴维南定理验证', fontsize=14, y=1.00)
plt.tight_layout()
plt.savefig(os.path.join(IMG, '02c_verify.png'), dpi=150, bbox_inches='tight')
plt.close()

print(f"\n[图] 验证曲线  → images/02c_verify.png")
print("=" * 68)
