import numpy as np
import pytest

from src import metrics
from src.boost_converter import mpp_duty
from src.mppt.flc_sinc_csi import build_fis
from src.pv_model import fit_parameters, mpp, pv_current


def test_pv_model_matches_datasheet():
    assert pv_current(0.0, 1000) == pytest.approx(5.65, abs=1e-6)
    assert pv_current(47.8, 1000) == pytest.approx(0.0, abs=1e-6)
    v, i, p = mpp(1000)
    assert p == pytest.approx(210.0, abs=0.01)
    assert v / i == pytest.approx(7.62, abs=0.01)   # paper: R_mpp = 7.62 ohm


def test_pv_parameters_physical():
    d = fit_parameters()
    assert d.rs > 0 and d.rsh > 0 and d.i0 > 0


def test_mpp_duty_matches_paper():
    v, i, _ = mpp(1000)
    assert mpp_duty(v / i, 50.0) == pytest.approx(0.61, abs=0.01)   # paper: D_mpp = 0.61


def test_fis_sign_and_symmetry():
    f = build_fis()
    assert f.infer(0.0, 0.0) == pytest.approx(0.0, abs=1e-9)   # at the MPP -> hold
    assert f.infer(-1.0, 0.0) > 0                              # right of the MPP -> increase D
    assert f.infer(1.0, 0.0) < 0                               # left of the MPP -> decrease D
    assert f.infer(-0.12, 1.0) == pytest.approx(0.0, abs=1e-9)  # SInC NS & CSI large -> hold (Table 5)


def test_metrics():
    p_opt = np.full(100, 200.0)
    assert metrics.mppt_efficiency(p_opt * 0.9, p_opt) == pytest.approx(90.0)
    assert metrics.rmse(p_opt - 10, p_opt) == pytest.approx(10.0)
    t = np.linspace(0, 1, 100, endpoint=False)
    p = np.where(t < 0.3, 100.0, 200.0)
    assert metrics.convergence_times(t, p, p_opt, [0.0])[0] == pytest.approx(0.3, abs=0.011)
