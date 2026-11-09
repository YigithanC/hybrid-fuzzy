"""Incremental Conductance with a fixed duty step: conventional baseline (paper Fig. 5).

    dI/dV = -I/V  -> at the MPP, hold
    dI/dV > -I/V  -> left of the MPP  -> raise V -> decrease D
    dI/dV < -I/V  -> right of the MPP -> lower V -> increase D
"""
from __future__ import annotations

from .base import MPPTController
from .po import STEP


class Controller(MPPTController):
    name = "InC"

    def __init__(self, d_init: float = 0.1, step: float = STEP, tol: float = 0.005, eps_v: float = 1e-3, **kw):
        super().__init__(d_init, **kw)
        self.step, self.tol, self.eps_v = step, tol, eps_v
        self.v_prev: float | None = None
        self.i_prev: float | None = None

    def update(self, v: float, i: float) -> float:
        if self.v_prev is not None and v > 0.5:
            dv, di = v - self.v_prev, i - self.i_prev
            if abs(dv) < self.eps_v:
                if di > 0:            # irradiance went up -> MPP voltage higher -> decrease D
                    self.d -= self.step
                elif di < 0:
                    self.d += self.step
            else:
                s = i / v + di / dv   # = (dP/dV) / V
                if s > self.tol:
                    self.d -= self.step
                elif s < -self.tol:
                    self.d += self.step
        self.v_prev, self.i_prev = v, i
        self.d = self._clip(self.d)
        return self.d
