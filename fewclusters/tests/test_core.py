"""Tests for art.py, folds.py, pooling.py, scores.py (no learners needed)."""

import numpy as np
import pytest

from fewclusters import (
    FoldPlan, art_confint, art_pvalue, art_test, attainable_size, cluster_scores, sign_group,
)
from fewclusters.art import art_statistics, ols_cluster_estimates
from fewclusters.pooling import ls_pooling_weight


# ----------------------------------------------------------------- sign group
def test_sign_group_exact_shape_and_identity():
    signs, exact = sign_group(6)
    assert exact and signs.shape == (64, 6)
    assert np.all(signs[0] == 1)
    assert len({tuple(r) for r in signs}) == 64


def test_sign_group_random_when_large():
    signs, exact = sign_group(25, max_exact=20, n_random=500, random_state=1)
    assert not exact and signs.shape == (500, 25) and np.all(signs[0] == 1)


# ----------------------------------------------------------------- p-values
def test_pvalue_against_brute_force():
    rng = np.random.default_rng(0)
    s = rng.standard_normal(7)
    signs, _ = sign_group(7)
    p = art_pvalue(s, signs)
    T0 = abs(s.mean())
    count = 0
    for g in signs:
        if abs(np.mean(g * s)) >= T0:
            count += 1
    assert p == count / 128


def test_pvalue_pairing_floor():
    """T(g) = T(-g), so the smallest p-value is 2 / 2^q."""
    s = np.array([3.0, 2.5, 2.0, 1.5, 1.0, 0.5])
    signs, _ = sign_group(6)
    assert art_pvalue(s, signs) == pytest.approx(2 / 64)


def test_never_rejects_with_five_clusters_at_five_percent():
    s = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
    signs, exact = sign_group(5)
    res = art_test(s, np.ones(5), 0.0, signs, exact, alpha=0.05)
    assert not res.reject and res.p_value == pytest.approx(2 / 32)
    assert attainable_size(5, 0.05) == 0.0
    assert attainable_size(6, 0.05) == pytest.approx(1 / 32)
    assert attainable_size(8, 0.05) == pytest.approx(6 / 128)


def test_statistic_weights():
    s = np.array([1.0, -2.0, 3.0])
    signs, _ = sign_group(3)
    w = np.array([0.5, 0.25, 0.25])
    T = art_statistics(s, signs, w)
    assert T[0] == pytest.approx(abs(0.5 - 0.5 + 0.75))


# ----------------------------------------------------------------- CI inversion
def test_confint_contains_center_and_is_symmetric_in_sign_flip():
    rng = np.random.default_rng(3)
    q = 8
    n = np.full(q, 400.0)
    theta_j = 1.0 + rng.standard_normal(q) * 0.2
    a, b = np.sqrt(n) * theta_j, np.sqrt(n)
    signs, _ = sign_group(q)
    lo, hi = art_confint(a, b, signs, alpha=0.05)
    center = a.sum() / b.sum()
    assert lo < center < hi
    # endpoints are accepted, slightly outside are rejected
    assert art_pvalue(a - b * lo, signs) > 0.05
    assert art_pvalue(a - b * hi, signs) > 0.05
    assert art_pvalue(a - b * (lo - 1e-3), signs) <= 0.05
    assert art_pvalue(a - b * (hi + 1e-3), signs) <= 0.05
    # flipping the sign of all estimates flips the interval
    lo2, hi2 = art_confint(-a, b, signs, alpha=0.05)
    assert lo2 == pytest.approx(-hi, abs=1e-6) and hi2 == pytest.approx(-lo, abs=1e-6)


def test_confint_infinite_when_cannot_reject():
    a, b = np.array([1.0, 2.0, 3.0, 4.0]), np.ones(4)
    signs, _ = sign_group(4)
    assert art_confint(a, b, signs, alpha=0.05) == (-np.inf, np.inf)


