"""
simulate.py -- data-generating processes for the simulation study.

One function, `simulate_plm`, with knobs for each experiment in the plan:

    tau_m, tau_l        cluster heterogeneity of the treatment / outcome
                        regressions (0 = common functions; larger = more
                        cluster-specific). Vary separately to study the
                        asymmetry of Section 7.1.
    known_propensity    treatment probability constant within cluster and
                        independent of X (Corollary 2); returned as `m0`.
    gamma               per-cluster treatment-effect deviations, theta_j =
                        theta + gamma_j (array of length q, or None). Use a
                        skewed draw to reproduce the over-rejection example.
    dependence_R        MA(R) errors within cluster (Corollary 1); 0 = iid.
    covariate_shift     size of cluster-specific shifts of the covariate
                        distribution (overlap experiment).

Returned dict contains y, d, X, cluster, and the TRUE functions evaluated at
the sample (m0, l0, g0) so an oracle ART can be run as the benchmark.

Model:
    m_0j(x) = sigmoid(0.8 x1 - 0.5 x2 + 0.5 sin(x3) + tau_m (A_j + 0.5 B_j x1))
    g_0j(x) = x1^2 - x2 + cos(x3) + 0.5 x1 x4 + tau_l (C_j + 0.5 E_j x2)
    D ~ Bernoulli(m_0j(X)),   Y = theta_j D + g_0j(X) + U,   U ~ N(0,1) (MA(R) if R>0)
    ell_0j(x) = theta_j m_0j(x) + g_0j(x)
with (A_j, B_j, C_j, E_j) i.i.d. N(0,1) cluster draws fixed by `seed`.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Union

import numpy as np


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def simulate_plm(q: int = 6, n_j: Union[int, Sequence[int]] = 500, theta: float = 1.0,
                 p: int = 4, tau_m: float = 0.0, tau_l: float = 0.0,
                 known_propensity: bool = False, gamma: Optional[np.ndarray] = None,
                 dependence_R: int = 0, covariate_shift: float = 0.0,
                 seed: Optional[int] = None) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    p = max(p, 4)
    sizes = np.full(q, int(n_j)) if np.isscalar(n_j) else np.asarray(n_j, dtype=int)
    if sizes.size != q:
        raise ValueError("n_j must be an int or a sequence of length q.")
    A, B, C, E = (rng.standard_normal(q) for _ in range(4))
    shift = covariate_shift * rng.standard_normal(q)
    p_known = 0.3 + 0.4 * rng.random(q)             # used only if known_propensity
    gamma = np.zeros(q) if gamma is None else np.asarray(gamma, dtype=float)
    theta_j = theta + gamma

    y_all, d_all, X_all, c_all = [], [], [], []
    m0_all, l0_all, g0_all = [], [], []
    for j in range(q):
        n = int(sizes[j])
        X = rng.standard_normal((n, p))
        X[:, 0] += shift[j]
        x1, x2, x3, x4 = X[:, 0], X[:, 1], X[:, 2], X[:, 3]
        if known_propensity:
            m0 = np.full(n, p_known[j])
        else:
            m0 = _sigmoid(0.8 * x1 - 0.5 * x2 + 0.5 * np.sin(x3) + tau_m * (A[j] + 0.5 * B[j] * x1))
        d = (rng.random(n) < m0).astype(float)
        g0 = x1 ** 2 - x2 + np.cos(x3) + 0.5 * x1 * x4 + tau_l * (C[j] + 0.5 * E[j] * x2)
        e = rng.standard_normal(n + dependence_R)
        if dependence_R > 0:
            u = np.zeros(n)
            for lag in range(dependence_R + 1):
                u += e[lag:lag + n]
            u /= np.sqrt(dependence_R + 1.0)
        else:
            u = e[:n]
        y = theta_j[j] * d + g0 + u
        y_all.append(y); d_all.append(d); X_all.append(X); c_all.append(np.full(n, j))
        m0_all.append(m0); g0_all.append(g0); l0_all.append(theta_j[j] * m0 + g0)

    return {
        "y": np.concatenate(y_all), "d": np.concatenate(d_all), "X": np.vstack(X_all),
        "cluster": np.concatenate(c_all), "m0": np.concatenate(m0_all),
        "l0": np.concatenate(l0_all), "g0": np.concatenate(g0_all),
        "theta_j": theta_j, "theta": float(theta),
    }


def skewed_gamma(q: int, rng: np.random.Generator, lo: float = -1.0, hi: float = 2.0,
                 p_lo: float = 2.0 / 3.0, scale: float = 0.3) -> np.ndarray:
    """Mean-zero but skewed cluster effects: lo w.p. p_lo, hi w.p. 1 - p_lo (scaled)."""
    draws = np.where(rng.random(q) < p_lo, lo, hi)
    return scale * (draws - (p_lo * lo + (1 - p_lo) * hi))


def symmetric_gamma(q: int, rng: np.random.Generator, scale: float = 0.3) -> np.ndarray:
    """Mean-zero symmetric (Rademacher) cluster effects of the same scale."""
    return scale * rng.choice([-1.0, 1.0], size=q)
