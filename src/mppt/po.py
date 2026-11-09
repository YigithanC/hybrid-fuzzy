"""Perturb & Observe with a fixed duty step: conventional baseline (paper Fig. 3).

The paper's rule: if dP/dV > 0 raise the PV voltage, otherwise lower it.
With a boost converter a higher PV voltage means a lower D, so
    dP/dV > 0 (left of the MPP)  -> D -= step
    dP/dV < 0 (right of the MPP) -> D += step
The paper drives a voltage reference through a PI loop (Fig. 4); we perturb D
directly. Neither the step size nor the period is given in the paper; both
are tuned for P&O and InC in experiments/baseline/tune_conventional.py.
Selection rule: the highest efficiency among the settings that settle in every
interval. For both P&O and InC this is step 0.005 at a 1 ms period
(results/tables/conventional_tuning_grid.csv).
"""
from __future__ import annotations

from .base import MPPTController

STEP = 0.005


class Controller(MPPTController):
    name = "P&O"

    def __init__(self, d_init: float = 0.1, step: float = STEP, eps_v: float = 1e-3, **kw):
        super().__init__(d_init, **kw)
        self.step, self.eps_v = step, eps_v
        self.direction = +1          # +1 = increase D
        self.v_prev: float | None = None
        self.p_prev: float | None = None

    def update(self, v: float, i: float) -> float:
        p = v * i
        if self.v_prev is not None:
            dv, dp = v - self.v_prev, p - self.p_prev
            if abs(dv) >= self.eps_v and dp != 0:
                self.direction = -1 if dp / dv > 0 else +1
        self.v_prev, self.p_prev = v, p
        self.d = self._clip(self.d + self.direction * self.step)
        return self.d
