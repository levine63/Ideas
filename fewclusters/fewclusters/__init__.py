"""
fewclusters
===========

Approximate randomization tests (ART) with cross-fitted, machine-learned
nuisance functions and a FIXED, SMALL number of clusters.

The method is the Cai, Canay, Kim and Shaikh (2023) weighted-score ART,
with the cluster scores built from Double/Debiased-ML residuals instead of
OLS residuals. The nuisances are fitted ONCE (cross-fitted within each
cluster, optionally borrowing from other clusters with an adaptively chosen
weight) and then held fixed for every sign transformation and every
hypothesised value of the treatment effect.

Module map (read in this order)
-------------------------------
folds.py      how each cluster's observations are split into evaluation,
              calibration and base-training roles (with optional buffers
              for serially dependent data).
learners.py   thin wrappers so that any scikit-learn style estimator can be
              used, plus the "cluster identity as a feature" transformer.
pooling.py    the clipped least-squares weight that mixes a local and a
              borrowing prediction (equation (7) of the note).
nuisance.py   runs the cross-fitting loop for one nuisance (m or ell) and
              returns out-of-fold predictions plus diagnostics.
scores.py     turns residuals into the per-cluster quantities
              Q_j, theta_j and the weighted score S_j(lambda) (eq. (2)-(3)).
art.py        the sign-group randomization test, p-values and confidence
              intervals by test inversion (eq. (4)); pure numpy.
model.py      ARTDML, the user-facing class that ties everything together.
simulate.py   data-generating processes for the simulation study.

Notation follows the note: clusters j = 1..q, observations i = 1..n_j,
outcome Y, treatment D, controls X, m_0j(x) = E[D|X=x], ell_0j(x) = E[Y|X=x].
"""

from .model import ARTDML, ARTDMLResult
from .art import (
    sign_group,
    art_pvalue,
    art_test,
    art_confint,
    attainable_size,
    ARTTestResult,
)
from .folds import FoldPlan, FoldRoles
from .nuisance import NuisanceSpec, crossfit_nuisance
from .scores import ClusterScores, cluster_scores
from .simulate import simulate_plm

__all__ = [
    "ARTDML",
    "ARTDMLResult",
    "sign_group",
    "art_pvalue",
    "art_test",
    "art_confint",
    "attainable_size",
    "ARTTestResult",
    "FoldPlan",
    "FoldRoles",
    "NuisanceSpec",
    "crossfit_nuisance",
    "ClusterScores",
    "cluster_scores",
    "simulate_plm",
]

__version__ = "0.1.0"
