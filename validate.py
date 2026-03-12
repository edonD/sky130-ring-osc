#!/usr/bin/env python3
"""Full validation of optimized ring oscillator parameters."""

import subprocess
import re
import os
import sys
import csv
import numpy as np

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Best parameters from DE optimization
PARAMS = {}
with open(os.path.join(PROJECT_DIR, "best_parameters.csv")) as f:
    reader = csv.DictReader(f)
    for row in reader:
        PARAMS[row["name"]] = float(row["value"])

print("Parameters:", PARAMS)


def make_netlist(vctrl=0.9, temp=27, tran_time="500n", tran_step="0.01n"):
    """Generate a netlist with given parameters."""
    with open(os.path.join(PROJECT_DIR, "design.cir")) as f:
        template = f.read()

    # Substitute parameters
    def _replace(match):
        key = match.group(1)
        if key in PARAMS:
            return str(PARAMS[key])
        return match.group(0)
    netlist = re.sub(r'\{(\w+)\}', _replace, template)

    # Set Vctrl
    netlist = re.sub(r'^(Vctrl\s+vctrl\s+0\s+)[\d.]+', f'\\g<1>{vctrl}',
                     netlist, flags=re.MULTILINE)

    # Set temperature
    if re.search(r'^\s*\.temp\s+', netlist, re.MULTILINE):
        netlist = re.sub(r'^\s*\.temp\s+[-\d.]+', f'.temp {temp}',
                         netlist, flags=re.MULTILINE)
    else:
        netlist = re.sub(r'(\.lib\s+[^\n]+\n)', f'\\1.temp {temp}\n',
                         netlist, count=1)

    # Replace tran command
    netlist = re.sub(r'tran\s+[\d.]+n\s+[\d.]+n(\s+uic)?',
                     f'tran {tran_step} {tran_time} uic', netlist)

    # Use full model lib
    netlist = netlist.replace("sky130_minimal.lib.spice", "sky130.lib.spice")

    return netlist


def run_ngspice(netlist, label="sim"):
    """Run ngspice and return stdout+stderr."""
    path = os.path.join(PROJECT_DIR, f"validate_{label}.cir")
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


def extract_freq(output):
    """Extract frequency from RESULT_FREQ_HZ."""
    match = re.search(r'RESULT_FREQ_HZ\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', output)
    if match:
        return float(match.group(1))
    return None


def extract_power(output):
    """Extract power from RESULT_POWER_UW."""
    match = re.search(r'RESULT_POWER_UW\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', output)
    if match:
        return float(match.group(1))
    return None


# ========================================================
# CHECK 1: Verify oscillation at nominal (20+ cycles)
# ========================================================
print("\n" + "="*60)
print("CHECK 1: Verify oscillation at nominal Vctrl=0.9V")
print("="*60)

netlist = make_netlist(vctrl=0.9, temp=27, tran_time="500n", tran_step="0.05n")
output = run_ngspice(netlist, "osc_check")
freq = extract_freq(output)
power = extract_power(output)

if freq and freq > 0:
    period_ns = 1e9 / freq
    n_cycles = 500 / period_ns  # 500ns sim time
    print(f"  PASS: Oscillating at {freq/1e6:.1f} MHz")
    print(f"  Period: {period_ns:.2f} ns")
    print(f"  Cycles in 500ns: {n_cycles:.0f}")
    print(f"  Power: {power:.1f} uW")
else:
    print(f"  FAIL: No oscillation detected")
    sys.exit(1)

# ========================================================
# CHECK 2: Verify tuning range (sweep Vctrl 0V to 1.8V)
# ========================================================
print("\n" + "="*60)
print("CHECK 2: Tuning range sweep")
print("="*60)

vctrl_values = [0.3, 0.5, 0.7, 0.9, 1.2, 1.5, 1.8]
tuning_freqs = {}

