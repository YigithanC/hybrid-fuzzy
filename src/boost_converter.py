"""Boost converter model.

Two options (decide in Checkpoint 2):
1. Averaged steady-state model: the panel sees R_in = R_load * (1 - D)^2.
   Fast and simple, but it has no transient dynamics.
2. Averaged state-space model with L, C_in and C_out (ODE). It captures the
   convergence-time behaviour that the paper reports. This is the recommended
   option for reproducing Table 6.
"""
from .config import CONVERTER, ConverterParams


def input_resistance(d: float, r_load: float, c: ConverterParams = CONVERTER) -> float:
    """Resistance the panel sees through an ideal boost converter in CCM."""
    return r_load * (1.0 - d) ** 2


def step(state, d: float, g: float, r_load: float, dt: float):
    """Advance the converter + PV state by dt. TODO: implement option 2."""
    raise NotImplementedError
