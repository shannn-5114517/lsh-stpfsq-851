# -*- coding: utf-8 -*-
"""
参数探索实验 —— 用仿真看「参数一变，结果怎么变」

⚠️ 本脚本完全独立，**不会改动**作业脚本（01/02/03_*.py）。

运行：python parameter_explorer.py
输出：控制台对比表 + experiments/images/ 里的规律图

三个实验：
  实验一  RC 低通     改变 R，看时间常数 τ 和截止频率 fc 怎么变
  实验二  戴维南定理   改变 R2，看等效电压 V_th 和等效电阻 R_th 怎么变
  实验三  NMOS 共源   改变 R_d，看静态工作点会不会掉出饱和区
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
    """把 PySpice 的返回值转成 float"""
    return float(np.asarray(x).flatten()[0])


# ══════════════════════════════════════════════════════════════════
#  实验一：RC 低通 —— 改变 R
# ══════════════════════════════════════════════════════════════════
def exp1_rc():
    print("\n" + "=" * 78)
    print("  实验一：RC 低通滤波 —— 改变 R，看 τ 和 fc 怎么变")
    print("=" * 78)
    print("  固定：C = 100 nF        变量：R")
    print()
    print(f"  {'R (kΩ)':>8} {'τ = RC (μs)':>14} {'fc = 1/(2πRC) (Hz)':>21} {'仿真 fc (Hz)':>14} {'误差':>8}")
    print("  " + "-" * 72)

    C_FAR = 1000e-9
    R_LIST = [0.1,0.5, 1, 5, 10, 50]

    rows = []
    curves = []
    for r_k in R_LIST:
        R = r_k * 1000
        tau = R * C_FAR
        fc_theory = 1 / (2 * np.pi * R * C_FAR)

        # 用仿真验证
        c = Circuit(f'RC R={r_k}k')
        c.SinusoidalVoltageSource('in', 'vin', c.gnd, amplitude=1 @ u_V)
        c.R('1', 'vin', 'vo', r_k @ u_kOhm)
        c.C('1', 'vo', c.gnd, C_FAR @ u_F)      # 用变量，别写死
        sim = c.simulator(temperature=25, nominal_temperature=25)
        # 扫频范围 1 Hz ~ 10 MHz（比原来的 10 Hz~1 MHz 更宽，避免 fc 掉出范围）
        ac = sim.ac(start_frequency=1 @ u_Hz, stop_frequency=10 @ u_MHz,
                    number_of_points=60, variation='dec')
        freq = np.array(ac.frequency)
        vo = np.asarray(ac['vo'])
        gain_db = 20 * np.log10(np.abs(vo))

        # 从仿真曲线里找 -3dB 点
        idx = int(np.argmin(np.abs(gain_db + 3.0)))
        fc_sim = float(freq[idx])
        err = abs(fc_sim - fc_theory) / fc_theory * 100

        # 范围检查：如果真 fc 落在扫频范围之外，测出来的一定不准
        warn = ''
        if fc_theory < float(freq[0]) or fc_theory > float(freq[-1]):
            warn = '  ⚠️ fc 超出扫频范围！'
        elif idx == 0 or idx == len(freq) - 1:
            warn = '  ⚠️ −3dB 点落在边界上，结果不可信'

        rows.append((r_k, tau * 1e6, fc_theory, fc_sim, err))
        curves.append((r_k, freq, gain_db, np.degrees(np.angle(vo))))
        print(f"  {r_k:>8.1f} {tau*1e6:>14.1f} {fc_theory:>21.1f} {fc_sim:>14.1f} {err:>7.2f}%{warn}")

    # 画图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 7.5), sharex=True)
    colors = plt.cm.viridis(np.linspace(0, 0.85, len(curves)))

    for k, (r_k, freq, gain_db, phase) in enumerate(curves):
        ax1.semilogx(freq, gain_db, color=colors[k], lw=1.9, label=f'R = {r_k:g} kΩ')
        ax2.semilogx(freq, phase, color=colors[k], lw=1.9)

    ax1.axhline(-3, color='red', ls=':', lw=1.4)
    ax1.text(12, -2.6, '−3 dB', color='red', fontsize=10)
    ax1.set_ylabel('幅值 (dB)', fontsize=11)
    ax1.set_title('实验一：改变 R，看截止频率往哪边跑', fontsize=13)
    ax1.grid(True, which='both', alpha=0.25)
    ax1.legend(fontsize=9, loc='lower left')
    ax1.set_ylim(-45, 3)

    ax2.axhline(-45, color='red', ls=':', lw=1.4)
    ax2.set_ylabel('相位 (°)', fontsize=11)
    ax2.set_xlabel('频率 (Hz)', fontsize=11)
    ax2.grid(True, which='both', alpha=0.25)
    ax2.set_ylim(-95, 5)

    plt.tight_layout()
    plt.savefig(os.path.join(IMG, 'exp1_rc_sweep.png'), dpi=150, bbox_inches='tight')
    plt.close()

    print()
    print("  💡 规律总结")
    print("     · R 增大 → τ = RC 变大 → fc = 1/(2πτ) 变小")
    print("     · R 每翻一倍，τ 也翻一倍，fc 就减半（反比关系）")
    print("     · 每条波特图的形状完全一样，只是整体左右平移")
    print("     · 高频段斜率都是 −20 dB/十倍频，和 R 取多少无关")
    print(f"\n  [图] → experiments/images/exp1_rc_sweep.png")


# ══════════════════════════════════════════════════════════════════
#  实验二：戴维南 —— 改变 R2
# ══════════════════════════════════════════════════════════════════
def exp2_thevenin():
    print("\n" + "=" * 78)
    print("  实验二：戴维南定理 —— 改变 R2，看等效电源怎么变")
    print("=" * 78)
    print("  固定：V1 = 20 V，R1 = 1.5 kΩ        变量：R2")
    print()
    print(f"  {'R2 (kΩ)':>8} {'V_th (V)':>10} {'R_th (kΩ)':>11} {'I_sc (mA)':>11} "
          f"{'仿真 V_oc (V)':>14} {'误差':>8}")
    print("  " + "-" * 74)

    V1, R1 = 20.0, 1.5
    R2_LIST = [0.1,1,10,100,1000]

    vths, rths, r2s = [], [], []
    for r2 in R2_LIST:
        vth = V1 * r2 / (R1 + r2)
        rth = R1 * r2 / (R1 + r2)
        isc = vth / rth

        # 仿真：开路测 V_oc
        c = Circuit(f'Thevenin R2={r2}k')
        c.V('1', 'n1', c.gnd, V1 @ u_V)
        c.R('1', 'n1', 'a', R1 @ u_kOhm)
        c.R('2', 'a', c.gnd, r2 @ u_kOhm)
        c.R('L', 'a', c.gnd, 1 @ u_GOhm)      # 近似开路
        sim = c.simulator(temperature=25, nominal_temperature=25)
        op = sim.operating_point()
        voc = val(op['a'])
        err = abs(voc - vth) / vth * 100

        vths.append(vth); rths.append(rth); r2s.append(r2)
        print(f"  {r2:>8.1f} {vth:>10.4f} {rth:>11.4f} {isc:>11.4f} {voc:>14.4f} {err:>7.3f}%")

    # 画图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))

    ax1.plot(r2s, vths, 'o-', color='#2563eb', lw=2, ms=7)
    for x, y in zip(r2s, vths):
        ax1.annotate(f'{y:.2f}', (x, y), textcoords='offset points',
                     xytext=(0, 9), ha='center', fontsize=9)
    ax1.axhline(V1, color='gray', ls='--', lw=1.2)
    ax1.text(1.2, V1 - 1.2, f'上限 = V1 = {V1:g} V（R2→∞ 时）', fontsize=9, color='gray')
    ax1.set_xscale('log')                       # 横轴跨度大，用对数轴才看得清
    ax1.set_xlabel('R2 (kΩ) —— 对数轴', fontsize=11)
    ax1.set_ylabel('V_th (V)', fontsize=11)
    ax1.set_title('R2 越大，V_th 越接近 V1', fontsize=12)
    ax1.grid(True, which='both', alpha=0.3)
    ax1.set_ylim(0, V1 + 2)

    ax2.plot(r2s, rths, 's-', color='#dc2626', lw=2, ms=7)
    for x, y in zip(r2s, rths):
        ax2.annotate(f'{y:.3f}', (x, y), textcoords='offset points',
                     xytext=(0, 9), ha='center', fontsize=9)
    ax2.axhline(R1, color='gray', ls='--', lw=1.2)
    ax2.text(0.13, R1 - 0.32, f'上限 = R1 = {R1:g} kΩ', fontsize=9, color='gray')
    ax2.set_xscale('log')
    ax2.set_xlabel('R2 (kΩ) —— 对数轴', fontsize=11)
    ax2.set_ylabel('R_th (kΩ)', fontsize=11)
    ax2.set_title('R2 越大，R_th 越接近 R1', fontsize=12)
    ax2.grid(True, which='both', alpha=0.3)
    ax2.set_ylim(0, R1 + 0.5)

    plt.suptitle('实验二：改变 R2，看戴维南等效参数怎么变', fontsize=13.5, y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG, 'exp2_thevenin_sweep.png'), dpi=150, bbox_inches='tight')
    plt.close()

    print()
    print("  💡 规律总结")
    print("     · R2 增大 → 分压点抬高 → V_th 增大，最终趋近 V1 = 20 V")
    print("     · R2 增大 → 并联电阻变大 → R_th 增大，最终趋近 R1 = 1.5 kΩ")
    print("     · 两个量都单调变化，但 V_th 是「减速上升」，R_th 也是")
    print("     · R2 = R1 时，V_th = V1/2 = 10 V，R_th = R1/2 = 0.75 kΩ")
    print(f"\n  [图] → experiments/images/exp2_thevenin_sweep.png")


# ══════════════════════════════════════════════════════════════════
#  实验三：NMOS 共源 —— 改变 R_d
# ══════════════════════════════════════════════════════════════════
def exp3_nmos():
    print("\n" + "=" * 78)
    print("  实验三：NMOS 共源放大 —— 改变 R_d，看工作点会不会掉出饱和区")
    print("=" * 78)
    print("  固定：V_DD = 5 V，Rg1 = 60 kΩ，Rg2 = 40 kΩ，K = 0.8 mA/V²，")
    print("        V_th = 1 V，λ = 0.02 /V        变量：R_d")
    print()

    VDD = 3.0
    RG1, RG2 = 60.0, 40.0
    K, VTH, LAM = 0.8e-3, 1.0, 0.02
    VG = VDD * RG2 / (RG1 + RG2)      # = 2 V
    VOV = VG - VTH                     # = 1 V

    # 先固定 V_GS 做 gm 测量（用差分法）
    def gm_measure(vds):
        def id_at(vg):
            c = Circuit('gm')
            c.model('NMOD', 'NMOS', LEVEL=1, VTO=VTH, KP=K, LAMBDA=LAM,
                    W=1 @ u_um, L=1 @ u_um)
            c.V('DS', 'd', c.gnd, vds @ u_V)
            c.V('G', 'g', c.gnd, vg @ u_V)
            c.MOSFET('1', 'd', 'g', c.gnd, c.gnd, model='NMOD')
            o = c.simulator(temperature=25, nominal_temperature=25).operating_point()
            return abs(val(o.branches['vds']))

        dv = 0.05
        return (id_at(VG + dv) - id_at(VG - dv)) / (2 * dv)

    print(f"  {'Rd (kΩ)':>8} {'I_D (mA)':>10} {'V_DS (V)':>10} {'V_GS−V_th (V)':>14} "
          f"{'工作区':>9} {'g_m (mA/V)':>12} {'|A_v|':>8}")
    print("  " + "-" * 78)

    RD_LIST = [0.5, 1, 1.5, 2, 2.5, 3, 4, 6]
    rds, vdss, avs, ids = [], [], [], []

    for rd_k in RD_LIST:
        rd = rd_k * 1000
        # 手算（计入 λ，解一次方程）
        a = 0.5 * K * VOV ** 2
        id_ = a * (1 + LAM * VDD) / (1 + a * LAM * rd)
        vds = VDD - id_ * rd

        # 判断工作区
        if VG <= VTH:
            region = '截止'
        elif vds < VOV:
            region = '线性区'
        else:
            region = '饱和区'

        # 仿真验证
        c = Circuit(f'NMOS Rd={rd_k}k')
        c.model('NMOD', 'NMOS', LEVEL=1, VTO=VTH, KP=K, LAMBDA=LAM,
                W=1 @ u_um, L=1 @ u_um)
        c.V('DD', 'vdd', c.gnd, VDD @ u_V)
        c.V('G', 'g', c.gnd, VG @ u_V)
        c.R('d', 'vdd', 'd', rd_k @ u_kOhm)      # 注意用 rd_k（kΩ 数值），不是 rd（欧姆）
        c.MOSFET('1', 'd', 'g', c.gnd, c.gnd, model='NMOD')
        o = c.simulator(temperature=25, nominal_temperature=25).operating_point()
        vds_sim = val(o['d'])
        id_sim = (VDD - vds_sim) / rd

        if id_sim > 1e-9 and vds_sim > VOV:
            gm = gm_measure(vds_sim)
            # λ = 0 表示没有沟道长度调制，管子是「理想恒流源」，此时 ro → ∞
            if LAM > 0:
                ro = 1 / (LAM * id_sim)
                av = gm * (rd * ro) / (rd + ro)
            else:
                ro = float('inf')
                av = gm * rd
        else:
            gm, ro, av = 0.0, float('inf'), 0.0

        rds.append(rd_k); vdss.append(vds_sim); avs.append(av); ids.append(id_sim * 1000)
        print(f"  {rd_k:>8.1f} {id_sim*1000:>10.4f} {vds_sim:>10.4f} {VOV:>14.4f} "
              f"{region:>9} {gm*1000:>12.4f} {av:>8.4f}")

    # 画图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8))

    ax1.plot(rds, vdss, 'o-', color='#7c3aed', lw=2, ms=7, label='V_DS（仿真）')
    ax1.axhline(VOV, color='#dc2626', ls='--', lw=1.8, label=f'饱和边界 V_DS = V_ov = {VOV:g} V')
    ax1.fill_between([min(rds), max(rds)], VOV, max(vdss) + 0.5,
                     color='#dcfce7', alpha=0.5, zorder=0)
    ax1.text(min(rds) + 0.15, max(vdss) - 0.35, '饱和区（能放大）', fontsize=10, color='#15803d')
    ax1.text(min(rds) + 0.15, VOV + 0.12, '线性区（不能放大）', fontsize=10, color='#b91c1c')
    ax1.set_xlabel('R_d (kΩ)', fontsize=11)
    ax1.set_ylabel('V_DS (V)', fontsize=11)
    ax1.set_title('R_d 太大 → V_DS 掉到饱和边界以下', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9, loc='upper right')

    ax2.plot(rds, avs, 's-', color='#0891b2', lw=2, ms=7)
    for x, y in zip(rds, avs):
        ax2.annotate(f'{y:.3f}', (x, y), textcoords='offset points',
                     xytext=(0, 9), ha='center', fontsize=9)
    ax2.set_xlabel('R_d (kΩ)', fontsize=11)
    ax2.set_ylabel('|A_v|（电压增益）', fontsize=11)
    ax2.set_title('增益随 R_d 增大而增大（但在饱和区内才有意义）', fontsize=12)
    ax2.grid(True, alpha=0.3)

    plt.suptitle('实验三：改变 R_d，看静态工作点会不会掉出饱和区', fontsize=13.5, y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG, 'exp3_nmos_sweep.png'), dpi=150, bbox_inches='tight')
    plt.close()

    # 找临界值
    a = 0.5 * K * VOV ** 2
    rd_crit = (VDD - VOV) / (a * (1 + LAM * VOV))
    print()
    print("  💡 规律总结")
    print(f"     · R_d 越大 → 上面压降越大 → V_DS 越小")
    print(f"     · 临界点：R_d 超过约 {rd_crit/1000:.2f} kΩ 时，V_DS 会跌破 V_ov = 1 V")
    print(f"       此时管子从「饱和区」掉进「线性区」，就不再是放大器了")
    print("     · 在饱和区内，增益 |A_v| ≈ g_m·R_d 随 R_d 增大而增大")
    print("     · 这就是「工作点设计」要权衡的地方：")
    print("       想要高增益 → 加大 R_d，但会压缩 V_DS 的余量，容易掉出饱和区")
    print(f"\n  [图] → experiments/images/exp3_nmos_sweep.png")


# ══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("╔" + "═" * 76 + "╗")
    print("║" + "  参数探索实验：改一个参数，看结果怎么变".center(64) + " " * 12 + "║")
    print("║" + "  （独立实验，不会改动作业脚本）".center(66) + " " * 10 + "║")
    print("╚" + "═" * 76 + "╝")

    exp1_rc()
    exp2_thevenin()
    exp3_nmos()

    print("\n" + "=" * 78)
    print("  三个实验都跑完了，图在 experiments/images/ 目录里。")
    print("  想试试别的参数？打开本文件，改上面的 XXX_LIST 列表再跑一次就行。")
    print("=" * 78)
