"""Algorithm 3: InC-FLC with the single input SInC (paper Table 4)."""
from __future__ import annotations

from .. import membership as M
from ..fuzzy_engine import LinguisticVariable, MamdaniFIS
from ..fuzzy_rules import RULES_ALG3
from .base import MPPTController
from .sinc import SIncEstimator


def build_fis(shape: str = "tri") -> MamdaniFIS:
    sinc = LinguisticVariable(M.SINC_PEAKS, shape)
    dd = LinguisticVariable(M.DD_PEAKS, "tri")
    rules = {(s,): out for s, out in RULES_ALG3.items()}
    return MamdaniFIS([sinc], dd, rules, M.DD_UNIVERSE, M.DD_RESOLUTION)


class Controller(MPPTController):
    name = "Alg. 3 (SInC)"

    def __init__(self, d_init: float = 0.1, **kw):
        super().__init__(d_init, **kw)
        self.est = SIncEstimator()
        self.fis = build_fis()

    def update(self, v: float, i: float) -> float:
        sinc, _ = self.est.update(v, i)
        self.d = self._clip(self.d + self.fis.infer(sinc))
        return self.d
