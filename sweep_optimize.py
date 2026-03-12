"""Targeted parameter sweep around known-good design point."""

import os
import re
import csv
import json
import subprocess
import tempfile
import itertools
import time
import numpy as np

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_template():
    with open(os.path.join(PROJECT_DIR, "design.cir")) as f:
        return f.read()

def format_netlist(template, params):
    return re.sub(r'\{(\w+)\}', lambda m: str(params.get(m.group(1), m.group(0))), template)

def set_vctrl(netlist, vctrl):
    return re.sub(r'^(Vctrl\s+vctrl\s+0\s+)[\d.]+', f'\\g<1>{vctrl}', netlist, flags=re.MULTILINE)

def set_temp(netlist, temp):
    if re.search(r'^\s*\.temp\s+', netlist, re.MULTILINE):
        return re.sub(r'^\s*\.temp\s+[-\d.]+', f'.temp {temp}', netlist, flags=re.MULTILINE)
    return re.sub(r'(\.lib\s+[^\n]+\n)', f'\\1.temp {temp}\n', netlist, count=1)

def set_tran(netlist, tran_time, cross_a, cross_b, meas_from, meas_to):
    n = re.sub(r'tran\s+[\d.]+n\s+[\d.]+n(\s+uic)?', f'tran 0.05n {tran_time} uic', netlist)
    count = [0]
    def _rc(m):
        count[0] += 1
        return f'cross={cross_a}' if count[0] == 1 else f'cross={cross_b}'
    n = re.sub(r'cross=\d+', _rc, n)
    n_periods = (cross_b - cross_a) / 2
    n = re.sub(r'let period = \(tcross_b - tcross_a\) / \d+',
               f'let period = (tcross_b - tcross_a) / {int(n_periods)}', n)
    n = re.sub(r'from=[\d.]+n\s+to=[\d.]+n', f'from={meas_from} to={meas_to}', n)
    return n

def run_sim(netlist, label="sim"):
    path = os.path.join(tempfile.gettempdir(), f"sweep_{label}.cir")
    with open(path, "w") as f:
        f.write(netlist)
    try:
        r = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True,
                           timeout=90, cwd=PROJECT_DIR)
        out = r.stdout + r.stderr
    except:
        return None
    finally:
        try: os.unlink(path)
        except: pass

    if "RESULT_DONE" not in out:
        return None
    for line in out.split("\n"):
        m = re.search(r'RESULT_FREQ_HZ\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', line)
        if m:
            return float(m.group(1))
    return None

def evaluate_full(params):
    """Evaluate freq, tuning range, power, temp variation."""
    template = load_template()
    netlist = format_netlist(template, params)

    # Nominal
    freq_nom = run_sim(netlist, "nom")
    if not freq_nom or freq_nom <= 0:
        return None

    # Measure power from output
    path = os.path.join(tempfile.gettempdir(), "sweep_pwr.cir")
    with open(path, "w") as f:
        f.write(netlist)
    try:
        r = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True,
                           timeout=90, cwd=PROJECT_DIR)
        out = r.stdout + r.stderr
        power = None
        for line in out.split("\n"):
            m = re.search(r'RESULT_POWER_UW\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', line)
            if m:
                power = float(m.group(1))
    except:
        power = None
    finally:
        try: os.unlink(path)
        except: pass

    # Low Vctrl (tuning range)
    low_net = set_vctrl(netlist, 0.5)
    low_net = set_tran(low_net, "2000n", 4, 14, "500n", "2000n")
    freq_low = run_sim(low_net, "low")

    # High Vctrl
    high_net = set_vctrl(netlist, 1.8)
    freq_high = run_sim(high_net, "high")

    tuning = 1.0
    if freq_low and freq_high and freq_low > 0:
        tuning = freq_high / freq_low
    elif freq_high and freq_high > 0:
        tuning = freq_high / freq_nom

    # Temperature
    temp_freqs = []
    for temp in [-40, 27, 125]:
        t_net = set_temp(netlist, temp)
        f = run_sim(t_net, f"t{temp}")
        if f and f > 0:
            temp_freqs.append(f)

    temp_var = 50.0
    if len(temp_freqs) >= 2:
        avg = sum(temp_freqs) / len(temp_freqs)
        rng = max(temp_freqs) - min(temp_freqs)
        temp_var = (rng / avg) * 100

    return {
        "freq": freq_nom,
        "power": power or 0,
        "tuning": tuning,
        "temp_var": temp_var,
    }


if __name__ == "__main__":
    # Base parameters (known good)
    base = {
        "Wp": 2.0, "Lp": 0.15, "Wn": 1.0, "Ln": 0.15,
        "Wsp": 2.0, "Lsp": 1.0, "Wsn": 1.0, "Lsn": 1.0,
        "Wbp": 2.0, "Lbp": 1.0, "Wbn": 1.0, "Lbn": 1.0,
    }

    print("=== Baseline evaluation ===")
    baseline = evaluate_full(base)
    print(f"Freq: {baseline['freq']/1e6:.1f} MHz | Power: {baseline['power']:.1f} µW | "
          f"Tuning: {baseline['tuning']:.2f}x | Temp var: {baseline['temp_var']:.1f}%")

    # Try variations to improve temperature stability
    print("\n=== Parameter sweep for temperature stability ===")
    best = baseline.copy()
    best["params"] = base.copy()
    best_score = -baseline["temp_var"]  # minimize temp variation

    # Sweep starving transistor sizes (these most affect temp stability)
    sweep_params = {
        "Lsp": [0.5, 0.8, 1.0, 1.5, 2.0],
        "Lsn": [0.5, 0.8, 1.0, 1.5, 2.0],
        "Wsp": [1.0, 2.0, 3.0, 5.0],
        "Wsn": [0.5, 1.0, 2.0, 3.0],
        "Lbp": [0.5, 1.0, 1.5, 2.0],
        "Lbn": [0.5, 1.0, 1.5, 2.0],
    }

    # One-at-a-time sweep first
    for param_name, values in sweep_params.items():
        for val in values:
            if val == base.get(param_name):
                continue
            params = base.copy()
            params[param_name] = val
            result = evaluate_full(params)
            if result is None:
                continue

            # Score: all specs must pass, then minimize temp_var
            specs_pass = (result["freq"] > 50e6 and result["tuning"] > 2.0 and
                          result["power"] < 500 and result["temp_var"] < 10)

            print(f"  {param_name}={val:.1f}: freq={result['freq']/1e6:.1f}MHz "
                  f"tune={result['tuning']:.2f}x pwr={result['power']:.1f}µW "
                  f"temp={result['temp_var']:.1f}% {'PASS' if specs_pass else 'FAIL'}")

            if specs_pass and result["temp_var"] < best["temp_var"]:
                best = result.copy()
                best["params"] = params.copy()
                best_score = -result["temp_var"]
                print(f"    ** New best! temp_var={result['temp_var']:.1f}%")

    print(f"\n=== Best result ===")
    print(f"Freq: {best['freq']/1e6:.1f} MHz | Power: {best['power']:.1f} µW | "
          f"Tuning: {best['tuning']:.2f}x | Temp var: {best['temp_var']:.1f}%")
    print(f"Parameters: {best['params']}")

    # Save if better
    if best["temp_var"] < baseline["temp_var"]:
        with open("best_parameters.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["name", "value"])
            for name, val in sorted(best["params"].items()):
                w.writerow([name, val])
        print("Saved improved parameters to best_parameters.csv")
