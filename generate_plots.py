"""Generate all required plots for the ring oscillator design."""

import os
import re
import csv
import subprocess
import tempfile
import numpy as np

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.join(PROJECT_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Dark theme
plt.rcParams.update({
    'figure.facecolor': '#1a1a2e', 'axes.facecolor': '#16213e',
    'axes.edgecolor': '#e94560', 'axes.labelcolor': '#eee',
    'text.color': '#eee', 'xtick.color': '#aaa', 'ytick.color': '#aaa',
    'grid.color': '#333', 'grid.alpha': 0.5, 'lines.linewidth': 2,
    'font.size': 11,
})


def load_best_params():
    params = {}
    with open(os.path.join(PROJECT_DIR, "best_parameters.csv")) as f:
        reader = csv.DictReader(f)
        for row in reader:
            params[row["name"]] = float(row["value"])
    return params


def format_netlist(template, params):
    def _replace(m):
        key = m.group(1)
        return str(params[key]) if key in params else m.group(0)
    return re.sub(r'\{(\w+)\}', _replace, template)


def make_waveform_netlist(template, params):
    """Create netlist that exports waveform data."""
    netlist = format_netlist(template, params)
    netlist = re.sub(
        r'\.control.*?\.endc',
        """.control
tran 0.05n 200n uic
wrdata /tmp/ring_osc_wave.txt v(n3) v(out)
meas tran tcross_a when v(n3)=0.9 cross=20
meas tran tcross_b when v(n3)=0.9 cross=30
let period = (tcross_b - tcross_a) / 5
let freq = 1 / period
echo "RESULT_FREQ_HZ" $&freq
meas tran avg_idd avg i(Vdd) from=50n to=200n
let pwr = abs(avg_idd) * 1.8 * 1e6
echo "RESULT_POWER_UW" $&pwr
echo "RESULT_DONE"
.endc""",
        netlist, flags=re.DOTALL)
    return netlist


def make_vctrl_netlist(template, params, vctrl, tran_time="200n", cross_a=20, cross_b=30, meas_from="50n", meas_to="200n"):
    """Create netlist for a specific Vctrl value."""
    netlist = format_netlist(template, params)
    netlist = re.sub(r'^(Vctrl\s+vctrl\s+0\s+)[\d.]+',
                     f'\\g<1>{vctrl}', netlist, flags=re.MULTILINE)
    n_periods = (cross_b - cross_a) / 2
    netlist = re.sub(
        r'\.control.*?\.endc',
        f""".control
tran 0.05n {tran_time} uic
meas tran tcross_a when v(n3)=0.9 cross={cross_a}
meas tran tcross_b when v(n3)=0.9 cross={cross_b}
let period = (tcross_b - tcross_a) / {int(n_periods)}
let freq = 1 / period
echo "RESULT_FREQ_HZ" $&freq
meas tran avg_idd avg i(Vdd) from={meas_from} to={meas_to}
let pwr = abs(avg_idd) * 1.8 * 1e6
echo "RESULT_POWER_UW" $&pwr
echo "RESULT_DONE"
.endc""",
        netlist, flags=re.DOTALL)
    return netlist


def make_temp_netlist(template, params, temp):
    """Create netlist for a specific temperature."""
    netlist = format_netlist(template, params)
    if re.search(r'^\s*\.temp\s+', netlist, re.MULTILINE):
        netlist = re.sub(r'^\s*\.temp\s+[-\d.]+', f'.temp {temp}', netlist, flags=re.MULTILINE)
    else:
        netlist = re.sub(r'(\.lib\s+[^\n]+\n)', f'\\1.temp {temp}\n', netlist, count=1)
    return netlist


def run_sim(netlist, label="sim"):
    """Run ngspice and return stdout+stderr."""
    path = os.path.join(tempfile.gettempdir(), f"plot_{label}.cir")
    with open(path, "w") as f:
        f.write(netlist)
    try:
        result = subprocess.run(
            ["ngspice", "-b", path],
            capture_output=True, text=True, timeout=120,
            cwd=PROJECT_DIR
        )
        return result.stdout + result.stderr
    except Exception as e:
        print(f"  Sim error ({label}): {e}")
        return ""
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def parse_freq(output):
    for line in output.split("\n"):
        if "RESULT_FREQ_HZ" in line:
            m = re.search(r'RESULT_FREQ_HZ\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', line)
            if m:
                return float(m.group(1))
    return None


def parse_power(output):
    for line in output.split("\n"):
        if "RESULT_POWER_UW" in line:
            m = re.search(r'RESULT_POWER_UW\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', line)
            if m:
                return float(m.group(1))
    return None


def read_wrdata_file(path):
    """Read ngspice wrdata ASCII output file."""
    data_cols = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('#', '*')):
                continue
            parts = line.split()
            try:
                vals = [float(x) for x in parts]
                data_cols.append(vals)
            except ValueError:
                continue
    if not data_cols:
        return None
    arr = np.array(data_cols)
    return arr


