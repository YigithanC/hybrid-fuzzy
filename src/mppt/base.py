from abc import ABC, abstractmethod


class MPPTController(ABC):
    ts: float | None = None   # MPPT sampling period [s]; None = simulator default (1 ms)

    def __init__(self, d_init: float = 0.1, d_min: float = 0.05, d_max: float = 0.95, ts: float | None = None):
        if ts is not None:
            self.ts = ts
        self.d = d_init
        self.d_min, self.d_max = d_min, d_max

    def _clip(self, d: float) -> float:
        return min(max(d, self.d_min), self.d_max)

    @abstractmethod
    def update(self, v: float, i: float) -> float:
        """Take a new measurement (V, I) and return the next duty cycle."""
