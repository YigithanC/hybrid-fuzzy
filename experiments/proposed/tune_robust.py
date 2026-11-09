"""Choose alpha (EMA) and delta_v (dead band) of the robust estimator.

To avoid tuning on the numbers we report, this grid uses seeds 100-102;
the reported noise sweep uses seeds 0-4. Score = mean efficiency over noise
levels 0, 0.2 %, 0.5 % and 1 % FS, so noise-free performance also counts.

    python -m experiments.proposed.tune_robust
"""
from __future__ import annotations

import itertools
from pathlib import Path

import pandas as pd

from experiments.proposed.noise_sweep import aggregate, sweep

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    variants = [f"prop:alpha={a},delta={d}" for a, d in itertools.product((1.0, 0.5, 0.3), (0.0, 0.2, 0.5, 1.0))]
    df = sweep(variants, levels=(0.0, 0.002, 0.005, 0.01), seeds=range(100, 103))
    agg = aggregate(df)
    score = agg.groupby("variant")["efficiency_mean"].mean().rename("score_mean_eff").reset_index()
    wide = agg.pivot(index="variant", columns="noise_pct_fs", values="efficiency_mean")
    wide.columns = [f"eff@{c:g}%" for c in wide.columns]
    out = score.merge(wide.reset_index(), on="variant").sort_values("score_mean_eff", ascending=False)
    out.to_csv(ROOT / "results" / "tables" / "robust_tuning_grid.csv", index=False, float_format="%.3f")
    print(out.to_string(index=False, float_format=lambda x: f"{x:.2f}"))


if __name__ == "__main__":
    main()
