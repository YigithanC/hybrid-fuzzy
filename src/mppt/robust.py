"""Noise-robust SInC estimation: the project's extension.

Problem (measured in experiments/proposed/noise_sweep.py): the paper's
two-point estimate dI/dV = (I[k]-I[k-1]) / (V[k]-V[k-1]) divides by a voltage
step of only tens of mV near the MPP. Sensor noise of a few tenths of a percent
then flips the sign of SInC, and CSI (a difference of SInC) amplifies it again.

The robust estimator has three independent parts, each of which can be
switched off for the ablation study:

F  measurement filter: first-order EMA on V and I
       x_f[k] = x_f[k-1] + alpha * (x[k] - x_f[k-1])          (alpha = 1 -> off)
D  accumulated-difference dead band: the incremental conductance is computed
   against a reference sample (V_ref, I_ref) that only moves when the voltage
   has changed by at least delta_v:
       if |V[k] - V_ref| >= delta_v:
           dI/dV = (I[k] - I_ref) / (V[k] - V_ref);  V_ref, I_ref <- V[k], I[k]
       else: keep the previous SInC
   The denominator is therefore never smaller than delta_v, so the error of
   dI/dV from noise is bounded by about sqrt(2)*sigma_I/delta_v.   (delta_v = 0 -> paper's two-point estimate)
C  clipping: SInC is limited to +/- sinc_clip, so a single bad sample cannot
   create a huge CSI spike.                                       (None -> off)
"""
from __future__ import annotations

import math

from .base import MPPTController
from .sinc import SIncEstimator

# Defaults chosen in experiments/proposed/tune_robust.py (tuning seeds 100-102, separate from the report seeds 0-4)
ALPHA = 0.5
DELTA_V = 0.5      # V, about 2 sigma for 0.5 % FS voltage noise
SINC_CLIP = 1.5    # S, just outside the SInC range of the duty sweep (+/-1.33)


class RobustSIncEstimator(SIncEstimator):
    def __init__(self, alpha: float = ALPHA, delta_v: float = DELTA_V, sinc_clip: float | None = SINC_CLIP,
                 v_min: float = 0.5):
        super().__init__(eps_v=max(delta_v, 1e-3), v_min=v_min)
        self.alpha, self.delta_v, self.sinc_clip = alpha, delta_v, sinc_clip
        self.vf: float | None = None
        self.if_: float | None = None
        self.v_ref: float | None = None
        self.i_ref: float | None = None

    def update(self, v: float, i: float) -> tuple[float, float]:
        # F: measurement filter
        if self.vf is None:
            self.vf, self.if_ = v, i
        else:
            self.vf += self.alpha * (v - self.vf)
            self.if_ += self.alpha * (i - self.if_)
        v, i = self.vf, self.if_

        sinc_prev = self.sinc
        if self.v_ref is None:
            self.v_ref, self.i_ref = v, i
        elif v > self.v_min:
            dv = v - self.v_ref
            if abs(dv) >= self.eps_v:          # D: accumulated difference against the reference sample
                s = i / v + (i - self.i_ref) / dv
                if self.sinc_clip is not None:  # C: clipping
                    s = max(-self.sinc_clip, min(self.sinc_clip, s))
                self.sinc = s
                self.v_ref, self.i_ref = v, i
        self.csi = self.sinc - sinc_prev
        return self.sinc, self.csi


class FilteredController(MPPTController):
    """Wrap any controller with the same EMA measurement filter (part F), for a fair comparison."""

    def __init__(self, inner: MPPTController, alpha: float = ALPHA):
        self.inner, self.alpha = inner, alpha
        self.ts = inner.ts
        self.vf: float | None = None
        self.if_: float | None = None

    @property
    def d(self):
        return self.inner.d

    def update(self, v: float, i: float) -> float:
        if self.vf is None:
            self.vf, self.if_ = v, i
        else:
            self.vf += self.alpha * (v - self.vf)
            self.if_ += self.alpha * (i - self.if_)
        return self.inner.update(self.vf, self.if_)


def robust_proposed(alpha=ALPHA, delta_v=DELTA_V, sinc_clip=SINC_CLIP, shape="tri"):
    from .flc_sinc_csi import Controller, build_fis
    c = Controller(fis=build_fis(shape=shape))
    c.est = RobustSIncEstimator(alpha=alpha, delta_v=delta_v, sinc_clip=sinc_clip)
    return c


def robust_alg3(alpha=ALPHA, delta_v=DELTA_V, sinc_clip=SINC_CLIP):
    from .flc_sinc import Controller
    c = Controller()
    c.est = RobustSIncEstimator(alpha=alpha, delta_v=delta_v, sinc_clip=sinc_clip)
    return c


def make_variant(name: str) -> MPPTController:
    """Return a controller for the named variant (used by the experiment scripts).

    Ablation of the proposed controller ("prop" = paper's SInC+CSI FLC):
        prop+F, prop+D, prop+C, prop+FD, prop+FDC (= full robust), prop+FDC+gauss
    Fair baselines with the same measurement filter:
        po+F, inc+F, alg3+FDC
    Tuning grid entries: prop:alpha=..,delta=..
    """
    from . import inc, po
    if name.startswith("prop:"):
        kv = dict(p.split("=") for p in name[5:].split(","))
        return robust_proposed(alpha=float(kv.get("alpha", ALPHA)), delta_v=float(kv.get("delta", DELTA_V)))
    parts = {
        "prop+F": dict(alpha=ALPHA, delta_v=0.0, sinc_clip=None),
        "prop+D": dict(alpha=1.0, delta_v=DELTA_V, sinc_clip=None),
        "prop+C": dict(alpha=1.0, delta_v=0.0, sinc_clip=SINC_CLIP),
        "prop+FD": dict(alpha=ALPHA, delta_v=DELTA_V, sinc_clip=None),
        "prop+FDC": dict(alpha=ALPHA, delta_v=DELTA_V, sinc_clip=SINC_CLIP),
    }
    if name in parts:
        return robust_proposed(**parts[name])
    if name == "prop+FDC+gauss":
        return robust_proposed(shape="gauss")
    if name == "alg3+FDC":
        return robust_alg3()
    if name == "po+F":
        return FilteredController(po.Controller())
    if name == "inc+F":
        return FilteredController(inc.Controller())
    raise KeyError(name)


assert math.isfinite(DELTA_V)
