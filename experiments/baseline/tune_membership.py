"""Small grid search over the membership-function peaks of the proposed controller.

The paper does not publish its MF breakpoints and says they must be tuned.
This script documents how ours were chosen: a few scale factors around the
values read from Fig. 13 / our duty sweep, scored on the Fig. 17 irradiance profile.

    python -m experiments.baseline.tune_membership
"""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from src import membership as M
from src.mppt.flc_sinc_csi import Controller, build_fis
from src.simulate import run, summarize

ROOT = Path(__file__).resolve().parents[2]
CHANGES = np.arange(0.0, 2.0, 0.2)


def scaled(peaks: dict[str, float], pos: float = 1.0, neg: float = 1.0) -> dict[str, float]:
    return {k: v * (pos if v > 0 else neg) for k, v in peaks.items()}


def main() -> None:
    rows = []
    grid = itertools.product((1.0, 1.5, 2.0),    # SInC positive-side scale (left of the MPP)
                             (1.0, 2.0),         # CSI scale
                             (0.7, 1.0))         # dD scale (step size)
    for s_pos, c_scale, d_scale in grid:
        fis = build_fis(sinc_peaks=scaled(M.SINC_PEAKS, pos=s_pos),
                        csi_peaks=scaled(M.CSI_PEAKS, c_scale, c_scale),
                        dd_peaks=scaled(M.DD_PEAKS, d_scale, d_scale))
        log = run(Controller(fis=fis))
        s = summarize(log, CHANGES)
        # duty chatter in the last 50 ms of every interval (steady-state oscillation)
        chatter = np.mean([np.std(log["d"][(log["t"] > t0 + 0.15) & (log["t"] < t0 + 0.2)]) for t0 in CHANGES])
        rows.append({"sinc_pos_scale": s_pos, "csi_scale": c_scale, "dd_scale": d_scale,
                     **s, "duty_chatter_std": chatter})
        print(rows[-1])
    df = pd.DataFrame(rows).sort_values(["conv_failed", "efficiency_pct"], ascending=[True, False])
    out = ROOT / "results" / "tables" / "mf_tuning_grid.csv"
    df.to_csv(out, index=False, float_format="%.4f")
    print(df.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
