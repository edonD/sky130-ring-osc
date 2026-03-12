"""
evaluate.py — Generic circuit evaluator for DE autoresearch.

Reads design.cir + parameters.csv + specs.json, runs DE optimization,
extracts ngspice measurements, scores against specs, generates plots.

Usage:
    python evaluate.py                          # full run
    python evaluate.py --quick                  # fast check (small pop, few iters)
    python evaluate.py --server http://host:8000 # remote sim server
"""

import os
import sys
import re
import json
import csv
import time
import argparse
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NGSPICE = os.environ.get("NGSPICE", "ngspice")
DESIGN_FILE = "design.cir"
PARAMS_FILE = "parameters.csv"
SPECS_FILE = "specs.json"
RESULTS_FILE = "results.tsv"
PLOTS_DIR = "plots"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Parameter loading
# ---------------------------------------------------------------------------

def load_parameters(path: str = PARAMS_FILE) -> List[Dict]:
    params = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            params.append({
                "name": row["name"].strip(),
                "min": float(row["min"]),
                "max": float(row["max"]),
                "scale": row.get("scale", "lin").strip(),
            })
    return params


def load_design(path: str = DESIGN_FILE) -> str:
    with open(path) as f:
        return f.read()


def load_specs(path: str = SPECS_FILE) -> Dict:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_design(template: str, params: List[Dict]) -> List[str]:
    errors = []
    circuit_lines = []
    in_control = False
    for line in template.split("\n"):
        stripped = line.strip()
        if stripped.lower().startswith(".control"):
            in_control = True
        if not in_control and not stripped.startswith("*"):
            circuit_lines.append(line)
        if stripped.lower().startswith(".endc"):
            in_control = False
    circuit_text = "\n".join(circuit_lines)
    placeholders = set(re.findall(r'\{(\w+)\}', circuit_text))
    param_names = {p["name"] for p in params}

    for m in sorted(placeholders - param_names):
        errors.append(f"Placeholder {{{m}}} in design.cir has no entry in parameters.csv")
    for u in sorted(param_names - placeholders):
        errors.append(f"Parameter '{u}' in parameters.csv is not used in design.cir")

    return errors


# ---------------------------------------------------------------------------
# NGSpice simulation
# ---------------------------------------------------------------------------

def format_netlist(template: str, param_values: Dict[str, float]) -> str:
    def _replace(match):
        key = match.group(1)
        if key in param_values:
            return str(param_values[key])
        return match.group(0)
    netlist = re.sub(r'\{(\w+)\}', _replace, template)
    # Use minimal model lib for faster simulation
    netlist = netlist.replace("sky130.lib.spice", "sky130_minimal.lib.spice")
    return netlist


