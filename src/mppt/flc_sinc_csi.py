"""Proposed controller: InC-FLC with inputs SInC and CSI (paper Table 5, Fig. 16).

Each MPPT period:
    1. measure V, I
    2. SInC = I/V + dI/dV,  CSI = change of SInC
    3. dD = Mamdani FIS(SInC, CSI)  (Table 5 rules, centroid)
    4. D <- D + dD
"""
from __future__ import annotations

from .. import membership as M
from ..fuzzy_engine import LinguisticVariable, MamdaniFIS
from ..fuzzy_rules import RULES_PROPOSED
from .base import MPPTController
from .sinc import SIncEstimator


def build_fis(shape: str = "tri", sinc_peaks=None, csi_peaks=None, dd_peaks=None) -> MamdaniFIS:
    sinc = LinguisticVariable(sinc_peaks or M.SINC_PEAKS, shape)
    csi = LinguisticVariable(csi_peaks or M.CSI_PEAKS, shape)
    dd = LinguisticVariable(dd_peaks or M.DD_PEAKS, "tri")
    rules = {(s, c): out for c, row in RULES_PROPOSED.items() for s, out in row.items()}
    return MamdaniFIS([sinc, csi], dd, rules, M.DD_UNIVERSE, M.DD_RESOLUTION)


class Controller(MPPTController):
    name = "Proposed (SInC+CSI)"

    def __init__(self, d_init: float = 0.1, fis: MamdaniFIS | None = None, **kw):
        super().__init__(d_init, **kw)
        self.est = SIncEstimator()
        self.fis = fis or build_fis()

    def update(self, v: float, i: float) -> float:
        sinc, csi = self.est.update(v, i)
        self.d = self._clip(self.d + self.fis.infer(sinc, csi))
        return self.d
