# Autonomous Circuit Design — Ring Oscillator

You are an autonomous analog circuit designer. Your goal: design a voltage-controlled ring oscillator that meets every specification in `specs.json` using the SKY130 foundry PDK.

You have Differential Evolution (DE) as your optimizer. You define topology and parameter ranges — DE finds optimal values. You NEVER set component values manually.

## Files

| File | Editable? | Purpose |
|------|-----------|---------|
| `design.cir` | YES | Parametric SPICE netlist |
| `parameters.csv` | YES | Parameter names, min, max for DE |
| `evaluate.py` | YES | Runs DE, measures, scores, plots |
| `specs.json` | **NO** | Target specifications |
| `program.md` | **NO** | These instructions |
| `de/engine.py` | **NO** | DE optimizer engine |
| `results.tsv` | YES | Experiment log — append after every run |

## Technology

- **PDK:** SkyWater SKY130 (130nm). Models: `.lib "sky130_models/sky130.lib.spice" tt`
- **Devices:** `sky130_fd_pr__nfet_01v8`, `sky130_fd_pr__pfet_01v8` (and LVT/HVT variants)
- **Instantiation:** `XM1 drain gate source bulk sky130_fd_pr__nfet_01v8 W=10u L=0.5u nf=1`
- **Supply:** 1.8V single supply. Nodes: `vdd` = 1.8V, `vss` = 0V
- **Units:** Always specify W and L with `u` suffix (micrometers). Capacitors with `p` or `f`.
- **ngspice settings:** `.spiceinit` must contain `set ngbehavior=hsa` and `set skywaterpdk`

## Design Freedom

You are free to explore any ring oscillator topology. Single-ended inverter chain, differential delay cells, current-starved inverters, interpolating VCO, multi-path ring oscillator — whatever you think will work. Experiment boldly.

The number of stages is your choice (odd number for single-ended, any number for differential). Frequency tuning can be via current starving, varactor loading, supply modulation, or any other technique.

The only constraints are physical reality:

1. **All values parametric.** Every W, L, resistor, capacitor, and bias current uses `{name}` in design.cir with a matching row in parameters.csv.
2. **Ranges must be physically real.** W: 0.5u–500u. L: 0.15u–10u. Bias currents: 1µA–5mA. Caps: 10fF–100pF. Resistors: 50Ω–500kΩ. Ranges must span at least 10× (one decade).
3. **No hardcoding to game the optimizer.** A range of [5.0, 5.001] is cheating. Every parameter must have real design freedom.
4. **No editing specs.json or model files.** You optimize the circuit to meet the specs, not the other way around.

## The Loop

### 1. Read current state
- `results.tsv` — what you've tried and how it scored
- `design.cir` + `parameters.csv` — current topology
- `specs.json` — what you're targeting

### 2. Design or modify the topology
Change whatever you think will improve performance. You can make small tweaks or try a completely different architecture. Your call.

### 3. Implement
- Edit `design.cir` with the new/modified circuit
- Update `parameters.csv` with ranges for all parameters
- Update `evaluate.py` if measurements need changes
- Verify every `{placeholder}` in design.cir has a parameters.csv entry

### 4. Commit topology
```bash
git add -A
git commit -m "topology: <what changed>"
git push
```
Commit ALL files so any commit can be cloned and understood standalone.

### 5. Run DE
```bash
python evaluate.py 2>&1 | tee run.log          # full run
python evaluate.py --quick 2>&1 | tee run.log   # quick sanity check
```

### 6. Validate — THIS IS MANDATORY

DE found numbers. Now prove they're real. **Do not skip any of these checks.**

#### a) Verify oscillation
Run a transient simulation long enough to see at least 20 full cycles. The circuit MUST oscillate — if the output is stuck at VDD, VSS, or mid-rail, it's not working. Measure frequency from zero-crossings in steady state (skip the first 5 cycles for startup).

#### b) Verify tuning range
Sweep the control voltage from 0V to 1.8V (or your defined control range). Measure oscillation frequency at multiple control voltages. The tuning range must meet spec. Frequency should vary monotonically with control voltage.

#### c) Sanity check against physics
- A 3-stage ring osc at 130nm should oscillate in the range of 0.1–5 GHz depending on sizing. If frequency is < 1 MHz, something is wrong (too much load or too little current).
- Power should scale roughly linearly with frequency. If power is very low but frequency is high, check that the simulation is actually oscillating and not just ringing.

#### d) Temperature check
Simulate at -40°C, 27°C, and 125°C. Frequency will shift — measure the variation. If variation is > 50%, the design is too temperature-sensitive.

**Only after all four checks pass do you log the result.**

### 7. Generate plots and log results

#### a) Functional plots — `plots/`
Generate these plots every iteration (overwrite previous):
- **`waveform.png`** — Steady-state output waveform (last 10 cycles). Annotate frequency and amplitude.
- **`freq_vs_vctrl.png`** — Oscillation frequency vs control voltage. Annotate tuning range ratio.
- **`spectrum.png`** — FFT of output waveform. Show fundamental and harmonics.
- **`freq_vs_temp.png`** — Frequency at -40°C, 27°C, 125°C. Annotate % variation.

Use a dark theme. Label axes with units. Annotate key measurements directly on each plot.

#### b) Progress plot — `plots/progress.png`
Regenerate from `results.tsv` after every run:
- X axis: iteration number
- Y axis: best score so far
- Mark topology changes with vertical dashed lines
- Mark the point where all specs were first met

#### c) Log to results.tsv
Append one line:
```
<commit_hash>	<score>	<topology>	<specs_met>/<total>	<notes>
```

#### d) Commit and push everything
```bash
git add -A
git commit -m "results: <score> — <summary>"
git push
```
Every commit must include ALL files — source, parameters, plots, logs, measurements.

### 8. Decide next step
- Specs not met → analyze what's failing, change topology or ranges
- DE didn't converge → widen ranges or try different architecture
- Specs met → keep improving margins, then check stopping condition

## Stopping Condition

Track a counter: `steps_without_improvement`. After each run:
- If the best score improved → reset counter to 0
- If it did not improve → increment counter

**Stop when BOTH conditions are true:**
1. All specifications in `specs.json` are met (verified by transient oscillation check)
2. `steps_without_improvement >= 50`

Until both conditions are met, keep iterating.

## Known Pitfalls

**Simulation must be long enough.** If the transient sim is too short, you won't see steady-state oscillation. Run at least 50× the expected period. A 100 MHz oscillator has a 10ns period — simulate for at least 500ns.

**Startup.** Ring oscillators need a perturbation to start. In simulation, numerical noise usually triggers it, but if the simulator converges to a DC operating point, add a small initial pulse or voltage kick on one node.

**Jitter measurement requires long simulation.** To measure period jitter accurately, you need many cycles (100+). This makes jitter the most expensive spec to evaluate — consider measuring it only when other specs are already close.

**Current-starved frequency limit.** When starving current to reduce frequency, transistors enter subthreshold. The model is less accurate there and the oscillator may stop. Make sure the minimum control voltage still produces oscillation.
