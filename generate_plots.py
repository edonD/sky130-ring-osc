#!/usr/bin/env python3
"""Generate all required plots for ring oscillator validation."""

import subprocess
import re
import os
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.join(PROJECT_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

# Load best parameters
PARAMS = {}
with open(os.path.join(PROJECT_DIR, "best_parameters.csv")) as f:
    reader = csv.DictReader(f)
    for row in reader:
        PARAMS[row["name"]] = float(row["value"])

# Dark theme
plt.rcParams.update({
    'figure.facecolor': '#1a1a2e', 'axes.facecolor': '#16213e',
    'axes.edgecolor': '#e94560', 'axes.labelcolor': '#eee',
    'text.color': '#eee', 'xtick.color': '#aaa', 'ytick.color': '#aaa',
    'grid.color': '#333', 'grid.alpha': 0.5, 'lines.linewidth': 2,
    'font.size': 11,
})


def make_netlist(vctrl=0.9, temp=27, tran_time="500n", tran_step="0.05n", save_raw=False):
    with open(os.path.join(PROJECT_DIR, "design.cir")) as f:
        template = f.read()

    def _replace(match):
        key = match.group(1)
        return str(PARAMS[key]) if key in PARAMS else match.group(0)
    netlist = re.sub(r'\{(\w+)\}', _replace, template)
    netlist = re.sub(r'^(Vctrl\s+vctrl\s+0\s+)[\d.]+', f'\\g<1>{vctrl}',
                     netlist, flags=re.MULTILINE)
    if re.search(r'^\s*\.temp\s+', netlist, re.MULTILINE):
        netlist = re.sub(r'^\s*\.temp\s+[-\d.]+', f'.temp {temp}',
                         netlist, flags=re.MULTILINE)
    else:
        netlist = re.sub(r'(\.lib\s+[^\n]+\n)', f'\\1.temp {temp}\n', netlist, count=1)
    netlist = re.sub(r'tran\s+[\d.]+n\s+[\d.]+n(\s+uic)?',
                     f'tran {tran_step} {tran_time} uic', netlist)

    if save_raw:
        control = f"""
.control
tran {tran_step} {tran_time} uic
wrdata {os.path.join(PROJECT_DIR, 'sim_output.txt')} v(n5)
echo "RESULT_DONE"
.endc
"""
        netlist = re.sub(r'\.control.*?\.endc', control, netlist, flags=re.DOTALL)

    return netlist


def run_ngspice(netlist, label="sim"):
    path = os.path.join(PROJECT_DIR, f"plot_{label}.cir")
    with open(path, "w") as f:
        f.write(netlist)
    try:
        result = subprocess.run(
            ["ngspice", "-b", path],
            capture_output=True, text=True, timeout=120,
            cwd=PROJECT_DIR
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


# ========================================================
# 1. Waveform plot
# ========================================================
print("Generating waveform plot...")
nl = make_netlist(vctrl=0.9, temp=27, tran_time="500n", tran_step="0.01n", save_raw=True)
out = run_ngspice(nl, "waveform")

data_file = os.path.join(PROJECT_DIR, "sim_output.txt")
if os.path.exists(data_file):
    times, voltages = [], []
    with open(data_file) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    t = float(parts[0])
                    v = float(parts[1])
                    times.append(t)
                    voltages.append(v)
                except ValueError:
                    continue
    times = np.array(times)
    voltages = np.array(voltages)

    threshold = 0.9
    crossings = []
    for i in range(1, len(voltages)):
        if voltages[i-1] < threshold and voltages[i] >= threshold:
            frac = (threshold - voltages[i-1]) / (voltages[i] - voltages[i-1])
            t_cross = times[i-1] + frac * (times[i] - times[i-1])
            crossings.append(t_cross)

    if len(crossings) >= 12:
        periods = np.diff(crossings[5:])
        avg_period = np.mean(periods)
        freq = 1.0 / avg_period

        t_end = times[-1]
        t_start = max(t_end - 10 * avg_period, 0)
        mask = (times >= t_start) & (times <= t_end)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(times[mask] * 1e9, voltages[mask], color='#e94560', linewidth=1.5)
        ax.set_xlabel('Time (ns)')
        ax.set_ylabel('Voltage (V)')
        ax.set_title('Ring Oscillator Output Waveform')
        ax.annotate(f'f = {freq/1e6:.1f} MHz\nT = {avg_period*1e9:.2f} ns',
                    xy=(0.02, 0.95), xycoords='axes fraction',
                    fontsize=12, color='#e94560', va='top',
                    bbox=dict(boxstyle='round', facecolor='#1a1a2e', alpha=0.8))
        v_min, v_max = np.min(voltages[mask]), np.max(voltages[mask])
        ax.annotate(f'Vpp = {v_max - v_min:.2f} V',
                    xy=(0.02, 0.75), xycoords='axes fraction',
                    fontsize=11, color='#0f3460', va='top')
        ax.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, "waveform.png"), dpi=150)
        plt.close()
        print(f"  Saved waveform.png (f={freq/1e6:.1f} MHz)")

        # ========================================================
        # 3. Spectrum plot (FFT)
        # ========================================================
        print("Generating spectrum plot...")
        ss_start = times[-1] - 50 * avg_period
        ss_mask = times >= max(ss_start, 0)
        ss_t = times[ss_mask]
        ss_v = voltages[ss_mask]

        if len(ss_v) > 100:
            dt = np.mean(np.diff(ss_t))
            N = len(ss_v)
            fft_vals = np.fft.rfft(ss_v - np.mean(ss_v))
            fft_freq = np.fft.rfftfreq(N, dt)
            magnitude = 2.0 / N * np.abs(fft_vals)

            fig, ax = plt.subplots(figsize=(12, 5))
            max_plot_freq = min(5 * freq, fft_freq[-1])
            mask_f = fft_freq <= max_plot_freq
            ax.plot(fft_freq[mask_f] / 1e6, 20 * np.log10(magnitude[mask_f] + 1e-12),
                    color='#e94560', linewidth=1)
            ax.set_xlabel('Frequency (MHz)')
            ax.set_ylabel('Magnitude (dB)')
            ax.set_title('Output Spectrum (FFT)')
            fund_idx = np.argmax(magnitude[1:]) + 1
            ax.axvline(x=fft_freq[fund_idx] / 1e6, color='#533483', linestyle='--', alpha=0.7)
            ax.annotate(f'f1 = {fft_freq[fund_idx]/1e6:.1f} MHz',
                        xy=(fft_freq[fund_idx] / 1e6, 20 * np.log10(magnitude[fund_idx] + 1e-12)),
                        xytext=(10, 10), textcoords='offset points',
                        fontsize=11, color='#e94560',
                        arrowprops=dict(arrowstyle='->', color='#e94560'))
            ax.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(PLOTS_DIR, "spectrum.png"), dpi=150)
            plt.close()
            print(f"  Saved spectrum.png")

    os.unlink(data_file)

