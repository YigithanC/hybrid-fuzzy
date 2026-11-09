"""Algorithm 3: InC-FLC with the single input SInC (paper Table 4)."""
from .base import MPPTController


class Controller(MPPTController):
    def update(self, v: float, i: float) -> float:
        raise NotImplementedError  # TODO
