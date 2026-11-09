"""Membership function definitions.

The paper gives only the labels (SInC: 7 MFs, CSI: 5 MFs, dD: 7 MFs), not the
numeric breakpoints. The input ranges below are read from Fig. 13 (PDF p. 13),
which shows SInC and CSI during the duty sweep `scenarios.duty_sweep`:

    G = 1000 W/m^2: SInC ~ [-1.2, +1.25], CSI ~ [-0.05, +0.04]
    G =  500 W/m^2: SInC ~ [-0.65, +1.05], CSI ~ [-0.04, +0.03]
    G =  200 W/m^2: SInC ~ [-0.05, +0.75], CSI ~ [-0.02, +0.015]

CSI is a per-sample difference, so its range depends on the sampling period.
Re-measure it with our own model and sampling period before tuning.
The breakpoints are still PLACEHOLDERS. Document the final values in the report as our own design choice.
"""
SINC_UNIVERSE = (-1.3, 1.3)    # from Fig. 13
CSI_UNIVERSE = (-0.05, 0.05)   # from Fig. 13; depends on the sampling period
DD_UNIVERSE = (-0.02, 0.02)    # placeholder: duty cycle step, not given in the paper
