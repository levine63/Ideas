"""
pooling.py -- combining a local and a borrowing prediction.

Equation (7) of the note. With both candidate predictors frozen, and a
calibration sample (X_t, Z_t), t = 1..s, from the target cluster, let

    L(x)  local prediction,   P(x)  borrowing prediction,   d(x) = P(x) - L(x)

and choose

    w_hat = clip( sum_t d(X_t) (Z_t - L(X_t)) / sum_t d(X_t)^2 ,  0, 1 )

with w_hat = 0 when the denominator is zero. The final predictor is
f_hat = L + w_hat * d. Proposition 2 bounds the expected excess risk of this
choice by a constant over the calibration sample size.

The weight is chosen separately for each nuisance (m and ell), each target
cluster and each evaluation fold. Nothing here depends on the learners.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class PoolingWeight:
    w: float
    denominator: float
    n_calib: int
    mse_local: float       # calibration MSE of L, a diagnostic only
    mse_borrow: float      # calibration MSE of P, a diagnostic only
    mse_mixture: float     # calibration MSE of the chosen mixture (in-sample)


def ls_pooling_weight(z: np.ndarray, local_pred: np.ndarray, borrow_pred: np.ndarray) -> PoolingWeight:
    """Clipped least-squares weight on the calibration sample, equation (7)."""
    z = np.asarray(z, dtype=float)
    L = np.asarray(local_pred, dtype=float)
    P = np.asarray(borrow_pred, dtype=float)
    d = P - L
    denom = float(np.sum(d * d))
    if denom > 0.0:
        w = float(np.sum(d * (z - L)) / denom)
        w = min(1.0, max(0.0, w))
    else:
        w = 0.0
    mix = L + w * d
    return PoolingWeight(
        w=w,
        denominator=denom,
        n_calib=int(z.size),
        mse_local=float(np.mean((z - L) ** 2)),
        mse_borrow=float(np.mean((z - P) ** 2)),
        mse_mixture=float(np.mean((z - mix) ** 2)),
    )


class MixturePredictor:
    """f_hat(x) = L(x) + w * (P(x) - L(x)) for frozen predictors L and P."""

    def __init__(self, local: Any, borrow: Any, w: float):
        self.local = local
        self.borrow = borrow
        self.w = float(w)

    def predict(self, X: np.ndarray) -> np.ndarray:
        L = np.asarray(self.local.predict(X)).ravel()
        if self.w == 0.0:
            return L
        P = np.asarray(self.borrow.predict(X)).ravel()
        return L + self.w * (P - L)
