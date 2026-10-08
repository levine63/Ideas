"""
scores.py -- from residuals to the per-cluster weighted score.

Equations (2)-(3) of the note. With out-of-fold residuals

    vhat_ij = D_ij - mhat(X_ij),      ytilde_ij = Y_ij - ellhat(X_ij),

define for each cluster j (sums over the scored rows of cluster j)

    Qhat_j   = n_j^{-1} sum_i vhat_ij^2
    thetahat_j = sum_i vhat_ij ytilde_ij / sum_i vhat_ij^2
    S_j(lambda) = Qhat_j^{-1} n_j^{-1/2} sum_i vhat_ij (ytilde_ij - lambda vhat_ij)
                = sqrt(n_j) (thetahat_j - lambda)                        (exact)

S_j is affine in lambda:  S_j(lambda) = a_j - b_j * lambda  with
a_j = sqrt(n_j) thetahat_j and b_j = sqrt(n_j). The ART core (art.py) only
ever sees (a, b).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ClusterScores:
    labels: np.ndarray      # original cluster labels, length q
    n: np.ndarray           # scored observations per cluster
    Q: np.ndarray           # Qhat_j
    theta: np.ndarray       # thetahat_j
    a: np.ndarray           # sqrt(n_j) * thetahat_j
    b: np.ndarray           # sqrt(n_j)

    @property
    def q(self) -> int:
        return int(self.labels.size)

    def S(self, lam: float) -> np.ndarray:
        """Vector of weighted scores S_j(lambda)."""
        return self.a - self.b * lam

    def pooled_theta(self, weights: np.ndarray) -> float:
        """The lambda at which the weighted score sum is exactly zero."""
        return float(np.sum(weights * self.a) / np.sum(weights * self.b))


def cluster_scores(vhat: np.ndarray, ytilde: np.ndarray, cluster: np.ndarray,
                   scored: np.ndarray, labels: np.ndarray) -> ClusterScores:
    """
    Compute per-cluster scores from residuals.

    Raises
    ------
    ValueError if some cluster has sum(vhat^2) == 0 (no residual treatment
    variation): the within-cluster estimate does not exist and the note says
    to report the failure rather than a p-value.
    """
    vhat = np.asarray(vhat, dtype=float)
    ytilde = np.asarray(ytilde, dtype=float)
    cluster = np.asarray(cluster)
    scored = np.asarray(scored, dtype=bool)
    q = int(labels.size)
    n = np.zeros(q, dtype=int)
    Q = np.zeros(q)
    theta = np.zeros(q)
    for j in range(q):
        rows = (cluster == j) & scored
        v = vhat[rows]
        y = ytilde[rows]
        n[j] = v.size
        if n[j] == 0:
            raise ValueError(f"Cluster {labels[j]} has no scored observations.")
        denom = float(np.sum(v * v))
        if denom <= 0.0:
            raise ValueError(f"Cluster {labels[j]}: sum of squared treatment residuals is zero; "
                             "no within-cluster identifying variation (Q_j = 0).")
        Q[j] = denom / n[j]
        theta[j] = float(np.sum(v * y)) / denom
    b = np.sqrt(n.astype(float))
    return ClusterScores(labels=labels, n=n, Q=Q, theta=theta, a=b * theta, b=b)
