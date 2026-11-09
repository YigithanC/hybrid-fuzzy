"""Single-diode PV model of the SunPower SPR-210 panel.

    I = Iph - I0 * (exp((V + I*Rs) / (n*Ns*Vth)) - 1) - (V + I*Rs) / Rsh

The paper gives the datasheet points (Table 1) but not Iph, I0, Rs, Rsh or n.
We fix the ideality factor n and solve the other four unknowns from four conditions:
  I(0) = Isc,   I(Voc) = 0,   I(Vmp) = Imp,   dP/dV = 0 at (Vmp, Imp).
Irradiance scales Iph linearly. Temperature uses the coefficients from Table 1;
all paper experiments run at 25 degC.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy.optimize import fsolve, minimize_scalar

from .config import PANEL, PanelParams

K_B = 1.380649e-23   # J/K
Q_E = 1.602176634e-19  # C


@dataclass(frozen=True)
class DiodeParams:
    iph: float   # A, photo current at STC
    i0: float    # A, diode saturation current at STC
    rs: float    # ohm, series resistance
    rsh: float   # ohm, shunt resistance
    n: float     # ideality factor
    vt: float    # V, n * Ns * k*T/q at STC


@lru_cache(maxsize=None)
def fit_parameters(n: float = 1.0, p: PanelParams = PANEL) -> DiodeParams:
    """Solve Iph, I0, Rs and Rsh for the given ideality factor n."""
    vt = n * p.n_cells * K_B * (p.t_ref + 273.15) / Q_E

    def residuals(x):
        iph, log_i0, rs, rsh = x
        i0 = math.exp(log_i0)
        # I(0) = Isc
        r1 = iph - i0 * math.expm1(p.isc * rs / vt) - p.isc * rs / rsh - p.isc
        # I(Voc) = 0
        r2 = iph - i0 * math.expm1(p.voc / vt) - p.voc / rsh
        # I(Vmp) = Imp
        vd = p.vmp + p.imp * rs
        r3 = iph - i0 * math.expm1(vd / vt) - vd / rsh - p.imp
        # dP/dV = 0  <=>  dI/dV = -Imp/Vmp
        g = i0 / vt * math.exp(vd / vt) + 1.0 / rsh
        didv = -g / (1.0 + rs * g)
        r4 = didv + p.imp / p.vmp
        return [r1, r2, r3, r4]

    i0_guess = p.isc / math.expm1(p.voc / vt)
    x0 = [p.isc, math.log(i0_guess), 0.3, 300.0]
    sol, info, ok, msg = fsolve(residuals, x0, full_output=True, xtol=1e-12)
    iph, log_i0, rs, rsh = sol
    if ok != 1 or rs <= 0 or rsh <= 0:
        raise RuntimeError(f"PV parameter fit failed for n={n}: {msg} -> {sol}")
    return DiodeParams(iph=iph, i0=math.exp(log_i0), rs=rs, rsh=rsh, n=n, vt=vt)


DEFAULT_N = 1.0
"""Ideality factor. 1.0 gives physically valid Rs and Rsh for SPR-210; see tests/test_pv_model.py."""


def _conditions(g: float, t: float, p: PanelParams, d: DiodeParams) -> tuple[float, float, float]:
    """Return Iph, I0 and Vt at irradiance g and temperature t."""
    dt = t - p.t_ref
    vt = d.vt * (t + 273.15) / (p.t_ref + 273.15)
    isc_t = p.isc * (1 + p.k_isc * dt)
    voc_t = p.voc * (1 + p.k_voc * dt)
    iph = d.iph * (1 + p.k_isc * dt) * g / p.g_ref
    # I0 chosen so that Voc follows its temperature coefficient (common practice, e.g. Villalva 2009)
    i0 = d.i0 if dt == 0 else isc_t / math.expm1(voc_t / vt)
    return iph, i0, vt


def pv_current(v: float, g: float, t: float = 25.0, p: PanelParams = PANEL,
               i_guess: float | None = None) -> float:
    """Return the panel current [A] at voltage v [V], irradiance g [W/m^2] and temperature t [degC].

    The implicit equation is solved with Newton iterations, warm-started from i_guess.
    """
    d = fit_parameters(DEFAULT_N, p)
    iph, i0, vt = _conditions(g, t, p, d)
    i = iph if i_guess is None else i_guess
    for _ in range(50):
        e = math.exp(min((v + i * d.rs) / vt, 700.0))
        f = iph - i0 * (e - 1.0) - (v + i * d.rs) / d.rsh - i
        df = -i0 * e * d.rs / vt - d.rs / d.rsh - 1.0
        step = f / df
        i -= step
        if abs(step) < 1e-10:
            break
    return i


def iv_curve(g: float, t: float = 25.0, n_points: int = 300, p: PanelParams = PANEL):
    """Return arrays (v, i, p) from 0 to Voc."""
    v = np.linspace(0.0, p.voc * 1.02, n_points)
    i = np.empty_like(v)
    guess = None
    for k, vk in enumerate(v):
        guess = pv_current(vk, g, t, p, guess)
        i[k] = guess
    i = np.maximum(i, 0.0)
    return v, i, v * i


@lru_cache(maxsize=256)
def mpp(g: float, t: float = 25.0, p: PanelParams = PANEL) -> tuple[float, float, float]:
    """Return the true MPP (v_mp, i_mp, p_mp). Used as P_opt in the metrics."""
    res = minimize_scalar(lambda v: -v * pv_current(v, g, t, p), bounds=(0.0, p.voc), method="bounded",
                          options={"xatol": 1e-6})
    v = float(res.x)
    i = pv_current(v, g, t, p)
    return v, i, v * i
