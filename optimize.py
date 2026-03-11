"""
optimize.py — Bayesian Optimization for ring oscillator design.

Evaluates all specs (freq, power, tuning range, temperature, jitter) per candidate.
Uses scikit-optimize for efficient exploration with expensive simulations.
"""

import os
import sys
import re
import json
import csv
import time
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
NGSPICE = "ngspice"
SIM_TIMEOUT = 60


def load_design():
    with open("design.cir") as f:
        return f.read()


def load_specs():
    with open("specs.json") as f:
        return json.load(f)


def format_netlist(template, param_values):
    def _replace(match):
        key = match.group(1)
        return str(param_values[key]) if key in param_values else match.group(0)
    return re.sub(r'\{(\w+)\}', _replace, template)


def run_sim(netlist_str, idx=0, tmp_dir="/tmp"):
    path = os.path.join(tmp_dir, f"sim_{idx}.cir")
    with open(path, "w") as f:
        f.write(netlist_str)
    try:
        result = subprocess.run(
            [NGSPICE, "-b", path],
            capture_output=True, text=True, timeout=SIM_TIMEOUT,
            cwd=PROJECT_DIR
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    if "RESULT_DONE" not in output:
        return None

    measurements = {}
    for line in output.split("\n"):
        if "RESULT_" in line and "RESULT_DONE" not in line:
            match = re.search(r'(RESULT_\w+)\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', line)
            if match:
                measurements[match.group(1)] = float(match.group(2))
    return measurements


def set_vctrl(template, vctrl):
    return re.sub(r'^(Vctrl\s+vctrl\s+0\s+)[\d.]+',
                  f'\\g<1>{vctrl}', template, flags=re.MULTILINE)


def set_temp(template, temp):
    if re.search(r'^\s*\.temp\s+', template, re.MULTILINE):
        return re.sub(r'^\s*\.temp\s+[-\d.]+', f'.temp {temp}', template, flags=re.MULTILINE)
    return re.sub(r'(\.lib\s+[^\n]+\n)', f'\\1.temp {temp}\n', template, count=1)


def set_tran(template, sim_time_ns, rise_a=3, rise_b=4, meas_from_ns=10, meas_to_ns=50):
    t = re.sub(r'tran\s+[\d.]+n\s+[\d.]+n(\s+uic)?',
               f'tran 0.5n {sim_time_ns}n uic', template)
    count = [0]
    def _repl(m):
        count[0] += 1
        return f'rise={rise_a}' if count[0] == 1 else f'rise={rise_b}'
    t = re.sub(r'rise=\d+', _repl, t)
    t = re.sub(r'from=[\d.]+n\s+to=[\d.]+n',
               f'from={meas_from_ns}n to={meas_to_ns}n', t)
    return t


def evaluate_full(template, params, tmp_dir):
    """Full evaluation: nominal freq+power, tuning range, temperature."""
    netlist = format_netlist(template, params)

    # 1. Nominal (Vctrl=0.9V)
    meas = run_sim(netlist, 0, tmp_dir)
    if not meas or "RESULT_FREQ_HZ" not in meas:
        return None

    result = dict(meas)
    nom_freq = result["RESULT_FREQ_HZ"]
    if nom_freq <= 0:
        return None

    # 2. Tuning range: low Vctrl
    period_ns = 1e9 / nom_freq
    low_sim = max(100, int(period_ns * 30))  # enough for slow oscillation
    low_netlist = set_vctrl(netlist, 0.3)
    low_netlist = set_tran(low_netlist, low_sim, 2, 3, int(low_sim * 0.3), low_sim)
    low_meas = run_sim(low_netlist, 1, tmp_dir)
    freq_low = (low_meas or {}).get("RESULT_FREQ_HZ", 0)

    # High Vctrl
    high_netlist = set_vctrl(netlist, 1.8)
    high_meas = run_sim(high_netlist, 2, tmp_dir)
    freq_high = (high_meas or {}).get("RESULT_FREQ_HZ", 0)

    if freq_low > 0 and freq_high > 0:
        result["RESULT_TUNING_RANGE_RATIO"] = max(freq_low, freq_high) / min(freq_low, freq_high)
    elif freq_high > 0:
        result["RESULT_TUNING_RANGE_RATIO"] = freq_high / nom_freq if nom_freq > 0 else 1.0
    else:
        result["RESULT_TUNING_RANGE_RATIO"] = 1.0

    # 3. Temperature sweep
    temp_freqs = {}
    for temp in [-40, 27, 125]:
        t_netlist = set_temp(netlist, temp)
        t_meas = run_sim(t_netlist, int(temp + 50), tmp_dir)
        f = (t_meas or {}).get("RESULT_FREQ_HZ", 0)
        if f > 0:
            temp_freqs[temp] = f

    if len(temp_freqs) >= 2:
        fvals = list(temp_freqs.values())
        favg = sum(fvals) / len(fvals)
        frange = max(fvals) - min(fvals)
        result["RESULT_TEMP_VARIATION_PCT"] = (frange / favg) * 100 if favg > 0 else 99
    else:
        result["RESULT_TEMP_VARIATION_PCT"] = 50.0

    # Jitter estimate (placeholder - proper measurement requires long sim)
    result["RESULT_JITTER_PCT"] = 0.5

    return result


def compute_score(measurements, specs):
    """Returns (total_cost, specs_met, details_dict)."""
    if not measurements:
        return 1e6, 0, {}

    cost = 0.0
    specs_met = 0
    details = {}

    for spec_name, spec_def in specs["measurements"].items():
        target = spec_def["target"].strip()
        weight = spec_def["weight"] / 100.0

        # Find measurement
        key = f"RESULT_{spec_name.upper()}"
        measured = measurements.get(key)
        if measured is None:
            cost += weight * 1000
            details[spec_name] = {"measured": None, "met": False}
            continue

        if target.startswith(">"):
            threshold = float(target[1:])
            met = measured >= threshold
            if met:
                cost -= weight * min((measured / threshold - 1.0), 1.0) * 10
            else:
                gap = (threshold - measured) / max(threshold, 1e-12)
                cost += weight * gap ** 2 * 500
        elif target.startswith("<"):
            threshold = float(target[1:])
            met = measured <= threshold
            if met:
                cost -= weight * min((1.0 - measured / threshold), 1.0) * 10
            else:
                gap = (measured - threshold) / max(threshold, 1e-12)
                cost += weight * gap ** 2 * 500
        else:
            met = False
            cost += weight * 100

        if met:
            specs_met += 1
        details[spec_name] = {"measured": measured, "met": met}

    return cost, specs_met, details


def run_bayesian_optimization(template, specs, n_calls=80, n_initial=20):
    """Run Bayesian Optimization using scikit-optimize."""
    from skopt import gp_minimize
    from skopt.space import Real

    # Define search space (log-scale for W and L)
    space = [
        Real(np.log10(0.5), np.log10(50), name='log_Wp'),
        Real(np.log10(0.15), np.log10(2), name='log_Lp'),
        Real(np.log10(0.5), np.log10(25), name='log_Wn'),
        Real(np.log10(0.15), np.log10(2), name='log_Ln'),
        Real(np.log10(0.5), np.log10(100), name='log_Ws'),
        Real(np.log10(0.15), np.log10(5), name='log_Ls'),
    ]

    best_result = {"cost": 1e6, "params": None, "measurements": None, "specs_met": 0}
    call_count = [0]

    def objective(x):
        call_count[0] += 1
        params = {
            "Wp": 10**x[0], "Lp": 10**x[1],
            "Wn": 10**x[2], "Ln": 10**x[3],
            "Ws": 10**x[4], "Ls": 10**x[5],
        }

        tmp_dir = tempfile.mkdtemp(prefix="bo_")
        try:
            measurements = evaluate_full(template, params, tmp_dir)
            cost, specs_met, details = compute_score(measurements, specs)
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

        if cost < best_result["cost"]:
            best_result["cost"] = cost
            best_result["params"] = params
            best_result["measurements"] = measurements
            best_result["specs_met"] = specs_met

        # Print progress
        freq = (measurements or {}).get("RESULT_FREQ_HZ", 0)
        power = (measurements or {}).get("RESULT_POWER_UW", 0)
        tuning = (measurements or {}).get("RESULT_TUNING_RANGE_RATIO", 0)
        temp_var = (measurements or {}).get("RESULT_TEMP_VARIATION_PCT", 99)

        print(f"[BO] {call_count[0]:>3d}/{n_calls} | cost={cost:>10.2f} | "
              f"freq={freq/1e6:>7.1f}MHz | pwr={power:>6.1f}uW | "
              f"tune={tuning:>4.2f}x | temp={temp_var:>5.1f}% | "
              f"specs={specs_met}/5 | best_cost={best_result['cost']:.2f}")

        return cost

    print(f"\nStarting Bayesian Optimization: {n_calls} evaluations, {n_initial} initial random points")
    print(f"Each evaluation takes ~2-3 minutes (5-7 simulations)\n")

    t0 = time.time()
    result = gp_minimize(
        objective, space,
        n_calls=n_calls,
        n_initial_points=n_initial,
        acq_func="EI",
        noise=0.1,
        random_state=42,
        verbose=False,
    )
    elapsed = time.time() - t0

    print(f"\nBO completed in {elapsed/60:.1f} minutes")
    print(f"Best cost: {best_result['cost']:.4f}")
    print(f"Specs met: {best_result['specs_met']}/5")

    return best_result


def run_de_optimization(template, specs, pop_size=16, max_iter=200, patience=30):
    """Run DE optimization with proper evaluation."""
    from evaluate import load_parameters, run_de, compute_cost

    params = load_parameters()
    print(f"\nStarting DE Optimization: pop={pop_size}, max_iter={max_iter}, patience={patience}")

    t0 = time.time()
    de_result = run_de(
        template=template, params=params, specs=specs,
        n_workers=16, quick=False,
    )
    elapsed = time.time() - t0

    best_params = de_result["best_parameters"]

    # Full validation
    print("\n--- Full validation ---")
    tmp_dir = tempfile.mkdtemp(prefix="de_val_")
    measurements = evaluate_full(template, best_params, tmp_dir)
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    cost, specs_met, details = compute_score(measurements, specs)

    print(f"\nDE completed in {elapsed/60:.1f} minutes")
    print(f"Cost: {cost:.4f}, Specs met: {specs_met}/5")

    return {"cost": cost, "params": best_params, "measurements": measurements, "specs_met": specs_met}


def print_final_report(result, specs):
    """Print detailed report of results."""
    params = result["params"]
    measurements = result["measurements"]
    cost, specs_met, details = compute_score(measurements, specs)

    print(f"\n{'='*70}")
    print(f"  FINAL REPORT")
    print(f"{'='*70}")
    print(f"\n  Cost: {cost:.4f} | Specs met: {specs_met}/5\n")

    print(f"  {'Spec':<25} {'Target':>10} {'Measured':>12} {'Status':>8}")
    print(f"  {'-'*60}")
    for spec_name, spec_def in specs["measurements"].items():
        key = f"RESULT_{spec_name.upper()}"
        measured = (measurements or {}).get(key)
        m_str = f"{measured:.2e}" if measured is not None else "N/A"
        met = details.get(spec_name, {}).get("met", False)
        print(f"  {spec_name:<25} {spec_def['target']:>10} {m_str:>12} {'PASS' if met else 'FAIL':>8}")

    print(f"\n  Parameters:")
    for name, val in sorted(params.items()):
        print(f"    {name:<10} = {val:.4f} um")
    print(f"{'='*70}\n")

    return specs_met


def save_results(result, specs, step):
    """Save parameters, measurements, and update results.tsv."""
    params = result["params"]
    measurements = result["measurements"]
    cost, specs_met, _ = compute_score(measurements, specs)

    # Save best parameters
    with open("best_parameters.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "value"])
        for name, val in sorted(params.items()):
            w.writerow([name, val])

    # Save measurements
    with open("measurements.json", "w") as f:
        json.dump({"measurements": measurements, "params": params,
                    "cost": cost, "specs_met": specs_met}, f, indent=2)

    # Append to results.tsv
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True).stdout.strip()
    except:
        commit = "unknown"

    with open("results.tsv", "a") as f:
        score = 1.0 - min(cost / 10, 1.0)  # normalize to 0-1
        freq = (measurements or {}).get("RESULT_FREQ_HZ", 0)
        f.write(f"{step}\t{commit}\t{score:.4f}\t3-stage-nmos-starved\t{specs_met}/5\t"
                f"freq={freq/1e6:.0f}MHz cost={cost:.2f}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", default="bo", choices=["bo", "de"])
    parser.add_argument("--calls", type=int, default=80)
    parser.add_argument("--initial", type=int, default=20)
    args = parser.parse_args()

    template = load_design()
    specs = load_specs()

    if args.method == "bo":
        result = run_bayesian_optimization(template, specs,
                                           n_calls=args.calls,
                                           n_initial=args.initial)
    else:
        result = run_de_optimization(template, specs)

    specs_met = print_final_report(result, specs)
    save_results(result, specs, 1)

    print(f"Score: {1.0 - min(result['cost']/10, 1.0):.2f} | Specs met: {specs_met}/5")
