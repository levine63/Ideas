"""Shrinkage of the pooling weight, the local-fit floor, and the small-cluster warning."""

import warnings

import numpy as np
import pytest
from sklearn.linear_model import LinearRegression

from fewclusters import ARTDML, SmallClusterWarning, simulate_plm
from fewclusters.pooling import ls_pooling_weight

SIZES = [10, 25, 40, 200, 400, 800]


def test_shrinkage_formula_and_limits():
    rng = np.random.default_rng(0)
    L = rng.standard_normal(8)
    P = L + rng.standard_normal(8)
    z = L + 0.2 * (P - L)
    raw = ls_pooling_weight(z, L, P)
    assert raw.w == raw.w_raw == pytest.approx(0.2)
    shr = ls_pooling_weight(z, L, P, shrink_kappa=20)
    assert shr.w_raw == pytest.approx(0.2)
    assert shr.w == pytest.approx((8 * 0.2 + 20) / 28)
    assert ls_pooling_weight(z, L, P, shrink_kappa=1e9).w == pytest.approx(1.0)
    with pytest.raises(ValueError):
        ls_pooling_weight(z, L, P, shrink_kappa=-1)


def test_shrinkage_never_increases_distance_to_one():
    rng = np.random.default_rng(1)
    for _ in range(50):
        L, P = rng.standard_normal(5), rng.standard_normal(5)
        z = rng.standard_normal(5)
        a = ls_pooling_weight(z, L, P)
        b = ls_pooling_weight(z, L, P, shrink_kappa=10)
        assert 0 <= a.w <= b.w <= 1


def _fit(**kw):
    d = simulate_plm(q=6, n_j=SIZES, known_propensity=True, tau_l=1.0, seed=3)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ARTDML(learner_l=LinearRegression(), n_folds=5, pooling_l="adaptive",
                      random_state=0, **kw).fit(d["y"], d["d"], d["X"], d["cluster"], m_known=d["m0"])


def test_default_shrinks_outcome_model_and_floor_skips_tiny_clusters():
    m = _fit()
    tab = {r["cluster"]: r for r in m.cluster_table()}
    # n = 10 and 25: base-training rows (~6 and ~15) < 20, local fit skipped, weight 1
    assert tab[0]["local_skipped"] and tab[0]["mean_w_l"] == 1.0
    assert tab[1]["local_skipped"]
    # large cluster: local fit used, shrinkage pulls the weight toward 1 but not all the way
    assert not tab[5]["local_skipped"]
    big = [dg for dg in m.result_.diagnostics_l if dg.cluster == 5]
    for dg in big:
        s = dg.n_calib
        assert dg.weight == pytest.approx((s * dg.weight_raw + 20) / (s + 20))


def test_shrinkage_and_floor_can_be_turned_off():
    m = _fit(shrink_l=0.0, min_local_train=0)
    for dg in m.result_.diagnostics_l:
        assert not dg.local_skipped and dg.weight == dg.weight_raw


def test_treatment_model_not_shrunk_by_default():
    d = simulate_plm(q=6, n_j=SIZES, seed=4)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = ARTDML(learner_m=LinearRegression(), learner_l=LinearRegression(), n_folds=5,
                   pooling_m="adaptive", pooling_l="adaptive", random_state=0
                   ).fit(d["y"], d["d"], d["X"], d["cluster"])
    for dg in m.result_.diagnostics_m:
        if not dg.local_skipped:
            assert dg.weight == dg.weight_raw


def test_small_cluster_warning():
    d = simulate_plm(q=6, n_j=SIZES, known_propensity=True, seed=5)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        m = ARTDML(learner_l=LinearRegression(), n_folds=5, pooling_l="local"
                   ).fit(d["y"], d["d"], d["X"], d["cluster"], m_known=d["m0"])
    assert any(issubclass(x.category, SmallClusterWarning) for x in w)
    assert "fewer than 50" in m.summary()
