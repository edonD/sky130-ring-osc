#!/usr/bin/env python3
"""Extended simulation for low Vctrl values with relaxed measurement."""

import subprocess
import os

PROJECT_DIR = "/home/ubuntu/sky130-ring-osc"
VAL_DIR = os.path.join(PROJECT_DIR, "validation")

PARAMS = {
    "Wp": 0.8453, "Lp": 0.4786,
    "Wn": 1.0032, "Ln": 1.3918,
    "Ws": 1.6835, "Ls": 0.9940,
}

def make_netlist_low(vctrl, sim_time, cross_start, cross_end, filename):
    netlist = f"""* SKY130 5-Stage Current-Starved Ring Oscillator - Low Vctrl
* Vctrl={vctrl}V

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

.control
tran 0.1n {sim_time}n uic

* Try to measure with fewer crossings
meas tran tcross_a when v(n5)=0.9 cross={cross_start}
meas tran tcross_b when v(n5)=0.9 cross={cross_end}
let ncross = {(cross_end - cross_start) / 2}
let period = (tcross_b - tcross_a) / ncross
let freq = 1 / period
echo "RESULT_FREQ_HZ" $&freq

* Also measure peak-to-peak to verify oscillation
meas tran vmax max v(n5) from=100n to={sim_time}n
meas tran vmin min v(n5) from=100n to={sim_time}n
echo "RESULT_VMAX" $&vmax
echo "RESULT_VMIN" $&vmin

echo "RESULT_DONE"
.endc

.end
"""
    path = os.path.join(VAL_DIR, filename)
    with open(path, "w") as f:
        f.write(netlist)
    return path


def run_sim(path):
    result = subprocess.run(
        ["ngspice", "-b", path],
        capture_output=True, text=True, timeout=600,
        cwd=PROJECT_DIR
    )
    output = result.stdout + result.stderr

    freq = None
    vmax = None
    vmin = None

    for line in output.split("\n"):
        if "RESULT_FREQ_HZ" in line:
            parts = line.split()
            for p in parts:
                try:
                    freq = float(p)
                except ValueError:
                    pass
        elif "RESULT_VMAX" in line:
            parts = line.split()
            for p in parts:
                try:
                    vmax = float(p)
                except ValueError:
                    pass
        elif "RESULT_VMIN" in line:
            parts = line.split()
            for p in parts:
                try:
                    vmin = float(p)
                except ValueError:
                    pass

    return freq, vmax, vmin, output


# Try progressively longer sims and fewer crossings
configs = [
    (0.3, 2000, 4, 10),   # 2us sim, cross 4-10
    (0.3, 5000, 4, 10),   # 5us sim
    (0.5, 1000, 4, 10),
    (0.5, 2000, 4, 10),
    (0.7, 500, 4, 10),
    (0.7, 1000, 6, 14),
]

for vctrl, sim_time, cs, ce in configs:
    print(f"\nVctrl={vctrl}V, sim_time={sim_time}ns, cross={cs}-{ce}")
    path = make_netlist_low(vctrl, sim_time, cs, ce, f"low_vctrl_{vctrl}_{sim_time}.cir")
    freq, vmax, vmin, output = run_sim(path)

    if freq:
        print(f"  Frequency: {freq/1e6:.2f} MHz")
        print(f"  Vmax={vmax:.3f}V, Vmin={vmin:.3f}V")
        # If we got a good result for this Vctrl, skip longer sims
    else:
        if vmax is not None and vmin is not None:
            swing = vmax - vmin
            print(f"  No freq measured. Vmax={vmax:.3f}V, Vmin={vmin:.3f}V, swing={swing:.3f}V")
            if swing < 0.5:
                print(f"  -> Circuit likely NOT oscillating at Vctrl={vctrl}V")
        else:
            print(f"  Measurement completely failed")
            # Check for "failed" in output
            if "failed" in output.lower():
                # Look for specific measurement failures
                for line in output.split("\n"):
                    if "failed" in line.lower():
                        print(f"    {line.strip()}")
