# -*- coding: utf-8 -*-
"""
作业 ①：RC 低通滤波电路
包含：
  1. 电路图绘制（schemdraw）
  2. AC 扫频分析  → 波特图（幅频 + 相频）
  3. 方波瞬态分析 → 阶跃响应波形，从中测出时间常数 τ
  4. τ 与截止频率 fc 的「手算 vs 仿真」对比

运行：python 01_rc_lowpass_filter.py
输出：images/01_*.png
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


def arr(waveform):
    return np.asarray(waveform).flatten()


# ==================== 电路参数（可自行修改）====================
R_VALUE  = 1.5 @u_kOhm
C_VALUE  = 100 @u_nF
F_START  = 10  @u_Hz
F_STOP   = 1   @u_MHz
N_POINTS = 200          # 每十倍频程点数

SQ_AMP   = 1   @u_V     # 方波幅度
SQ_FREQ  = 500 @u_Hz    # 方波频率（周期 2 ms，与 τ 同量级便于观察充放电）

R_ohm = float(R_VALUE)
C_far = float(C_VALUE)
TAU   = R_ohm * C_far                 # 时间常数 τ = RC
FC    = 1.0 / (2 * np.pi * TAU)       # 截止频率

print("=" * 66)
print("  ① RC 低通滤波电路")
print("=" * 66)
print(f"  R = {R_ohm:.0f} Ω      C = {C_far*1e9:.0f} nF")
print()
print("  【手算】")
print(f"    时间常数  τ  = R·C        = {R_ohm:.0f} × {C_far*1e9:.0f}nF"
      f" = {TAU*1e6:.1f} μs")
print(f"    截止频率  fc = 1/(2πRC)   = {FC:.2f} Hz")
print(f"    上升时间  tr = 2.2τ       = {2.2*TAU*1e6:.1f} μs  (10%→90%)")
print(f"    τ 时刻电压 = 0.632 × 终值 = {0.632:.3f} V  (输入 1 V 时)")


# ==================== 1. 画电路图 ====================
import schemdraw
import schemdraw.elements as elm
schemdraw.config(font='Microsoft YaHei', fontsize=13, lw=1.9)

with schemdraw.Drawing(file=os.path.join(IMG, '01a_circuit.png'), show=False) as d:
    d.config(unit=2.6)
    d += elm.Dot(open=True).at((0, 0)).label('$v_i$', loc='left', fontsize=13)
    d += (R1 := elm.Resistor().at((0, 0)).right().label(f'$R$\n{R_ohm/1000:g} kΩ', loc='top'))
    node = (4.4, 0)
    d += elm.Line().to(node)
    d += elm.Dot().at(node)
    d += (C1 := elm.Capacitor().at(node).down().label(f'$C$\n{C_far*1e9:g} nF', loc='right'))
    d += elm.Ground().at(C1.end)
    d += elm.Line().at(node).right().to((6.4, 0))
    d += elm.Dot(open=True).at((6.4, 0)).label('$v_o$', loc='right', fontsize=13)
    d += elm.Line().at((0, 0)).left().to((-1.2, 0))
    d += elm.Ground().at((-1.2, 0))
    d += elm.Label().at((3.0, 1.4)) \
            .label('RC 低通滤波电路', fontsize=13)
print(f"\n[图] 电路图  → images/01a_circuit.png")


# ==================== 2. AC 扫频分析（波特图）====================
ac_circuit = Circuit('RC Low Pass - AC')
ac_circuit.V('input', 'vin', ac_circuit.gnd, 'AC 1')
ac_circuit.R(1, 'vin', 'vout', R_VALUE)
ac_circuit.C(1, 'vout', ac_circuit.gnd, C_VALUE)

sim_ac = ac_circuit.simulator(temperature=25, nominal_temperature=25)
ac = sim_ac.ac(start_frequency=F_START, stop_frequency=F_STOP,
               number_of_points=N_POINTS, variation='dec')

freq   = arr(ac.frequency)
vout_a = arr(ac['vout'])
vin_a  = arr(ac['vin'])
gain    = vout_a / vin_a
gain_db = 20 * np.log10(np.abs(gain))
phase   = np.angle(gain, deg=True)

idx_fc   = int(np.argmin(np.abs(gain_db + 3.0)))
fc_sim   = freq[idx_fc]
gain_fc  = gain_db[idx_fc]
phase_fc = phase[idx_fc]

slope = (gain_db[-1] - gain_db[np.searchsorted(freq, 1e4)]) / \
        (np.log10(freq[-1]) - np.log10(1e4))


# ==================== 3. 方波瞬态分析（测 τ）====================
sq_circuit = Circuit('RC Low Pass - Square Wave')
period = 1.0 / float(SQ_FREQ)
sq_circuit.PulseVoltageSource(
    'in', 'vin', sq_circuit.gnd,
    initial_value=0 @u_V, pulsed_value=SQ_AMP,
    delay_time=0 @u_s, rise_time=1 @u_ns, fall_time=1 @u_ns,
    pulse_width=(period / 2) @u_s, period=period @u_s)
sq_circuit.R(1, 'vin', 'vout', R_VALUE)
sq_circuit.C(1, 'vout', sq_circuit.gnd, C_VALUE)

sim_sq = sq_circuit.simulator(temperature=25, nominal_temperature=25)
tran = sim_sq.transient(step_time=1 @u_us, end_time=(5 * period) @u_s)

t  = arr(tran.time)
vi = arr(tran['vin'])
vo = arr(tran['vout'])

# --- 从第一个上升沿测 τ ---
# 取第一个周期的充电段
m_chg = (t >= 0) & (t < period * 0.5)
tc = t[m_chg]; vc = vo[m_chg]

v_final = float(SQ_AMP)
target  = 0.632 * v_final
i_tau   = int(np.argmax(vc >= target))
tau_sim = tc[i_tau]

# --- 用 10%→90% 上升时间反推 τ ---
i_10 = int(np.argmax(vc >= 0.1 * v_final))
i_90 = int(np.argmax(vc >= 0.9 * v_final))
tr_sim  = tc[i_90] - tc[i_10]
tau_sim2 = tr_sim / 2.197


# ==================== 4. 输出对比表 ====================
print("\n" + "=" * 66)
print("  【理论值 vs 仿真值 对比表】")
print("=" * 66)
print(f"  {'项目':<26}{'理论值':>14}{'仿真值':>14}{'误差':>12}")
print("  " + "-" * 64)

def row(name, th, sim, unit='', prec=3):
    err = abs(sim - th) / abs(th) * 100 if th else 0
    print(f"  {name:<26}{th:>13.{prec}f}{unit}{sim:>13.{prec}f}{unit}{err:>11.2f}%")

row('时间常数 τ', TAU*1e6, tau_sim*1e6, ' μs')
row('时间常数 τ (10-90%)', TAU*1e6, tau_sim2*1e6, ' μs')
row('上升时间 tr = 2.2τ', 2.2*TAU*1e6, tr_sim*1e6, ' μs')
row('截止频率 fc', FC, fc_sim, ' Hz', 2)
row('fc 处幅值', -3.0, gain_fc, ' dB', 2)
row('fc 处相位', -45.0, phase_fc, ' °', 2)


# ==================== 5. 画图 ====================
# --- 图 1：方波瞬态波形 ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.6), sharex=True)
ax1.plot(t*1000, vi, color='#1f77b4', linewidth=1.8)
ax1.set_ylabel('$v_i$ (V)', fontsize=11)
ax1.set_title('① RC 低通滤波电路 — 方波输入的瞬态响应', fontsize=13, pad=10)
ax1.grid(True, alpha=0.3); ax1.set_ylim(-0.2, 1.3)

ax2.plot(t*1000, vo, color='#d62728', linewidth=1.8, label='输出 $v_o$')
ax2.axhline(0.632, color='#2ca02c', linestyle='--', linewidth=1.1,
            label='0.632 × 终值')
ax2.axvline(tau_sim*1000, color='#2ca02c', linestyle=':', linewidth=1.4)
ax2.plot(tau_sim*1000, 0.632, 'o', color='#2ca02c', markersize=8, zorder=5,
         label=f'实测 τ = {tau_sim*1e6:.1f} μs')
ax2.axvspan(tc[i_10]*1000, tc[i_90]*1000, color='orange', alpha=0.18,
            label=f'10%→90% = {tr_sim*1e6:.1f} μs')
ax2.set_xlabel('时间 (ms)', fontsize=11)
ax2.set_ylabel('$v_o$ (V)', fontsize=11)
ax2.grid(True, alpha=0.3); ax2.set_ylim(-0.05, 1.15)
ax2.legend(fontsize=9.5, loc='upper right')
plt.tight_layout()
plt.savefig(os.path.join(IMG, '01b_square_response.png'), dpi=150, bbox_inches='tight')
plt.close()

# --- 图 2：波特图 ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 7.5), sharex=True)
ax1.semilogx(freq, gain_db, color='#1f77b4', linewidth=2.2, label='仿真幅频特性')
ax1.axhline(-3, color='#d62728', linestyle='--', linewidth=1.2, label='−3 dB 线')
ax1.axvline(FC, color='#2ca02c', linestyle=':', linewidth=1.8,
            label=f'理论 $f_c$ = {FC:.0f} Hz')
ax1.plot(fc_sim, gain_fc, 'o', color='#d62728', markersize=8, zorder=5,
         label=f'实测 −3dB = {fc_sim:.0f} Hz')
ax1.set_ylabel('幅值 (dB)', fontsize=11)
ax1.set_title('① RC 低通滤波电路 — 波特图', fontsize=13, pad=12)
ax1.grid(True, which='both', alpha=0.3); ax1.legend(fontsize=9.5, loc='lower left')
ax1.set_ylim(-45, 5)

ax2.semilogx(freq, phase, color='#9467bd', linewidth=2.2, label='仿真相频特性')
ax2.axvline(FC, color='#2ca02c', linestyle=':', linewidth=1.8)
ax2.axhline(-45, color='#d62728', linestyle='--', linewidth=1.2, label='−45° 线')
ax2.set_xlabel('频率 (Hz)', fontsize=11)
ax2.set_ylabel('相位 (°)', fontsize=11)
ax2.grid(True, which='both', alpha=0.3); ax2.legend(fontsize=9.5)
ax2.set_ylim(-95, 5)
plt.tight_layout()
plt.savefig(os.path.join(IMG, '01c_bode.png'), dpi=150, bbox_inches='tight')
plt.close()

print(f"\n[图] 方波瞬态波形 → images/01b_square_response.png")
print(f"[图] 波特图       → images/01c_bode.png")
print("=" * 66)
