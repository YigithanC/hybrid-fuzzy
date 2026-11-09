"""PV panel model (single-diode), fitted to the SPR-210 datasheet values in config.

TODO (Checkpoint 2):
- Extract Rs, Rsh, I0 and the ideality factor from voc, isc, vmp and imp
  (e.g. the Villalva iterative method).
- Solve I(V) implicitly (Newton iterations or Lambert-W).
- Validate: Pmax at STC is about 210 W, and the curves look like the paper's Fig. 2.
"""
from .config import PANEL, PanelParams


def pv_current(v: float, g: float, t: float = 25.0, p: PanelParams = PANEL) -> float:
    """Return the panel current [A] at voltage v [V], irradiance g [W/m^2] and temperature t [degC]."""
    raise NotImplementedError


def mpp(g: float, t: float = 25.0, p: PanelParams = PANEL) -> tuple[float, float, float]:
    """Return the true MPP (v_mp, i_mp, p_mp). Used as the reference for the efficiency metrics."""
    raise NotImplementedError
