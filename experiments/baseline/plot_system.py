"""Descriptive figures for the report and slides: PV curves, membership functions,
fuzzy control surface and the system block diagram.

    python -m experiments.baseline.plot_system
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

from src import membership as M
from src.fuzzy_engine import LinguisticVariable
from src.mppt.flc_sinc_csi import build_fis
from src.pv_model import iv_curve, mpp

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "results" / "figures"


def pv_curves() -> None:
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    for g in (1000, 800, 600, 400, 200):
        v, i, p = iv_curve(g)
        vm, im, pm = mpp(g)
        ax[0].plot(v, i, label=f"{g} W/m²")
        ax[1].plot(v, p, label=f"{g} W/m²")
        ax[0].plot(vm, im, "ko", ms=4)
        ax[1].plot(vm, pm, "ko", ms=4)
    ax[0].set(xlabel="V (V)", ylabel="I (A)", title="I–V", xlim=(0, 50), ylim=(0, 6))
    ax[1].set(xlabel="V (V)", ylabel="P (W)", title="P–V (● = MPP)", xlim=(0, 50), ylim=(0, 225))
    for a in ax:
        a.grid(alpha=0.3)
    ax[1].legend(fontsize=8)
    fig.suptitle("SPR-210 single-diode model, 25 °C")
    fig.tight_layout()
    fig.savefig(FIG / "pv_curves.png", dpi=150)


def membership() -> None:
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.4))
    specs = [("SInC (S)", M.SINC_PEAKS, (-1.3, 1.3)), ("CSI (S)", M.CSI_PEAKS, (-0.12, 0.12)),
             ("ΔD", M.DD_PEAKS, M.DD_UNIVERSE)]
    for a, (name, peaks, rng) in zip(ax, specs):
        var = LinguisticVariable(peaks)
        x = np.linspace(*rng, 600)
        for lab in var.labels:
            a.plot(x, var.mf_curve(lab, x), label=lab)
        a.set(title=name, ylim=(-0.02, 1.08), xlim=rng)
        a.grid(alpha=0.3)
    ax[0].set_ylabel("μ")
    ax[2].legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(FIG / "fis_membership.png", dpi=150)


def surface() -> None:
    fis = build_fis()
    s = np.linspace(-1.0, 1.0, 61)
    c = np.linspace(-0.1, 0.1, 41)
    S, C = np.meshgrid(s, c)
    Z = np.vectorize(fis.infer)(S, C)
    fig = plt.figure(figsize=(6.5, 4.8))
    ax = fig.add_subplot(projection="3d")
    ax.plot_surface(S, C, Z, cmap="coolwarm", linewidth=0, antialiased=True)
    ax.set(xlabel="SInC (S)", ylabel="CSI (S)", zlabel="ΔD", title="Control surface of the SInC+CSI controller")
    ax.view_init(elev=25, azim=-130)
    fig.tight_layout()
    fig.savefig(FIG / "fis_surface.png", dpi=150)


def diagram() -> None:
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.set_xlim(0, 11); ax.set_ylim(0, 3.6); ax.axis("off")

    def box(x, y, w, h, text, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=fc, ec="k"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9)

    def arrow(x0, y0, x1, y1, text=None, dy=0.12):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12, color="k"))
        if text:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, text, ha="center", fontsize=8)

    box(0.2, 2.3, 1.8, 1.0, "PV panel\nSPR-210\n(G, T)", "#fff3c4")
    box(2.8, 2.3, 2.2, 1.0, "Boost converter\nL=12 mH, Ce=150 µF\nCo=250 µF", "#dbeafe")
    box(5.8, 2.3, 1.4, 1.0, "Load\nR = 50 Ω", "#e5e7eb")
    arrow(2.0, 2.8, 2.8, 2.8, "V, I")
    arrow(5.0, 2.8, 5.8, 2.8, "Vout")
    box(0.2, 0.3, 2.4, 1.0, "SInC = I/V + ΔI/ΔV\nCSI = ΔSInC\n(+ robust estimator)", "#dcfce7")
    box(3.3, 0.3, 2.4, 1.0, "Mamdani FIS\n35 rules (Table 5)\ncentroid → ΔD", "#fce7f3")
    box(6.4, 0.3, 1.8, 1.0, "D[k] = D[k−1] + ΔD\n0.05 ≤ D ≤ 0.95", "#ede9fe")
    arrow(1.1, 2.3, 1.1, 1.3, "sample every 1 ms", dy=0.0)
    arrow(2.6, 0.8, 3.3, 0.8)
    arrow(5.7, 0.8, 6.4, 0.8)
    ax.add_patch(FancyArrowPatch((8.2, 0.8), (8.8, 0.8), arrowstyle="-", color="k"))
    ax.add_patch(FancyArrowPatch((8.8, 0.8), (8.8, 1.9), arrowstyle="-", color="k"))
    ax.add_patch(FancyArrowPatch((8.8, 1.9), (3.9, 1.9), arrowstyle="-", color="k"))
    arrow(3.9, 1.9, 3.9, 2.3)
    ax.text(6.4, 2.0, "duty cycle D (PWM 10 kHz)", fontsize=8, ha="center")
    ax.text(9.1, 2.8, "Plant: averaged model,\nforward Euler, dt = 10 µs", fontsize=8, va="center")
    ax.text(9.1, 0.8, "MPPT controller\n(Python)", fontsize=8, va="center")
    fig.tight_layout()
    fig.savefig(FIG / "system_diagram.png", dpi=150)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    pv_curves()
    membership()
    surface()
    diagram()
    print("saved: pv_curves.png, fis_membership.png, fis_surface.png, system_diagram.png")


if __name__ == "__main__":
    main()
