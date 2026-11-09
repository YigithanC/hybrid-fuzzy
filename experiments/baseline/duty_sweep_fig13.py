"""Reproduce paper Fig. 11b / Fig. 13: open-loop duty sweep 0.1 -> 0.9 -> 0.1.

Checks that the plant model behaves like the paper's and measures the SInC / CSI
ranges used to place the membership functions.

    python -m experiments.baseline.duty_sweep_fig13
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import scenarios
from src.mppt.sinc import SIncEstimator
from src.simulate import run, TS

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "results" / "figures"
TAB = ROOT / "results" / "tables"


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(3, 3, figsize=(13, 9), sharex=True)
    rows = []
    for col, g in enumerate((1000, 500, 200)):
        log = run(duty_fn=scenarios.duty_sweep, g_fn=lambda t, g=g: np.full_like(t, g), t_end=0.5)
        # resample at the MPPT period, as the controller would see it
        step = int(round(TS / (log["t"][1] - log["t"][0])))
        t, v, i = log["t"][::step], log["v_pv"][::step], log["i_pv"][::step]
        est = SIncEstimator()
        sinc, csi = np.array([est.update(vk, ik) for vk, ik in zip(v, i)]).T
        m = t >= 0.2
        rows.append({"G": g, "P_max_seen_W": log["p_pv"].max(), "P_opt_W": log["p_opt"][0],
                     "SInC_min": sinc[m].min(), "SInC_max": sinc[m].max(),
                     "CSI_min": csi[m].min(), "CSI_max": csi[m].max(),
                     "SInC_p05": np.percentile(sinc[m], 5), "SInC_p95": np.percentile(sinc[m], 95),
                     "CSI_p05": np.percentile(csi[m], 5), "CSI_p95": np.percentile(csi[m], 95)})
        ax[0, col].plot(log["t"], log["p_pv"], "k", label="P_pv")
        ax[0, col].axhline(log["p_opt"][0], color="r", ls=":", label="P_opt")
        ax[0, col].set_title(f"G = {g} W/m²")
        ax[1, col].plot(t[m], sinc[m], "k")
        ax[1, col].axhline(0, color="gray", lw=0.5)
        ax[2, col].plot(t[m], csi[m], "tab:blue")
        ax[2, col].set_xlabel("Time (s)")
    ax[0, 0].set_ylabel("P_pv (W)"); ax[1, 0].set_ylabel("SInC (S)"); ax[2, 0].set_ylabel("CSI (S)")
    ax[0, 0].legend()
    for a in ax[1:].ravel():
        a.set_xlim(0.2, 0.5)
    fig.suptitle("Open-loop duty sweep 0.1→0.9→0.1 (reproduction of paper Fig. 11b / Fig. 13)")
    fig.tight_layout()
    fig.savefig(FIG / "fig13_duty_sweep_sinc_csi.png", dpi=150)
    df = pd.DataFrame(rows)
    df.to_csv(TAB / "fig13_sinc_csi_ranges.csv", index=False, float_format="%.4f")
    print(df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))


if __name__ == "__main__":
    main()
