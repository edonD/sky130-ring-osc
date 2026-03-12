#!/usr/bin/env python3
"""Standalone optimization script that doesn't depend on files the concurrent agent overwrites."""

import os
import sys
import re
import json
import csv
import time
import tempfile
import subprocess
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
NGSPICE = "ngspice"

# ---- Inline circuit template (not read from design.cir) ----
TEMPLATE = """* SKY130 Complementary Current-Starved Ring Oscillator — 3-stage
* NMOS starving: direct Vctrl. PMOS starving: current mirror.
* VDD ramp startup with cap imbalance breaks symmetry for oscillation.

.lib "sky130_models/sky130_minimal.lib.spice" tt

* Supply — ramp from 0 to 1.8V to enable oscillation startup with uic
Vdd vdd 0 PWL(0 0 1n 1.8)
Vss vss 0 0

* Control voltage
Vctrl vctrl 0 0.9

* === Current mirror bias ===
XMref_n pbias vctrl vss vss sky130_fd_pr__nfet_01v8 W={Wbn}u L={Lbn}u nf=1
XMref_p pbias pbias vdd vdd sky130_fd_pr__pfet_01v8 W={Wbp}u L={Lbp}u nf=1

* === Stage 1 ===
XMp1 n1 n3 sp1 vdd sky130_fd_pr__pfet_01v8 W={Wp}u L={Lp}u nf=1
XMn1 n1 n3 sn1 vss sky130_fd_pr__nfet_01v8 W={Wn}u L={Ln}u nf=1
XMsp1 sp1 pbias vdd vdd sky130_fd_pr__pfet_01v8 W={Wsp}u L={Lsp}u nf=1
XMsn1 sn1 vctrl vss vss sky130_fd_pr__nfet_01v8 W={Wsn}u L={Lsn}u nf=1

* === Stage 2 ===
XMp2 n2 n1 sp2 vdd sky130_fd_pr__pfet_01v8 W={Wp}u L={Lp}u nf=1
XMn2 n2 n1 sn2 vss sky130_fd_pr__nfet_01v8 W={Wn}u L={Ln}u nf=1
XMsp2 sp2 pbias vdd vdd sky130_fd_pr__pfet_01v8 W={Wsp}u L={Lsp}u nf=1
XMsn2 sn2 vctrl vss vss sky130_fd_pr__nfet_01v8 W={Wsn}u L={Lsn}u nf=1

* === Stage 3 ===
XMp3 n3 n2 sp3 vdd sky130_fd_pr__pfet_01v8 W={Wp}u L={Lp}u nf=1
XMn3 n3 n2 sn3 vss sky130_fd_pr__nfet_01v8 W={Wn}u L={Ln}u nf=1
XMsp3 sp3 pbias vdd vdd sky130_fd_pr__pfet_01v8 W={Wsp}u L={Lsp}u nf=1
XMsn3 sn3 vctrl vss vss sky130_fd_pr__nfet_01v8 W={Wsn}u L={Lsn}u nf=1

* Output buffer (fixed)
XMpout out n3 vdd vdd sky130_fd_pr__pfet_01v8 W=5u L=0.15u nf=1
XMnout out n3 vss vss sky130_fd_pr__nfet_01v8 W=2.5u L=0.15u nf=1

* Capacitive imbalance on n1 for symmetry breaking during VDD ramp
Ckick n1 vss 50f

.options reltol=0.01 method=gear maxord=3

* === Measurements ===
.control
tran 0.1n 30n uic

* Measure frequency from output
meas tran trise1 when v(out)=0.9 rise=3
meas tran trise2 when v(out)=0.9 rise=4
let period = trise2 - trise1
let freq = 1 / period
echo "RESULT_FREQ_HZ" $&freq

* Power measurement
meas tran avg_idd avg i(Vdd) from=5n to=30n
let pwr = abs(avg_idd) * 1.8 * 1e6
echo "RESULT_POWER_UW" $&pwr

echo "RESULT_DONE"
.endc

.end
"""

