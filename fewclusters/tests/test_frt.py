"""Tests for the stratified randomization test and the placebo tuner."""

import inspect

import numpy as np
import pytest
from sklearn.linear_model import LinearRegression

from fewclusters import Design, StratifiedFRT, placebo_tune, residualize, simulate_plm
from fewclusters.frt import frt_pvalue, linear_coefficients, site_weights

SIZES = [10, 25, 40, 200, 400, 800]


def _data(seed=0, sizes=SIZES, **kw):
    return simulate_plm(q=len(sizes), n_j=sizes, known_propensity=True, tau_l=1.0, seed=seed, **kw)


# ------------------------------------------------------------------ design
def test_bernoulli_and_complete_draws():
    strata = np.repeat([0, 1, 2], [10, 20, 30])
    p = np.repeat([0.3, 0.5, 0.7], [10, 20, 30])
    rng = np.random.default_rng(0)
    dz = Design(strata, p=p)
    draws = dz.draw(rng, 4000)
    assert np.allclose(draws.mean(0), p, atol=0.04)
    dc = Design(strata, kind="complete", n_treated=np.array([3, 10, 21]))
    dr = dc.draw(rng, 50)
    for s, k in enumerate([3, 10, 21]):
        assert np.all(dr[:, strata == s].sum(1) == k)
    assert np.allclose(dc.p, np.repeat([0.3, 0.5, 0.7], [10, 20, 30]))
    with pytest.raises(ValueError):
        Design(strata, p=np.where(strata == 0, 1.0, 0.5))


# ------------------------------------------------------------------ statistic
def test_statistic_is_weighted_mean_of_site_estimates():
    rng = np.random.default_rng(1)
    strata = np.repeat([0, 1, 2], [15, 25, 60])
    p = np.full(100, 0.4)
    dz = Design(strata, p=p)
    e = rng.standard_normal(100)
    d = (rng.random(100) < p).astype(float)
    for rule in ("equal", "size", "invvar"):
        w = site_weights(e, dz, rule)
        assert w.sum() == pytest.approx(1.0) and np.all(w > 0)
        tau = np.array([np.sum((d - p)[strata == s] * e[strata == s]) / np.sum((p * (1 - p))[strata == s])
                        for s in range(3)])
        a = linear_coefficients(e, dz, rule)
        assert (d - p) @ a == pytest.approx(np.sum(w * tau))
    assert np.allclose(site_weights(e, dz, "size"), [0.15, 0.25, 0.60])


def test_two_dimensional_coefficients_match_rowwise():
    rng = np.random.default_rng(2)
    strata = np.repeat([0, 1], [20, 30])
    dz = Design(strata, p=np.full(50, 0.5))
    E = rng.standard_normal((4, 50))
    A = linear_coefficients(E, dz, "invvar")
    for b in range(4):
        assert np.allclose(A[b], linear_coefficients(E[b], dz, "invvar"))


# ------------------------------------------------------------------ exactness
def test_frt_is_exact_under_sharp_null_with_tiny_sites_and_skewed_errors():
    rej = []
    for r in range(400):
        d = simulate_plm(q=3, n_j=[8, 12, 30], known_propensity=True, error_dist="lognormal", seed=100 + r)
        frt = StratifiedFRT(adjustments=("site_mean",), weight_rules=("invvar",), tune=False,
                            fixed=("site_mean", "invvar"), B=199, random_state=r)
        rej.append(frt.test(d["y"], d["d"], d["X"], d["cluster"], d["m0"], lam=d["theta"]).p_value <= 0.10)
    assert 0.06 <= np.mean(rej) <= 0.14          # exact 0.10; MC s.e. 0.015


# ------------------------------------------------------------------ tuner never sees D
def test_tuner_and_residualizer_take_no_treatment_argument():
    assert "d" not in inspect.signature(residualize).parameters
    assert "d" not in inspect.signature(placebo_tune).parameters


def test_choice_does_not_depend_on_real_treatment_given_null_outcome():
    data = _data(3)
    R = data["y"] - data["theta"] * data["d"]          # null-adjusted outcome at the true effect
    rng = np.random.default_rng(9)
    d_other = (rng.random(R.size) < data["m0"]).astype(float)
    frt = StratifiedFRT(LinearRegression(), B=99, B_tune=40, B_null_tune=60, random_state=1)
    # same R, two different treatment vectors -> identical tuning
    r1 = frt.test(R + 0.0 * data["d"], data["d"], data["X"], data["cluster"], data["m0"], lam=0.0)
    r2 = frt.test(R + 0.0 * d_other, d_other, data["X"], data["cluster"], data["m0"], lam=0.0)
    assert r1.choice == r2.choice
    assert r1.tuning.table == r2.tuning.table


def test_tuned_test_runs_and_reports_all_configurations():
    data = _data(4)
    frt = StratifiedFRT(LinearRegression(), B=199, B_tune=50, B_null_tune=80, random_state=0)
    res = frt.test(data["y"], data["d"], data["X"], data["cluster"], data["m0"], lam=0.0)
    assert len(res.pvalues_all) == 15
    assert res.choice in res.pvalues_all and res.p_value == res.pvalues_all[res.choice]
    assert 0 < res.p_value <= 1
    assert res.tuning is not None and res.tuning.delta > 0
    assert abs(res.estimate - data["theta"]) < 0.5


def test_input_validation():
    data = _data(5)
    frt = StratifiedFRT(LinearRegression(), B=99, tune=False)
    with pytest.raises(ValueError):
        frt.test(data["y"], data["d"] * 2, data["X"], data["cluster"], data["m0"])
    with pytest.raises(ValueError):
        frt.test(data["y"], data["d"], data["X"], data["cluster"], np.ones_like(data["m0"]))
    with pytest.raises(ValueError):
        StratifiedFRT(learner=None)                       # default adjustments need a learner