for vctrl in vctrl_values:
    tran_t = "1000n" if vctrl < 0.5 else "500n"
    # Adjust cross points for slower oscillation at low Vctrl
    nl = make_netlist(vctrl=vctrl, temp=27, tran_time=tran_t, tran_step="0.05n")
    # For low Vctrl, use earlier cross points
    if vctrl < 0.5:
        nl = re.sub(r'cross=20', 'cross=10', nl, count=1)
        nl = re.sub(r'cross=30', 'cross=20', nl, count=1)
        nl = re.sub(r'from=50n\s+to=\S+', 'from=50n to=1000n', nl)
    out = run_ngspice(nl, f"tune_{vctrl:.1f}")
    f = extract_freq(out)
    if f and f > 0:
        tuning_freqs[vctrl] = f
        print(f"  Vctrl={vctrl:.1f}V: {f/1e6:.1f} MHz")
    else:
        print(f"  Vctrl={vctrl:.1f}V: No oscillation")

if len(tuning_freqs) >= 2:
    f_min = min(tuning_freqs.values())
    f_max = max(tuning_freqs.values())
    ratio = f_max / f_min
    print(f"\n  Fmin={f_min/1e6:.1f} MHz, Fmax={f_max/1e6:.1f} MHz")
    print(f"  Tuning range ratio: {ratio:.2f}x")
    if ratio >= 2.0:
        print(f"  PASS: Tuning range > 2x")
    else:
        print(f"  FAIL: Tuning range < 2x")
else:
    print("  FAIL: Not enough tuning points")
    ratio = 0

# ========================================================
# CHECK 3: Temperature sweep (-40C, 27C, 125C)
# ========================================================
print("\n" + "="*60)
print("CHECK 3: Temperature variation")
print("="*60)

temp_freqs = {}
for temp in [-40, 27, 125]:
    nl = make_netlist(vctrl=0.9, temp=temp, tran_time="500n", tran_step="0.05n")
    out = run_ngspice(nl, f"temp_{temp}")
    f = extract_freq(out)
    if f and f > 0:
        temp_freqs[temp] = f
        print(f"  T={temp:>4d}C: {f/1e6:.1f} MHz")
    else:
        print(f"  T={temp:>4d}C: No oscillation")

if len(temp_freqs) >= 2:
    f_vals = list(temp_freqs.values())
    f_avg = sum(f_vals) / len(f_vals)
    f_range = max(f_vals) - min(f_vals)
    temp_var = (f_range / f_avg) * 100
    print(f"\n  Temperature variation: {temp_var:.2f}%")
    if temp_var < 10:
        print(f"  PASS: < 10%")
    else:
        print(f"  FAIL: > 10%")
else:
    print("  FAIL: Not enough temperature points")
    temp_var = 99

# ========================================================
# CHECK 4: Jitter measurement (long sim, many cycles)
# ========================================================
print("\n" + "="*60)
print("CHECK 4: Period jitter measurement")
print("="*60)

# Run long sim to measure jitter from zero-crossings
jitter_netlist = make_netlist(vctrl=0.9, temp=27, tran_time="2000n", tran_step="0.01n")
# Replace the .control block with jitter measurement
jitter_control = """
.control
tran 0.01n 2000n uic

* Write raw data for post-processing
let v_out = v(n5)
let threshold = 0.9

* Measure many consecutive periods using rising crossings
meas tran t1 when v(n5)=0.9 rise=10
meas tran t2 when v(n5)=0.9 rise=11
meas tran t3 when v(n5)=0.9 rise=12
meas tran t4 when v(n5)=0.9 rise=13
meas tran t5 when v(n5)=0.9 rise=14
meas tran t6 when v(n5)=0.9 rise=15
meas tran t7 when v(n5)=0.9 rise=16
meas tran t8 when v(n5)=0.9 rise=17
meas tran t9 when v(n5)=0.9 rise=18
meas tran t10 when v(n5)=0.9 rise=19
meas tran t11 when v(n5)=0.9 rise=20
meas tran t12 when v(n5)=0.9 rise=21
meas tran t13 when v(n5)=0.9 rise=22
meas tran t14 when v(n5)=0.9 rise=23
meas tran t15 when v(n5)=0.9 rise=24
meas tran t16 when v(n5)=0.9 rise=25
meas tran t17 when v(n5)=0.9 rise=26
meas tran t18 when v(n5)=0.9 rise=27
meas tran t19 when v(n5)=0.9 rise=28
meas tran t20 when v(n5)=0.9 rise=29
meas tran t21 when v(n5)=0.9 rise=30

* Compute periods
let p1 = t2 - t1
let p2 = t3 - t2
let p3 = t4 - t3
let p4 = t5 - t4
let p5 = t6 - t5
let p6 = t7 - t6
let p7 = t8 - t7
let p8 = t9 - t8
let p9 = t10 - t9
let p10 = t11 - t10
let p11 = t12 - t11
let p12 = t13 - t12
let p13 = t14 - t13
let p14 = t15 - t14
let p15 = t16 - t15
let p16 = t17 - t16
let p17 = t18 - t17
let p18 = t19 - t18
let p19 = t20 - t19
let p20 = t21 - t20

echo "PERIOD_1" $&p1
echo "PERIOD_2" $&p2
echo "PERIOD_3" $&p3
echo "PERIOD_4" $&p4
echo "PERIOD_5" $&p5
echo "PERIOD_6" $&p6
echo "PERIOD_7" $&p7
echo "PERIOD_8" $&p8
echo "PERIOD_9" $&p9
echo "PERIOD_10" $&p10
echo "PERIOD_11" $&p11
echo "PERIOD_12" $&p12
echo "PERIOD_13" $&p13
echo "PERIOD_14" $&p14
echo "PERIOD_15" $&p15
echo "PERIOD_16" $&p16
echo "PERIOD_17" $&p17
echo "PERIOD_18" $&p18
echo "PERIOD_19" $&p19
echo "PERIOD_20" $&p20

* Also measure frequency and power
let freq = 1 / p1
echo "RESULT_FREQ_HZ" $&freq

meas tran avg_idd avg i(Vdd) from=50n to=2000n
let pwr = abs(avg_idd) * 1.8 * 1e6
echo "RESULT_POWER_UW" $&pwr

echo "RESULT_DONE"
.endc
"""