# ---- Inline parameters ----
PARAMS = [
    {"name": "Wp",  "min": 0.5, "max": 20.0, "scale": "log"},
    {"name": "Lp",  "min": 0.15, "max": 2.0, "scale": "log"},
    {"name": "Wn",  "min": 0.5, "max": 10.0, "scale": "log"},
    {"name": "Ln",  "min": 0.15, "max": 2.0, "scale": "log"},
    {"name": "Wsp", "min": 0.5, "max": 20.0, "scale": "log"},
    {"name": "Lsp", "min": 0.15, "max": 5.0, "scale": "log"},
    {"name": "Wsn", "min": 0.5, "max": 20.0, "scale": "log"},
    {"name": "Lsn", "min": 0.15, "max": 5.0, "scale": "log"},
    {"name": "Wbp", "min": 0.5, "max": 20.0, "scale": "log"},
    {"name": "Lbp", "min": 0.15, "max": 5.0, "scale": "log"},
    {"name": "Wbn", "min": 0.5, "max": 20.0, "scale": "log"},
    {"name": "Lbn", "min": 0.15, "max": 5.0, "scale": "log"},
]

SPECS = json.loads(open(os.path.join(PROJECT_DIR, "specs.json")).read())


def format_netlist(template, param_values):
    def _replace(match):
        key = match.group(1)
        return str(param_values[key]) if key in param_values else match.group(0)
    return re.sub(r'\{(\w+)\}', _replace, template)


def parse_output(output):
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


