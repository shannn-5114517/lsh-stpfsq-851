# -*- coding: utf-8 -*-
"""
作业 ③：NMOS 共源级放大电路

电路（题卡给定）：
    VDD = 5V
    Rg1 = 60kΩ（接 VDD）,  Rg2 = 40kΩ（接地）
    Rd  = 2kΩ
    Cb1 足够大（输入耦合电容）
    NMOS: K = 0.8 mA/V², Vth = 1V, λ = 0.02 /V
    Vi = 10 mV / 1 kHz 正弦波

要求：
  1. 直流工作点：V_GS, I_D, V_DS，判断饱和区
  2. 小信号：gm, Av
  3. 仿真验证：直流 OP 对比、瞬态看波形、实测增益
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('MPLCONFIGDIR',
                      os.path.join(os.path.dirname(os.path.abspath(__file__)), '.mplcache'))

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


def val(waveform):
    return float(np.asarray(waveform).flatten()[0])


# ==================== 电路参数 ====================
VDD  = 5      @u_V
RG1  = 60     @u_kOhm
RG2  = 40     @u_kOhm
RD   = 2      @u_kOhm
CB1  = 10     @u_uF          # 足够大：转折频率 1/(2π·24k·10µ) ≈ 0.66 Hz
K_PARAM = 0.8e-3             # A/V²  （K = µnCox·W/L）
VTH_N   = 1.0                # V
LAMBDA  = 0.02               # 1/V
VI_AMP  = 10     @u_mV
VI_FREQ = 1      @u_kHz

vdd = float(VDD); rg1 = float(RG1); rg2 = float(RG2); rd = float(RD)

# ==================== 手算 ====================
VG   = vdd * rg2 / (rg1 + rg2)
VGS  = VG                       # 源极接地
VOV  = VGS - VTH_N
ID_ideal = 0.5 * K_PARAM * VOV**2
VDS_ideal = vdd - ID_ideal * rd

# 计入 λ 的迭代
vds_it = VDS_ideal
for _ in range(20):
    id_it = 0.5 * K_PARAM * VOV**2 * (1 + LAMBDA * vds_it)
    vds_new = vdd - id_it * rd
    if abs(vds_new - vds_it) < 1e-9:
        vds_it = vds_new
        break
    vds_it = vds_new
ID_real = 0.5 * K_PARAM * VOV**2 * (1 + LAMBDA * vds_it)
VDS_real = vds_it

GM_IDEAL = K_PARAM * VOV                       # 理想跨导（完全忽略 λ）
GM   = 2 * ID_real / VOV                       # 实际跨导（计入 λ）
RO   = 1.0 / (LAMBDA * ID_real)          # 输出电阻
AV_ideal = -GM_IDEAL * rd                 # 忽略 ro 与 λ
AV_real  = -GM * (rd * RO) / (rd + RO)   # 计入 ro

print("=" * 68)
print("  ③ NMOS 共源级放大电路")
print("=" * 68)
print(f"  VDD={vdd:.0f}V  Rg1={rg1/1000:.0f}kΩ  Rg2={rg2/1000:.0f}kΩ  Rd={rd/1000:.0f}kΩ")
print(f"  NMOS: K={K_PARAM*1000:.2f} mA/V²  Vth={VTH_N} V  λ={LAMBDA} /V")
print(f"  输入: {float(VI_AMP)*1000:.0f} mV / {float(VI_FREQ)/1000:.0f} kHz 正弦波")

print("\n【一、手算静态工作点】")
print("-" * 68)
print(f"  栅极分压   V_G  = VDD·Rg2/(Rg1+Rg2) = {vdd:.0f}×{rg2/1000:.0f}/{((rg1+rg2)/1000):.0f}"
      f" = {VG:.4f} V")
print(f"  栅源电压   V_GS = V_G − 0            = {VGS:.4f} V")
print(f"  过驱动电压 V_ov = V_GS − Vth         = {VOV:.4f} V")
print(f"  漏极电流   I_D  = ½K·V_ov²           = {ID_ideal*1000:.4f} mA   (忽略 λ)")
print(f"  漏源电压   V_DS = VDD − I_D·Rd       = {VDS_ideal:.4f} V")
print(f"  饱和判据   V_DS > V_ov ?  {VDS_ideal:.4f} > {VOV:.4f}  →  "
      f"{'✅ 工作在饱和区' if VDS_ideal > VOV else '❌ 线性区'}")
print()
print(f"  计入 λ 迭代后：I_D = {ID_real*1000:.4f} mA,  V_DS = {VDS_real:.4f} V")

print("\n【二、手算小信号参数】")
print("-" * 68)
print(f"  跨导  gm = K·V_ov   (忽略 λ) = {GM_IDEAL*1000:.4f} mA/V")
print(f"        gm = 2·I_D/V_ov (计入 λ) = {GM*1000:.4f} mA/V")
print(f"  输出电阻   ro = 1/(λ·I_D)           = {RO/1000:.2f} kΩ")
print(f"  增益(忽略 ro) Av = −gm·Rd           = {AV_ideal:.4f}")
print(f"  增益(计入 ro) Av = −gm·(Rd∥ro)      = {AV_real:.4f}")
print(f"  预期输出幅度 |vo| = |Av|·|vi|       = {abs(AV_real)*float(VI_AMP)*1000:.2f} mV"
      f" (峰值)")

# ==================== 搭建电路 ====================
circuit = Circuit('NMOS Common Source Amplifier')

# MOS 模型：SPICE Level 1
circuit.model('NMOD', 'NMOS',
              LEVEL=1, VTO=VTH_N, KP=K_PARAM,
              LAMBDA=LAMBDA, W=1 @u_um, L=1 @u_um)

circuit.V('DD', 'vdd', circuit.gnd, VDD)
circuit.R('g1', 'vdd', 'g', RG1)
circuit.R('g2', 'g', circuit.gnd, RG2)
circuit.R('d', 'vdd', 'd', RD)
circuit.C('b1', 'vin', 'g', CB1)
circuit.SinusoidalVoltageSource('in', 'vin', circuit.gnd,
                                amplitude=VI_AMP,
                                frequency=VI_FREQ,
                                offset=0 @u_V)
# 漏极 d、栅极 g、源极 s(=gnd)、衬底 b(=s)
circuit.MOSFET('1', 'd', 'g', circuit.gnd, circuit.gnd, model='NMOD')

print("\n【三、生成的 SPICE 网表】")
print("-" * 68)
print(circuit)

# ==================== 仿真 1：直流工作点 ====================
print("\n【四、仿真验证 —— 直流工作点】")
print("-" * 68)
sim = circuit.simulator(temperature=25, nominal_temperature=25)
op = sim.operating_point()

v_g  = val(op['g'])
v_d  = val(op['d'])
v_s  = 0.0
id_sim = (vdd - v_d) / rd            # 通过 Rd 的电流

print(f"  仿真 V_G  = {v_g:.6f} V     手算 {VG:.4f} V     误差 {abs(v_g-VG)/VG*100:.4f} %")
print(f"  仿真 V_GS = {v_g-v_s:.6f} V     手算 {VGS:.4f} V")
print(f"  仿真 V_DS = {v_d-v_s:.6f} V     手算 {VDS_real:.4f} V   "
      f"误差 {abs((v_d-v_s)-VDS_real)/VDS_real*100:.4f} %")
print(f"  仿真 I_D  = {id_sim*1000:.6f} mA  手算 {ID_real*1000:.4f} mA   "
      f"误差 {abs(id_sim-ID_real)/ID_real*100:.4f} %")
print(f"  饱和判据  V_DS({v_d:.3f}V) > V_ov({VOV:.3f}V)  →  "
      f"{'✅ 饱和区' if v_d > VOV else '❌ 线性区'}")

# ==================== 仿真 1.5：gm 的仿真测量 ====================
print("\n【四·补、跨导 gm 的仿真测量】")
print("-" * 68)
print("  方法：栅极加理想电压源、漏源之间也加理想电压源（把 V_DS 钉在 Q 点值），")
print("        在 Q 点两侧各取一点，用两点差分 gm = ΔI_D/ΔV_GS 求跨导。")
print("        注意 V_DS 必须固定，否则测到的是'沿负载线的斜率'而非 gm")


def measure_id_fixed_vds(vg_value, vds_value):
    """固定 V_DS，测漏极电流"""
    c = Circuit('gm fixed vds')
    c.model('NMOD', 'NMOS', LEVEL=1, VTO=VTH_N, KP=K_PARAM,
            LAMBDA=LAMBDA, W=1 @u_um, L=1 @u_um)
    c.V('DS', 'd', c.gnd, vds_value @u_V)
    c.V('G', 'g', c.gnd, vg_value @u_V)
    c.MOSFET('1', 'd', 'g', c.gnd, c.gnd, model='NMOD')
    s = c.simulator(temperature=25, nominal_temperature=25)
    o = s.operating_point()
    return abs(float(np.asarray(o.branches['vds']).flatten()[0]))


DV = 0.05                                     # 差分步长 ±50 mV
id_p = measure_id_fixed_vds(VGS + DV, VDS_real)
id_m = measure_id_fixed_vds(VGS - DV, VDS_real)
gm_sim = (id_p - id_m) / (2 * DV)

print(f"  固定 V_DS = {VDS_real:.4f} V")
print(f"  V_GS = {VGS-DV:.3f} V 时  I_D = {id_m*1000:.6f} mA")
print(f"  V_GS = {VGS+DV:.3f} V 时  I_D = {id_p*1000:.6f} mA")
print(f"  仿真 gm = ΔI_D/ΔV_GS = {gm_sim*1000:.4f} mA/V")
print(f"  手算 gm = {GM*1000:.4f} mA/V   （计入 λ）")
print(f"  误差    = {abs(gm_sim-GM)/GM*100:.2f} %")

# ==================== 仿真 2：瞬态分析 ====================
print("\n【五、仿真验证 —— 瞬态分析与实测增益】")
print("-" * 68)

period = 1.0 / float(VI_FREQ)
tran = sim.transient(step_time=period/2000, end_time=10*period)

t  = np.array(tran.time)
vi = np.array(tran['vin']).flatten()
vo = np.array(tran['d']).flatten()

# 取最后一个完整周期做幅度与相位测量（此时耦合电容已稳定）
mask = t >= (t[-1] - period)
vi_m = vi[mask]; vo_m = vo[mask]; t_m = t[mask]

vi_amp_sim = (vi_m.max() - vi_m.min()) / 2
vo_amp_sim = (vo_m.max() - vo_m.min()) / 2
gain_sim   = vo_amp_sim / vi_amp_sim

# 相位差：用单频 DFT 提取基波相位（比找峰值稳健，不受采样点影响）
f0  = float(VI_FREQ)
ref = np.exp(-2j * np.pi * f0 * t_m)
Va  = np.sum((vi_m - vi_m.mean()) * ref)
Vb  = np.sum((vo_m - vo_m.mean()) * ref)
phase_shift = float(np.degrees(np.angle(Vb) - np.angle(Va)))
while phase_shift >  180: phase_shift -= 360
while phase_shift < -180: phase_shift += 360

print(f"  输入幅度 (实测) : {vi_amp_sim*1000:.4f} mV")
print(f"  输出幅度 (实测) : {vo_amp_sim*1000:.4f} mV")
print(f"  实测增益 |Av|   : {gain_sim:.4f}")
print(f"  手算增益 |Av|   : {abs(AV_real):.4f}   (忽略 ro 时 {abs(AV_ideal):.4f})")
print(f"  增益误差        : {abs(gain_sim-abs(AV_real))/abs(AV_real)*100:.2f} %")
inverted = abs(abs(phase_shift) - 180) < 15
print(f"  输出相位        : {phase_shift:.1f}°   " f"{'✅ 反相，符合共源放大器' if inverted else '⚠️ 未反相'}")

# ==================== 画图 ====================
import schemdraw
import schemdraw.elements as elm
schemdraw.config(font='Microsoft YaHei', fontsize=13, lw=1.9)

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
os.makedirs(out_dir, exist_ok=True)

# --- 图 0：原电路图 ---
with schemdraw.Drawing(file=os.path.join(out_dir, '03a_circuit.png'), show=False) as d:
    d.config(unit=2.3)
    # 顶部 VDD 电源轨
    d += elm.Line().at((0, 0)).to((7.2, 0))
    d += elm.Vdd().at((0, 0)).up().label('$V_{DD}=5$ V', loc='top')

    # Rg1
    d += elm.Resistor().at((1.6, 0)).down().to((1.6, -2.7)) \
            .label('$R_{g1}$\n60 kΩ', loc='bottom')
    gnode = (1.6, -2.7)
    d += elm.Dot().at(gnode)

    # Rg2
    d += elm.Resistor().at(gnode).down().to((1.6, -5.2)) \
            .label('$R_{g2}$\n40 kΩ', loc='bottom')
    d += elm.Ground().at((1.6, -5.2))

    # 输入支路：vi + Cb1
    d += elm.SourceSin().at((-1.8, -5.2)).up().to((-1.8, -2.7)) \
            .label('$v_i$', loc='left')
    d += elm.Ground().at((-1.8, -5.2))
    d += elm.Capacitor().at((-1.8, -2.7)).right().to((1.6, -2.7)) \
            .label('$C_{b1}$', loc='top')

    # Rd
    d += elm.Resistor().at((4.9, 0)).down().to((4.9, -2.7)) \
            .label('$R_d$\n2 kΩ', loc='right')
    dnode = (4.9, -2.7)
    d += elm.Dot().at(dnode)

    # MOSFET
    Q = elm.NFet().at(dnode).anchor('drain').label('T', loc='center')
    d += Q

    # 栅极连到分压节点
    d += elm.Line().at(Q.gate).to((1.6, Q.gate[1]))
    d += elm.Line().at((1.6, Q.gate[1])).to(gnode)

    # 源极接地
    d += elm.Line().at(Q.source).down().to((4.9, -5.2))
    d += elm.Ground().at((4.9, -5.2))

    # 输出
    d += elm.Line().at(dnode).right().to((7.2, -2.7))
    d += elm.Dot(open=True).at((7.2, -2.7)).label('$v_o$', loc='right', fontsize=13)

    d += elm.Label().at((2.7, 1.35)) \
            .label('NMOS 共源级放大电路', fontsize=13)
print(f"\n[图] 原电路图  → images/03a_circuit.png")

fig = plt.figure(figsize=(11, 8.5))
gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 0.9], hspace=0.45)

ax1 = fig.add_subplot(gs[0])
ax1.plot(t*1000, vi*1000, color='#1f77b4', linewidth=2)
ax1.set_ylabel('$v_i$ (mV)', fontsize=11)
ax1.set_title('③ NMOS 共源放大电路 — 输入输出波形', fontsize=13, pad=10)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, t[-1]*1000)
ax1.text(0.02, 0.85, f'输入 {vi_amp_sim*1000:.2f} mV / 1 kHz',
         transform=ax1.transAxes, fontsize=10,
         bbox=dict(boxstyle='round', fc='#e8f2ff', ec='#1f77b4'))

ax2 = fig.add_subplot(gs[1], sharex=ax1)
ax2.plot(t*1000, vo*1000, color='#d62728', linewidth=2)
ax2.set_ylabel('$v_o$ (mV)', fontsize=11)
ax2.set_xlabel('时间 (ms)', fontsize=11)
ax2.grid(True, alpha=0.3)
ax2.text(0.02, 0.82, f'输出 {vo_amp_sim*1000:.2f} mV，与输入反相',
         transform=ax2.transAxes, fontsize=10,
         bbox=dict(boxstyle='round', fc='#ffecec', ec='#d62728'))

ax3 = fig.add_subplot(gs[2])
labels = ['手算\n(忽略 $r_o$)', '手算\n(计入 $r_o$)', '仿真\n实测']
values = [abs(AV_ideal), abs(AV_real), gain_sim]
colors = ['#94a3b8', '#60a5fa', '#d62728']
bars = ax3.bar(labels, values, color=colors, alpha=0.88, width=0.55)
for b, vv in zip(bars, values):
    ax3.text(b.get_x()+b.get_width()/2, vv+0.02, f'{vv:.3f}',
             ha='center', fontsize=11, fontweight='bold')
ax3.set_ylabel('|$A_v$|', fontsize=11)
ax3.set_title('增益对比：手算 vs 仿真', fontsize=12)
ax3.grid(True, axis='y', alpha=0.3)
ax3.set_ylim(0, max(values)*1.22)

plt.savefig(os.path.join(out_dir, '03_nmos_cs_amp.png'), dpi=150, bbox_inches='tight')
plt.close()

# 额外：工作点标注图（转移特性 + 负载线）
fig2, ax = plt.subplots(figsize=(8, 5.5))
vgs_scan = np.linspace(0, 3, 400)
id_sat = np.where(vgs_scan > VTH_N,
                  0.5*K_PARAM*(vgs_scan - VTH_N)**2 * (1 + LAMBDA*VDS_real), 0)
ax.plot(vgs_scan, id_sat*1000, color='#2ca02c', linewidth=2,
        label='转移特性 $I_D$–$V_{GS}$（$V_{DS}$=%.2f V）' % VDS_real)
ax.plot([VGS], [ID_real*1000], 'o', color='#d62728', markersize=11, zorder=5,
        label=f'静态工作点 Q ({VGS:.2f} V, {ID_real*1000:.3f} mA)')
ax.axvline(VTH_N, color='gray', linestyle='--', linewidth=1.2,
           label=f'$V_{{th}}$ = {VTH_N} V')
ax.axhline(ID_real*1000, color='#d62728', linestyle=':', linewidth=1, alpha=0.6)
ax.set_xlabel('$V_{GS}$ (V)', fontsize=11)
ax.set_ylabel('$I_D$ (mA)', fontsize=11)
ax.set_title('③ 静态工作点 Q 在转移特性上的位置', fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9.5)
ax.set_xlim(0, 3); ax.set_ylim(0, max(id_sat)*1000*1.15)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '03_nmos_qpoint.png'), dpi=150, bbox_inches='tight')
plt.close()

print(f"\n[波形图已保存]")
print(f"  {os.path.join(out_dir, '03_nmos_cs_amp.png')}")
print(f"  {os.path.join(out_dir, '03_nmos_qpoint.png')}")
print("=" * 68)


# ==================== 附加图：直流通路 与 小信号等效模型 ====================
# （作业③要求的另外两张图）

#  A. 直流通路：Cb1 开路，只留偏置网络 + MOSFET + Rd
# ============================================================
path_a = os.path.join(out_dir, '03a_dc_path.png')
with schemdraw.Drawing(file=path_a, show=False) as d:
    d.config(unit=2.6)

    # 顶部电源轨
    d += elm.Line().at((0, 0)).to((6.6, 0))
    d += elm.Vdd().at((0, 0)).up().label('$V_{DD}=5$ V', loc='top')

    # 左支 Rg1
    d += elm.Resistor().at((1.6, 0)).down().label('$R_{g1}$\n60 kΩ', loc='bottom')
    gnode = (1.6, -2.8)
    d += elm.Dot().at(gnode)

    # Rg2 到地
    d += elm.Resistor().at(gnode).down().label('$R_{g2}$\n40 kΩ', loc='bottom')
    d += elm.Ground().at((1.6, -5.6))

    # 右支 Rd
    d += elm.Resistor().at((5.0, 0)).down().label('$R_d$\n2 kΩ', loc='bottom')
    dnode = (5.0, -2.8)
    d += elm.Dot().at(dnode)

    # MOSFET
    Q = elm.NFet().at(dnode).anchor('drain').label('T', loc='center')
    d += Q

    # 栅极接到分压点
    d += elm.Line().at(Q.gate).to((1.6, Q.gate[1]))
    d += elm.Line().at((1.6, Q.gate[1])).to(gnode)

    # 源极 / 衬底接地
    d += elm.Line().at(Q.source).down().to((5.0, -5.6))
    d += elm.Ground().at((5.0, -5.6))

    # 关键工作点标注
    d += elm.Label().at((1.6, -6.6)).label('$V_G = V_{GS} = 2$ V', fontsize=11.5)
    d += elm.Label().at((5.2, -6.6)).label('$V_D = V_{DS} = 4.13$ V', fontsize=11.5)
    d += elm.Label().at((3.3, -7.5)) \
            .label('$I_D \\approx 0.43$ mA （工作在饱和区）',
                   fontsize=11.5, color='#d62728')
    d += elm.Label().at((3.3, 1.5)) \
            .label('直流通路（$C_{b1}$ 开路，输入源置零）', fontsize=12.5)

print(f"[图 A] {path_a}")


# ============================================================
#  B. 小信号等效模型
# ============================================================
path_b = os.path.join(out_dir, '03b_small_signal.png')
with schemdraw.Drawing(file=path_b, show=False) as d:
    d.config(unit=3.1)

    TOP = -1.6
    BOT = -5.4

    # ---- 输入源 vi ----
    d += elm.SourceSin().at((0.4, BOT)).up().to((0.4, TOP)).label('$v_i$', loc='left')
    d += elm.Ground().at((0.4, BOT))

    # ---- 顶部公共线（栅极节点）----
    d += elm.Line().at((0.4, TOP)).to((9.6, TOP))
    d += elm.Dot().at((0.4, TOP)).label('$g$', loc='left')

    # ---- Rg1 ∥ Rg2 ----
    d += elm.Resistor().at((2.4, TOP)).down().to((2.4, BOT)) \
            .label('$R_{g1}\\,\\|\\,R_{g2}$', loc='left')
    d += elm.Label().at((2.4, BOT - 0.62)).label('24 kΩ', fontsize=10.5)
    d += elm.Ground().at((2.4, BOT))

    # ---- 受控电流源 gm·vgs ----
    d += elm.SourceControlledI().at((5.0, TOP)).down().to((5.0, BOT)) \
            .label('$g_m v_{gs}$', loc='left')
    d += elm.Label().at((5.0, BOT - 0.62)).label('0.866 mA/V', fontsize=10.5)

    # ---- ro ----
    d += elm.Resistor().at((7.0, TOP)).down().to((7.0, BOT)) \
            .label('$r_o$', loc='left')
    d += elm.Label().at((7.0, BOT - 0.62)).label('115 kΩ', fontsize=10.5)

    # ---- Rd（VDD 交流接地）----
    d += elm.Resistor().at((9.0, TOP)).down().to((9.0, BOT)) \
            .label('$R_d$', loc='left')
    d += elm.Label().at((9.0, BOT - 0.62)).label('2 kΩ', fontsize=10.5)

    # ---- 底部公共地线 ----
    d += elm.Line().at((2.4, BOT)).to((9.0, BOT))
    d += elm.Ground().at((5.9, BOT))

    # ---- 输出节点 ----
    d += elm.Dot().at((9.0, TOP)).label('$d$', loc='top')
    d += elm.Line().at((9.0, TOP)).right().to((10.2, TOP))
    d += elm.Dot(open=True).at((10.2, TOP))
    d += elm.Label().at((10.45, TOP)).label('$v_o$', loc='right', fontsize=13)

    # ---- 说明 ----
    d += elm.Label().at((5.0, TOP + 1.15)) \
            .label('$v_{gs} = v_i$（源极交流接地，$V_{DD}$ 亦接地）',
                   fontsize=12, color='#2ca02c')

print(f"[图 B] {path_b}")
print("\n完成。")
