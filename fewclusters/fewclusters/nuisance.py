"""
nuisance.py -- cross-fit ONE nuisance function (m or ell) over a FoldPlan.

For every (cluster j, evaluation fold k) role in the plan, the final
predictor for the evaluation observations is built according to
`NuisanceSpec.pooling`:

    "local"      fit the learner on the target cluster's base-training rows
    "pooled"     fit on target base rows + other clusters' allowed rows
    "pooled_id"  as "pooled", with one-hot cluster identity appended to X
    "adaptive"   fit the local candidate AND a borrowing candidate
                 (spec.borrow in {"pooled", "pooled_id"}), then choose the
                 mixing weight on the calibration rows (pooling.py)

The output is a vector of out-of-fold predictions, one per scored row, with
NaN for rows that are never evaluated (buffer rows). Nothing from an
evaluation fold is ever used to fit or calibrate the model that scores it.

Diagnostics record, per (j, k): the chosen weight, sample sizes, and the
calibration MSE of each candidate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

import numpy as np

from .folds import FoldPlan, FoldRoles
from .learners import BoundPredictor, ClusterIdLearner, fit_fresh
from .pooling import MixturePredictor, ls_pooling_weight

PoolingMode = Literal["local", "pooled", "pooled_id", "adaptive"]
BorrowMode = Literal["pooled", "pooled_id"]


@dataclass
class NuisanceSpec:
    """What to fit for one nuisance function."""

    learner: Any
    pooling: PoolingMode = "adaptive"
    borrow: BorrowMode = "pooled_id"
    name: str = "nuisance"

    def __post_init__(self) -> None:
        if self.pooling not in ("local", "pooled", "pooled_id", "adaptive"):
            raise ValueError(f"Unknown pooling mode {self.pooling!r}.")
        if self.borrow not in ("pooled", "pooled_id"):
            raise ValueError(f"Unknown borrow mode {self.borrow!r}.")

    @property
    def needs_calibration(self) -> bool:
        return self.pooling == "adaptive"


@dataclass
class NuisanceDiagnostics:
    name: str
    cluster: int
    fold: int
    pooling: str
    weight: Optional[float]
    n_eval: int
    n_calib: int
    n_base_target: int
    n_base_other: int
    mse_local: Optional[float] = None
    mse_borrow: Optional[float] = None
    mse_mixture: Optional[float] = None

    def as_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class NuisanceFit:
    predictions: np.ndarray                       # (n,), NaN where not scored
    diagnostics: List[NuisanceDiagnostics] = field(default_factory=list)


# --------------------------------------------------------------------------
# candidate builders: each returns an object with predict(X) -> (n_eval,)
# --------------------------------------------------------------------------

def _fit_local(spec: NuisanceSpec, X: np.ndarray, z: np.ndarray, role: FoldRoles) -> Any:
    idx = role.base_target_idx
    if idx.size == 0:
        raise ValueError(f"No base-training rows for cluster {role.cluster}, fold {role.fold}. "
                         "Increase n_folds or reduce buffer.")
    return fit_fresh(spec.learner, X[idx], z[idx])


def _fit_pooled(spec: NuisanceSpec, X: np.ndarray, z: np.ndarray, role: FoldRoles) -> Any:
    idx = np.concatenate([role.base_target_idx, role.base_other_idx])
    return fit_fresh(spec.learner, X[idx], z[idx])


def _fit_pooled_id(spec: NuisanceSpec, X: np.ndarray, z: np.ndarray,
                   cluster: np.ndarray, n_clusters: int, role: FoldRoles) -> Any:
    idx = np.concatenate([role.base_target_idx, role.base_other_idx])
    model = ClusterIdLearner(spec.learner, n_clusters).fit(X[idx], z[idx], cluster[idx])
    # freeze the target cluster id so the result is a plain predict(X)
    return BoundPredictor(model, cluster_id=role.cluster)


def _fit_borrow(spec: NuisanceSpec, X: np.ndarray, z: np.ndarray,
                cluster: np.ndarray, n_clusters: int, role: FoldRoles) -> Any:
    if spec.borrow == "pooled":
        return _fit_pooled(spec, X, z, role)
    return _fit_pooled_id(spec, X, z, cluster, n_clusters, role)


# --------------------------------------------------------------------------
# main loop
# --------------------------------------------------------------------------

def crossfit_nuisance(z: np.ndarray, X: np.ndarray, cluster: np.ndarray,
                      plan: FoldPlan, spec: NuisanceSpec) -> NuisanceFit:
    """
    Cross-fit one nuisance over the plan.

    Parameters
    ----------
    z : (n,) response of the nuisance regression (D for m, Y for ell)
    X : (n, p) controls
    cluster : (n,) cluster ids coded 0..q-1
    plan : FoldPlan
    spec : NuisanceSpec
    """
    z = np.asarray(z, dtype=float)
    X = np.asarray(X, dtype=float)
    cluster = np.asarray(cluster)
    n = z.size
    if spec.needs_calibration and not plan.use_calibration:
        raise ValueError("Adaptive pooling needs a FoldPlan with use_calibration=True.")

    out = NuisanceFit(predictions=np.full(n, np.nan))
    for role in plan.roles:
        X_eval = X[role.eval_idx]
        weight: Optional[float] = None
        mse_local = mse_borrow = mse_mix = None

        if spec.pooling == "local":
            predictor = _fit_local(spec, X, z, role)
        elif spec.pooling == "pooled":
            predictor = _fit_pooled(spec, X, z, role)
        elif spec.pooling == "pooled_id":
            predictor = _fit_pooled_id(spec, X, z, cluster, plan.q, role)
        else:  # adaptive
            local = _fit_local(spec, X, z, role)
            borrow = _fit_borrow(spec, X, z, cluster, plan.q, role)
            cal = role.calib_idx
            if cal.size == 0:
                raise ValueError(f"No calibration rows for cluster {role.cluster}, fold {role.fold}.")
            pw = ls_pooling_weight(
                z[cal],
                np.asarray(local.predict(X[cal])).ravel(),
                np.asarray(borrow.predict(X[cal])).ravel(),
            )
            predictor = MixturePredictor(local, borrow, pw.w)
            weight, mse_local, mse_borrow, mse_mix = pw.w, pw.mse_local, pw.mse_borrow, pw.mse_mixture

        out.predictions[role.eval_idx] = np.asarray(predictor.predict(X_eval)).ravel()
        out.diagnostics.append(NuisanceDiagnostics(
            name=spec.name, cluster=role.cluster, fold=role.fold, pooling=spec.pooling,
            weight=weight, n_eval=role.n_eval, n_calib=int(role.calib_idx.size),
            n_base_target=int(role.base_target_idx.size), n_base_other=int(role.base_other_idx.size),
            mse_local=mse_local, mse_borrow=mse_borrow, mse_mixture=mse_mix,
        ))
    return out