# ----------------------------------------------------------------- folds
def test_foldplan_roles_are_disjoint_and_cover_cluster():
    cluster = np.repeat(np.arange(4), 30)
    plan = FoldPlan(cluster, n_folds=5, use_calibration=True, random_state=0)
    assert plan.scored.all()
    for r in plan.roles:
        assert np.all(cluster[r.eval_idx] == r.cluster)
        assert np.all(cluster[r.calib_idx] == r.cluster)
        assert np.all(cluster[r.base_target_idx] == r.cluster)
        assert np.all(cluster[r.base_other_idx] != r.cluster)
        assert set(r.eval_idx).isdisjoint(r.calib_idx)
        assert set(r.eval_idx).isdisjoint(r.base_target_idx)
        assert set(r.calib_idx).isdisjoint(r.base_target_idx)
        # exclude_same_fold: other clusters' fold k is absent
        assert np.all(plan.fold_of_row[r.base_other_idx] != r.fold)
    # each row of each cluster is evaluated exactly once
    counts = np.zeros(cluster.size, dtype=int)
    for r in plan.roles:
        counts[r.eval_idx] += 1
    assert np.all(counts == 1)


def test_foldplan_buffer_removes_neighbours():
    cluster = np.repeat(np.arange(2), 100)
    plan = FoldPlan(cluster, n_folds=4, use_calibration=True, buffer=3, contiguous=True)
    r = [x for x in plan.roles if x.cluster == 0 and x.fold == 1][0]
    lo, hi = r.eval_idx.min(), r.eval_idx.max()
    forbidden = set(range(lo - 3, lo)) | set(range(hi + 1, hi + 4))
    assert forbidden.isdisjoint(r.calib_idx) and forbidden.isdisjoint(r.base_target_idx)
    assert plan.scored.all()      # rotating design: every row is scored in its own fold
    with pytest.raises(ValueError):
        FoldPlan(cluster, n_folds=4, buffer=2, contiguous=False)
    with pytest.raises(ValueError):
        FoldPlan(cluster, n_folds=2, use_calibration=True)


# ----------------------------------------------------------------- pooling
def test_pooling_weight_matches_closed_form_and_clips():
    rng = np.random.default_rng(1)
    L = rng.standard_normal(50)
    P = L + rng.standard_normal(50)
    z = L + 0.4 * (P - L) + 0.01 * rng.standard_normal(50)
    pw = ls_pooling_weight(z, L, P)
    d = P - L
    assert pw.w == pytest.approx(min(1, max(0, np.sum(d * (z - L)) / np.sum(d * d))))
    assert pw.w == pytest.approx(0.4, abs=0.05)
    assert ls_pooling_weight(L + 5 * d, L, P).w == 1.0
    assert ls_pooling_weight(L - 5 * d, L, P).w == 0.0
    assert ls_pooling_weight(z, L, L).w == 0.0        # zero denominator


# ----------------------------------------------------------------- scores
def test_cluster_scores_identity():
    rng = np.random.default_rng(2)
    cluster = np.repeat(np.arange(3), 40)
    vhat = rng.standard_normal(120)
    ytilde = 0.7 * vhat + rng.standard_normal(120)
    labels = np.array([10, 20, 30])
    sc = cluster_scores(vhat, ytilde, cluster, np.ones(120, bool), labels)
    for j in range(3):
        v, y = vhat[cluster == j], ytilde[cluster == j]
        assert sc.theta[j] == pytest.approx(np.sum(v * y) / np.sum(v * v))
        assert sc.Q[j] == pytest.approx(np.mean(v * v))
        lam = 0.3
        direct = np.sum(v * (y - lam * v)) / sc.Q[j] / np.sqrt(40)
        assert sc.S(lam)[j] == pytest.approx(direct)
    with pytest.raises(ValueError):
        cluster_scores(np.zeros(120), ytilde, cluster, np.ones(120, bool), labels)


def test_ols_cluster_estimates():
    rng = np.random.default_rng(4)
    cluster = np.repeat(np.arange(5), 60)
    X = rng.standard_normal((300, 2))
    y = 1 + 2 * X[:, 0] - X[:, 1] + 0.1 * rng.standard_normal(300)
    beta, n = ols_cluster_estimates(y, X, cluster, coef=0)
    assert np.allclose(beta, 2.0, atol=0.1) and np.all(n == 60)