# ========================================================
# 2. Frequency vs Vctrl plot
# ========================================================
print("Generating freq_vs_vctrl plot...")
vctrl_values = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]
tune_freqs = []
tune_vctrls = []

for vc in vctrl_values:
    tran_t = "800n" if vc < 0.6 else "500n"
    nl = make_netlist(vctrl=vc, temp=27, tran_time=tran_t, tran_step="0.05n")
    if vc < 0.6:
        nl = re.sub(r'cross=20', 'cross=10', nl, count=1)
        nl = re.sub(r'cross=30', 'cross=20', nl, count=1)
        nl = re.sub(r'from=50n\s+to=\S+', f'from=50n to={tran_t}', nl)
    out = run_ngspice(nl, f"vctrl_{vc:.1f}")
    match = re.search(r'RESULT_FREQ_HZ\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', out)
    if match:
        f = float(match.group(1))
        if f > 0:
            tune_freqs.append(f)
            tune_vctrls.append(vc)
            print(f"  Vctrl={vc:.1f}V: {f/1e6:.1f} MHz")

if len(tune_freqs) >= 2:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(tune_vctrls, [f/1e6 for f in tune_freqs], 'o-', color='#e94560',
            markersize=6, linewidth=2)
    ax.set_xlabel('Control Voltage (V)')
    ax.set_ylabel('Frequency (MHz)')
    ax.set_title('Oscillation Frequency vs Control Voltage')
    f_min, f_max = min(tune_freqs), max(tune_freqs)
    ratio = f_max / f_min
    ax.annotate(f'Tuning range: {ratio:.2f}x\nFmin={f_min/1e6:.1f} MHz\nFmax={f_max/1e6:.1f} MHz',
                xy=(0.98, 0.05), xycoords='axes fraction', ha='right',
                fontsize=11, color='#e94560',
                bbox=dict(boxstyle='round', facecolor='#1a1a2e', alpha=0.8))
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "freq_vs_vctrl.png"), dpi=150)
    plt.close()
    print(f"  Saved freq_vs_vctrl.png (ratio={ratio:.2f}x)")