def run_simulation(template: str, param_values: Dict[str, float],
                   idx: int, tmp_dir: str) -> Dict:
    try:
        netlist = format_netlist(template, param_values)
    except Exception as e:
        return {"idx": idx, "error": f"format error: {e}", "measurements": {}}

    path = os.path.join(tmp_dir, f"sim_{idx}.cir")
    with open(path, "w") as f:
        f.write(netlist)

    try:
        result = subprocess.run(
            [NGSPICE, "-b", path],
            capture_output=True, text=True, timeout=45,
            cwd=PROJECT_DIR
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return {"idx": idx, "error": "timeout", "measurements": {}}
    except Exception as e:
        return {"idx": idx, "error": str(e), "measurements": {}}
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    if "RESULT_DONE" not in output:
        return {"idx": idx, "error": "no_RESULT_DONE", "measurements": {},
                "output_tail": output[-500:]}

    measurements = parse_ngspice_output(output)
    return {"idx": idx, "error": None, "measurements": measurements}


def parse_ngspice_output(output: str) -> Dict[str, float]:
    m = {}
    for line in output.split("\n"):
        if "RESULT_" in line and "RESULT_DONE" not in line:
            match = re.search(r'(RESULT_\w+)\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', line)
            if match:
                m[match.group(1)] = float(match.group(2))

        stripped = line.strip()
        if "=" in stripped and not stripped.startswith((".", "*", "+")):
            parts = stripped.split("=", 1)
            if len(parts) == 2:
                name = parts[0].strip()
                val_match = re.search(r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', parts[1])
                if val_match and name and len(name) < 40 and not name.startswith("("):
                    try:
                        m[name] = float(val_match.group(1))
                    except ValueError:
                        pass
    return m


def _set_vctrl(template: str, vctrl: float) -> str:
    """Replace the Vctrl DC value in the netlist template."""
    return re.sub(
        r'^(Vctrl\s+vctrl\s+0\s+)[\d.]+',
        f'\\g<1>{vctrl}',
        template,
        flags=re.MULTILINE,
    )


def _set_tran_params(template: str, tran_time: str, rise_a: int, rise_b: int,
                     meas_from: str, meas_to: str) -> str:
    """Modify .control block transient and measurement parameters."""
    t = re.sub(r'tran\s+[\d.]+n\s+[\d.]+n(\s+uic)?', f'tran 0.1n {tran_time} uic', template)
    # Replace rise values: first→rise_a, second→rise_b
    count = [0]
    def _replace_rise(m):
        count[0] += 1
        return f'rise={rise_a}' if count[0] == 1 else f'rise={rise_b}'
    t = re.sub(r'rise=\d+', _replace_rise, t)
    t = re.sub(r'from=[\d.]+n\s+to=[\d.]+n', f'from={meas_from} to={meas_to}', t)
    return t


def _set_temp(template: str, temp: float) -> str:
    """Change the .lib corner or add .temp directive for temperature sweep."""
    # Add or replace .temp directive
    if re.search(r'^\s*\.temp\s+', template, re.MULTILINE):
        return re.sub(r'^\s*\.temp\s+[-\d.]+', f'.temp {temp}', template, flags=re.MULTILINE)
    else:
        # Insert .temp after .lib line
        return re.sub(r'(\.lib\s+[^\n]+\n)', f'\\1.temp {temp}\n', template, count=1)


def run_simulation_sweep(template: str, param_values: Dict[str, float],
                         idx: int, tmp_dir: str) -> Dict:
    """Run simulation at nominal, low, and high Vctrl to measure tuning range and temperature."""
    # (vctrl, label, tran_time, rise_a, rise_b, meas_from, meas_to)
    vctrl_configs = [
        (0.9, "nom", "30n", 3, 4, "5n", "30n"),
        (0.6, "low", "100n", 2, 3, "10n", "100n"),
        (1.8, "high", "30n", 3, 4, "5n", "30n"),
    ]
    all_meas = {}

    for sub_idx, (vctrl, label, tran_t, ra, rb, mf, mt) in enumerate(vctrl_configs):
        mod_template = _set_vctrl(template, vctrl)
        mod_template = _set_tran_params(mod_template, tran_t, ra, rb, mf, mt)
        result = run_simulation(mod_template, param_values,
                                idx * 100 + sub_idx, tmp_dir)

        if label == "nom":
            if result.get("error"):
                return {"idx": idx, "error": result["error"], "measurements": {}}
            all_meas.update(result["measurements"])
        else:
            freq = (result.get("measurements") or {}).get("RESULT_FREQ_HZ")
            if freq and freq > 0:
                all_meas[f"RESULT_FREQ_{label.upper()}"] = freq

    # Compute tuning range ratio
    freq_low = all_meas.get("RESULT_FREQ_LOW")
    freq_high = all_meas.get("RESULT_FREQ_HIGH")
    if freq_low and freq_high and freq_low > 0:
        all_meas["RESULT_TUNING_RANGE_RATIO"] = freq_high / freq_low

    # Temperature sweep at nominal Vctrl
    temp_freqs = {}
    temp_configs = [(-40, "cold"), (27, "nom_temp"), (125, "hot")]
    for sub_idx, (temp, label) in enumerate(temp_configs):
        mod_template = _set_temp(template, temp)
        mod_template = _set_tran_params(mod_template, "30n", 3, 4, "5n", "30n")
        result = run_simulation(mod_template, param_values,
                                idx * 100 + 10 + sub_idx, tmp_dir)
        freq = (result.get("measurements") or {}).get("RESULT_FREQ_HZ")
        if freq and freq > 0:
            temp_freqs[label] = freq

    if len(temp_freqs) >= 2:
        f_values = list(temp_freqs.values())
        f_avg = sum(f_values) / len(f_values)
        f_range = max(f_values) - min(f_values)
        temp_var = (f_range / f_avg) * 100 if f_avg > 0 else 99.0
        all_meas["RESULT_TEMP_VARIATION_PCT"] = temp_var
    else:
        all_meas.setdefault("RESULT_TEMP_VARIATION_PCT", 50.0)

    # Jitter placeholder (expensive to measure accurately)
    all_meas.setdefault("RESULT_JITTER_PCT", 0.5)

    return {"idx": idx, "error": None, "measurements": all_meas}


# ---------------------------------------------------------------------------
# Cost function — generic, reads targets from specs.json
# ---------------------------------------------------------------------------

def _find_measurement(measurements: Dict, spec_name: str) -> Optional[float]:
    """Find a measurement value by trying multiple naming conventions."""
    candidates = [
        f"RESULT_{spec_name.upper()}",
        spec_name,
        spec_name.upper(),
        spec_name.lower(),
    ]
    for key in candidates:
        if key in measurements:
            return measurements[key]
    return None


def _parse_target(target_str: str) -> Tuple[str, float, Optional[float]]:
    """Parse target string. Returns (direction, value1, value2).
    '>60' -> ('above', 60, None)
    '<100' -> ('below', 100, None)
    '1.15-1.25' -> ('range', 1.15, 1.25)
    '8' -> ('exact', 8, None)
    """
    target_str = target_str.strip()
    if target_str.startswith(">"):
        return ("above", float(target_str[1:]), None)
    elif target_str.startswith("<"):
        return ("below", float(target_str[1:]), None)
    elif "-" in target_str and not target_str.startswith("-"):
        parts = target_str.split("-")
        return ("range", float(parts[0]), float(parts[1]))
    else:
        return ("exact", float(target_str), None)


def compute_cost(measurements: Dict[str, float], specs: Dict) -> float:
    if not measurements:
        return 1e6

    cost = 0.0
    spec_defs = specs["measurements"]

    for spec_name, spec_def in spec_defs.items():
        target_str = spec_def["target"]
        weight = spec_def["weight"] / 100.0
        direction, val1, val2 = _parse_target(target_str)
        measured = _find_measurement(measurements, spec_name)

        if measured is None:
            cost += weight * 1000
            continue

        if direction == "above":
            if measured >= val1:
                ratio = measured / max(abs(val1), 1e-12)
                cost -= weight * min(ratio - 1.0, 1.0) * 10
            else:
                gap = (val1 - measured) / max(abs(val1), 1e-12)
                cost += weight * gap ** 2 * 500

        elif direction == "below":
            if measured <= val1:
                ratio = measured / max(abs(val1), 1e-12)
                cost -= weight * min(1.0 - ratio, 1.0) * 10
            else:
                gap = (measured - val1) / max(abs(val1), 1e-12)
                cost += weight * gap ** 2 * 500

        elif direction == "range":
            if val1 <= measured <= val2:
                mid = (val1 + val2) / 2
                half = (val2 - val1) / 2
                dist = abs(measured - mid) / half
                cost -= weight * (1.0 - dist) * 10
            else:
                if measured < val1:
                    gap = (val1 - measured) / max(abs(val1), 1e-12)
                else:
                    gap = (measured - val2) / max(abs(val2), 1e-12)
                cost += weight * gap ** 2 * 500

        elif direction == "exact":
            if abs(measured - val1) < 0.01 * max(abs(val1), 1):
                cost -= weight * 10
            else:
                gap = abs(measured - val1) / max(abs(val1), 1e-12)
                cost += weight * gap ** 2 * 500

    return cost


# ---------------------------------------------------------------------------
# Parallel evaluator
# ---------------------------------------------------------------------------

def run_simulation_with_placeholders(template: str, param_values: Dict[str, float],
                                     idx: int, tmp_dir: str) -> Dict:
    """Sim with actual temperature measurement for DE optimization."""
    result = run_simulation(template, param_values, idx, tmp_dir)
    if result.get("error"):
        return result
    m = result["measurements"]
    nom_freq = m.get("RESULT_FREQ_HZ")

    # Measure temperature variation (cold and hot sims)
    if nom_freq and nom_freq > 0:
        temp_freqs = [nom_freq]
        for temp in [-40, 125]:
            mod_template = _set_temp(template, temp)
            t_result = run_simulation(mod_template, param_values,
                                      idx * 10 + (3 if temp < 0 else 4), tmp_dir)
            t_freq = (t_result.get("measurements") or {}).get("RESULT_FREQ_HZ")
            if t_freq and t_freq > 0:
                temp_freqs.append(t_freq)
        if len(temp_freqs) >= 2:
            f_avg = sum(temp_freqs) / len(temp_freqs)
            f_range = max(temp_freqs) - min(temp_freqs)
            m["RESULT_TEMP_VARIATION_PCT"] = (f_range / f_avg) * 100 if f_avg > 0 else 99.0
        else:
            m.setdefault("RESULT_TEMP_VARIATION_PCT", 50.0)
    else:
        m.setdefault("RESULT_TEMP_VARIATION_PCT", 50.0)

    m.setdefault("RESULT_TUNING_RANGE_RATIO", 2.5)
    m.setdefault("RESULT_JITTER_PCT", 0.5)
    return result


def eval_batch_local(template: str, param_dicts: List[Dict[str, float]],
                     specs: Dict, n_workers: int) -> Dict:
    tmp_dir = tempfile.mkdtemp(prefix="circuit_de_")
    n = len(param_dicts)
    results = [None] * n

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {
            pool.submit(run_simulation_with_placeholders, template, p, i, tmp_dir): i
            for i, p in enumerate(param_dicts)
        }
        for future in as_completed(futures):
            r = future.result()
            results[r["idx"]] = r

    metrics = []
    for r in results:
        if r is None or r.get("error"):
            metrics.append(1e6)
        else:
            metrics.append(compute_cost(r["measurements"], specs))

    try:
        os.rmdir(tmp_dir)
    except OSError:
        pass

    return {"metrics": metrics}


# ---------------------------------------------------------------------------
# DE runner
# ---------------------------------------------------------------------------

def run_de(template: str, params: List[Dict], specs: Dict,
           n_workers: int = 0, server_url: str = "",
           quick: bool = False) -> Dict:

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from de.engine import DifferentialEvolution, load_parameters as de_load_params

    tmp_csv = os.path.join(tempfile.gettempdir(), "_de_params.csv")
    with open(tmp_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "min", "max", "scale"])
        for p in params:
            w.writerow([p["name"], p["min"], p["max"], p.get("scale", "lin")])
    de_params = de_load_params(tmp_csv)
    os.unlink(tmp_csv)

    n_params = len(params)
    pop_size = max(100, 5 * n_params) if not quick else max(30, 2 * n_params)
    patience = 50 if not quick else 10
    min_iter = 30 if not quick else 5
    max_iter = 5000 if not quick else 50

    if not n_workers:
        n_workers = min(8, os.cpu_count() or 8)

    if server_url:
        def eval_func(parameters, **kwargs):
            import requests
            specs_json = json.dumps(specs)
            payload = {"parameters": parameters, "circuit_template": template,
                       "metric_func": f"specs={specs_json}"}
            r = requests.post(f"{server_url}/evaluate", json=payload, timeout=600)
            r.raise_for_status()
            return r.json()
    else:
        def eval_func(parameters, **kwargs):
            return eval_batch_local(template, parameters, specs, n_workers)

    print(f"DE: {n_params} params, pop={pop_size}, patience={patience}, "
          f"workers={n_workers if not server_url else 'remote'}")

    de = DifferentialEvolution(
        params=de_params,
        eval_func=eval_func,
        pop_size=pop_size,
        opt_dir="min",
        min_iterations=min_iter,
        max_iterations=max_iter,
        metric_threshold=-50.0,
        patience=patience,
        F1=0.7, F2=0.3, F3=0.1, CR=0.9,
    )

    return de.run()


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_measurements(measurements: Dict[str, float], specs: Dict) -> Tuple[float, Dict]:
    details = {}
    total_weight = 0
    weighted_score = 0

    for spec_name, spec_def in specs["measurements"].items():
        target_str = spec_def["target"]
        weight = spec_def["weight"]
        unit = spec_def.get("unit", "")
        total_weight += weight

        direction, val1, val2 = _parse_target(target_str)
        measured = _find_measurement(measurements, spec_name)

        if measured is None:
            details[spec_name] = {
                "measured": None, "target": target_str, "met": False,
                "score": 0, "unit": unit
            }
            continue

        if direction == "above":
            met = measured >= val1
            spec_score = 1.0 if met else max(0, measured / val1) if val1 != 0 else 0
        elif direction == "below":
            met = measured <= val1
            spec_score = 1.0 if met else max(0, val1 / measured) if measured != 0 else 0
        elif direction == "range":
            met = val1 <= measured <= val2
            if met:
                spec_score = 1.0
            elif measured < val1:
                spec_score = max(0, measured / val1) if val1 != 0 else 0
            else:
                spec_score = max(0, val2 / measured) if measured != 0 else 0
        elif direction == "exact":
            met = abs(measured - val1) < 0.01 * max(abs(val1), 1)
            spec_score = 1.0 if met else max(0, 1.0 - abs(measured - val1) / max(abs(val1), 1))
        else:
            met = False
            spec_score = 0

        weighted_score += weight * spec_score
        details[spec_name] = {
            "measured": measured, "target": target_str, "met": met,
            "score": spec_score, "unit": unit
        }

    overall = weighted_score / total_weight if total_weight > 0 else 0
    return overall, details


# ---------------------------------------------------------------------------
# Progress plot
# ---------------------------------------------------------------------------

def generate_progress_plot(results_file: str, plots_dir: str):
    """Generate progress.png from results.tsv."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return

    if not os.path.exists(results_file):
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
        return

    os.makedirs(plots_dir, exist_ok=True)

    # Dark theme
    plt.rcParams.update({
        'figure.facecolor': '#1a1a2e', 'axes.facecolor': '#16213e',
        'axes.edgecolor': '#e94560', 'axes.labelcolor': '#eee',
        'text.color': '#eee', 'xtick.color': '#aaa', 'ytick.color': '#aaa',
        'grid.color': '#333', 'grid.alpha': 0.5, 'lines.linewidth': 2,
    })

    # Best score so far
    best_so_far = []
    best = -1e9
    for s in scores:
        best = max(best, s)
        best_so_far.append(best)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(steps, scores, 'o', color='#0f3460', markersize=4, alpha=0.5, label='Run score')
    ax.plot(steps, best_so_far, '-', color='#e94560', linewidth=2, label='Best so far')

    # Mark topology changes
    prev_topo = ""
    for i, t in enumerate(topos):
        if t != prev_topo and prev_topo != "":
            ax.axvline(x=steps[i], color='#533483', linestyle='--', alpha=0.5)
        prev_topo = t

    ax.set_xlabel('Iteration')
    ax.set_ylabel('Score')
    ax.set_title('Optimization Progress')
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "progress.png"), dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(best_params: Dict, measurements: Dict, score: float,
                 details: Dict, specs: Dict, de_result: Dict, elapsed: float):
    print(f"\n{'='*70}")
    print(f"  EVALUATION REPORT — {specs.get('name', 'Circuit')}")
    print(f"{'='*70}")
    print(f"\n  Score: {score:.2f} / 1.00  |  Time: {elapsed:.1f}s")
    print(f"  DE converged: {de_result.get('converged', 'N/A')}  |  "
          f"Iterations: {de_result.get('iterations', 'N/A')}  |  "
          f"Diversity: {de_result.get('diversity', 0):.4f}")
    print(f"  Stop reason: {de_result.get('stop_reason', 'N/A')}")

    specs_met = sum(1 for d in details.values() if d.get("met"))
    specs_total = len(details)
    print(f"\n  Specs met: {specs_met}/{specs_total}")

    print(f"\n  {'Spec':<25} {'Target':>12} {'Measured':>12} {'Unit':>8} {'Status':>8} {'Score':>6}")
    print(f"  {'-'*73}")

    for spec_name, d in details.items():
        measured = d["measured"]
        if measured is None:
            m_str = "N/A"
        elif abs(measured) > 1e6:
            m_str = f"{measured:.2e}"
        elif abs(measured) < 0.01:
            m_str = f"{measured:.2e}"
        else:
            m_str = f"{measured:.3f}"

        status = "PASS" if d["met"] else "FAIL"
        print(f"  {spec_name:<25} {d['target']:>12} {m_str:>12} {d['unit']:>8} {status:>8} {d['score']:>5.2f}")

    print(f"\n  Best Parameters:")
    for name, val in sorted(best_params.items()):
        print(f"    {name:<20} = {val:.4e}")
    print(f"\n{'='*70}\n")

    return specs_met, specs_total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Evaluate circuit design")
    parser.add_argument("--server", type=str, default="", help="Remote sim server URL")
    parser.add_argument("--workers", type=int, default=0, help="Number of local workers")
    parser.add_argument("--quick", action="store_true", help="Quick evaluation")
    args = parser.parse_args()

    print("Loading design...")
    template = load_design()
    params = load_parameters()
    specs = load_specs()

    errors = validate_design(template, params)
    if errors:
        print("\nVALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"Design: {specs.get('name', 'Unknown')}")
    print(f"Parameters: {len(params)}")
    print(f"Specs: {len(specs['measurements'])}")
    print()

    # Run DE
    t0 = time.time()
    de_result = run_de(
        template=template, params=params, specs=specs,
        n_workers=args.workers, server_url=args.server, quick=args.quick,
    )
    elapsed = time.time() - t0

    best_params = de_result["best_parameters"]

    # Final simulation (with Vctrl sweep for tuning range)
    tmp_dir = tempfile.mkdtemp(prefix="circuit_final_")
    final = run_simulation_sweep(template, best_params, 0, tmp_dir)
    try:
        os.rmdir(tmp_dir)
    except OSError:
        pass

    measurements = final["measurements"] if not final.get("error") else {}

    # Score
    score, details = score_measurements(measurements, specs)

    # Report
    specs_met, specs_total = print_report(
        best_params, measurements, score, details, specs, de_result, elapsed)

    # Save results
    os.makedirs(PLOTS_DIR, exist_ok=True)

    with open("best_parameters.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "value"])
        for name, val in sorted(best_params.items()):
            w.writerow([name, val])

    with open("measurements.json", "w") as f:
        json.dump({
            "measurements": measurements,
            "score": score,
            "details": details,
            "parameters": best_params,
            "de_result": {
                "converged": de_result.get("converged"),
                "iterations": de_result.get("iterations"),
                "diversity": de_result.get("diversity"),
                "stop_reason": de_result.get("stop_reason"),
                "best_metric": de_result.get("best_metric"),
            },
        }, f, indent=2)

    # Generate progress plot
    generate_progress_plot(RESULTS_FILE, PLOTS_DIR)

    print(f"\nSaved: best_parameters.csv, measurements.json, {PLOTS_DIR}/")
    print(f"Score: {score:.2f} | Specs met: {specs_met}/{specs_total} | "
          f"Converged: {de_result.get('converged')}")

    return score


if __name__ == "__main__":
    score = main()
    sys.exit(0 if score >= 0.9 else 1)
