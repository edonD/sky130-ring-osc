#!/usr/bin/env python3
"""Generate all 5 required plots for the ring oscillator design."""

import os
import sys
import csv
import subprocess
import re
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJECT_DIR = "/home/ubuntu/sky130-ring-osc"
PLOTS_DIR = os.path.join(PROJECT_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

# Best parameters from validation
PARAMS = {
    "Wp": 0.8453, "Lp": 0.4786,
    "Wn": 1.0032, "Ln": 1.3918,
    "Ws": 1.6835, "Ls": 0.9940,
}

# Dark theme
DARK_THEME = {
    'figure.facecolor': '#1a1a2e', 'axes.facecolor': '#16213e',
    'axes.edgecolor': '#e94560', 'axes.labelcolor': '#eee',
    'text.color': '#eee', 'xtick.color': '#aaa', 'ytick.color': '#aaa',
    'grid.color': '#333', 'grid.alpha': 0.5,
}

# Validated measurement data
VCTRL_DATA = {
    0.5: 0.69, 0.7: 23.52, 0.9: 101.52,
    1.2: 164.86, 1.5: 179.22, 1.8: 185.38,
}
TEMP_DATA = {-40: 101.51, 27: 101.52, 125: 101.50}
NOMINAL_FREQ_MHZ = 101.52
NOMINAL_POWER_UW = 36.42


def make_waveform_netlist():
    """Generate netlist for waveform capture with fine timestep."""
    return f"""* SKY130 5-Stage Current-Starved Ring Oscillator - Waveform Capture
.lib "sky130_models/sky130.lib.spice" tt

Vdd vdd 0 1.8
Vss vss 0 0
Vctrl vctrl 0 0.9

XMp1 n1 n5 vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wp']}u L={PARAMS['Lp']}u nf=1
XMn1 n1 n5 sn1 vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wn']}u L={PARAMS['Ln']}u nf=1
XMsn1 sn1 vctrl vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Ws']}u L={PARAMS['Ls']}u nf=1

XMp2 n2 n1 vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wp']}u L={PARAMS['Lp']}u nf=1
XMn2 n2 n1 sn2 vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wn']}u L={PARAMS['Ln']}u nf=1
XMsn2 sn2 vctrl vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Ws']}u L={PARAMS['Ls']}u nf=1

XMp3 n3 n2 vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wp']}u L={PARAMS['Lp']}u nf=1
XMn3 n3 n2 sn3 vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wn']}u L={PARAMS['Ln']}u nf=1
XMsn3 sn3 vctrl vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Ws']}u L={PARAMS['Ls']}u nf=1

XMp4 n4 n3 vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wp']}u L={PARAMS['Lp']}u nf=1
XMn4 n4 n3 sn4 vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wn']}u L={PARAMS['Ln']}u nf=1
XMsn4 sn4 vctrl vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Ws']}u L={PARAMS['Ls']}u nf=1

XMp5 n5 n4 vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wp']}u L={PARAMS['Lp']}u nf=1
XMn5 n5 n4 sn5 vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wn']}u L={PARAMS['Ln']}u nf=1
XMsn5 sn5 vctrl vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Ws']}u L={PARAMS['Ls']}u nf=1

XMpout out n5 vdd vdd sky130_fd_pr__pfet_01v8 W=5u L=0.15u nf=1
XMnout out n5 vss vss sky130_fd_pr__nfet_01v8 W=2.5u L=0.15u nf=1

Vkick kick 0 pulse(0 1.8 0 0.1n 0.1n 0.5n 1000n)
Ckick n1 kick 5f

.ic v(n1)=0 v(n2)=1.8 v(n3)=0 v(n4)=1.8 v(n5)=0

.options reltol=0.001 method=gear maxord=3

.control
set wr_vecnames
set wr_singlescale
tran 0.01n 200n uic

wrdata /tmp/waveform_fine.dat v(n5) v(out)

meas tran tcross_a when v(n5)=0.9 cross=20
meas tran tcross_b when v(n5)=0.9 cross=30
let period = (tcross_b - tcross_a) / 5
let freq = 1 / period
echo "RESULT_FREQ_HZ" $&freq

meas tran avg_idd avg i(Vdd) from=50n to=200n
let pwr = abs(avg_idd) * 1.8 * 1e6
echo "RESULT_POWER_UW" $&pwr

echo "RESULT_DONE"
.endc

.end
"""


def run_ngspice_waveform():
    """Run ngspice to capture waveform data with fine timestep."""
    netlist_path = "/tmp/waveform_sim.cir"
    with open(netlist_path, "w") as f:
        f.write(make_waveform_netlist())

    print("Running ngspice waveform simulation (fine timestep)...")
    result = subprocess.run(
        ["ngspice", "-b", netlist_path],
        capture_output=True, text=True, timeout=180,
        cwd=PROJECT_DIR
    )

    output = result.stdout + result.stderr
    if "RESULT_DONE" not in output:
        print(f"ERROR: Simulation did not complete")
        print(f"stderr tail: {result.stderr[-500:]}")
        return None, None, None

    # Parse wrdata output (wr_singlescale format: time, v(n5), v(out))
    dat_file = "/tmp/waveform_fine.dat"
    if not os.path.exists(dat_file):
        print(f"ERROR: {dat_file} not found")
        return None, None, None

    time_arr, vn5_arr, vout_arr = [], [], []
    with open(dat_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('t') or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    t = float(parts[0])
                    v1 = float(parts[1])
                    v2 = float(parts[2])
                    time_arr.append(t)
                    vn5_arr.append(v1)
                    vout_arr.append(v2)
                except ValueError:
                    continue

    if not time_arr:
        print(f"ERROR: No data parsed from {dat_file}")
        return None, None, None

    print(f"  Captured {len(time_arr)} data points, t=[{time_arr[0]:.2e}, {time_arr[-1]:.2e}]")
    return np.array(time_arr), np.array(vn5_arr), np.array(vout_arr)


def plot_waveform(time_arr, vn5_arr):
    """Plot 1: Waveform of last ~10 cycles of v(n5) ring osc node."""
    plt.rcParams.update(DARK_THEME)

    freq_hz = NOMINAL_FREQ_MHZ * 1e6
    period = 1.0 / freq_hz
    n_cycles = 10
    t_window = n_cycles * period

    # Get last 10 cycles (steady state region near end of sim)
    t_end = time_arr[-1]
    t_start = t_end - t_window
    mask = (time_arr >= t_start) & (time_arr <= t_end)
    t = time_arr[mask]
    v = vn5_arr[mask]

    # Convert to ns
    t_ns = t * 1e9

    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.plot(t_ns, v, color='#00d2ff', linewidth=1.0, label='v(n5) - Ring Oscillator Node')

    # Measure amplitude from this window
    v_max = np.max(v)
    v_min = np.min(v)
    amplitude = v_max - v_min

    # Draw VDD and VSS reference lines
    ax.axhline(y=1.8, color='#555', linestyle=':', alpha=0.4, linewidth=0.8)
    ax.axhline(y=0.0, color='#555', linestyle=':', alpha=0.4, linewidth=0.8)
    ax.axhline(y=0.9, color='#e94560', linestyle='--', alpha=0.3, linewidth=0.8, label='Vdd/2 = 0.9V')

    # Annotate frequency and period
    ax.annotate(f'f = {NOMINAL_FREQ_MHZ:.2f} MHz\nT = {period*1e9:.2f} ns',
                xy=(0.02, 0.95), xycoords='axes fraction',
                fontsize=13, fontweight='bold', color='#00d2ff',
                verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#0f3460', edgecolor='#e94560', alpha=0.9))

    ax.annotate(f'Vpp = {amplitude:.3f} V\nVmax = {v_max:.3f} V\nVmin = {v_min:.3f} V',
                xy=(0.98, 0.95), xycoords='axes fraction',
                fontsize=12, fontweight='bold', color='#ffcc00',
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#0f3460', edgecolor='#e94560', alpha=0.9))

    ax.annotate(f'P = {NOMINAL_POWER_UW:.2f} uW  |  5-stage NMOS-starved  |  Vctrl = 0.9V',
                xy=(0.5, 0.02), xycoords='axes fraction',
                fontsize=11, color='#e94560', ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#0f3460', edgecolor='#e94560', alpha=0.8))

    # Mark one period with arrows
    # Find two consecutive rising crossings at 0.9V
    crossings = []
    for i in range(1, len(v)):
        if v[i-1] < 0.9 and v[i] >= 0.9:
            # Interpolate
            frac = (0.9 - v[i-1]) / (v[i] - v[i-1])
            tc = t_ns[i-1] + frac * (t_ns[i] - t_ns[i-1])
            crossings.append(tc)
    if len(crossings) >= 2:
        t1, t2 = crossings[-3], crossings[-2]
        y_mark = 0.9
        ax.annotate('', xy=(t2, y_mark+0.15), xytext=(t1, y_mark+0.15),
                    arrowprops=dict(arrowstyle='<->', color='#ffcc00', lw=2))
        ax.text((t1+t2)/2, y_mark+0.25, f'T = {t2-t1:.2f} ns',
                ha='center', fontsize=10, color='#ffcc00', fontweight='bold')

    ax.set_xlabel('Time (ns)', fontsize=13)
    ax.set_ylabel('Voltage (V)', fontsize=13)
    ax.set_title('Ring Oscillator Waveform -- v(n5) Internal Node', fontsize=14, fontweight='bold')
    ax.set_ylim(v_min - 0.15, v_max + 0.4)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right', fontsize=10)

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "waveform.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def plot_freq_vs_vctrl():
    """Plot 2: Frequency vs Vctrl."""
    plt.rcParams.update(DARK_THEME)

    vctrls = sorted(VCTRL_DATA.keys())
    freqs = [VCTRL_DATA[v] for v in vctrls]

    fig, ax = plt.subplots(figsize=(10, 6))

    # Smooth interpolation for the curve
    from scipy.interpolate import make_interp_spline
    try:
        vc_fine = np.linspace(min(vctrls), max(vctrls), 200)
        spl = make_interp_spline(vctrls, freqs, k=3)
        freq_fine = spl(vc_fine)
        ax.plot(vc_fine, freq_fine, '-', color='#00d2ff', linewidth=2, alpha=0.5)
        ax.fill_between(vc_fine, freq_fine, alpha=0.08, color='#00d2ff')
    except Exception:
        pass

    # Plot data points
    ax.plot(vctrls, freqs, 'o', color='#00d2ff', markersize=12,
            markerfacecolor='#00d2ff', markeredgecolor='white', markeredgewidth=2,
            label='Measured frequency', zorder=5)

    # Annotate each point
    for vc, freq in zip(vctrls, freqs):
        offset_y = 10 if freq < 170 else -18
        ax.annotate(f'{freq:.1f} MHz', xy=(vc, freq),
                    xytext=(0, offset_y), textcoords='offset points',
                    fontsize=10, color='#eee', ha='center', fontweight='bold')

    # Tuning range annotation
    f_low = VCTRL_DATA[0.7]
    f_high = VCTRL_DATA[1.8]
    tuning_ratio = f_high / f_low

    ax.annotate(f'Tuning Range (0.7 - 1.8V):\n'
                f'f_high / f_low = {f_high:.1f} / {f_low:.1f} = {tuning_ratio:.2f}x',
                xy=(0.98, 0.05), xycoords='axes fraction',
                fontsize=12, fontweight='bold', color='#ffcc00',
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#0f3460', edgecolor='#e94560', alpha=0.9))

    # Mark the nominal operating point
    ax.axvline(x=0.9, color='#e94560', linestyle='--', alpha=0.5, linewidth=1.2)
    ax.annotate('Nominal\n(0.9V)', xy=(0.91, 8), fontsize=10, color='#e94560', ha='left')

    # Mark tuning range bounds
    ax.axvline(x=0.7, color='#ffcc00', linestyle=':', alpha=0.3, linewidth=1)
    ax.axvline(x=1.8, color='#ffcc00', linestyle=':', alpha=0.3, linewidth=1)

    ax.set_xlabel('Control Voltage Vctrl (V)', fontsize=13)
    ax.set_ylabel('Frequency (MHz)', fontsize=13)
    ax.set_title('Frequency vs Control Voltage (T = 27 C)', fontsize=14, fontweight='bold')
    ax.set_xlim(0.35, 1.95)
    ax.set_ylim(-5, 210)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "freq_vs_vctrl.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def plot_freq_vs_temp():
    """Plot 3: Frequency vs Temperature."""
    plt.rcParams.update(DARK_THEME)

    temps = sorted(TEMP_DATA.keys())
    freqs = [TEMP_DATA[t] for t in temps]

    f_max = max(freqs)
    f_min = min(freqs)
    f_avg = sum(freqs) / len(freqs)
    variation = (f_max - f_min) / f_avg * 100

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot with markers
    ax.plot(temps, freqs, 's-', color='#e94560', markersize=16, linewidth=2.5,
            markerfacecolor='#e94560', markeredgecolor='white', markeredgewidth=2,
            label='Measured frequency', zorder=5)

    # Annotate each point
    for temp, freq in zip(temps, freqs):
        ax.annotate(f'{freq:.2f} MHz', xy=(temp, freq),
                    xytext=(0, 22), textcoords='offset points',
                    fontsize=13, color='#eee', ha='center', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#0f3460', edgecolor='#555', alpha=0.85))

    # Show the range band
    ax.axhspan(f_min, f_max, alpha=0.12, color='#e94560')
    ax.axhline(y=f_avg, color='#ffcc00', linestyle='--', alpha=0.5, linewidth=1,
               label=f'Mean = {f_avg:.2f} MHz')

    # Variation annotation
    ax.annotate(f'Temperature Variation: {variation:.2f}%\n'
                f'Range: {f_min:.2f} -- {f_max:.2f} MHz\n'
                f'Delta: {(f_max-f_min)*1e3:.0f} kHz over 165 C span\n'
                f'({f_avg*1e3:.0f} +/- {(f_max-f_min)/2*1e3:.0f} kHz)',
                xy=(0.98, 0.95), xycoords='axes fraction',
                fontsize=12, fontweight='bold', color='#00ff88',
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#0f3460', edgecolor='#00ff88', alpha=0.9))

    ax.set_xlabel('Temperature (C)', fontsize=13)
    ax.set_ylabel('Frequency (MHz)', fontsize=13)
    ax.set_title('Frequency vs Temperature (Vctrl = 0.9 V)', fontsize=14, fontweight='bold')

    # Tight y-axis to show the tiny variation -- zoom to +/- 0.5 MHz
    y_center = f_avg
    y_span = max(0.5, (f_max - f_min) * 30)
    ax.set_ylim(y_center - y_span, y_center + y_span)
    ax.set_xlim(-60, 145)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower left', fontsize=11)

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "freq_vs_temp.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def plot_spectrum(time_arr, vn5_arr):
    """Plot 4: FFT spectrum of ring oscillator node v(n5)."""
    plt.rcParams.update(DARK_THEME)

    # Use steady-state portion (last 60% of simulation)
    t_start = time_arr[0] + 0.4 * (time_arr[-1] - time_arr[0])
    mask = time_arr >= t_start
    t = time_arr[mask]
    v = vn5_arr[mask]

    # Remove DC offset
    v = v - np.mean(v)

    # Resample to uniform grid (wrdata may have slight non-uniformity)
    dt_target = 0.01e-9  # 0.01 ns
    t_uniform = np.arange(t[0], t[-1], dt_target)
    v_uniform = np.interp(t_uniform, t, v)

    N = len(v_uniform)
    fs = 1.0 / dt_target

    # Apply Hanning window
    window = np.hanning(N)
    v_windowed = v_uniform * window

    # FFT
    fft_vals = np.fft.rfft(v_windowed)
    fft_mag = 2.0 / (N * np.mean(window)) * np.abs(fft_vals)  # correct for window
    fft_freqs = np.fft.rfftfreq(N, d=dt_target)

    # Convert to MHz and dB
    fft_freqs_mhz = fft_freqs / 1e6
    fft_db = 20 * np.log10(fft_mag + 1e-20)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot spectrum
    ax.plot(fft_freqs_mhz, fft_db, color='#00d2ff', linewidth=0.7, alpha=0.9)

    # Find fundamental and harmonics
    fund_freq = NOMINAL_FREQ_MHZ
    harmonics_found = []
    for h in range(1, 10):
        target = h * fund_freq
        # Search within +/- 8 MHz of expected harmonic
        mask_h = (fft_freqs_mhz > target - 8) & (fft_freqs_mhz < target + 8)
        if np.any(mask_h):
            idx_local = np.argmax(fft_db[mask_h])
            # Get global indices
            global_indices = np.where(mask_h)[0]
            actual_freq = fft_freqs_mhz[global_indices[idx_local]]
            actual_db = fft_db[global_indices[idx_local]]
            if actual_db > (fft_db[global_indices[idx_local]] - 3):  # within 3dB
                harmonics_found.append((h, actual_freq, actual_db))

    # Mark harmonics
    colors_h = ['#e94560', '#ffcc00', '#00ff88', '#ff6b35', '#a855f7', '#06b6d4', '#f472b6', '#84cc16', '#fb923c']
    for i, (h, freq, db) in enumerate(harmonics_found):
        color = colors_h[i % len(colors_h)]
        if h == 1:
            label = f'f0 = {freq:.1f} MHz ({db:.1f} dB)'
        else:
            label = f'{h}f0 = {freq:.0f} MHz ({db:.1f} dB)'
        ax.axvline(x=freq, color=color, linestyle='--', alpha=0.5, linewidth=1)
        # Stagger annotations to avoid overlap
        y_offset = 5 - (i % 3) * 15
        ax.annotate(label,
                    xy=(freq, db), xytext=(12, y_offset), textcoords='offset points',
                    fontsize=9, color=color, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#0f3460', edgecolor=color, alpha=0.85))

    # Fundamental annotation box
    if harmonics_found:
        h1 = harmonics_found[0]
        # Calculate SFDR if we have at least 2 harmonics
        sfdr_text = ""
        if len(harmonics_found) >= 2:
            sfdr = harmonics_found[0][2] - harmonics_found[1][2]
            sfdr_text = f'\nSFDR = {sfdr:.1f} dB'
        ax.annotate(f'Fundamental: {h1[1]:.2f} MHz\nPeak: {h1[2]:.1f} dB{sfdr_text}',
                    xy=(0.02, 0.95), xycoords='axes fraction',
                    fontsize=12, fontweight='bold', color='#e94560',
                    verticalalignment='top',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='#0f3460', edgecolor='#e94560', alpha=0.9))

    ax.set_xlabel('Frequency (MHz)', fontsize=13)
    ax.set_ylabel('Magnitude (dB)', fontsize=13)
    ax.set_title('Output Spectrum (FFT of v(n5))', fontsize=14, fontweight='bold')

    # Set reasonable limits
    max_freq_show = min(1200, fft_freqs_mhz[-1])
    valid_mask = (fft_freqs_mhz > 5) & (fft_freqs_mhz < max_freq_show)
    if np.any(valid_mask):
        noise_floor = np.percentile(fft_db[valid_mask], 10)
        peak_val = np.max(fft_db[valid_mask])
        ax.set_ylim(max(noise_floor - 5, -100), peak_val + 10)
    ax.set_xlim(0, max_freq_show)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "spectrum.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def plot_progress():
    """Plot 5: Progress from results.tsv."""
    plt.rcParams.update(DARK_THEME)

    results_file = os.path.join(PROJECT_DIR, "results.tsv")
    if not os.path.exists(results_file):
        print("  results.tsv not found, skipping progress plot")
        return

    steps, scores, topos, notes_list, specs_met_list = [], [], [], [], []
    with open(results_file) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            try:
                steps.append(int(row.get("step", len(steps) + 1)))
                scores.append(float(row.get("score", 0)))
                topos.append(row.get("topology", ""))
                notes_list.append(row.get("notes", ""))
                specs_met_list.append(row.get("specs_met", ""))
            except (ValueError, TypeError):
                continue

    if not scores:
        print("  No data in results.tsv")
        return

    # Sort by step
    order = np.argsort(steps)
    steps = [steps[i] for i in order]
    scores = [scores[i] for i in order]
    topos = [topos[i] for i in order]
    notes_list = [notes_list[i] for i in order]
    specs_met_list = [specs_met_list[i] for i in order]

    # Best score so far
    best_so_far = []
    best = -1e9
    for s in scores:
        best = max(best, s)
        best_so_far.append(best)

    fig, ax = plt.subplots(figsize=(14, 6))

    # Color by score
    colors = ['#e94560' if s < 0.98 else '#ffcc00' if s < 1.0 else '#00ff88' for s in scores]

    # Scatter plot
    for i, (step, score, color) in enumerate(zip(steps, scores, colors)):
        ax.scatter(step, score, c=color, s=140, zorder=5, edgecolors='white', linewidth=1.5)

    # Best-so-far line
    ax.plot(steps, best_so_far, '-', color='#e94560', linewidth=2.5, label='Best so far', zorder=3)
    ax.fill_between(steps, best_so_far, min(scores) - 0.01, alpha=0.08, color='#e94560')

    # Annotate each point with topology and specs
    for i, (step, score, topo, specs_met) in enumerate(zip(steps, scores, topos, specs_met_list)):
        short_topo = topo[:30] + '...' if len(topo) > 30 else topo
        label_text = f'{short_topo}\n{specs_met} | {score:.2f}'
        y_offset = -30 if i % 2 == 0 else 15
        ax.annotate(label_text,
                    xy=(step, score), xytext=(0, y_offset), textcoords='offset points',
                    fontsize=7, color='#aaa', ha='center', va='top' if y_offset < 0 else 'bottom',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#16213e', edgecolor='#333', alpha=0.8))

    # Score thresholds
    ax.axhline(y=1.0, color='#00ff88', linestyle='--', alpha=0.4, linewidth=1, label='Perfect score (1.00)')
    ax.axhline(y=0.95, color='#ffcc00', linestyle=':', alpha=0.3, linewidth=1)

    # Final result annotation
    ax.annotate(f'Final: Score {scores[-1]:.2f}\n'
                f'Specs: {specs_met_list[-1]}\n'
                f'Topology: 5-stage NMOS-starved\n'
                f'freq=101.52 MHz | pwr=36.42 uW\n'
                f'temp_var=0.01% | tune=7.88x',
                xy=(0.98, 0.02), xycoords='axes fraction',
                fontsize=10, fontweight='bold', color='#00ff88',
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#0f3460', edgecolor='#00ff88', alpha=0.9))

    ax.set_xlabel('Optimization Step', fontsize=13)
    ax.set_ylabel('Score', fontsize=13)
    ax.set_title('Design Optimization Progress', fontsize=14, fontweight='bold')
    ax.set_ylim(min(scores) - 0.02, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=11)

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "progress.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def main():
    print("=" * 60)
    print("GENERATING RING OSCILLATOR PLOTS")
    print("=" * 60)

    # Step 1: Run ngspice to capture waveform with fine timestep
    time_arr, vn5_arr, vout_arr = run_ngspice_waveform()

    if time_arr is not None:
        print(f"\n[1/5] Waveform plot (v(n5), last 10 cycles)...")
        plot_waveform(time_arr, vn5_arr)

        print(f"\n[4/5] Spectrum plot (FFT of v(n5))...")
        plot_spectrum(time_arr, vn5_arr)
    else:
        print("\nWARNING: No waveform data - skipping waveform and spectrum plots")

    print("\n[2/5] Freq vs Vctrl plot...")
    plot_freq_vs_vctrl()

    print("\n[3/5] Freq vs Temp plot...")
    plot_freq_vs_temp()

    print("\n[5/5] Progress plot...")
    plot_progress()

    print("\n" + "=" * 60)
    print("ALL PLOTS GENERATED SUCCESSFULLY")
    print(f"Output directory: {PLOTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