# ========================================================
# 4. Frequency vs Temperature plot
# ========================================================
print("Generating freq_vs_temp plot...")
temps = [-40, -20, 0, 27, 50, 75, 100, 125]
temp_freqs = []
temp_vals = []

for temp in temps:
    nl = make_netlist(vctrl=0.9, temp=temp, tran_time="500n", tran_step="0.05n")
    out = run_ngspice(nl, f"temp_{temp}")
    match = re.search(r'RESULT_FREQ_HZ\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', out)
    if match:
        f = float(match.group(1))
        if f > 0:
            temp_freqs.append(f)
            temp_vals.append(temp)
            print(f"  T={temp:>4d}C: {f/1e6:.1f} MHz")

if len(temp_freqs) >= 2:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(temp_vals, [f/1e6 for f in temp_freqs], 'o-', color='#e94560',
            markersize=6, linewidth=2)
    ax.set_xlabel('Temperature (C)')
    ax.set_ylabel('Frequency (MHz)')
    ax.set_title('Oscillation Frequency vs Temperature')
    f_avg = sum(temp_freqs) / len(temp_freqs)
    f_range = max(temp_freqs) - min(temp_freqs)
    temp_var = (f_range / f_avg) * 100
    ax.annotate(f'Variation: {temp_var:.2f}%\nf_avg = {f_avg/1e6:.1f} MHz',
                xy=(0.98, 0.95), xycoords='axes fraction', ha='right', va='top',
                fontsize=11, color='#e94560',
                bbox=dict(boxstyle='round', facecolor='#1a1a2e', alpha=0.8))
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "freq_vs_temp.png"), dpi=150)
    plt.close()
    print(f"  Saved freq_vs_temp.png (variation={temp_var:.2f}%)")

# ========================================================
# 5. Progress plot from results.tsv
# ========================================================
print("Generating progress plot...")
results_file = os.path.join(PROJECT_DIR, "results.tsv")
if os.path.exists(results_file):
    steps, scores, topos = [], [], []
    with open(results_file) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            try:
                steps.append(int(row.get("step", len(steps) + 1)))
                scores.append(float(row.get("score", 0)))
                topos.append(row.get("topology", ""))
            except (ValueError, TypeError):
                continue

    if scores:
        best_so_far = []
        best = -1e9
        for s in scores:
            best = max(best, s)
            best_so_far.append(best)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(steps, scores, 'o', color='#0f3460', markersize=6, alpha=0.7, label='Run score')
        ax.plot(steps, best_so_far, '-', color='#e94560', linewidth=2, label='Best so far')

        prev_topo = ""
        for i, t in enumerate(topos):
            if t != prev_topo and prev_topo != "":
                ax.axvline(x=steps[i], color='#533483', linestyle='--', alpha=0.5)
            prev_topo = t

        ax.set_xlabel('Iteration')
        ax.set_ylabel('Score')
        ax.set_title('Optimization Progress')
        ax.set_ylim(0, 1.05)
        ax.legend()
        ax.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, "progress.png"), dpi=150)
        plt.close()
        print(f"  Saved progress.png")

print("\nAll plots generated!")
