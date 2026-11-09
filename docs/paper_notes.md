# Paper notes (Melhaoui et al., 2025)

Source: `references/s41598-025-03154-w.pdf` (25 pages; open access, CC BY 4.0).

## System
- Panel: SunPower SPR-210. Voc 47.8 V, Isc 5.65 A, Vmp 40 V, Imp 5.25 A, Pmax 210 W.
  Temperature coefficients: Voc −0.2792 %/°C, Isc +0.035894 %/°C.
- Boost converter, 10 kHz PWM, 50 Ω resistive load.
- At STC: R_opt = 7.62 Ω, D_opt = 0.61, Vout = 102 V, Iout = 2.04 A.
- L and C are sized for 4 % current ripple and 0.5 % voltage ripple, with 4.6 % overshoot (PDF p. 4):
  **L = 12 mH**, **Co = 250 µF**. Eq. 7 gives Ce = 131.6 µF (ξ = 0.7); the paper uses the standard value **Ce = 150 µF**.
- Tool: MATLAB/Simulink. The controller structure is MPPT → V_ref → PI → PWM, plus an inverter block.
- The fuzzy controller outputs ΔD directly; Eq. 9 is the discrete centroid: ΔD = Σ ΔDj·µ(ΔDj) / Σ µ(ΔDj).

## Proposed controller
- Inputs: SInC = I/V + dI/dV, and CSI = ΔSInC. Output: ΔD.
- Mamdani inference with centroid defuzzification.
- SInC has 7 MFs (NB…PB). CSI has 5 MFs (NB, NS, ZE, PS, PB). The rule base is Table 5, encoded in `src/fuzzy_rules.py`.
- **Numeric MF breakpoints are not given.** Input ranges read from Fig. 13 are listed in `src/membership.py` (SInC ≈ ±1.3, CSI ≈ ±0.05 at 1000 W/m²).

## Experiments
- Irradiance (Fig. 17, 2 s, 25 °C), one level per 0.2 s: 200, 600, 800, 400, 1000, 1000, 400, 800, 600, 200 W/m². Results are in Table 6.
- Load (Fig. 23): 50 → 20 Ω at t = 0.2 s, then 20 → 35 Ω at t = 0.4 s, at constant 500 and 1000 W/m². Results are in Table 7.
- Metrics (Eq. 12–14): efficiency = ΣPpv/ΣPopt; RMSE = sqrt(mean((Ppv−Popt)²)); RMS% = sqrt(mean(Ppv²))/Popt. Convergence time is not formally defined.

## Reported results (Table 6)
| Algo | Eff % | Conv. avg (min–max) ms | RMSE | RMS % |
|---|---|---|---|---|
| P&O | 95.41 | 65 (30–125) | 8.98 | 96.34 |
| InC | 95.6 | 60 (30–115) | 8.9 | 96.4 |
| Alg 1 | 97.5 | 56.6 (35–104) | 8.66 | 97.65 |
| Alg 2 | 96.82 | 70.87 (35–127) | 9.1 | 97.18 |
| Alg 3 | 96.6 | 76 (30–135) | 9 | 96.89 |
| Proposed | 97.7 | 53.5 (26–89) | 8.6 | 97.8 |

## Load test results (Table 7)
| G | Algo | RMSE | RMS % |
|---|---|---|---|
| 1000 | InC | 27.11 | 97.14 |
| 1000 | Alg 1 | 27.469 | 96.94 |
| 1000 | Proposed | 25.1514 | 97.92 |
| 500 | InC | 10.3091 | 96.57 |
| 500 | Alg 1 | 10.2597 | 97.35 |
| 500 | Proposed | 9.3007 | 97.88 |

## Limitations stated by the authors
- Sensitive to measurement precision and to the division in I/V.
- About 5 ms delay after sudden load changes.
- Simulation only. Partial shading is not studied.
