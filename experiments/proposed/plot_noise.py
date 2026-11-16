"""Figures and the summary table for the noise-robustness extension.

Needs results/tables/noise_runs_extension.csv (python -m experiments.proposed.noise_sweep --tag extension ...).

    python -m experiments.proposed.plot_noise
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiments.proposed.noise_sweep import make
from src.config import PANEL
from src.simulate import run

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "results" / "figures"
TAB = ROOT / "results" / "tables"

LABEL = {
    "po": "P&O", "po+F": "P&O + filter", "inc": "InC", "inc+F": "InC + filter",
    "flc_sinc": "Alg. 3 (paper)", "alg3+FDC": "Alg. 3 + robust est.",
    "flc_sinc_csi": "Proposed (paper)", "prop+F": "Proposed + F", "prop+D": "Proposed + D",
    "prop+C": "Proposed + C", "prop+FD": "Proposed + F + D", "prop+FDC": "Proposed + F + D + C (robust)",
    "prop+FDC+gauss": "Robust + Gaussian MF",
}
# Turkish names for the figures only (LABEL stays English: it is the key in the CSV tables the report reads).
LABEL_TR = {
    "po": "P&O", "po+F": "P&O + filtre", "inc": "InC", "inc+F": "InC + filtre",
    "flc_sinc": "Alg. 3 (makale)", "alg3+FDC": "Alg. 3 + dayanıklı kestirici",
    "flc_sinc_csi": "Önerilen (makale)", "prop+F": "Önerilen + F", "prop+D": "Önerilen + D",
    "prop+C": "Önerilen + C", "prop+FD": "Önerilen + F + D", "prop+FDC": "Önerilen + F + D + C (dayanıklı)",
    "prop+FDC+gauss": "Dayanıklı + Gauss ÜF",
}


def pct(x: float) -> str:
    """Turkish percent notation for figure labels: 0.5 -> '%0,5'."""
    return "%" + f"{x:g}".replace(".", ",")


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # Windows console (cp1254) cannot print the sigma sign
    runs = pd.read_csv(TAB / "noise_runs_extension.csv")
    agg = runs.groupby(["variant", "noise_pct_fs"]).agg(
        eff=("efficiency_pct", "mean"), eff_std=("efficiency_pct", "std"),
        rmse=("rmse_w", "mean"), rmse_std=("rmse_w", "std")).reset_index().fillna(0.0)

    # 1) efficiency vs noise: paper controllers vs robust versions
    fig, ax = plt.subplots(figsize=(8, 5))
    style = {"po": ("tab:gray", "--"), "inc": ("tab:brown", "--"), "flc_sinc": ("tab:blue", "--"),
             "flc_sinc_csi": ("tab:red", "--"), "alg3+FDC": ("tab:blue", "-"), "prop+FDC": ("tab:red", "-"),
             "po+F": ("tab:gray", "-"), "inc+F": ("tab:brown", "-")}
    for v, (c, ls) in style.items():
        d = agg[agg.variant == v]
        ax.errorbar(d.noise_pct_fs, d.eff, yerr=d.eff_std, color=c, ls=ls, marker="o", capsize=3, label=LABEL_TR[v])
    ax.set_xlabel("Ölçüm gürültüsü σ (tam ölçeğin yüzdesi: Voc, Isc)")
    ax.set_ylabel("Ortalama MPPT verimi (%)")
    ax.set_title("Gürültüye dayanıklılık (makale Şekil 17 profili, 5 tohum: ortalama ± std. sapma)")
    ax.set_ylim(30, 100)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIG / "noise_efficiency_vs_level.png", dpi=150)

    # 2) ablation bars
    abl = ["flc_sinc_csi", "prop+C", "prop+F", "prop+D", "prop+FD", "prop+FDC", "prop+FDC+gauss"]
    levels = [0.0, 0.5, 1.0]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    w = 0.25
    x = np.arange(len(abl))
    for k, lv in enumerate(levels):
        d = agg[agg.noise_pct_fs == lv].set_index("variant").loc[abl]
        ax.bar(x + (k - 1) * w, d.eff, w, yerr=d.eff_std, capsize=2, label=f"σ = {pct(lv)} tam ölçek")
    ax.set_xticks(x, [LABEL_TR[a] for a in abl], rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("Verim (%)")
    ax.set_ylim(40, 110)
    ax.set_yticks(range(40, 101, 10))
    ax.set_title("Dayanıklı SInC kestiricisinin ablasyonu (F: EMA filtresi, D: ölü bölge, C: kırpma)")
    ax.legend(loc="upper center", ncol=3, fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "noise_ablation.png", dpi=150)

    # 3) time series at 0.5 % FS noise, same seed
    lv = 0.005
    fig, ax = plt.subplots(2, 2, figsize=(13, 6), sharex=True)
    for col, v in enumerate(["flc_sinc_csi", "prop+FDC"]):
        lg = run(make(v), noise_std=(lv * PANEL.voc, lv * PANEL.isc), seed=0)
        ax[0, col].plot(lg["t"], lg["p_pv"], "k", lw=0.7, label="P_pv")
        ax[0, col].plot(lg["t"], lg["p_opt"], "r:", label="P_opt")
        ax[0, col].set_title(f"{LABEL_TR[v]}, σ = %0,5 tam ölçek")
        ax[1, col].plot(lg["t"], lg["d"], lw=0.7)
        ax[1, col].set_xlabel("Zaman (s)")
    ax[0, 0].set_ylabel("P (W)"); ax[1, 0].set_ylabel("D"); ax[0, 0].legend()
    fig.tight_layout()
    fig.savefig(FIG / "noise_timeseries_0p5pct.png", dpi=150)

    # summary table for the report: mean ± std
    keep = ["po", "po+F", "inc", "inc+F", "flc_sinc", "alg3+FDC", "flc_sinc_csi", "prop+C", "prop+F", "prop+D",
            "prop+FD", "prop+FDC", "prop+FDC+gauss"]
    t = agg[agg.variant.isin(keep)].copy()
    t["cell"] = t.eff.map("{:.2f}".format) + " ± " + t.eff_std.map("{:.2f}".format)
    table = t.pivot(index="variant", columns="noise_pct_fs", values="cell").loc[keep]
    table.columns = [f"σ={c:g}% FS" for c in table.columns]
    table.index = [LABEL[i] for i in table.index]
    table.to_csv(TAB / "noise_efficiency_table.csv")
    print(table.to_string())


if __name__ == "__main__":
    main()
