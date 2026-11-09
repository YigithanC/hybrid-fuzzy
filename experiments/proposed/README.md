# Proposed extension: noise-robust SInC estimation

**Hypothesis:** the two-point dI/dV used by SInC, together with CSI, makes the paper's controller fragile to sensor noise.
A filter plus an accumulated-difference dead band restores robustness at a small cost in the noise-free case.

**Success metric:** average MPPT efficiency (mean ± std over 5 seeds) at σ = 0, 0.1, 0.2, 0.5 and 1 % FS.

| Script | Purpose | Output |
|---|---|---|
| `noise_sweep.py --tag baseline` | Degradation of the paper controllers | `results/tables/noise_*_baseline.csv` |
| `tune_robust.py` | Choose α and δ_V on seeds 100–102 | `results/tables/robust_tuning_grid.csv` |
| `noise_sweep.py --tag extension --variants ...` | Ablation and fair baselines on seeds 0–4 | `results/tables/noise_*_extension.csv` |
| `plot_noise.py` | Figures and the summary table | `results/figures/noise_*.png`, `results/tables/noise_efficiency_table.csv` |

Variant names (see `src/mppt/robust.py`):

- `prop+F`, `prop+D`, `prop+C`, `prop+FD`, `prop+FDC`, `prop+FDC+gauss`: ablation of the robust estimator on the paper's controller
- `alg3+FDC`, `po+F`, `inc+F`: the same robustness tools given to the other controllers
