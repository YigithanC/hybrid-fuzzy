"""Proposed controller: InC-FLC with inputs SInC and CSI (paper Table 5). Main reproduction target."""
from .base import MPPTController


class Controller(MPPTController):
    def update(self, v: float, i: float) -> float:
        raise NotImplementedError  # TODO
