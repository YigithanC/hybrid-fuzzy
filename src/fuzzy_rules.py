"""Fuzzy rule bases transcribed from Melhaoui et al. (2025).

Sign convention (paper): SInC = I/V + dI/dV
  SInC < 0 -> operating point right of the MPP -> increase D (positive dD)
  SInC = 0 -> at the MPP                       -> keep D
  SInC > 0 -> left of the MPP                  -> decrease D (negative dD)
"""

SINC_LABELS = ["NB", "NM", "NS", "ZE", "PS", "PM", "PB"]   # 7 MFs
CSI_LABELS = ["NB", "NS", "ZE", "PS", "PB"]                # 5 MFs
OUT_LABELS = ["NB", "NM", "NS", "ZE", "PS", "PM", "PB"]    # dD, 7 MFs

# Table 4: Algorithm 3, single input SInC
RULES_ALG3: dict[str, str] = dict(zip(
    SINC_LABELS, ["PB", "PM", "PS", "ZE", "NS", "NM", "NM"]
))

# Table 5: proposed controller, RULES_PROPOSED[csi][sinc] -> dD
# Rows = CSI, columns = SInC (NB ... PB)
_T5 = {
    "NB": ["PB", "PM", "ZE", "ZE", "ZE", "NM", "NB"],
    "NS": ["PB", "PM", "PS", "ZE", "NS", "NM", "NB"],
    "ZE": ["PB", "PM", "PS", "ZE", "NM", "NB", "NB"],
    "PS": ["PB", "PM", "PS", "ZE", "NS", "NM", "NB"],
    "PB": ["PB", "PM", "ZE", "ZE", "ZE", "NM", "NB"],
}
RULES_PROPOSED: dict[str, dict[str, str]] = {
    csi: dict(zip(SINC_LABELS, row)) for csi, row in _T5.items()
}
