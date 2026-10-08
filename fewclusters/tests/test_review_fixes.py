"""
Regression tests for the issues raised in the October 2026 code audit:
classifier outputs, cluster-level treatment, input validation, the
calibration-fraction option, explicit folds, reproducibility, and the
dependent-score DGP.
"""

import warnings

import numpy as np
import pytest
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression

from fewclusters import ARTDML, FoldPlan, simulate_plm
from fewclusters.learners import fit_fresh
from fewclusters.model import IdentificationWarning
from fewclusters.simulate import lag1_autocorr, oracle_scores


def data6(seed=0, n=150):
    return simulate_plm(q=6, n_j=n, seed=seed)


# ------------------------------------------------------------- 1. classifiers
def test_classifier_nuisance_returns_probabilities_not_labels():
    d = data6()
    model = ARTDML(learner_m=LogisticRegression(), learner_l=LinearRegression(), n_folds=3,
                   pooling_m="local", pooling_l="local", random_state=0)
    model.fit(d["y"], d["d"], d["X"], d["cluster"])
    mhat = model.result_.mhat
    assert np.all((mhat > 0) & (mhat < 1))
    assert np.unique(np.round(mhat, 6)).size > 50          # not hard labels


def test_fitted_classifier_matches_predict_proba():
    rng = np.random.default_rng(0)
    X = rng.standard_normal((300, 2))
    z = (rng.random(300) < 0.4).astype(float)
    fitted = fit_fresh(LogisticRegression(), X, z)
    ref = LogisticRegression().fit(X, z.astype(int)).predict_proba(X)[:, 1]
    assert np.allclose(fitted.predict(X), ref)


def test_classifier_single_class_and_nonbinary_response():
    from fewclusters.learners import FittedNuisance

    class OneClass:                      # a classifier whose training data had only class 1
        classes_ = np.array([1])
        def predict_proba(self, X): return np.ones((len(X), 1))

    assert np.all(FittedNuisance(OneClass(), classifier=True).predict(np.zeros((4, 2))) == 1.0)
    with pytest.raises(ValueError):
        fit_fresh(LogisticRegression(), np.random.randn(10, 1), np.arange(10.0))


def test_adaptive_pooling_with_classifier_runs():
    d = data6(1)
    model = ARTDML(learner_m=LogisticRegression(), learner_l=LinearRegression(), n_folds=4,
                   pooling_m="adaptive", pooling_l="adaptive", random_state=0)
    model.fit(d["y"], d["d"], d["X"], d["cluster"])
    assert np.all((model.result_.mhat > 0) & (model.result_.mhat < 1))


# ------------------------------------------------------------- 2. identification
def test_cluster_level_treatment_is_rejected():
    rng = np.random.default_rng(0)
    q, n = 6, 100
    cl = np.repeat(np.arange(q), n)
    D = np.repeat(np.array([0, 1, 0, 1, 0, 1.0]), n)
    X = rng.standard_normal((q * n, 2))
    Y = D + X[:, 0] + rng.standard_normal(q * n)
    with pytest.raises(ValueError, match="constant within cluster"):
        ARTDML(learner_m=DummyRegressor(), learner_l=LinearRegression(), n_folds=3,
               pooling_m="pooled", pooling_l="local").fit(Y, D, X, cl)


def test_one_constant_cluster_is_rejected():
    d = data6()
    dd = d["d"].copy()
    dd[d["cluster"] == 2] = 1.0
    with pytest.raises(ValueError, match="cluster"):
        ARTDML(learner_m=LinearRegression(), learner_l=LinearRegression(), n_folds=3,
               pooling_m="local", pooling_l="local").fit(d["y"], dd, d["X"], d["cluster"])


def test_spurious_residual_variance_triggers_warning():
    # within-cluster treatment varies only a little; a pooled model that ignores
    # cluster differences leaves residual variance far above the raw within-cluster variance
    rng = np.random.default_rng(1)
    q, n = 6, 300
    cl = np.repeat(np.arange(q), n)
    base = np.repeat(np.array([0.05, 0.95, 0.05, 0.95, 0.05, 0.95]), n)
    D = (rng.random(q * n) < base).astype(float)
    X = rng.standard_normal((q * n, 2))
    Y = D + X[:, 0] + rng.standard_normal(q * n)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        model = ARTDML(learner_m=DummyRegressor(), learner_l=LinearRegression(), n_folds=3,
                       pooling_m="pooled", pooling_l="local").fit(Y, D, X, cl)
    assert any(issubclass(x.category, IdentificationWarning) for x in w)
    assert model.result_.warnings and "WARNING" in model.summary()


