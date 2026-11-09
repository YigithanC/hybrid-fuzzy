"""Tune the fixed step and MPPT period of the conventional baselines (P&O, InC).

The paper does not report them. To keep the comparison fair we give the
baselines the best (step, period) pair on the same Fig. 17 profile that was
used to tune the fuzzy membership functions.

    python -m experiments.baseline.tune_conventional
"""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from src.mppt import inc, po
from src.simulate import run, summarize

ROOT = Path(__file__).resolve().parents[2]
CHANGES = np.arange(0.0, 2.0, 0.2)


def main() -> None:
    rows = []
    for (name, cls), ts, step in itertools.product((("po", po.Controller), ("inc", inc.Controller)),
                                                   (1e-3, 2e-3, 5e-3), (0.005, 0.01, 0.02)):
        s = summarize(run(cls(step=step, ts=ts)), CHANGES)
        rows.append({"algo": name, "ts_ms": ts * 1e3, "step": step, **s})
        print(rows[-1])
    df = pd.DataFrame(rows).sort_values(["algo", "efficiency_pct"], ascending=[True, False])
    df.to_csv(ROOT / "results" / "tables" / "conventional_tuning_grid.csv", index=False, float_format="%.4f")
    print(df.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
