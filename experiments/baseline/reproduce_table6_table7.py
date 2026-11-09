"""Reproduction experiments: paper Table 6 (irradiance steps, Fig. 17) and Table 7 (load steps, Fig. 23).

    python -m experiments.baseline.reproduce_table6_table7

Outputs:
    results/tables/table6_reproduction.csv
    results/tables/table7_reproduction.csv
    results/figures/table6_power_duty.png
    results/figures/table7_load_<G>.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import scenarios
from src.mppt import CONTROLLERS
from src.simulate import run, summarize

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "results" / "figures"
TAB = ROOT / "results" / "tables"

ALGOS = ["po", "inc", "flc_sinc", "flc_sinc_csi"]
LABELS = {"po": "P&O", "inc": "InC", "flc_sinc": "Alg. 3 (SInC)", "flc_sinc_csi": "Proposed (SInC+CSI)"}

PAPER_T6 = {  # efficiency %, conv avg ms, RMSE, RMS %
    "po": (95.41, 65.0, 8.98, 96.34), "inc": (95.6, 60.0, 8.9, 96.4),
    "flc_sinc": (96.6, 76.0, 9.0, 96.89), "flc_sinc_csi": (97.7, 53.5, 8.6, 97.8),
}
PAPER_T7 = {  # (G, algo): RMSE, RMS %
    (1000, "inc"): (27.11, 97.14), (1000, "flc_sinc_csi"): (25.1514, 97.92),
    (500, "inc"): (10.3091, 96.57), (500, "flc_sinc_csi"): (9.3007, 97.88),
}


def table6() -> pd.DataFrame:
    changes = np.arange(0.0, 2.0, 0.2)
    rows, logs = [], {}
    for a in ALGOS:
        logs[a] = run(CONTROLLERS[a]())
        s = summarize(logs[a], changes)
        p = PAPER_T6[a]
        rows.append({"algorithm": LABELS[a], **s,
                     "paper_efficiency_pct": p[0], "paper_conv_avg_ms": p[1], "paper_rmse_w": p[2], "paper_rms_pct": p[3]})
    fig, ax = plt.subplots(len(ALGOS), 2, figsize=(13, 2.4 * len(ALGOS)), sharex=True)
    for r, a in enumerate(ALGOS):
        lg = logs[a]
        ax[r, 0].plot(lg["t"], lg["p_pv"], "k", lw=0.8, label="P_pv")
        ax[r, 0].plot(lg["t"], lg["p_opt"], "r:", label="P_opt")
        ax[r, 0].set_ylabel(f"{LABELS[a]}\nP (W)")
        ax[r, 1].plot(lg["t"], lg["d"], lw=0.8)
        ax[r, 1].set_ylabel("D")
    ax[0, 0].legend(loc="upper left")
    ax[-1, 0].set_xlabel("Time (s)"); ax[-1, 1].set_xlabel("Time (s)")
    fig.suptitle("Fig. 17 irradiance profile, 25 °C: PV power and duty cycle (cf. paper Figs. 18–22)")
    fig.tight_layout()
    fig.savefig(FIG / "table6_power_duty.png", dpi=150)
    return pd.DataFrame(rows)


def table7() -> pd.DataFrame:
    rows = []
    for g in (1000, 500):
        fig, ax = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
        for a in ("inc", "flc_sinc_csi"):
            lg = run(CONTROLLERS[a](), g_fn=lambda t, g=g: np.full_like(t, float(g)), r_fn=scenarios.load_steps,
                     t_end=0.6)
            s = summarize(lg, [0.0, 0.2, 0.4])
            p = PAPER_T7[(g, a)]
            rows.append({"G": g, "algorithm": LABELS[a], **s, "paper_rmse_w": p[0], "paper_rms_pct": p[1]})
            ax[0].plot(lg["t"], lg["p_pv"], lw=0.8, label=LABELS[a])
            ax[1].plot(lg["t"], lg["d"], lw=0.8, label=LABELS[a])
        ax[0].plot(lg["t"], lg["p_opt"], "r:", label="P_opt")
        ax[0].set_ylabel("P (W)"); ax[1].set_ylabel("D"); ax[1].set_xlabel("Time (s)")
        ax[0].legend(); ax[0].set_title(f"Load steps 50→20→35 Ω at G = {g} W/m² (cf. paper Figs. 24–25)")
        fig.tight_layout()
        fig.savefig(FIG / f"table7_load_{g}.png", dpi=150)
    return pd.DataFrame(rows)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    t6 = table6()
    t6.to_csv(TAB / "table6_reproduction.csv", index=False, float_format="%.3f")
    print(t6.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    t7 = table7()
    t7.to_csv(TAB / "table7_reproduction.csv", index=False, float_format="%.3f")
    print(t7.to_string(index=False, float_format=lambda x: f"{x:.2f}"))


if __name__ == "__main__":
    main()