def plot_waveform(template, params):
    """Plot 1: Steady-state waveform."""
    print("Generating waveform.png...")
    netlist = make_waveform_netlist(template, params)
    output = run_sim(netlist, "waveform")
    freq = parse_freq(output)
    power = parse_power(output)

    if not freq:
        print("  WARNING: Could not measure frequency")
        return

    # Read wrdata output
    data_path = "/tmp/ring_osc_wave.txt"
    if not os.path.exists(data_path):
        print("  WARNING: Data file not found")
        return

    arr = read_wrdata_file(data_path)
    if arr is None or arr.shape[1] < 2:
        print("  WARNING: Could not parse data file")
        return

    time_ns = arr[:, 0] * 1e9
    v_n3_all = arr[:, 1]
    v_out_all = arr[:, 2] if arr.shape[1] > 2 else None

    # Show last 10 cycles
    period_ns = 1e9 / freq
    t_end = time_ns[-1]
    t_start = max(0, t_end - 10 * period_ns)

    mask = time_ns >= t_start
    t = time_ns[mask]
    v_n3 = v_n3_all[mask]
    v_out = v_out_all[mask] if v_out_all is not None else None

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(t, v_n3, color='#e94560', label='v(n3) ring node')
    if v_out is not None:
        ax.plot(t, v_out, color='#0f3460', alpha=0.7, label='v(out) buffer')

    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Voltage (V)')
    ax.set_title('Steady-State Waveform — Last 10 Cycles')
    ax.set_ylim(-0.1, 2.0)
    ax.legend(loc='upper right')
    ax.grid(True)

    # Annotate
    ax.annotate(f'f = {freq/1e6:.1f} MHz\nP = {power:.1f} µW\nT = {period_ns:.2f} ns',
                xy=(0.02, 0.95), xycoords='axes fraction', va='top',
                fontsize=12, color='#e94560',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#1a1a2e', edgecolor='#e94560', alpha=0.8))

    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "waveform.png"), dpi=150)
    plt.close()
    print(f"  Done: freq={freq/1e6:.1f} MHz, power={power:.1f} µW")
    os.unlink(data_path)


def plot_freq_vs_vctrl(template, params):
    """Plot 2: Frequency vs control voltage."""
    print("Generating freq_vs_vctrl.png...")
    vctrl_values = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]
    freqs = []
    powers = []

    for vc in vctrl_values:
        # For low Vctrl, use longer sim and fewer crossings
        if vc <= 0.4:
            netlist = make_vctrl_netlist(template, params, vc,
                                         tran_time="5000n", cross_a=4, cross_b=10,
                                         meas_from="2000n", meas_to="5000n")
        elif vc <= 0.7:
            netlist = make_vctrl_netlist(template, params, vc,
                                         tran_time="2000n", cross_a=4, cross_b=14,
                                         meas_from="500n", meas_to="2000n")
        else:
            netlist = make_vctrl_netlist(template, params, vc)

        output = run_sim(netlist, f"vctrl_{vc}")
        f = parse_freq(output)
        p = parse_power(output)
        freqs.append(f)
        powers.append(p)
        if f:
            print(f"  Vctrl={vc:.1f}V: f={f/1e6:.1f} MHz, P={p:.1f} µW")
        else:
            print(f"  Vctrl={vc:.1f}V: no oscillation")

    # Filter valid points
    valid = [(v, f, p) for v, f, p in zip(vctrl_values, freqs, powers) if f and f > 0]
    if len(valid) < 2:
        print("  WARNING: Not enough valid points")
        return

    vc_valid = [v[0] for v in valid]
    f_valid = [v[1] for v in valid]
    p_valid = [v[2] for v in valid]

    tuning_ratio = max(f_valid) / min(f_valid)

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(vc_valid, [f/1e6 for f in f_valid], 'o-', color='#e94560', markersize=6, label='Frequency')
    ax1.set_xlabel('Control Voltage (V)')
    ax1.set_ylabel('Frequency (MHz)', color='#e94560')
    ax1.tick_params(axis='y', labelcolor='#e94560')
    ax1.set_title('VCO Characteristic — Frequency vs Control Voltage')
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(vc_valid, p_valid, 's--', color='#0f3460', markersize=5, alpha=0.7, label='Power')
    ax2.set_ylabel('Power (µW)', color='#0f3460')
    ax2.tick_params(axis='y', labelcolor='#0f3460')

    # Annotate tuning range
    ax1.annotate(f'Tuning Range: {tuning_ratio:.2f}x\n'
                 f'f_min = {min(f_valid)/1e6:.1f} MHz\n'
                 f'f_max = {max(f_valid)/1e6:.1f} MHz',
                 xy=(0.02, 0.95), xycoords='axes fraction', va='top',
                 fontsize=12, color='#e94560',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#1a1a2e', edgecolor='#e94560', alpha=0.8))

    fig.legend(loc='upper right', bbox_to_anchor=(0.95, 0.85))
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "freq_vs_vctrl.png"), dpi=150)
    plt.close()
    print(f"  Done: tuning ratio = {tuning_ratio:.2f}x")
    return tuning_ratio, min(f_valid), max(f_valid)


