"""Averaged (state-space) model of the PV + boost converter + resistive load.

The paper uses a switched Simulink model at 10 kHz. We use the standard
averaged model over one switching period, which keeps the low-frequency
dynamics (L-Ce resonance, output RC) that set the MPPT convergence time but
drops the 10 kHz ripple. This is a documented simplification.

States:  v_pv (voltage of Ce),  i_L (inductor current),  v_out (voltage of Co)

    Ce * dv_pv/dt  = i_pv(v_pv, G) - i_L
    L  * di_L/dt   = v_pv - (1 - D) * v_out
    Co * dv_out/dt = (1 - D) * i_L - v_out / R

The diode blocks reverse inductor current, so i_L >= 0 (discontinuous mode is approximated by clamping).
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import CONVERTER, ConverterParams
from .pv_model import pv_current


def input_resistance(d: float, r_load: float) -> float:
    """Return the resistance the panel sees through an ideal boost converter in CCM: R*(1-D)^2."""
    return r_load * (1.0 - d) ** 2


def mpp_duty(r_mpp: float, r_load: float) -> float:
    """Return the ideal duty cycle at the MPP, paper Eq. 3: D = 1 - sqrt(Rmpp / R)."""
    return 1.0 - (r_mpp / r_load) ** 0.5


@dataclass
class PVBoostPlant:
    c: ConverterParams = CONVERTER
    v_pv: float = 0.0
    i_l: float = 0.0
    v_out: float = 0.0
    i_pv: float = 0.0

    def step(self, d: float, g: float, r_load: float, dt: float, t_cell: float = 25.0) -> None:
        """Advance the states by dt with forward Euler. dt <= 1e-5 s is stable for these parameters."""
        self.i_pv = max(pv_current(self.v_pv, g, t_cell, i_guess=self.i_pv), 0.0)
        dv_pv = (self.i_pv - self.i_l) / self.c.c_in
        di_l = (self.v_pv - (1.0 - d) * self.v_out) / self.c.L
        dv_out = ((1.0 - d) * self.i_l - self.v_out / r_load) / self.c.c_out
        self.v_pv = max(self.v_pv + dt * dv_pv, 0.0)
        self.i_l = max(self.i_l + dt * di_l, 0.0)
        self.v_out = max(self.v_out + dt * dv_out, 0.0)

    @property
    def p_pv(self) -> float:
        return self.v_pv * self.i_pv
