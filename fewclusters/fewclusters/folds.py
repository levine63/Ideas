"""
folds.py -- how observations are assigned to roles inside each cluster.

The note (Section 2) keeps three uses of the data separate:

    base training  -> fits the candidate nuisance models (local and borrowing)
    calibration    -> chooses the mixing weight between the two candidates
    evaluation     -> computes residuals, hence the cluster score

For each cluster j and each evaluation fold k (k = 0..K-1):

    evaluation   = fold k of cluster j
    calibration  = one of two designs (only if use_calibration):
                     calib_fraction=None : fold (k+1) mod K of cluster j  (needs K >= 3)
                     calib_fraction=f    : a random f-share of cluster j's rows
                                           outside fold k, redrawn for each k (K >= 2)
    base target  = cluster j's remaining rows
    base other   = the OTHER clusters' rows, minus their own fold k when
                   exclude_same_fold=True (so a row never trains a model that
                   scores a same-numbered fold anywhere)

Fold labels come from `fold_ids` if supplied (full reproducibility, and
the hook used by the metamorphic tests), otherwise from a per-cluster
random partition seeded by (random_state, cluster index), or from
contiguous blocks in row order.

Dependence (Corollary 1): with `buffer > 0` folds are contiguous blocks in
the order rows appear within the cluster, and rows within `buffer`
positions of the evaluation block (or of the calibration block) are kept
out of the roles that must be independent of it. Every row is still scored
exactly once, in its own fold; the buffer only restricts which rows may
train or calibrate the model that scores a given block.

Everything here is index bookkeeping; nothing is fitted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


@dataclass
class FoldRoles:
    """Row indices (into the full sample) for one (cluster, fold) pair."""

    cluster: int
    fold: int
    eval_idx: np.ndarray
    calib_idx: np.ndarray          # empty array if no calibration is used
    base_target_idx: np.ndarray    # same cluster, outside eval/calib/buffers
    base_other_idx: np.ndarray     # other clusters (possibly minus their fold k)

    @property
    def n_eval(self) -> int:
        return int(self.eval_idx.size)


@dataclass
class FoldPlan:
    """
    Complete role assignment for every (cluster, fold).

    Parameters
    ----------
    cluster : int array (n,)
        Cluster code of each row, 0..q-1.
    n_folds : int
        K >= 2. With fold-based calibration (calib_fraction=None) K >= 3.
    use_calibration : bool
        Reserve calibration rows in the target cluster.
    calib_fraction : float in (0, 1) or None
        Share of each cluster used for calibration when scoring a fold. None
        means "use the next fold". Not available with contiguous folds.
    exclude_same_fold : bool
        When building `base_other_idx`, drop the other clusters' fold k.
    buffer : int
        Positions dropped around evaluation/calibration blocks (0 = iid design).
    contiguous : bool
        Contiguous folds (required when buffer > 0).
    fold_ids : int array (n,) or None
        Explicit fold label of each row, 0..K-1; every cluster must contain
        every fold. Overrides random/contiguous assignment.
    random_state : int, SeedSequence or None
    """

    cluster: np.ndarray
    n_folds: int = 5
    use_calibration: bool = True
    calib_fraction: Optional[float] = None
    exclude_same_fold: bool = True
    buffer: int = 0
    contiguous: bool = False
    fold_ids: Optional[np.ndarray] = None
    random_state: Optional[object] = None
    roles: List[FoldRoles] = field(init=False, default_factory=list)
    fold_of_row: np.ndarray = field(init=False)
    scored: np.ndarray = field(init=False)   # bool (n,); all True in this rotating design

    def __post_init__(self) -> None:
        self._validate()
        self.cluster = np.asarray(self.cluster)
        self.q = int(self.cluster.max()) + 1
        n = self.cluster.size
        K = self.n_folds
        seeds = np.random.SeedSequence(self.random_state).spawn(self.q)

        # 1. fold label and within-cluster position of every row
        self.fold_of_row = np.empty(n, dtype=int)
        position = np.empty(n, dtype=int)
        for j in range(self.q):
            rows = np.flatnonzero(self.cluster == j)
            n_j = rows.size
            if n_j < K:
                raise ValueError(f"Cluster {j} has {n_j} rows, fewer than n_folds={K}.")
            pos = np.arange(n_j)
            position[rows] = pos
            if self.fold_ids is not None:
                f = np.asarray(self.fold_ids)[rows].astype(int)
                if set(np.unique(f)) != set(range(K)):
                    raise ValueError(f"fold_ids for cluster {j} must contain every fold 0..{K - 1}.")
                self.fold_of_row[rows] = f
            elif self.contiguous:
                self.fold_of_row[rows] = (pos * K) // n_j
            else:
                perm = np.random.default_rng(seeds[j]).permutation(n_j)
                f = np.empty(n_j, dtype=int)
                f[perm] = (pos * K) // n_j
                self.fold_of_row[rows] = f

        # 2. roles for each (cluster, fold)
        self.scored = np.zeros(n, dtype=bool)
        for j in range(self.q):
            rows = np.flatnonzero(self.cluster == j)
            pos = position[rows]
            folds_j = self.fold_of_row[rows]
            others = np.flatnonzero(self.cluster != j)
            calib_rng = np.random.default_rng(seeds[j].spawn(1)[0])
            for k in range(K):
                in_eval = folds_j == k
                near_eval = self._near(pos, in_eval)
                in_calib = np.zeros_like(in_eval)
                near_calib = np.zeros_like(in_eval)
                if self.use_calibration:
                    if self.calib_fraction is None:
                        in_calib = (folds_j == (k + 1) % K) & ~near_eval
                        near_calib = self._near(pos, folds_j == (k + 1) % K)
                    else:
                        candidates = np.flatnonzero(~in_eval & ~near_eval)
                        m = int(round(self.calib_fraction * rows.size))
                        m = min(max(m, 1), candidates.size - 1)
                        in_calib[calib_rng.choice(candidates, size=m, replace=False)] = True
                in_base = ~in_eval & ~in_calib & ~near_eval & ~near_calib
                if self.use_calibration and self.calib_fraction is None:
                    in_base &= folds_j != (k + 1) % K
                base_other = others[self.fold_of_row[others] != k] if self.exclude_same_fold else others
                self.roles.append(FoldRoles(
                    cluster=j, fold=k,
                    eval_idx=rows[in_eval], calib_idx=rows[in_calib],
                    base_target_idx=rows[in_base], base_other_idx=base_other,
                ))
                self.scored[rows[in_eval]] = True

    def _validate(self) -> None:
        K = self.n_folds
        if not isinstance(K, (int, np.integer)) or K < 2:
            raise ValueError("n_folds must be an integer >= 2.")
        if self.use_calibration and self.calib_fraction is None and K < 3:
            raise ValueError("Fold-based calibration needs n_folds >= 3 (evaluation, calibration and "
                             "base training must be distinct); or set calib_fraction.")
        if self.calib_fraction is not None:
            if not (0.0 < self.calib_fraction < 1.0):
                raise ValueError("calib_fraction must lie strictly between 0 and 1.")
            if self.contiguous or self.buffer > 0:
                raise ValueError("calib_fraction is not available with contiguous/buffered folds; "
                                 "use fold-based calibration (calib_fraction=None).")
        if self.buffer < 0:
            raise ValueError("buffer must be non-negative.")
        if self.buffer > 0 and not self.contiguous:
            raise ValueError("buffer > 0 requires contiguous=True.")
        if self.fold_ids is not None and (self.contiguous or self.buffer > 0):
            raise ValueError("fold_ids cannot be combined with contiguous/buffered folds.")

    def _near(self, pos: np.ndarray, in_block: np.ndarray) -> np.ndarray:
        """Rows within `buffer` positions of a contiguous block, excluding the block."""
        if self.buffer == 0 or not in_block.any():
            return np.zeros_like(in_block)
        lo, hi = pos[in_block].min(), pos[in_block].max()
        near = (pos >= lo - self.buffer) & (pos <= hi + self.buffer)
        return near & ~in_block

    def describe(self) -> str:
        lines = [f"FoldPlan: q={self.q} clusters, K={self.n_folds}, calibration={self.use_calibration}, "
                 f"calib_fraction={self.calib_fraction}, buffer={self.buffer}, contiguous={self.contiguous}"]
        for r in self.roles:
            lines.append(f"  cluster {r.cluster} fold {r.fold}: eval={r.n_eval} calib={r.calib_idx.size} "
                         f"base_target={r.base_target_idx.size} base_other={r.base_other_idx.size}")
        return "\n".join(lines)