# ------------------------------------------------------------- 3. validation
@pytest.mark.parametrize("bad", ["nan_y", "inf_x", "m_out", "neg_weight"])
def test_invalid_inputs_raise(bad):
    d = data6()
    y, D, X, cl = d["y"].copy(), d["d"], d["X"].copy(), d["cluster"]
    kw = {}
    model_kw = dict(learner_l=LinearRegression(), n_folds=3, pooling_l="local")
    if bad == "nan_y":
        y[3] = np.nan
        model_kw["learner_m"] = LinearRegression(); model_kw["pooling_m"] = "local"
    elif bad == "inf_x":
        X[5, 0] = np.inf
        model_kw["learner_m"] = LinearRegression(); model_kw["pooling_m"] = "local"
    elif bad == "m_out":
        kw["m_known"] = np.where(np.arange(y.size) == 0, 1.0, 0.5)
    elif bad == "neg_weight":
        model_kw["learner_m"] = LinearRegression(); model_kw["pooling_m"] = "local"
        model_kw["weights"] = np.array([1, 1, 1, 1, 1, -1.0])
    with pytest.raises(ValueError):
        ARTDML(**model_kw).fit(y, D, X, cl, **kw)


def test_alpha_and_lambda_validated():
    d = data6()
    m = ARTDML(learner_m=LinearRegression(), learner_l=LinearRegression(), n_folds=3,
               pooling_m="local", pooling_l="local").fit(d["y"], d["d"], d["X"], d["cluster"])
    for bad in (0.0, 1.0, -0.1):
        with pytest.raises(ValueError):
            m.test(0.0, alpha=bad)
    with pytest.raises(ValueError):
        m.test(np.inf)


# ------------------------------------------------------------- 4. calibration fraction
def test_calib_fraction_allows_two_folds_and_has_requested_size():
    cl = np.repeat(np.arange(3), 100)
    plan = FoldPlan(cl, n_folds=2, use_calibration=True, calib_fraction=0.2, random_state=0)
    for r in plan.roles:
        assert r.calib_idx.size == 20
        assert set(r.calib_idx).isdisjoint(r.eval_idx) and set(r.calib_idx).isdisjoint(r.base_target_idx)
        assert r.calib_idx.size + r.base_target_idx.size + r.eval_idx.size == 100
    with pytest.raises(ValueError):
        FoldPlan(cl, n_folds=3, calib_fraction=0.2, contiguous=True)
    d = data6()
    m = ARTDML(learner_m=LinearRegression(), learner_l=LinearRegression(), n_folds=2,
               calib_fraction=0.2, random_state=0).fit(d["y"], d["d"], d["X"], d["cluster"])
    assert m.result_.diagnostics_l[0].n_calib == 30


# ------------------------------------------------------------- 5. folds and reproducibility
def test_explicit_folds_are_used():
    d = data6()
    folds = np.tile(np.arange(3), d["y"].size // 3)
    m = ARTDML(learner_m=LinearRegression(), learner_l=LinearRegression(), n_folds=3,
               pooling_m="local", pooling_l="local").fit(d["y"], d["d"], d["X"], d["cluster"], folds=folds)
    assert np.array_equal(m.result_.plan.fold_of_row, folds)


def test_same_seed_same_answer_different_seed_different_folds():
    d = data6()
    fit = lambda s: ARTDML(learner_m=LinearRegression(), learner_l=LinearRegression(), n_folds=4,
                           pooling_m="adaptive", pooling_l="adaptive", random_state=s
                           ).fit(d["y"], d["d"], d["X"], d["cluster"])
    a, b, c = fit(7), fit(7), fit(8)
    assert np.array_equal(a.result_.scores.a, b.result_.scores.a)
    assert not np.array_equal(a.result_.plan.fold_of_row, c.result_.plan.fold_of_row)


# ------------------------------------------------------------- 6. dependence DGP
def test_dependent_dgp_correlates_the_oracle_score_and_keeps_propensity_correct():
    d = simulate_plm(q=2, n_j=40000, dependence_R=3, dependence_share=0.9, seed=0)
    s = oracle_scores(d)
    assert lag1_autocorr(s, d["cluster"]) > 0.15
    assert abs(np.mean(d["d"] - d["m0"])) < 0.01
    iid = simulate_plm(q=2, n_j=40000, seed=0)
    assert abs(lag1_autocorr(oracle_scores(iid), iid["cluster"])) < 0.02
