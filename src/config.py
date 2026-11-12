"""System parameters taken from Melhaoui et al. (2025).

All converter values are from the PDF, p. 4 (Eq. 3-7 and the text after them).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PanelParams:
    """SunPower SPR-210 at STC (paper Table 1)."""
    voc: float = 47.8            # V
    isc: float = 5.65            # A
    vmp: float = 40.0            # V
    imp: float = 5.25            # A
    pmax: float = 210.0          # W
    k_voc: float = -0.2792e-2    # 1/degC  (-0.2792 %/degC)
    k_isc: float = 0.035894e-2   # 1/degC  (+0.035894 %/degC)
    n_cells: int = 72            # series cells; only the product n*Ns enters the model, and the fit compensates
    t_ref: float = 25.0          # degC
    g_ref: float = 1000.0        # W/m^2


@dataclass(frozen=True)
class ConverterParams:
    """Boost converter (paper section 'PV System description')."""
    f_sw: float = 10e3           # Hz, PWM frequency
    r_load: float = 50.0         # ohm
    d_opt_stc: float = 0.61      # optimal duty cycle at STC (R_opt = 7.62 ohm)
    L: float = 12e-3             # H, Eq. 4, sized for 4 % current ripple
    c_out: float = 250e-6        # F, Eq. 5, sized for 0.5 % voltage ripple
    c_in: float = 150e-6         # F, Eq. 7 gives 131.6 uF (xi = 0.7); the paper uses the standard value 150 uF
    d_min: float = 0.05
    d_max: float = 0.95


PANEL = PanelParams()
CONVERTER = ConverterParams()
# Simulation timing (plant step 10 us, MPPT period 1 ms) is defined in src/simulate.py.