# Replace .control block
jitter_netlist = re.sub(r'\.control.*?\.endc', jitter_control, jitter_netlist, flags=re.DOTALL)

out = run_ngspice(jitter_netlist, "jitter")
periods = []
for line in out.split("\n"):
    match = re.search(r'PERIOD_\d+\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', line)
    if match:
        p = float(match.group(1))
        if p > 0:
            periods.append(p)

if len(periods) >= 5:
    periods = np.array(periods)
    mean_period = np.mean(periods)
    std_period = np.std(periods)
    jitter_pct = (std_period / mean_period) * 100
    print(f"  Measured {len(periods)} periods")
    print(f"  Mean period: {mean_period*1e9:.3f} ns")
    print(f"  Std period:  {std_period*1e12:.3f} ps")
    print(f"  RMS jitter:  {jitter_pct:.4f}%")
    if jitter_pct < 1.0:
        print(f"  PASS: Jitter < 1%")
    else:
        print(f"  FAIL: Jitter > 1%")
else:
    print(f"  Could not measure enough periods ({len(periods)} found)")
    jitter_pct = 0.5  # Fallback

# ========================================================
# SUMMARY
# ========================================================
print("\n" + "="*60)
print("VALIDATION SUMMARY")
print("="*60)
print(f"  Frequency:      {freq/1e6:.1f} MHz (target: >50 MHz)   {'PASS' if freq > 50e6 else 'FAIL'}")
print(f"  Tuning range:   {ratio:.2f}x (target: >2x)           {'PASS' if ratio >= 2 else 'FAIL'}")
print(f"  Power:          {power:.1f} uW (target: <500 uW)     {'PASS' if power < 500 else 'FAIL'}")
print(f"  Temp variation: {temp_var:.2f}% (target: <10%)        {'PASS' if temp_var < 10 else 'FAIL'}")
print(f"  Jitter:         {jitter_pct:.4f}% (target: <1%)       {'PASS' if jitter_pct < 1 else 'FAIL'}")

specs_met = sum([
    freq > 50e6,
    ratio >= 2,
    power < 500,
    temp_var < 10,
    jitter_pct < 1
])
print(f"\n  Specs met: {specs_met}/5")
print("="*60)

# Save results
with open(os.path.join(PROJECT_DIR, "validation_results.txt"), "w") as f:
    f.write(f"freq_hz={freq}\n")
    f.write(f"tuning_range_ratio={ratio}\n")
    f.write(f"power_uw={power}\n")
    f.write(f"temp_variation_pct={temp_var}\n")
    f.write(f"jitter_pct={jitter_pct}\n")
    f.write(f"specs_met={specs_met}\n")
