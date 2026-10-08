"""
model.py -- ARTDML: the end-to-end procedure.

    0. checks              finite inputs; treatment must vary WITHIN every
                           cluster (otherwise the within-cluster estimand is
                           not identified and the procedure stops)
    1. FoldPlan            split each cluster into evaluation / calibration /
                           base-training roles (folds.py)
    2. crossfit_nuisance   out-of-fold predictions mhat and ellhat, each with
                           its own pooling mode (nuisance.py); m may instead be
                           supplied as known propensities (Corollary 2)
    3. cluster_scores      vhat = D - mhat, ytilde = Y - ellhat ->
                           (Qhat_j, thetahat_j, a_j, b_j) (scores.py)
    4. art_test/confint    sign-group test and interval (art.py)

Everything in steps 0-3 is computed exactly once in fit(). test() and
confint() only touch the (a, b) vectors, so they are cheap and never refit
anything: this is the "fit once" property of the note.

Typical use
-----------
    from sklearn.ensemble import HistGradientBoostingRegressor as GBR
    from sklearn.ensemble import HistGradientBoostingClassifier as GBC
    model = ARTDML(learner_m=GBC(), learner_l=GBR(), n_folds=5,
                   pooling_m="adaptive", pooling_l="adaptive", borrow="pooled_id",
                   random_state=0)
    model.fit(y, d, X, cluster)
    print(model.test(0.0)); print(model.confint(0.05)); print(model.summary())

A classifier for m (binary D) is used through predict_proba, so its
predictions are probabilities, not labels (learners.py).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .art import ARTTestResult, art_confint, art_test, attainable_size, sign_group
from .folds import FoldPlan
from .nuisance import NuisanceDiagnostics, NuisanceSpec, crossfit_nuisance
from .scores import ClusterScores, cluster_scores

# Q_hat_j above this multiple of the raw within-cluster variance of D means
# the treatment model predicts D worse than the cluster mean of D does.
Q_RATIO_WARN = 1.25


class IdentificationWarning(UserWarning):
    """Raised (as a warning) when residual treatment variation looks spurious."""


@dataclass
class ARTDMLResult:
    """Everything produced by fit(); kept separate so it is easy to inspect or pickle."""

    labels: np.ndarray
    scores: ClusterScores
    weights: np.ndarray
    signs: np.ndarray
    exact: bool
    mhat: np.ndarray
    lhat: np.ndarray
    vhat: np.ndarray
    ytilde: np.ndarray
    scored: np.ndarray
    plan: FoldPlan
    var_d: np.ndarray                      # raw within-cluster variance of D
    diagnostics_m: List[NuisanceDiagnostics] = field(default_factory=list)
    diagnostics_l: List[NuisanceDiagnostics] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _finite(name: str, a: np.ndarray) -> None:
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{name} contains missing or non-finite values; drop or impute them first.")


class ARTDML:
    """
    Approximate randomization test with cross-fitted DML scores and few clusters.

    Parameters
    ----------
    learner_m, learner_l : estimators with fit(X, z) / predict(X)
        Learners for m_0j(x) = E[D|X] and ell_0j(x) = E[Y|X]. learner_m may be
        a classifier (binary D); its predict_proba is used. learner_m is
        ignored when known propensities are passed to fit().
    n_folds : int
        K folds within each cluster.
    pooling_m, pooling_l : {"local", "pooled", "pooled_id", "adaptive"}
        How each nuisance is fitted (see nuisance.py). Section 7.1 of the note
        explains why borrowing for m is riskier than for ell.
    borrow : {"pooled", "pooled_id"}
        The borrowing candidate used by "adaptive".
    calib_fraction : float in (0, 1) or None
        Calibration sample for "adaptive": a random share of the target
        cluster outside the evaluation fold (K >= 2), or None to use the next
        fold (K >= 3). Not available with buffered/contiguous folds.
    exclude_same_fold : bool
        When borrowing, drop the other clusters' same-numbered fold.
    buffer : int
        Positions dropped around evaluation/calibration blocks (dependence).
        buffer > 0 forces contiguous folds in row order within each cluster.
    contiguous : bool
        Contiguous folds even without a buffer.
    weights : array (q,) or None
        omega_j > 0 in the statistic; None means 1/q.
    max_exact : int
        Enumerate all 2^q sign vectors when q <= max_exact; else sample.
    n_random_signs : int
        Number of random sign vectors when enumeration is not exact.
    random_state : int or None
        Seeds the fold partition, calibration draws and random signs. Learner
        randomness is controlled by the learner's own random_state.
    """

    def __init__(self, learner_m: Any = None, learner_l: Any = None, n_folds: int = 5,
                 pooling_m: str = "adaptive", pooling_l: str = "adaptive",
                 borrow: str = "pooled_id", calib_fraction: Optional[float] = None,
                 exclude_same_fold: bool = True, buffer: int = 0, contiguous: bool = False,
                 weights: Optional[np.ndarray] = None, max_exact: int = 20,
                 n_random_signs: int = 10_000, random_state: Optional[int] = None):
        self.learner_m = learner_m
        self.learner_l = learner_l
        self.n_folds = n_folds
        self.pooling_m = pooling_m
        self.pooling_l = pooling_l
        self.borrow = borrow
        self.calib_fraction = calib_fraction
        self.exclude_same_fold = exclude_same_fold
        self.buffer = buffer
        self.contiguous = contiguous
        self.weights = weights
        self.max_exact = max_exact
        self.n_random_signs = n_random_signs
        self.random_state = random_state
        self.result_: Optional[ARTDMLResult] = None

    # ------------------------------------------------------------------
    def fit(self, y: np.ndarray, d: np.ndarray, X: np.ndarray, cluster: np.ndarray,
            m_known: Optional[np.ndarray] = None, folds: Optional[np.ndarray] = None) -> "ARTDML":
        """
        Cross-fit the nuisances and compute the cluster scores.

        m_known : (n,) known treatment probabilities (Corollary 2). When given,
            vhat = d - m_known and learner_m / pooling_m are not used.
        folds : (n,) explicit fold labels 0..K-1 (every cluster must contain
            every fold). Overrides the random partition; use it for exact
            reproducibility across machines or to share folds between methods.
        """
        y = np.asarray(y, dtype=float).ravel()
        d = np.asarray(d, dtype=float).ravel()
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X[:, None]
        cluster = np.asarray(cluster).ravel()
        n = y.size
        if not (d.size == n and X.shape[0] == n and cluster.size == n):
            raise ValueError("y, d, X and cluster must have the same number of rows.")
        _finite("y", y); _finite("d", d); _finite("X", X)

        labels, cl = np.unique(cluster, return_inverse=True)
        q = labels.size
        if q < 2:
            raise ValueError("Need at least two clusters.")

        # identification: D must vary within every cluster
        var_d = np.array([np.var(d[cl == j]) for j in range(q)])
        no_var = labels[var_d <= 0.0]
        if no_var.size:
            raise ValueError(f"Treatment is constant within cluster(s) {list(no_var)}. The within-cluster "
                             "effect is not identified there (e.g. cluster-level treatment); this method "
                             "does not apply.")

        binary_d = np.all(np.isin(np.unique(d), [0.0, 1.0]))
        if m_known is not None:
            m_known = np.asarray(m_known, dtype=float).ravel()
            if m_known.size != n:
                raise ValueError("m_known must have one entry per row.")
            _finite("m_known", m_known)
            if binary_d and np.any((m_known <= 0) | (m_known >= 1)):
                raise ValueError("m_known must lie strictly between 0 and 1 for a binary treatment.")

        weights = self._check_weights(q)
        if folds is not None:
            folds = np.asarray(folds).ravel()
            if folds.size != n:
                raise ValueError("folds must have one entry per row.")

        spec_l = NuisanceSpec(self.learner_l, self.pooling_l, self.borrow, name="ell")
        use_m_learner = m_known is None
        spec_m = NuisanceSpec(self.learner_m, self.pooling_m, self.borrow, name="m") if use_m_learner else None
        needs_calib = spec_l.needs_calibration or (use_m_learner and spec_m.needs_calibration)

        plan = FoldPlan(cl, n_folds=self.n_folds, use_calibration=needs_calib,
                        calib_fraction=self.calib_fraction if needs_calib else None,
                        exclude_same_fold=self.exclude_same_fold, buffer=self.buffer,
                        contiguous=self.contiguous or self.buffer > 0, fold_ids=folds,
                        random_state=self.random_state)

        if use_m_learner:
            if self.learner_m is None:
                raise ValueError("learner_m is required unless m_known is supplied.")
            fit_m = crossfit_nuisance(d, X, cl, plan, spec_m)
            mhat, diag_m = fit_m.predictions, fit_m.diagnostics
        else:
            mhat, diag_m = m_known, []
        if self.learner_l is None:
            raise ValueError("learner_l is required.")
        fit_l = crossfit_nuisance(y, X, cl, plan, spec_l)
        lhat, diag_l = fit_l.predictions, fit_l.diagnostics

        vhat = d - mhat
        ytilde = y - lhat
        scores = cluster_scores(vhat, ytilde, cl, plan.scored, labels)
        signs, exact = sign_group(q, self.max_exact, self.n_random_signs, self.random_state)

        notes = []
        ratio = scores.Q / var_d
        for j in np.flatnonzero(ratio > Q_RATIO_WARN):
            notes.append(f"Cluster {labels[j]}: residual treatment variance Q_hat = {scores.Q[j]:.4g} is "
                         f"{ratio[j]:.2f} x the raw within-cluster variance of D ({var_d[j]:.4g}). The "
                         "treatment model predicts D worse than the cluster mean does; Q_hat may reflect "
                         "between-cluster variation rather than within-cluster identifying variation.")
        for msg in notes:
            warnings.warn(msg, IdentificationWarning, stacklevel=2)

        self.result_ = ARTDMLResult(
            labels=labels, scores=scores, weights=weights, signs=signs, exact=exact,
            mhat=mhat, lhat=lhat, vhat=vhat, ytilde=ytilde, scored=plan.scored, plan=plan,
            var_d=var_d, diagnostics_m=diag_m, diagnostics_l=diag_l, warnings=notes,
        )
        return self

    def _check_weights(self, q: int) -> np.ndarray:
        if self.weights is None:
            return np.full(q, 1.0 / q)
        w = np.asarray(self.weights, dtype=float).ravel()
        if w.shape != (q,) or not np.all(np.isfinite(w)) or np.any(w <= 0):
            raise ValueError(f"weights must be {q} positive finite numbers (one per cluster).")
        return w

    # ------------------------------------------------------------------
    def _require_fit(self) -> ARTDMLResult:
        if self.result_ is None:
            raise RuntimeError("Call fit() first.")
        return self.result_

    def test(self, lam: float = 0.0, alpha: float = 0.05) -> ARTTestResult:
        """Test H0: theta_0 = lam. Uses the fitted scores; nothing is refit."""
        r = self._require_fit()
        return art_test(r.scores.a, r.scores.b, lam, r.signs, r.exact, alpha, r.weights)

    def pvalue(self, lam: float = 0.0) -> float:
        return self.test(lam).p_value

    def confint(self, alpha: float = 0.05) -> Tuple[float, float]:
        """Confidence interval by inverting the test over lambda."""
        r = self._require_fit()
        return art_confint(r.scores.a, r.scores.b, r.signs, alpha, r.weights)

    def pooled_estimate(self) -> float:
        """The lambda at which the weighted score sum vanishes (a point estimate)."""
        r = self._require_fit()
        return r.scores.pooled_theta(r.weights)

    # ------------------------------------------------------------------
    def cluster_table(self) -> List[Dict[str, Any]]:
        """Per-cluster n, raw Var(D), Qhat, thetahat, and mean pooling weights."""
        r = self._require_fit()
        rows = []
        for j in range(r.scores.q):
            wm = [dg.weight for dg in r.diagnostics_m if dg.cluster == j and dg.weight is not None]
            wl = [dg.weight for dg in r.diagnostics_l if dg.cluster == j and dg.weight is not None]
            rows.append({
                "cluster": r.labels[j],
                "n_scored": int(r.scores.n[j]),
                "var_D": float(r.var_d[j]),
                "Q_hat": float(r.scores.Q[j]),
                "theta_hat": float(r.scores.theta[j]),
                "mean_w_m": float(np.mean(wm)) if wm else None,
                "mean_w_l": float(np.mean(wl)) if wl else None,
            })
        return rows

    def summary(self, alpha: float = 0.05) -> str:
        r = self._require_fit()
        q = r.scores.q
        lines = [
            f"ARTDML: q = {q} clusters, n_scored = {int(r.scores.n.sum())}, K = {self.n_folds}, "
            f"pooling_m = {'known' if not r.diagnostics_m else self.pooling_m}, pooling_l = {self.pooling_l}",
            f"sign group: {'exact (2^q rows)' if r.exact else f'{r.signs.shape[0]} random rows'}; "
            f"attainable size at alpha={alpha}: {attainable_size(q, alpha):.4f}",
            f"pooled point estimate: {self.pooled_estimate():.4f}",
            f"{int(round(100 * (1 - alpha)))}% CI by test inversion: {self.confint(alpha)}",
            "per cluster:",
        ]
        for row in self.cluster_table():
            lines.append("  " + ", ".join(f"{k}={v:.4g}" if isinstance(v, float) else f"{k}={v}"
                                          for k, v in row.items()))
        if attainable_size(q, alpha) == 0.0:
            lines.append(f"WARNING: with q = {q} the test can never reject at alpha = {alpha}; "
                         f"the smallest attainable p-value is {2 / 2 ** q:.4f}.")
        lines += [f"WARNING: {w}" for w in r.warnings]
        return "\n".join(lines)
