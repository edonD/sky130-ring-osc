#!/usr/bin/env python3
"""Validation script for 5-stage current-starved ring oscillator."""

import subprocess
import re
import os

PROJECT_DIR = "/home/ubuntu/sky130-ring-osc"
VAL_DIR = os.path.join(PROJECT_DIR, "validation")

# Best parameters
PARAMS = {
    "Wp": 0.8453, "Lp": 0.4786,
    "Wn": 1.0032, "Ln": 1.3918,
    "Ws": 1.6835, "Ls": 0.9940,
}

def make_netlist(vctrl, temp, sim_time, filename):
    """Generate a netlist with specific Vctrl, temperature, and sim time."""
    netlist = f"""* SKY130 5-Stage Current-Starved Ring Oscillator - Validation
* Vctrl={vctrl}V, Temp={temp}C

.lib "sky130_models/sky130.lib.spice" tt

* Supply
Vdd vdd 0 1.8
Vss vss 0 0

* Control voltage
Vctrl vctrl 0 {vctrl}

* === Stage 1 ===
XMp1 n1 n5 vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wp']}u L={PARAMS['Lp']}u nf=1
XMn1 n1 n5 sn1 vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wn']}u L={PARAMS['Ln']}u nf=1
XMsn1 sn1 vctrl vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Ws']}u L={PARAMS['Ls']}u nf=1

* === Stage 2 ===
XMp2 n2 n1 vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wp']}u L={PARAMS['Lp']}u nf=1
XMn2 n2 n1 sn2 vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wn']}u L={PARAMS['Ln']}u nf=1
XMsn2 sn2 vctrl vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Ws']}u L={PARAMS['Ls']}u nf=1

* === Stage 3 ===
XMp3 n3 n2 vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wp']}u L={PARAMS['Lp']}u nf=1
XMn3 n3 n2 sn3 vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wn']}u L={PARAMS['Ln']}u nf=1
XMsn3 sn3 vctrl vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Ws']}u L={PARAMS['Ls']}u nf=1

* === Stage 4 ===
XMp4 n4 n3 vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wp']}u L={PARAMS['Lp']}u nf=1
XMn4 n4 n3 sn4 vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wn']}u L={PARAMS['Ln']}u nf=1
XMsn4 sn4 vctrl vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Ws']}u L={PARAMS['Ls']}u nf=1

* === Stage 5 ===
XMp5 n5 n4 vdd vdd sky130_fd_pr__pfet_01v8 W={PARAMS['Wp']}u L={PARAMS['Lp']}u nf=1
XMn5 n5 n4 sn5 vss sky130_fd_pr__nfet_01v8 W={PARAMS['Wn']}u L={PARAMS['Ln']}u nf=1
XMsn5 sn5 vctrl vss vss sky130_fd_pr__nfet_01v8 W={PARAMS['Ws']}u L={PARAMS['Ls']}u nf=1

* Output buffer (fixed)
XMpout out n5 vdd vdd sky130_fd_pr__pfet_01v8 W=5u L=0.15u nf=1
XMnout out n5 vss vss sky130_fd_pr__nfet_01v8 W=2.5u L=0.15u nf=1

* Startup kick
Vkick kick 0 pulse(0 1.8 0 0.1n 0.1n 0.5n 1000n)
Ckick n1 kick 5f

.ic v(n1)=0 v(n2)=1.8 v(n3)=0 v(n4)=1.8 v(n5)=0

.options reltol=0.02 method=gear maxord=3
.temp {temp}

.control
tran 0.05n {sim_time}n uic

* Measure frequency using zero-crossings
meas tran tcross_a when v(n5)=0.9 cross=20
meas tran tcross_b when v(n5)=0.9 cross=30
let period = (tcross_b - tcross_a) / 5
let freq = 1 / period
echo "RESULT_FREQ_HZ" $&freq

* Power measurement
meas tran avg_idd avg i(Vdd) from=50n to={sim_time}n
let pwr = abs(avg_idd) * 1.8 * 1e6
echo "RESULT_POWER_UW" $&pwr

echo "RESULT_DONE"
.endc

.end
"""
    path = os.path.join(VAL_DIR, filename)
    with open(path, "w") as f:
        f.write(netlist)
    return path


def run_sim(path):
    """Run ngspice and extract results."""
    result = subprocess.run(
        ["ngspice", "-b", path],
        capture_output=True, text=True, timeout=300,
        cwd=PROJECT_DIR
    )
    output = result.stdout + result.stderr

    freq = None
    power = None

    for line in output.split("\n"):
        if "RESULT_FREQ_HZ" in line:
            parts = line.split()
            for p in parts:
                try:
                    freq = float(p)
                except ValueError:
                    pass
        elif "RESULT_POWER_UW" in line:
            parts = line.split()
            for p in parts:
                try:
                    power = float(p)
                except ValueError:
                    pass

    # Check for measurement failures
    if "failed" in output.lower() and freq is None:
        print(f"  WARNING: Measurement failed in {os.path.basename(path)}")
        # Try with more crossings at later time

    return freq, power, output


