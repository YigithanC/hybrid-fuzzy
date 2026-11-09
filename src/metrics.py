"""Performance metrics (paper Eq. 12-14, PDF p. 15-16).

Eq. 12: efficiency = sum(P_pv) / sum(P_opt) * 100. Implemented exactly.
Eq. 13: RMSE = sqrt(mean((P_pv - P_opt)^2)). Implemented exactly.
Eq. 14: RMS% = sqrt(mean(P_pv^2)) / P_opt. With time-varying irradiance P_opt is
        not a single number, so here we divide by the RMS of P_opt. This is our
        interpretation; state it in the report.
Convergence time is not formally defined in the paper. We use the time after
each change until P_pv enters the +/-2 % band around P_opt and stays there
until the next change.
"""
from __future__ import annotations

import numpy as np


def mppt_efficiency(p_pv: np.ndarray, p_opt: np.ndarray) -> float:
    """Return the average MPPT efficiency in %, Eq. 12 (uniform sampling)."""
    return 100.0 * float(np.sum(p_pv) / np.sum(p_opt))


def rmse(p_pv: np.ndarray, p_opt: np.ndarray) -> float:
    """Return the RMS error between the actual and optimal power in W, Eq. 13."""
    return float(np.sqrt(np.mean((p_opt - p_pv) ** 2)))


def rms_percent(p_pv: np.ndarray, p_opt: np.ndarray) -> float:
    """Return the RMS of P_pv normalised by the RMS of P_opt in %, our reading of Eq. 14."""
    return 100.0 * float(np.sqrt(np.mean(p_pv ** 2)) / np.sqrt(np.mean(p_opt ** 2)))


def convergence_times(t, p_pv, p_opt, change_times, tol: float = 0.02) -> list[float]:
    """Return the settling time [s] after each change in change_times; inf if it never settles.

    Settled = |P_pv - P_opt| <= tol * P_opt from that moment until the next change (or the end).
    """
    t = np.asarray(t)
    bounds = list(change_times) + [t[-1] + 1e-12]
    out = []
    for t0, t1 in zip(bounds[:-1], bounds[1:]):
        m = (t >= t0) & (t < t1)
        if not m.any():
            continue
        inside = np.abs(p_pv[m] - p_opt[m]) <= tol * p_opt[m]
        if inside.all():
            out.append(0.0)
            continue
        if not inside[-1]:
            out.append(float("inf"))
            continue
        last_out = np.flatnonzero(~inside)[-1]
        out.append(float(t[m][last_out + 1] - t0))
    return out