def plot_spectrum(template, params):
    """Plot 3: FFT spectrum."""
    print("Generating spectrum.png...")
    # Use longer sim for better frequency resolution
    netlist = format_netlist(template, params)
    netlist = re.sub(
        r'\.control.*?\.endc',
        """.control
tran 0.01n 500n uic
wrdata /tmp/ring_osc_fft.txt v(n3)
echo "RESULT_DONE"
.endc""",
        netlist, flags=re.DOTALL)

    output = run_sim(netlist, "fft")
    data_path = "/tmp/ring_osc_fft.txt"
    if not os.path.exists(data_path):
        print("  WARNING: Data file not found")
        return

    arr = read_wrdata_file(data_path)
    if arr is None or arr.shape[1] < 2:
        print("  WARNING: Could not parse data file")
        return

    time = arr[:, 0]
    v = arr[:, 1]

    # Use steady-state portion (skip first 50ns)
    mask = time >= 50e-9
    t_ss = time[mask]
    v_ss = v[mask]

    # Resample to uniform grid
    dt = 0.01e-9
    t_uniform = np.arange(t_ss[0], t_ss[-1], dt)
    v_uniform = np.interp(t_uniform, t_ss, v_ss)

    # FFT
    N = len(v_uniform)
    fft_vals = np.fft.rfft(v_uniform - np.mean(v_uniform))
    fft_mag = 2.0 / N * np.abs(fft_vals)
    fft_freq = np.fft.rfftfreq(N, d=dt)

    # Convert to dB (relative to max)
    fft_db = 20 * np.log10(fft_mag / np.max(fft_mag) + 1e-15)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot up to 2 GHz
    f_max_plot = 2e9
    mask_plot = fft_freq <= f_max_plot
    ax.plot(fft_freq[mask_plot] / 1e6, fft_db[mask_plot], color='#e94560', linewidth=1)

    ax.set_xlabel('Frequency (MHz)')
    ax.set_ylabel('Magnitude (dB)')
    ax.set_title('Output Spectrum — FFT of v(n3)')
    ax.set_ylim(-80, 5)
    ax.grid(True)

    # Find and annotate harmonics
    fund_idx = np.argmax(fft_mag[1:]) + 1
    fund_freq = fft_freq[fund_idx]
    ax.annotate(f'f₀ = {fund_freq/1e6:.1f} MHz',
                xy=(fund_freq/1e6, fft_db[fund_idx]),
                xytext=(fund_freq/1e6 + 100, fft_db[fund_idx] - 10),
                arrowprops=dict(arrowstyle='->', color='#e94560'),
                fontsize=11, color='#e94560')

    # Mark harmonics
    for n in range(2, 6):
        h_freq = n * fund_freq
        if h_freq < f_max_plot:
            h_idx = np.argmin(np.abs(fft_freq - h_freq))
            ax.annotate(f'{n}f₀', xy=(fft_freq[h_idx]/1e6, fft_db[h_idx]),
                        xytext=(fft_freq[h_idx]/1e6 + 30, fft_db[h_idx] + 5),
                        arrowprops=dict(arrowstyle='->', color='#aaa'),
                        fontsize=9, color='#aaa')

    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "spectrum.png"), dpi=150)
    plt.close()
    print(f"  Done: fundamental = {fund_freq/1e6:.1f} MHz")
    os.unlink(data_path)


