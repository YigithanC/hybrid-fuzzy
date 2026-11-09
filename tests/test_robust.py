import numpy as np
import pytest

from src.mppt.robust import RobustSIncEstimator, make_variant
from src.mppt.sinc import SIncEstimator


def test_robust_reduces_to_paper_estimator_when_disabled():
    rng = np.random.default_rng(0)
    v = 40 + np.cumsum(rng.normal(0, 0.3, 200))
    i = 5 - 0.05 * (v - 40) + rng.normal(0, 0.01, 200)
    a, b = SIncEstimator(), RobustSIncEstimator(alpha=1.0, delta_v=0.0, sinc_clip=None)
    for vk, ik in zip(v, i):
        assert a.update(vk, ik) == pytest.approx(b.update(vk, ik))


def test_dead_band_bounds_the_denominator():
    est = RobustSIncEstimator(alpha=1.0, delta_v=0.5, sinc_clip=None)
    est.update(40.0, 5.0)
    s1, _ = est.update(40.1, 4.0)      # |dV| < 0.5 -> no update, SInC stays 0
    assert s1 == 0.0
    s2, _ = est.update(40.6, 4.9)      # |dV| = 0.6 against the reference -> update
    assert s2 == pytest.approx(4.9 / 40.6 + (4.9 - 5.0) / 0.6)


def test_clipping():
    est = RobustSIncEstimator(alpha=1.0, delta_v=0.0, sinc_clip=1.5)
    est.update(40.0, 5.0)
    s, _ = est.update(40.01, 6.0)      # huge dI/dV (100 S)
    assert s == pytest.approx(1.5)


@pytest.mark.parametrize("name", ["prop+F", "prop+D", "prop+C", "prop+FD", "prop+FDC", "prop+FDC+gauss",
                                  "alg3+FDC", "po+F", "inc+F", "prop:alpha=0.5,delta=0.5"])
def test_variants_build_and_step(name):
    c = make_variant(name)
    d = c.update(40.0, 5.0)
    assert 0.0 < d < 1.0
