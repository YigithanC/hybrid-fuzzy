# Baseline / Reproduction experiments

Goal: reproduce the paper's results with its proposed controller (SInC + CSI) and its comparison methods (P&O, InC, Alg. 3).

- [x] Plant validation: open-loop duty sweep, compared with paper Fig. 13 (`duty_sweep_fig13.py`)
- [x] MF design: grid over SInC / CSI / dD scales (`tune_membership.py`)
- [x] Fair baselines: P&O and InC step and period grid (`tune_conventional.py`)
- [x] Exp B1: Fig. 17 irradiance profile, compared with paper Table 6 (`reproduce_table6_table7.py`)
- [x] Exp B2: load steps at 1000 and 500 W/m², compared with paper Table 7 (same script)

Run each one with `python -m experiments.baseline.<script>` from the repo root.