def plot_freq_vs_temp(template, params):
    """Plot 4: Frequency vs temperature."""
    print("Generating freq_vs_temp.png...")
    temps = [-40, -20, 0, 27, 50, 75, 100, 125]
    freqs = []
    powers = []

    for temp in temps:
        netlist = make_temp_netlist(template, params, temp)
        output = run_sim(netlist, f"temp_{temp}")
        f = parse_freq(output)
        p = parse_power(output)
        freqs.append(f)
        powers.append(p)
        if f:
            print(f"  T={temp:>4d}°C: f={f/1e6:.1f} MHz, P={p:.1f} µW")
        else:
            print(f"  T={temp:>4d}°C: no oscillation")

    valid = [(t, f, p) for t, f, p in zip(temps, freqs, powers) if f and f > 0]
    if len(valid) < 2:
        print("  WARNING: Not enough valid points")
        return

    t_valid = [v[0] for v in valid]
    f_valid = [v[1] for v in valid]
    p_valid = [v[2] for v in valid]

    f_avg = sum(f_valid) / len(f_valid)
    f_range = max(f_valid) - min(f_valid)
    temp_var = (f_range / f_avg) * 100

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(t_valid, [f/1e6 for f in f_valid], 'o-', color='#e94560', markersize=8, label='Frequency')
    ax1.set_xlabel('Temperature (°C)')
    ax1.set_ylabel('Frequency (MHz)', color='#e94560')
    ax1.tick_params(axis='y', labelcolor='#e94560')
    ax1.set_title('Frequency vs Temperature')
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(t_valid, p_valid, 's--', color='#0f3460', markersize=6, alpha=0.7, label='Power')
    ax2.set_ylabel('Power (µW)', color='#0f3460')
    ax2.tick_params(axis='y', labelcolor='#0f3460')

    # Annotate
    ax1.annotate(f'Variation: {temp_var:.1f}%\n'
                 f'f_avg = {f_avg/1e6:.1f} MHz\n'
                 f'Δf = {f_range/1e6:.1f} MHz',
                 xy=(0.02, 0.95), xycoords='axes fraction', va='top',
                 fontsize=12, color='#e94560',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#1a1a2e', edgecolor='#e94560', alpha=0.8))

    # Highlight spec region
    ax1.axhspan((f_avg - f_avg*0.05)/1e6, (f_avg + f_avg*0.05)/1e6, alpha=0.1, color='green')

    fig.legend(loc='upper right', bbox_to_anchor=(0.95, 0.85))
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "freq_vs_temp.png"), dpi=150)
    plt.close()
    print(f"  Done: temp variation = {temp_var:.1f}%")
    return temp_var


def plot_progress():
    """Plot 5: Progress plot from results.tsv."""
    print("Generating progress.png...")
    results_file = os.path.join(PROJECT_DIR, "results.tsv")
    if not os.path.exists(results_file):
        print("  No results.tsv found")
        return

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

    if not scores:
        print("  No data in results.tsv")
        return

    best_so_far = []
    best = -1e9
    for s in scores:
        best = max(best, s)
        best_so_far.append(best)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(steps, scores, 'o', color='#0f3460', markersize=8, alpha=0.7, label='Run score')
    ax.plot(steps, best_so_far, '-', color='#e94560', linewidth=2, label='Best so far')

    # Mark topology changes
    prev_topo = ""
    for i, t in enumerate(topos):
        if t != prev_topo and prev_topo != "":
            ax.axvline(x=steps[i], color='#533483', linestyle='--', alpha=0.5,
                       label='Topology change' if i == 1 else None)
        prev_topo = t

    ax.set_xlabel('Iteration')
    ax.set_ylabel('Score')
    ax.set_title('Optimization Progress')
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "progress.png"), dpi=150)
    plt.close()
    print("  Done")


if __name__ == "__main__":
    with open(os.path.join(PROJECT_DIR, "design.cir")) as f:
        template = f.read()
    params = load_best_params()

    print(f"Parameters: {params}\n")

    plot_waveform(template, params)
    plot_freq_vs_vctrl(template, params)
    plot_spectrum(template, params)
    plot_freq_vs_temp(template, params)
    plot_progress()

    print("\nAll plots generated in plots/")
