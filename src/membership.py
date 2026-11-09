"""Membership function design for the SInC / CSI fuzzy MPPT.

The paper gives only the labels (SInC: 7 MFs, CSI: 5 MFs, dD: 7 MFs), not the
numeric breakpoints. Each set is defined by its peak; neighbouring triangles
meet at the neighbours' peaks (a Ruspini partition, memberships sum to 1), and
the outermost sets are open shoulders.

Peaks are placed from our own duty sweep (results/tables/fig13_sinc_csi_ranges.csv),
which matches the paper's Fig. 13:
  - SInC is asymmetric: right of the MPP it falls to about -1.2 (at 1000 W/m^2);
    left of the MPP it stays at 0.1-0.3 over most of the curve and only shoots
    up near short circuit. So the positive sets are narrower.
  - CSI is mostly within +/-0.03 (5-95 % range) at the 1 ms MPPT period.
The dD peaks set the step sizes. Their values are our design choice (not in the paper).

Final values = initial guess x scale factors chosen by
experiments/baseline/tune_membership.py (results/tables/mf_tuning_grid.csv):
SInC positive side x1.5, CSI x2, dD x0.7. Initial guess:
  SInC  NB -0.8, NM -0.4, NS -0.12, ZE 0, PS 0.06, PM 0.25, PB 0.6
  CSI   NB -0.04, NS -0.01, ZE 0, PS 0.01, PB 0.04
  dD    +/-0.03, +/-0.012, +/-0.003, 0
With the initial guess the "SInC PS & CSI ZE -> NM" rule fired too close to the
MPP and caused duty chatter at high irradiance.
"""
from __future__ import annotations

SINC_PEAKS = {"NB": -0.8, "NM": -0.4, "NS": -0.12, "ZE": 0.0, "PS": 0.09, "PM": 0.375, "PB": 0.9}
CSI_PEAKS = {"NB": -0.08, "NS": -0.02, "ZE": 0.0, "PS": 0.02, "PB": 0.08}
DD_PEAKS = {"NB": -0.021, "NM": -0.0084, "NS": -0.0021, "ZE": 0.0, "PS": 0.0021, "PM": 0.0084, "PB": 0.021}

DD_UNIVERSE = (-0.04, 0.04)
DD_RESOLUTION = 801   # points used for the centroid integral
