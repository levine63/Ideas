"""
Numerical equivalence with rART (Canay & Thomas), via the line-by-line port
in rart_port.py. Our statistic is |q^-1 sum S_j| and rART's is
|q^-1 sum sqrt(q) S_j|, so p-values must agree exactly and critical values
must agree after multiplying ours by sqrt(q).
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from rart_port import crs_ci, crs_test, random_G  # noqa: E402

from fewclusters.art import art_confint, art_test, sign_group  # noqa: E402


def _cases(n=200, seed=0):
    rng = np.random.default_rng(seed)
    for t in range(n):
        q = int(rng.integers(3, 11))
        beta = rng.normal(1, 0.5, q)
        nj = rng.integers(50, 2000, q).astype(float) if t % 2 else np.ones(q)
        yield q, beta, nj, float(rng.normal(1, 0.3)), [0.05, 0.1, 0.2][t % 3]


def test_pvalue_and_critical_value_match_rart():
    for q, beta, nj, lam, alpha in _cases():
        G = random_G(q)
        signs, exact = sign_group(q)
        r = crs_test(beta, G, lam, alpha, nj)
        o = art_test(np.sqrt(nj) * beta, np.sqrt(nj), lam, signs, exact, alpha)
        assert o.p_value == r["p"]
        assert np.sqrt(q) * o.critical_value == pytest.approx(r["crit"], rel=1e-12, abs=1e-12)


def test_confidence_interval_matches_rart_closed_form():
    for q, beta, nj, _, alpha in _cases(seed=1):
        G = random_G(q)
        signs, _ = sign_group(q)
        ours = art_confint(np.sqrt(nj) * beta, np.sqrt(nj), signs, alpha)
        theirs = crs_ci(beta, G, alpha, nj)
        for x, y in zip(ours, theirs):
            if np.isinf(y):
                assert np.isinf(x) and np.sign(x) == np.sign(y)
            else:
                assert x == pytest.approx(y, rel=1e-6, abs=1e-8)
