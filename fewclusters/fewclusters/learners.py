"""
learners.py -- adapters so that any scikit-learn style estimator can be a
nuisance learner, with one rule that matters for correctness:

    every fitted nuisance model is wrapped in FittedNuisance, whose
    predict(X) returns the CONDITIONAL MEAN of the response.

For a regressor that is predict(X). For a classifier (anything exposing
predict_proba, e.g. LogisticRegression or a gradient-boosting classifier),
predict(X) would return hard 0/1 labels, which are NOT E[D | X]; using them
breaks the orthogonal score. FittedNuisance therefore returns the predicted
probability of the class labelled 1. Classifiers are only accepted for a
binary 0/1 response.

Contents
    is_classifier_like(est)   True if est has predict_proba (or is an sklearn classifier)
    fit_fresh(learner, X, z)  clone, fit, wrap -> FittedNuisance
    FittedNuisance            .predict(X) -> conditional mean, (n,)
    ClusterIdLearner          learner that sees X plus one-hot cluster identity
    ConstantPredictor         .predict(X) -> fixed value
    BoundPredictor            freezes extra predict() kwargs into a plain predict(X)

A "predictor" anywhere in this package is any object with predict(X) -> (n,).
"""

from __future__ import annotations

import copy
from typing import Any, Optional

import numpy as np

try:
    from sklearn.base import clone as _sk_clone
    from sklearn.base import is_classifier as _sk_is_classifier
except ImportError:  # scikit-learn is optional for the core
    _sk_clone = None
    _sk_is_classifier = None


def is_classifier_like(est: Any) -> bool:
    if _sk_is_classifier is not None:
        try:
            if _sk_is_classifier(est):
                return True
        except Exception:
            pass
    return hasattr(est, "predict_proba")


class FittedNuisance:
    """
    A fitted learner whose predict(X) is the conditional mean of the response.

    For classifiers: P(class 1 | X) from predict_proba. If the training data
    contained a single class c, the prediction is the constant c.
    """

    def __init__(self, model: Any, classifier: bool):
        self.model = model
        self.classifier = classifier
        if classifier:
            classes = np.asarray(model.classes_)
            if not np.all(np.isin(classes, [0, 1])):
                raise ValueError(f"Classifier trained on classes {classes}; expected a 0/1 response.")
            self._single = float(classes[0]) if classes.size == 1 else None
            self._col = None if classes.size == 1 else int(np.flatnonzero(classes == 1)[0])

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.classifier:
            return np.asarray(self.model.predict(X), dtype=float).ravel()
        if self._single is not None:
            return np.full(np.asarray(X).shape[0], self._single)
        return np.asarray(self.model.predict_proba(X), dtype=float)[:, self._col]


def _clone(learner: Any) -> Any:
    if _sk_clone is not None:
        try:
            return _sk_clone(learner)
        except Exception:
            pass
    return copy.deepcopy(learner)


def fit_fresh(learner: Any, X: np.ndarray, z: np.ndarray) -> FittedNuisance:
    """
    Fit a fresh copy of `learner` and wrap it so predict() is a conditional mean.

    A new copy is made for every fit so that fits for different folds and
    clusters never share state.
    """
    classifier = is_classifier_like(learner)
    z = np.asarray(z)
    if classifier:
        vals = np.unique(z)
        if not np.all(np.isin(vals, [0, 1])):
            raise ValueError("A classifier was supplied as a nuisance learner, but the response is not 0/1. "
                             "Use a regressor for non-binary responses.")
        z = z.astype(int)
    fresh = _clone(learner)
    fresh.fit(X, z)
    return FittedNuisance(fresh, classifier)


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
        self.fitted_: Optional[FittedNuisance] = None

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
        return self.fitted_.predict(self._augment(X, cl, self.n_clusters))


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
        return np.asarray(self.fitted.predict(X, **self.kwargs), dtype=float).ravel()
