"""
art.py -- the approximate randomization test over the sign group.

This is the Canay-Romano-Shaikh (2017) test as implemented in weighted-score
form by Cai, Canay, Kim and Shaikh (2023). It is pure numpy and knows
nothing about nuisances or learners: it takes a vector of cluster scores
that is affine in the hypothesised value,

    S_j(lambda) = a_j - b_j * lambda,         j = 1..q,

and a weight vector omega (default 1/q). For a sign vector g in {-1,+1}^q,

    T(g; lambda) = | sum_j omega_j g_j S_j(lambda) |,

and the p-value is the fraction of sign vectors with T(g) >= T(1):

    p_hat(lambda) = 2^{-q} sum_g 1{ T(g; lambda) >= T(1; lambda) }.        (4)

Reject when p_hat <= alpha. Because T(g) = T(-g), the attainable rejection
probability in the limit is floor(alpha * 2^{q-1}) / 2^{q-1}
(`attainable_size`), which is 0 for q <= 5 at alpha = 0.05.

Confidence set: {lambda : p_hat(lambda) > alpha}. Cai et al. prove it is an
interval for a scalar parameter, and it always contains the point where the
weighted score sum is zero, so each endpoint is found by bracketing outward
from that point and bisecting on the accept/reject indicator.

The sign group is enumerated exactly for q <= max_exact (default 20, i.e.
about one million rows); beyond that random signs are drawn and the result
is flagged as not exact.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Optional, Tuple

import numpy as np


# --------------------------------------------------------------------------
# sign group
# --------------------------------------------------------------------------

def sign_group(q: int, max_exact: int = 20, n_random: int = 10_000,
               random_state: Optional[object] = None) -> Tuple[np.ndarray, bool]:
    """
    Return (signs, exact). `signs` is an (M, q) array of +-1 with row 0 equal
    to the identity (all +1). exact=True means all 2^q sign vectors are present.
    """
    if q < 1:
        raise ValueError("q must be positive.")
    if q <= max_exact:
        signs = np.array(list(product((1, -1), repeat=q)), dtype=np.int8)
        return signs, True
    rng = np.random.default_rng(random_state)
    signs = rng.choice(np.array([1, -1], dtype=np.int8), size=(n_random, q))
    signs[0, :] = 1
    return signs, False


def attainable_size(q: int, alpha: float) -> float:
    """Limiting null rejection probability of the non-randomized test, floor(alpha 2^{q-1}) / 2^{q-1}."""
    m = 2 ** (q - 1)
    return float(np.floor(alpha * m) / m)


# --------------------------------------------------------------------------
# statistics and p-values
# --------------------------------------------------------------------------

def _check_alpha(alpha: float) -> None:
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must lie strictly between 0 and 1.")


def _check_scores(a: np.ndarray, b: np.ndarray) -> None:
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("a and b must be 1-d arrays of the same length (one entry per cluster).")
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        raise ValueError("cluster scores contain non-finite values.")
    if np.any(b <= 0):
        raise ValueError("score slopes b_j must be positive.")


def _check_weights(q: int, weights: Optional[np.ndarray]) -> np.ndarray:
    if weights is None:
        return np.full(q, 1.0 / q)
    w = np.asarray(weights, dtype=float)
    if w.shape != (q,) or not np.all(np.isfinite(w)) or np.any(w <= 0):
        raise ValueError(f"weights must be {q} positive finite numbers.")
    return w


def art_statistics(scores: np.ndarray, signs: np.ndarray, weights: Optional[np.ndarray] = None) -> np.ndarray:
    """T(g) for every row g of `signs`; row 0 is the observed statistic."""
    scores = np.asarray(scores, dtype=float)
    w = _check_weights(scores.size, weights)
    return np.abs(signs.astype(float) @ (w * scores))


def art_pvalue(scores: np.ndarray, signs: np.ndarray, weights: Optional[np.ndarray] = None) -> float:
    """Equation (4): share of sign vectors with T(g) >= observed T."""
    T = art_statistics(scores, signs, weights)
    return float(np.mean(T >= T[0]))


@dataclass
class ARTTestResult:
    lam: float
    statistic: float
    p_value: float
    alpha: float
    reject: bool
    critical_value: float   # (M - floor(M alpha))-th smallest orbit value; reject iff statistic > this
    exact: bool
    q: int
    attainable_size: float

    def __str__(self) -> str:
        tag = "exact" if self.exact else "random signs"
        return (f"ART test of theta = {self.lam:g}: T = {self.statistic:.4f}, "
                f"p = {self.p_value:.4f} ({tag}), alpha = {self.alpha}, "
                f"reject = {self.reject}; attainable size with q={self.q} is {self.attainable_size:.4f}")


def art_test(a: np.ndarray, b: np.ndarray, lam: float, signs: np.ndarray, exact: bool,
             alpha: float = 0.05, weights: Optional[np.ndarray] = None) -> ARTTestResult:
    """Test H0: theta = lam from affine scores S_j(lam) = a_j - b_j lam."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    _check_scores(a, b)
    _check_alpha(alpha)
    if not np.isfinite(lam):
        raise ValueError("lam must be finite.")
    scores = a - b * lam
    T = art_statistics(scores, signs, weights)
    p = float(np.mean(T >= T[0]))
    M = T.size
    k = M - int(np.floor(M * alpha))          # Lehmann-Romano (15.5) index
    crit = float(np.sort(T)[k - 1])
    return ARTTestResult(
        lam=float(lam), statistic=float(T[0]), p_value=p, alpha=alpha,
        reject=bool(p <= alpha), critical_value=crit, exact=exact,
        q=int(a.size), attainable_size=attainable_size(int(a.size), alpha),
    )


