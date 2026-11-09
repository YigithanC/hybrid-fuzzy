"""Discrete computation of the paper's fuzzy inputs from sampled V and I.

    SInC[k] = I[k]/V[k] + (I[k]-I[k-1]) / (V[k]-V[k-1])     (G + dG)
    CSI[k]  = SInC[k] - SInC[k-1]

The division by dV is the weak point that the paper itself mentions. When
|dV| < eps_v the incremental term is undefined; we then keep the previous SInC
(the operating point has not moved, so neither has its position relative to the MPP).
"""
from __future__ import annotations


class SIncEstimator:
    def __init__(self, eps_v: float = 1e-3, v_min: float = 0.5):
        self.eps_v = eps_v
        self.v_min = v_min
        self.v_prev: float | None = None
        self.i_prev: float | None = None
        self.sinc = 0.0
        self.csi = 0.0

    def update(self, v: float, i: float) -> tuple[float, float]:
        """Take a new sample (V, I) and return (SInC, CSI)."""
        sinc_prev = self.sinc
        if self.v_prev is not None and v > self.v_min:
            dv = v - self.v_prev
            if abs(dv) >= self.eps_v:
                self.sinc = i / v + (i - self.i_prev) / dv
        self.csi = self.sinc - sinc_prev
        self.v_prev, self.i_prev = v, i
        return self.sinc, self.csi
