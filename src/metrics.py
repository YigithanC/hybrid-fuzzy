"""Performance metrics (paper Eq. 12-14, PDF p. 15-16).

Eq. 12: efficiency = sum(P_pv) / sum(P_opt) * 100. Implemented exactly.
Eq. 13: RMSE = sqrt(mean((P_pv - P_opt)^2)). Implemented exactly.
Eq. 14: RMS% = sqrt(mean(P_pv^2)) / P_opt. With time-varying irradiance P_opt is
        not a single number, so here we divide by the RMS of P_opt. This is our
        interpretation; state it in the report.
Convergence time is not formally defined in the paper. We use a +/-2 % settling band.
"""
import numpy as np


def mppt_efficiency(p_pv: np.ndarray, p_mpp: np.ndarray, dt: float) -> float:
    """Return the average MPPT efficiency in % (integral of P_pv over integral of P_mpp)."""
    return 100.0 * float(np.sum(p_pv) * dt / (np.sum(p_mpp) * dt))


def rmse(p_pv: np.ndarray, p_mpp: np.ndarray) -> float:
    """Return the RMS error between the actual and optimal power, in W."""
    return float(np.sqrt(np.mean((p_mpp - p_pv) ** 2)))


def rms_percent(p_pv: np.ndarray, p_mpp: np.ndarray) -> float:
    """Return the RMS of P_pv normalised by the RMS of P_mpp, in %."""
    return 100.0 * float(np.sqrt(np.mean(p_pv ** 2)) / np.sqrt(np.mean(p_mpp ** 2)))


def convergence_times(t, p_pv, p_mpp, change_times, tol: float = 0.02) -> list[float]:
    """Return the time to enter and stay within +/-tol of P_mpp after each change. TODO."""
    raise NotImplementedError