def main():
    print("=" * 70)
    print("RING OSCILLATOR VALIDATION")
    print("=" * 70)
    print(f"\nParameters:")
    for k, v in sorted(PARAMS.items()):
        print(f"  {k} = {v}")

    # ===== STEP 1: Nominal simulation =====
    print("\n" + "=" * 70)
    print("STEP 1: Nominal simulation (Vctrl=0.9V, T=27C)")
    print("=" * 70)

    path = make_netlist(0.9, 27, 200, "nominal.cir")
    freq, power, output = run_sim(path)

    if freq:
        print(f"  Frequency: {freq/1e6:.2f} MHz ({freq:.4e} Hz)")
        print(f"  Power:     {power:.2f} uW")
        print(f"  Oscillating: YES")
    else:
        print(f"  Oscillating: NO (measurement failed)")
        print(f"  Trying longer simulation...")
        path = make_netlist(0.9, 27, 500, "nominal_long.cir")
        freq, power, output = run_sim(path)
        if freq:
            print(f"  Frequency: {freq/1e6:.2f} MHz ({freq:.4e} Hz)")
            print(f"  Power:     {power:.2f} uW")
        else:
            print(f"  FAILED - circuit does not oscillate")

    nominal_freq = freq
    nominal_power = power

    # ===== STEP 2: Temperature sweep =====
    print("\n" + "=" * 70)
    print("STEP 2: Temperature sweep (Vctrl=0.9V)")
    print("=" * 70)

    temps = [-40, 27, 125]
    temp_freqs = {}

    for temp in temps:
        path = make_netlist(0.9, temp, 200, f"temp_{temp}.cir")
        freq, power, output = run_sim(path)

        if freq is None:
            # Try longer sim
            path = make_netlist(0.9, temp, 500, f"temp_{temp}_long.cir")
            freq, power, output = run_sim(path)

        temp_freqs[temp] = freq
        if freq:
            print(f"  T={temp:>4d}C: freq = {freq/1e6:.2f} MHz, power = {power:.2f} uW")
        else:
            print(f"  T={temp:>4d}C: FAILED (no oscillation)")

    # Calculate temp variation
    valid_freqs = [f for f in temp_freqs.values() if f is not None]
    if len(valid_freqs) >= 2:
        fmax = max(valid_freqs)
        fmin = min(valid_freqs)
        favg = sum(valid_freqs) / len(valid_freqs)
        temp_var = (fmax - fmin) / favg * 100
        print(f"\n  fmax = {fmax/1e6:.2f} MHz")
        print(f"  fmin = {fmin/1e6:.2f} MHz")
        print(f"  favg = {favg/1e6:.2f} MHz")
        print(f"  temp_variation_pct = {temp_var:.2f}%")
    else:
        temp_var = None
        print(f"\n  Cannot calculate temp variation (insufficient data)")

    # ===== STEP 3: Vctrl sweep =====
    print("\n" + "=" * 70)
    print("STEP 3: Vctrl sweep (T=27C)")
    print("=" * 70)

    vctrls = [0.3, 0.5, 0.7, 0.9, 1.2, 1.5, 1.8]
    vctrl_freqs = {}

    for vc in vctrls:
        # Use longer sim time for low Vctrl
        sim_time = 500 if vc < 0.5 else 200
        path = make_netlist(vc, 27, sim_time, f"vctrl_{vc:.1f}.cir")
        freq, power, output = run_sim(path)

        if freq is None and sim_time == 200:
            # Try longer
            path = make_netlist(vc, 27, 500, f"vctrl_{vc:.1f}_long.cir")
            freq, power, output = run_sim(path)

        vctrl_freqs[vc] = freq
        if freq:
            print(f"  Vctrl={vc:.1f}V: freq = {freq/1e6:.2f} MHz, power = {power:.2f} uW")
        else:
            print(f"  Vctrl={vc:.1f}V: NO OSCILLATION")

    # Calculate tuning range
    valid_vctrl_freqs = {k: v for k, v in vctrl_freqs.items() if v is not None}
    if len(valid_vctrl_freqs) >= 2:
        fmax = max(valid_vctrl_freqs.values())
        fmin = min(valid_vctrl_freqs.values())
        tuning_ratio = fmax / fmin
        fmax_vc = [k for k, v in valid_vctrl_freqs.items() if v == fmax][0]
        fmin_vc = [k for k, v in valid_vctrl_freqs.items() if v == fmin][0]
        print(f"\n  fmax = {fmax/1e6:.2f} MHz (at Vctrl={fmax_vc:.1f}V)")
        print(f"  fmin = {fmin/1e6:.2f} MHz (at Vctrl={fmin_vc:.1f}V)")
        print(f"  Tuning range ratio (fmax/fmin) = {tuning_ratio:.2f}x")
    else:
        tuning_ratio = None
        print(f"\n  Cannot calculate tuning range (insufficient data)")

    # ===== SUMMARY =====
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"  Nominal freq (0.9V, 27C):  {nominal_freq/1e6:.2f} MHz" if nominal_freq else "  Nominal freq: FAILED")
    print(f"  Nominal power:             {nominal_power:.2f} uW" if nominal_power else "  Nominal power: FAILED")
    print(f"  Temp variation:            {temp_var:.2f}%" if temp_var is not None else "  Temp variation: N/A")
    print(f"  Tuning range ratio:        {tuning_ratio:.2f}x" if tuning_ratio is not None else "  Tuning range: N/A")

    print(f"\n  Spec check:")
    if nominal_freq:
        print(f"    freq_hz > 50MHz:          {'PASS' if nominal_freq > 50e6 else 'FAIL'} ({nominal_freq/1e6:.1f} MHz)")
    if nominal_power:
        print(f"    power_uw < 500:            {'PASS' if nominal_power < 500 else 'FAIL'} ({nominal_power:.1f} uW)")
    if temp_var is not None:
        print(f"    temp_variation_pct < 10:   {'PASS' if temp_var < 10 else 'FAIL'} ({temp_var:.2f}%)")
    if tuning_ratio is not None:
        print(f"    tuning_range_ratio > 2:    {'PASS' if tuning_ratio > 2 else 'FAIL'} ({tuning_ratio:.2f}x)")


if __name__ == "__main__":
    main()
