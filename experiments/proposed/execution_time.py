"""Execution time of one MPPT decision (controller.update) for every controller.

    python -m experiments.proposed.execution_time

Each controller runs the paper's Fig. 17 profile (2 s, 1999 MPPT decisions) in
closed loop, without noise and with 1 % FS noise. Every call to update(v, i) is
timed with time.perf_counter_ns. For the SInC-based controllers the estimator
call (SInC/CSI computation) is timed separately, so the fuzzy-inference part is
the remainder. Only the controller is timed, not the plant simulation.

Numbers are pure-Python timings on the development PC. They are useful for
comparing controllers with each other, not as absolute times on a microcontroller.
Output: results/tables/execution_time.csv
"""
from __future__ import annotations

import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PANEL
from src.mppt import CONTROLLERS
from src.mppt.robust import make_variant
from src.simulate import run

OUT = Path(__file__).resolve().parents[2] / "results" / "tables" / "execution_time.csv"
ALGOS = ["po", "inc", "flc_sinc", "flc_sinc_csi", "alg3+FDC", "prop+FDC"]
NOISE_LEVELS = [0.0, 0.01]
SEEDS = [0, 1, 2, 3, 4]


def make(name: str):
    return CONTROLLERS[name]() if name in CONTROLLERS else make_variant(name)


def timed_run(name: str, level: float, seed: int) -> tuple[list[int], list[int]]:
    """Run one closed-loop simulation and return per-call times (ns) of update() and of the estimator."""
    ctrl = make(name)
    total, est_times = [], []
    if hasattr(ctrl, "est"):
        est_update = ctrl.est.update

        def est_wrapped(v, i):
            t0 = time.perf_counter_ns()
            out = est_update(v, i)
            est_times.append(time.perf_counter_ns() - t0)
            return out
        ctrl.est.update = est_wrapped
    update = ctrl.update

    def wrapped(v, i):
        t0 = time.perf_counter_ns()
        d = update(v, i)
        total.append(time.perf_counter_ns() - t0)
        return d
    ctrl.update = wrapped
    run(ctrl, t_end=2.0, noise_std=(level * PANEL.voc, level * PANEL.isc), seed=seed)
    return total, est_times


def main() -> None:
    rows = []
    for level in NOISE_LEVELS:
        for name in ALGOS:
            total, est = [], []
            for seed in SEEDS:
                t, e = timed_run(name, level, seed)
                total += t
                est += e
            us = np.array(total) / 1e3
            row = {"noise_pct_fs": level * 100, "algorithm": name, "calls": len(us),
                   "median_us": np.median(us), "mean_us": us.mean(), "p95_us": np.percentile(us, 95)}
            if est:
                e_us = np.array(est) / 1e3
                row["estimator_median_us"] = np.median(e_us)
                row["fis_median_us"] = row["median_us"] - row["estimator_median_us"]
            rows.append(row)
            print(f"noise {level * 100:.0f} %  {name:13s} median {row['median_us']:7.1f} us  "
                  f"p95 {row['p95_us']:7.1f} us" + (f"  (estimator {row['estimator_median_us']:.1f} us)" if est else ""))
    df = pd.DataFrame(rows)
    df.attrs["platform"] = f"{platform.processor()} / Python {platform.python_version()}"
    df.to_csv(OUT, index=False, float_format="%.2f")
    print(f"wrote {OUT}  [{df.attrs['platform']}]")


if __name__ == "__main__":
    main()
