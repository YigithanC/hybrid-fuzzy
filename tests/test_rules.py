from src.fuzzy_rules import RULES_ALG3, RULES_PROPOSED, SINC_LABELS, CSI_LABELS


def test_rule_table_complete():
    assert set(RULES_PROPOSED) == set(CSI_LABELS)
    for row in RULES_PROPOSED.values():
        assert list(row) == SINC_LABELS


def test_paper_low_irradiance_rules():
    # Paper: "SInC is PS and CSI is ZE -> NM", "SInC is PM and CSI is ZE -> NB"
    assert RULES_PROPOSED["ZE"]["PS"] == "NM"
    assert RULES_PROPOSED["ZE"]["PM"] == "NB"


def test_irradiance_profile_matches_fig17():
    import numpy as np
    from src.scenarios import irradiance_steps, PAPER_IRRADIANCE_LEVELS
    t = np.arange(0, 2.0, 0.1)            # mid-slot and edge samples
    g = irradiance_steps(t)
    assert list(g[::2]) == list(PAPER_IRRADIANCE_LEVELS)
    assert list(g[1::2]) == list(PAPER_IRRADIANCE_LEVELS)


def test_sign_convention():
    assert RULES_ALG3["NB"] == "PB"   # far right of the MPP -> big increase of D
    assert RULES_ALG3["ZE"] == "ZE"
