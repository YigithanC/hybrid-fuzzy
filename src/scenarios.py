"""Test scenarios read from the paper's figures (PDF p. 16, Fig. 17, and p. 21, Fig. 23)."""
import numpy as np

# Fig. 17: one level per 0.2 s slot, 25 degC, 2 s in total
PAPER_IRRADIANCE_LEVELS = (200, 600, 800, 400, 1000, 1000, 400, 800, 600, 200)


def irradiance_steps(t: np.ndarray, levels=PAPER_IRRADIANCE_LEVELS, step_s: float = 0.2) -> np.ndarray:
    """Return a step irradiance profile [W/m^2] that changes every step_s seconds (Fig. 17)."""
    # +1e-9 so a step edge such as t = 1.8 does not fall into the previous slot through float rounding
    idx = np.minimum(np.floor(np.asarray(t) / step_s + 1e-9).astype(int), len(levels) - 1)
    return np.asarray(levels, dtype=float)[idx]


def load_steps(t: np.ndarray, r_values=(50.0, 20.0, 35.0), t_switch=(0.2, 0.4)) -> np.ndarray:
    """Return a load-resistance profile [ohm]: 50 -> 20 ohm at 0.2 s, then 20 -> 35 ohm at 0.4 s (Fig. 23).

    The paper runs this test at constant G = 500 and 1000 W/m^2.
    """
    r = np.full_like(t, r_values[0], dtype=float)
    r[t >= t_switch[0]] = r_values[1]
    r[t >= t_switch[1]] = r_values[2]
    return r


def duty_sweep(t: np.ndarray) -> np.ndarray:
    """Return the open-loop duty profile of Fig. 7a / Fig. 11a: 0.1 until 0.2 s, ramp to 0.9 at 0.35 s, back to 0.1 at 0.5 s.

    Used to log the SInC/CSI ranges for membership-function design (cf. Fig. 13).
    """
    return np.interp(t, [0.0, 0.2, 0.35, 0.5], [0.1, 0.1, 0.9, 0.1])
