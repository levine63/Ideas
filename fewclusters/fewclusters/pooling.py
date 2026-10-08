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

Shrinkage toward borrowing (small clusters). With a calibration sample of
s rows, the raw weight w_hat is noisy when s is small. Optionally shrink it
toward full borrowing,

    w_tilde = (s * w_hat + kappa * 1) / (s + kappa),

so kappa acts like kappa pseudo-observations voting for the borrowing
candidate. With 5 folds (s ~ n_j / 5) and kappa = 20, a cluster of 10
uses ~9% of its own choice, 40 -> 29%, 400 -> 80%, 2000 -> 95%.

Cost. The calibration risk R(w) = E[(L + w d - f_0)^2] is convex in w, so
with lam = s / (s + kappa)

    R(w_tilde) <= lam R(w_hat) + (1 - lam) R(1),

hence E R(w_tilde) - R(w_*) <= [Proposition 2 term] + (kappa / s) R(1).
When the borrowing candidate's risk R(1) is bounded, the extra term is
O(1/s), the same order as the calibration cost Proposition 2 already
charges, so the per-cluster rate condition is preserved. The bound is
uniform in nothing: in a small cluster a biased borrowing model is used
almost undiluted. That is acceptable for the outcome model when the
treatment probabilities are known (Corollary 2) and risky for the
treatment model (Section 7.1), which is why ARTDML shrinks the outcome
model by default and the treatment model only on request.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class PoolingWeight:
    w: float               # weight actually used (after shrinkage)
    w_raw: float           # clipped least-squares weight before shrinkage
    denominator: float
    n_calib: int
    mse_local: float       # calibration MSE of L, a diagnostic only
    mse_borrow: float      # calibration MSE of P, a diagnostic only
    mse_mixture: float     # calibration MSE of the chosen mixture (in-sample)


def ls_pooling_weight(z: np.ndarray, local_pred: np.ndarray, borrow_pred: np.ndarray,
                      shrink_kappa: float = 0.0) -> PoolingWeight:
    """Clipped least-squares weight on the calibration sample, equation (7),
    optionally shrunk toward 1 (full borrowing) with strength shrink_kappa."""
    if shrink_kappa < 0:
        raise ValueError("shrink_kappa must be non-negative.")
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
    w_raw = w
    s_ = z.size
    if shrink_kappa > 0:
        w = (s_ * w_raw + shrink_kappa) / (s_ + shrink_kappa)
    mix = L + w * d
    return PoolingWeight(
        w=w,
        w_raw=w_raw,
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
