"""
Line-by-line Python port of rART's CRS.test and CRS.CI (R/backend.R in
https://github.com/mwt/rART, MIT licence, Canay & Thomas), used ONLY as an
independent reference implementation in tests. It is deliberately written
to mirror the R code, not to share any code with fewclusters.art.

R conventions reproduced:
  * G is a q x M matrix whose columns are sign vectors.
  * quantile(x, p, type = 1) is the inverse empirical CDF: the smallest
    order statistic x_(j) with j / M >= p, i.e. j = ceil(M p) (1-based).
"""

from itertools import product

import numpy as np


def random_G(q: int) -> np.ndarray:
    """expand.grid over {1,-1}^q, as columns (q x 2^q). Only the exact case."""
    return np.array(list(product((1, -1), repeat=q)), dtype=float).T


def _quantile_type1(x: np.ndarray, p: float) -> float:
    xs = np.sort(x)
    M = xs.size
    j = int(np.ceil(M * p - 1e-12))
    j = min(max(j, 1), M)
    return float(xs[j - 1])


def crs_test(c_beta, G, lam=0.0, alpha=0.05, nj=1.0):
    c_beta = np.asarray(c_beta, dtype=float)
    q = c_beta.size
    M = G.shape[1]
    nj = np.asarray(nj, dtype=float)
    if nj.size not in (1, q):
        nj = np.array(1.0)
    Sn = np.sqrt(q) * np.sqrt(nj) * (c_beta - lam)
    ObsT = abs(np.mean(Sn))
    NewX = G * Sn[:, None]
    NewT = np.sort(np.abs(NewX.mean(axis=0)))
    k = M - int(np.floor(M * alpha))
    p_value = float(np.sum(NewT >= ObsT) / M)
    return {"crit": float(NewT[k - 1]), "t": float(ObsT), "p": p_value}


def crs_ci(c_beta, G, alpha=0.05, nj=1.0):
    c_beta = np.asarray(c_beta, dtype=float)
    q = c_beta.size
    M = G.shape[1]
    nj = np.asarray(nj, dtype=float) * np.ones(q) if np.asarray(nj).size == 1 else np.asarray(nj, float)
    Sn = np.sqrt(nj) * c_beta
    ai = np.mean(np.sqrt(nj))
    ag = (np.sqrt(nj)[:, None] * G).mean(axis=0)
    bi = np.mean(Sn)
    bg = (Sn[:, None] * G).mean(axis=0)
    l0 = bi / ai
    ll = np.full(M, -np.inf)
    lu = np.full(M, np.inf)
    zeroset = ag == 0
    if zeroset.any():
        dist = np.abs(bg) / ai
        ll[zeroset] = l0 - dist[zeroset]
        lu[zeroset] = l0 + dist[zeroset]
    nanset = np.abs(ag) == ai
    main = ~zeroset & ~nanset
    if main.any():
        agnz, bgnz = ag[main], bg[main]
        addterm = l0 * (ai / (ai + np.abs(agnz))) + (bgnz / agnz) * (np.abs(agnz) / (ai + np.abs(agnz)))
        subterm = l0 * (ai / (ai - np.abs(agnz))) - (bgnz / agnz) * (np.abs(agnz) / (ai - np.abs(agnz)))
        ratless = bgnz / agnz <= l0
        llm = np.where(ratless, addterm, subterm)
        lum = np.where(ratless, subterm, addterm)
        ll[main] = llm
        lu[main] = lum
    lb = _quantile_type1(ll, alpha)
    ub = -_quantile_type1(-lu, alpha)
    return lb, ub