# --------------------------------------------------------------------------
# confidence interval by test inversion
# --------------------------------------------------------------------------

def art_confint(a: np.ndarray, b: np.ndarray, signs: np.ndarray, alpha: float = 0.05,
                weights: Optional[np.ndarray] = None, tol: float = 1e-8,
                max_expansions: int = 60) -> Tuple[float, float]:
    """
    Endpoints of {lambda : p_hat(lambda) > alpha}.

    Returns (-inf, inf) when no lambda is rejected within the search range,
    which is the normal outcome when attainable_size(q, alpha) == 0.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    _check_scores(a, b)
    _check_alpha(alpha)
    w = _check_weights(a.size, weights)
    center = float(np.sum(w * a) / np.sum(w * b))  # p_hat(center) = 1

    def accept(lam: float) -> bool:
        return art_pvalue(a - b * lam, signs, w) > alpha

    # scale of the search: spread of the cluster estimates, floored to avoid zero
    theta_j = a / b
    scale = float(np.std(theta_j)) if a.size > 1 else 1.0
    scale = max(scale, 1e-6 * max(1.0, abs(center)))

    def endpoint(direction: float) -> float:
        step = scale
        outer = center + direction * step
        n_exp = 0
        while accept(outer):
            step *= 2.0
            outer = center + direction * step
            n_exp += 1
            if n_exp >= max_expansions:
                return direction * np.inf
        inner = center                     # accepted
        # bisection on the accept/reject boundary (acceptance region is an interval)
        while abs(outer - inner) > tol * max(1.0, abs(inner)):
            mid = 0.5 * (inner + outer)
            if accept(mid):
                inner = mid
            else:
                outer = mid
        return inner

    return endpoint(-1.0), endpoint(+1.0)


# --------------------------------------------------------------------------
# validation helper: Cai et al.'s OLS cluster-by-cluster estimates
# --------------------------------------------------------------------------

def ols_cluster_estimates(y: np.ndarray, X: np.ndarray, cluster: np.ndarray, coef: int,
                          add_intercept: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    Cluster-by-cluster OLS coefficient `coef` of y on X, as in the original
    (non-ML) ART. Returns (beta_hat_j, n_j). Use with b = 1 to test the
    cluster estimates directly, or b = sqrt(n_j) for the weighted-score form.
    Intended only for checking this package's ART core against rART.
    """
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    labels = np.unique(cluster)
    beta = np.zeros(labels.size)
    n = np.zeros(labels.size, dtype=int)
    for j, lab in enumerate(labels):
        rows = cluster == lab
        Xj = X[rows]
        if add_intercept:
            Xj = np.hstack([np.ones((Xj.shape[0], 1)), Xj])
        coefs, *_ = np.linalg.lstsq(Xj, y[rows], rcond=None)
        beta[j] = coefs[coef + (1 if add_intercept else 0)]
        n[j] = int(rows.sum())
    return beta, n
