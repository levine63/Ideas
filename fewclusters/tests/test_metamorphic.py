"""
Metamorphic tests: transform the input in a way that should not change (or
should change in a known way) the answer, and check that it doesn't.

1. Relabel clusters with an order-preserving map      -> identical results
2. Relabel clusters with an order-CHANGING map, explicit folds
                                                       -> identical per-cluster results, same p and CI
3. Permute rows (carrying explicit folds along)        -> identical per-cluster scores
4. Permute the order of clusters in the ART core       -> identical p-value and CI
5. Rescale the outcome y -> c*y (linear learners)      -> theta_j -> c*theta_j, p(c*lam) = p(lam), CI scales
6. Duplicate the dataset's sign group input (a, b) -> (k a, k b)
                                                       -> identical p-values (scale invariance of the test)
"""

import numpy as np
import pytest
from sklearn.linear_model import LinearRegression

from fewclusters import ARTDML, simulate_plm
from fewclusters.art import art_confint, art_pvalue, sign_group


def _data(seed=0):
    return simulate_plm(q=6, n_j=120, tau_m=0.5, tau_l=0.5, seed=seed)


def _fit(y, d, X, cl, folds=None, seed=0, pooling="adaptive"):
    return ARTDML(learner_m=LinearRegression(), learner_l=LinearRegression(), n_folds=4,
                  pooling_m=pooling, pooling_l=pooling, random_state=seed).fit(y, d, X, cl, folds=folds)


def _folds(cl, K=4):
    f = np.empty(cl.size, dtype=int)
    for j in np.unique(cl):
        rows = np.flatnonzero(cl == j)
        f[rows] = np.arange(rows.size) % K
    return f


def test_order_preserving_relabel():
    d = _data()
    a = _fit(d["y"], d["d"], d["X"], d["cluster"])
    b = _fit(d["y"], d["d"], d["X"], 100 + 7 * d["cluster"])
    assert np.allclose(a.result_.scores.theta, b.result_.scores.theta)
    assert a.pvalue(1.0) == b.pvalue(1.0)


def test_order_changing_relabel_with_explicit_folds():
    d = _data(1)
    f = _folds(d["cluster"])
    perm = np.array([3, 5, 0, 1, 4, 2])
    a = _fit(d["y"], d["d"], d["X"], d["cluster"], folds=f)
    b = _fit(d["y"], d["d"], d["X"], perm[d["cluster"]], folds=f)
    # cluster j in a is cluster perm[j] in b; b's results are sorted by new label
    assert np.allclose(a.result_.scores.theta, b.result_.scores.theta[perm], atol=1e-10)
    assert a.pvalue(1.0) == b.pvalue(1.0)
    assert np.allclose(a.confint(0.1), b.confint(0.1))


def test_row_permutation_with_explicit_folds():
    d = _data(2)
    f = _folds(d["cluster"])
    rng = np.random.default_rng(0)
    p = rng.permutation(d["y"].size)
    a = _fit(d["y"], d["d"], d["X"], d["cluster"], folds=f, pooling="local")
    b = _fit(d["y"][p], d["d"][p], d["X"][p], d["cluster"][p], folds=f[p], pooling="local")
    assert np.allclose(a.result_.scores.theta, b.result_.scores.theta, atol=1e-9)
    assert np.allclose(a.result_.scores.Q, b.result_.scores.Q, atol=1e-12)


def test_art_core_invariant_to_cluster_order():
    rng = np.random.default_rng(3)
    a = rng.normal(5, 2, 8)
    b = np.sqrt(rng.integers(100, 900, 8).astype(float))
    signs, _ = sign_group(8)
    p = rng.permutation(8)
    for lam in (-1.0, 0.0, 0.3, 2.0):
        assert art_pvalue(a - b * lam, signs) == art_pvalue(a[p] - b[p] * lam, signs)
    assert np.allclose(art_confint(a, b, signs, 0.05), art_confint(a[p], b[p], signs, 0.05))


@pytest.mark.parametrize("c", [3.0, -2.0, 0.01])
def test_outcome_rescaling_is_equivariant(c):
    d = _data(4)
    f = _folds(d["cluster"])
    a = _fit(d["y"], d["d"], d["X"], d["cluster"], folds=f, pooling="local")
    b = _fit(c * d["y"], d["d"], d["X"], d["cluster"], folds=f, pooling="local")
    assert np.allclose(b.result_.scores.theta, c * a.result_.scores.theta, rtol=1e-8)
    for lam in (0.0, 0.7, 1.4):
        assert a.pvalue(lam) == b.pvalue(c * lam)
    lo, hi = a.confint(0.1)
    blo, bhi = b.confint(0.1)
    expected = sorted((c * lo, c * hi))
    assert blo == pytest.approx(expected[0], rel=1e-6) and bhi == pytest.approx(expected[1], rel=1e-6)


def test_art_core_scale_invariance():
    rng = np.random.default_rng(5)
    a, b = rng.normal(size=7), np.ones(7) * 3
    signs, _ = sign_group(7)
    for lam in (0.0, 0.5):
        assert art_pvalue(a - b * lam, signs) == art_pvalue(4 * (a - b * lam), signs)
