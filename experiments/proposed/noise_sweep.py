"""Extension experiment: robustness of the MPPT controllers to measurement noise.

Motivation: the paper's conclusion says that the SInC controller "remains
sensitive to measurement accuracy and division calculations" but it never
tests this. SInC uses dI/dV = (I[k]-I[k-1]) / (V[k]-V[k-1]); near the MPP
the voltage change per sample is only tens of mV, so small sensor noise on
V can flip the sign of SInC. CSI is a difference of SInC, so it amplifies
the noise further.

Noise model: zero-mean Gaussian noise added to every V and I sample that the
MPPT controller sees, with sigma = level * full scale (Voc = 47.8 V, Isc = 5.65 A).
The plant itself is noise-free. Each (algorithm, level) pair is repeated
over several random seeds.

    python -m experiments.proposed.noise_sweep              # all variants
    python -m experiments.proposed.noise_sweep --quick      # fewer seeds
"""
from __future__ import annotations

import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PANEL
from src.simulate import run, summarize

ROOT = Path(__file__).resolve().parents[2]
TAB = ROOT / "results" / "tables"
CHANGES = np.arange(0.0, 2.0, 0.2)

NOISE_LEVELS = (0.0, 0.001, 0.002, 0.005, 0.01)   # fraction of full scale


def make(variant: str):
    """Build a controller from its variant name (top level, so worker processes can use it)."""
    from src.mppt import CONTROLLERS
    from src.mppt.robust import make_variant
    if variant in CONTROLLERS:
        return CONTROLLERS[variant]()
    return make_variant(variant)


def one_run(args: tuple[str, float, int]) -> dict:
    variant, level, seed = args
    log = run(make(variant), noise_std=(level * PANEL.voc, level * PANEL.isc), seed=seed)
    s = summarize(log, CHANGES)
    chatter = float(np.mean([np.std(log["d"][(log["t"] > t0 + 0.15) & (log["t"] < t0 + 0.2)]) for t0 in CHANGES]))
    return {"variant": variant, "noise_pct_fs": 100 * level, "seed": seed, **s, "duty_chatter_std": chatter}


def sweep(variants: list[str], levels=NOISE_LEVELS, seeds=range(5)) -> pd.DataFrame:
    jobs = [(v, l, s) for v in variants for l in levels for s in (seeds if l > 0 else [0])]
    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) - 1)) as ex:
        rows = list(ex.map(one_run, jobs))
    return pd.DataFrame(rows)


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["variant", "noise_pct_fs"])
    out = g.agg(efficiency_mean=("efficiency_pct", "mean"), efficiency_std=("efficiency_pct", "std"),
                rmse_mean=("rmse_w", "mean"), rmse_std=("rmse_w", "std"),
                conv_avg_ms_mean=("conv_avg_ms", "mean"), conv_failed_mean=("conv_failed", "mean"),
                chatter_mean=("duty_chatter_std", "mean"), runs=("seed", "count")).reset_index()
    return out.fillna({"efficiency_std": 0.0, "rmse_std": 0.0})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=["po", "inc", "flc_sinc", "flc_sinc_csi"])
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--tag", default="baseline")
    args = ap.parse_args()
    TAB.mkdir(parents=True, exist_ok=True)
    df = sweep(args.variants, seeds=range(args.seeds))
    df.to_csv(TAB / f"noise_runs_{args.tag}.csv", index=False, float_format="%.4f")
    agg = aggregate(df)
    agg.to_csv(TAB / f"noise_summary_{args.tag}.csv", index=False, float_format="%.4f")
    print(agg.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
