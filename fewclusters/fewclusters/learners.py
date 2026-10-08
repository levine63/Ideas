"""
learners.py -- small adapters so that any estimator with fit(X, z) and
predict(X) can be a nuisance learner.

Three things live here:

    fit_fresh(learner, X, z)        clone the learner, fit it, return the fit
    ClusterIdLearner                wraps a learner so that one-hot cluster
                                    identity is appended to X (the
                                    "pooled with cluster id" borrowing candidate)
    ConstantPredictor               a predictor returning a fixed vector/value;
                                    used for known propensities and in tests

A "predictor" anywhere in this package is any object with predict(X) -> (n,).
"""

from __future__ import annotations

import copy
from typing import Any, Optional

import numpy as np

try:
    from sklearn.base import clone as _sk_clone
except ImportError:  # scikit-learn is optional for the core
    _sk_clone = None


def fit_fresh(learner: Any, X: np.ndarray, z: np.ndarray) -> Any:
    """
    Return a freshly fitted copy of `learner`.

    A new copy is made for every fit so that fits for different folds and
    clusters never share state.
    """
    if _sk_clone is not None:
        try:
            fresh = _sk_clone(learner)
        except Exception:
            fresh = copy.deepcopy(learner)
    else:
        fresh = copy.deepcopy(learner)
    fresh.fit(X, z)
    return fresh


class ClusterIdLearner:
    """
    Wrap a learner so it sees X augmented with one-hot cluster indicators.

    The training rows come with their cluster ids; at prediction time the
    caller supplies the cluster id of the rows to predict (a scalar, since a
    prediction call always concerns one evaluation fold of one cluster).
    """

    def __init__(self, learner: Any, n_clusters: int):
        self.learner = learner
        self.n_clusters = n_clusters
        self.fitted_: Optional[Any] = None

    @staticmethod
    def _augment(X: np.ndarray, cluster: np.ndarray, n_clusters: int) -> np.ndarray:
        onehot = np.zeros((X.shape[0], n_clusters))
        onehot[np.arange(X.shape[0]), cluster] = 1.0
        return np.hstack([X, onehot])

    def fit(self, X: np.ndarray, z: np.ndarray, cluster: np.ndarray) -> "ClusterIdLearner":
        self.fitted_ = fit_fresh(self.learner, self._augment(X, cluster, self.n_clusters), z)
        return self

    def predict(self, X: np.ndarray, cluster_id: int) -> np.ndarray:
        if self.fitted_ is None:
            raise RuntimeError("ClusterIdLearner.predict called before fit.")
        cl = np.full(X.shape[0], cluster_id, dtype=int)
        return np.asarray(self.fitted_.predict(self._augment(X, cl, self.n_clusters))).ravel()


class ConstantPredictor:
    """predict(X) returns the stored value broadcast to X's number of rows."""

    def __init__(self, value: float):
        self.value = float(value)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(np.asarray(X).shape[0], self.value)


class BoundPredictor:
    """
    Freeze a fitted predictor whose predict() needs an extra argument
    (e.g. ClusterIdLearner needs the cluster id) into a plain predict(X).
    """

    def __init__(self, fitted: Any, **kwargs: Any):
        self.fitted = fitted
        self.kwargs = kwargs

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.asarray(self.fitted.predict(X, **self.kwargs)).ravel()