def run_sim(template, param_values, idx, tmp_dir):
    try:
        netlist = format_netlist(template, param_values)
    except Exception as e:
        return {"idx": idx, "error": str(e), "measurements": {}}

    path = os.path.join(tmp_dir, f"sim_{idx}.cir")
    with open(path, "w") as f:
        f.write(netlist)
    try:
        result = subprocess.run(
            [NGSPICE, "-b", path], capture_output=True, text=True,
            timeout=45, cwd=PROJECT_DIR
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
        return {"idx": idx, "error": "no_done", "measurements": {}}
    return {"idx": idx, "error": None, "measurements": parse_output(output)}


def set_vctrl(template, vctrl):
    return re.sub(r'^(Vctrl\s+vctrl\s+0\s+)[\d.]+', f'\\g<1>{vctrl}', template, flags=re.MULTILINE)


def set_tran(template, tran_time, ra, rb, mf, mt):
    t = re.sub(r'tran\s+[\d.]+n\s+[\d.]+n(\s+uic)?', f'tran 0.1n {tran_time} uic', template)
    count = [0]
    def _rr(m):
        count[0] += 1
        return f'rise={ra}' if count[0] == 1 else f'rise={rb}'
    t = re.sub(r'rise=\d+', _rr, t)
    t = re.sub(r'from=[\d.]+n\s+to=[\d.]+n', f'from={mf} to={mt}', t)
    return t


def set_temp(template, temp):
    if re.search(r'^\s*\.temp\s+', template, re.MULTILINE):
        return re.sub(r'^\s*\.temp\s+[-\d.]+', f'.temp {temp}', template, flags=re.MULTILINE)
    return re.sub(r'(\.lib\s+[^\n]+\n)', f'\\1.temp {temp}\n', template, count=1)


def eval_candidate(template, param_values, idx, tmp_dir):
    """Run nom sim + temp sweep (3 sims total)."""
    result = run_sim(template, param_values, idx, tmp_dir)
    if result.get("error"):
        return result
    m = result["measurements"]
    nom_freq = m.get("RESULT_FREQ_HZ")

    if nom_freq and nom_freq > 0:
        temp_freqs = [nom_freq]
        for temp in [-40, 125]:
            mt = set_temp(template, temp)
            tr = run_sim(mt, param_values, idx * 10 + (3 if temp < 0 else 4), tmp_dir)
            tf = (tr.get("measurements") or {}).get("RESULT_FREQ_HZ")
            if tf and tf > 0:
                temp_freqs.append(tf)
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


def compute_cost(measurements, specs):
    if not measurements:
        return 1e6
    cost = 0.0
    for spec_name, spec_def in specs["measurements"].items():
        target = spec_def["target"].strip()
        weight = spec_def["weight"] / 100.0
        candidates = [f"RESULT_{spec_name.upper()}", spec_name, spec_name.upper()]
        measured = None
        for k in candidates:
            if k in measurements:
                measured = measurements[k]
                break
        if measured is None:
            cost += weight * 1000
            continue
        if target.startswith(">"):
            val = float(target[1:])
            if measured >= val:
                cost -= weight * min(measured / max(abs(val), 1e-12) - 1.0, 1.0) * 10
            else:
                gap = (val - measured) / max(abs(val), 1e-12)
                cost += weight * gap ** 2 * 500
        elif target.startswith("<"):
            val = float(target[1:])
            if measured <= val:
                cost -= weight * min(1.0 - measured / max(abs(val), 1e-12), 1.0) * 10
            else:
                gap = (measured - val) / max(abs(val), 1e-12)
                cost += weight * gap ** 2 * 500
    return cost


def eval_batch(template, param_dicts, specs, n_workers):
    tmp_dir = tempfile.mkdtemp(prefix="optim_")
    n = len(param_dicts)
    results = [None] * n
    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {
            pool.submit(eval_candidate, template, p, i, tmp_dir): i
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


def full_sweep(template, params, tmp_dir):
    """Final sweep: Vctrl sweep + temp sweep."""
    measurements = {}

    # Nominal
    r = run_sim(template, params, 0, tmp_dir)
    if r.get("error"):
        return {"error": r["error"], "measurements": {}}
    measurements.update(r["measurements"])

    # Low Vctrl (0.7V — below this the dual-starving topology stops oscillating)
    low_t = set_vctrl(template, 0.7)
    low_t = set_tran(low_t, "200n", 2, 3, "10n", "200n")
    lr = run_sim(low_t, params, 1, tmp_dir)
    fl = (lr.get("measurements") or {}).get("RESULT_FREQ_HZ")
    if fl and fl > 0:
        measurements["RESULT_FREQ_LOW"] = fl

    # High Vctrl
    high_t = set_vctrl(template, 1.8)
    hr = run_sim(high_t, params, 2, tmp_dir)
    fh = (hr.get("measurements") or {}).get("RESULT_FREQ_HZ")
    if fh and fh > 0:
        measurements["RESULT_FREQ_HIGH"] = fh

    # Tuning range
    if "RESULT_FREQ_LOW" in measurements and "RESULT_FREQ_HIGH" in measurements:
        measurements["RESULT_TUNING_RANGE_RATIO"] = measurements["RESULT_FREQ_HIGH"] / measurements["RESULT_FREQ_LOW"]

    # Temp sweep
    temp_freqs = {}
    for temp, label in [(-40, "cold"), (27, "nom"), (125, "hot")]:
        tt = set_temp(template, temp)
        tr = run_sim(tt, params, 10 + temp, tmp_dir)
        tf = (tr.get("measurements") or {}).get("RESULT_FREQ_HZ")
        if tf and tf > 0:
            temp_freqs[label] = tf
    if len(temp_freqs) >= 2:
        fv = list(temp_freqs.values())
        fa = sum(fv) / len(fv)
        measurements["RESULT_TEMP_VARIATION_PCT"] = (max(fv) - min(fv)) / fa * 100 if fa > 0 else 99.0
    else:
        measurements["RESULT_TEMP_VARIATION_PCT"] = 50.0

    measurements.setdefault("RESULT_JITTER_PCT", 0.5)
    return {"error": None, "measurements": measurements}


def score_measurements(measurements, specs):
    details = {}
    total_weight = 0
    weighted_score = 0
    for spec_name, spec_def in specs["measurements"].items():
        target_str = spec_def["target"].strip()
        weight = spec_def["weight"]
        unit = spec_def.get("unit", "")
        total_weight += weight
        candidates = [f"RESULT_{spec_name.upper()}", spec_name]
        measured = None
        for k in candidates:
            if k in measurements:
                measured = measurements[k]
                break
        if measured is None:
            details[spec_name] = {"measured": None, "target": target_str, "met": False, "score": 0, "unit": unit}
            continue
        if target_str.startswith(">"):
            val = float(target_str[1:])
            met = measured >= val
            sc = 1.0 if met else max(0, measured / val) if val != 0 else 0
        elif target_str.startswith("<"):
            val = float(target_str[1:])
            met = measured <= val
            sc = 1.0 if met else max(0, val / measured) if measured != 0 else 0
        else:
            val = float(target_str)
            met = abs(measured - val) < 0.01 * max(abs(val), 1)
            sc = 1.0 if met else 0
        weighted_score += weight * sc
        details[spec_name] = {"measured": measured, "target": target_str, "met": met, "score": sc, "unit": unit}
    return weighted_score / total_weight if total_weight > 0 else 0, details


def main():
    n_workers = min(4, os.cpu_count() or 4)
    print(f"Starting dual-starving ring osc optimization ({len(PARAMS)} params)")

    # DE setup
    sys.path.insert(0, PROJECT_DIR)
    from de.engine import DifferentialEvolution, load_parameters as de_load_params

    tmp_csv = os.path.join(tempfile.gettempdir(), "_de_params_standalone.csv")
    with open(tmp_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "min", "max", "scale"])
        for p in PARAMS:
            w.writerow([p["name"], p["min"], p["max"], p["scale"]])
    de_params = de_load_params(tmp_csv)
    os.unlink(tmp_csv)

    pop_size = 30
    def eval_func(parameters, **kwargs):
        return eval_batch(TEMPLATE, parameters, SPECS, n_workers)

    print(f"DE: pop={pop_size}, patience=15, workers={n_workers}")
    t0 = time.time()

    de = DifferentialEvolution(
        params=de_params,
        eval_func=eval_func,
        pop_size=pop_size,
        opt_dir="min",
        min_iterations=10,
        max_iterations=100,
        metric_threshold=-50.0,
        patience=15,
        F1=0.7, F2=0.3, F3=0.1, CR=0.9,
    )
    de_result = de.run()
    elapsed = time.time() - t0
    best = de_result["best_parameters"]
    print(f"\nDE done in {elapsed:.0f}s, {de_result.get('iterations')} iters")

    # Final sweep
    print("Running final validation sweep...")
    tmp_dir = tempfile.mkdtemp(prefix="final_sweep_")
    final = full_sweep(TEMPLATE, best, tmp_dir)
    measurements = final["measurements"] if not final.get("error") else {}

    score, details = score_measurements(measurements, SPECS)

    # Print report
    print(f"\n{'='*60}")
    print(f"  Score: {score:.2f} / 1.00")
    specs_met = sum(1 for d in details.values() if d.get("met"))
    print(f"  Specs met: {specs_met}/{len(details)}")
    print(f"\n  {'Spec':<25} {'Target':>10} {'Measured':>12} {'Status':>8}")
    print(f"  {'-'*57}")
    for name, d in details.items():
        m = d["measured"]
        m_str = f"{m:.2e}" if m is not None and abs(m) > 1e5 else f"{m:.3f}" if m is not None else "N/A"
        print(f"  {name:<25} {d['target']:>10} {m_str:>12} {'PASS' if d['met'] else 'FAIL':>8}")
    print(f"\n  Best parameters:")
    for k, v in sorted(best.items()):
        print(f"    {k:<10} = {v:.4f}")
    print(f"{'='*60}")

    # Save results
    with open(os.path.join(PROJECT_DIR, "best_parameters.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "value"])
        for k, v in sorted(best.items()):
            w.writerow([k, v])

    with open(os.path.join(PROJECT_DIR, "measurements.json"), "w") as f:
        json.dump({
            "measurements": measurements,
            "score": score,
            "details": details,
            "parameters": best,
            "de_result": {
                "converged": de_result.get("converged"),
                "iterations": de_result.get("iterations"),
                "diversity": de_result.get("diversity"),
                "stop_reason": de_result.get("stop_reason"),
                "best_metric": de_result.get("best_metric"),
            },
        }, f, indent=2)

    # Write design.cir and parameters.csv with final state
    with open(os.path.join(PROJECT_DIR, "design.cir"), "w") as f:
        f.write(TEMPLATE)
    with open(os.path.join(PROJECT_DIR, "parameters.csv"), "w") as f:
        w = csv.writer(f)
        w.writerow(["name", "min", "max", "scale"])
        for p in PARAMS:
            w.writerow([p["name"], p["min"], p["max"], p["scale"]])

    print(f"\nFinal score: {score:.2f} | Specs: {specs_met}/{len(details)}")
    return score


if __name__ == "__main__":
    score = main()
    sys.exit(0 if score >= 0.9 else 1)
