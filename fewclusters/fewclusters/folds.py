"""
folds.py -- how observations are assigned to roles inside each cluster.

The note (Section 2) keeps three uses of the data separate:

    base training  -> fits the candidate nuisance models (local and borrowing)
    calibration    -> chooses the mixing weight between the two candidates
    evaluation     -> computes residuals, hence the cluster score

For each cluster j and each evaluation fold k (k = 0..K-1):

    evaluation   = fold k of cluster j
    calibration  = fold (k+1) mod K of cluster j        (only if adaptive pooling)
    base target  = the remaining folds of cluster j
    base other   = observations of the OTHER clusters, optionally excluding
                   their own fold k ("exclude_same_fold", the convenient design
                   that keeps every evaluation observation out of every model
                   that scores a same-numbered fold anywhere)

Dependence (Corollary 1): if `buffer > 0` the folds are contiguous blocks in
the order the rows appear within the cluster, and observations within
`buffer` positions of the evaluation block (or of the calibration block)
are dropped from the roles that must be independent of it. In this rotating
design every row is still scored exactly once (in its own fold); the buffer
only restricts which rows may train or calibrate the model that scores a
given block. `scored` is kept as an attribute for generality and is all
True here.

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
        Cluster id of each row, coded 0..q-1.
    n_folds : int
        K. Needs K >= 2, and K >= 3 when a calibration fold is used.
    use_calibration : bool
        Reserve fold (k+1) mod K of the target cluster as calibration data.
    exclude_same_fold : bool
        When building `base_other_idx`, drop the other clusters' fold k.
    buffer : int
        Number of positions on each side of a block to drop (0 = iid design).
    contiguous : bool
        Use contiguous blocks (required when buffer > 0). If False, folds are
        a random partition of each cluster.
    random_state : int or Generator
        Only used for the random partition.
    """

    cluster: np.ndarray
    n_folds: int = 5
    use_calibration: bool = True
    exclude_same_fold: bool = True
    buffer: int = 0
    contiguous: bool = False
    random_state: Optional[object] = None
    roles: List[FoldRoles] = field(init=False, default_factory=list)
    fold_of_row: np.ndarray = field(init=False)
    scored: np.ndarray = field(init=False)   # bool (n,), False for buffer rows

    def __post_init__(self) -> None:
        self.cluster = np.asarray(self.cluster)
        self.q = int(self.cluster.max()) + 1
        n = self.cluster.size
        K = self.n_folds
        if K < 2:
            raise ValueError("n_folds must be at least 2.")
        if self.use_calibration and K < 3:
            raise ValueError("Adaptive pooling needs n_folds >= 3 "
                             "(evaluation, calibration and base training must be distinct).")
        if self.buffer > 0 and not self.contiguous:
            raise ValueError("buffer > 0 requires contiguous=True.")
        rng = np.random.default_rng(self.random_state)

        # 1. fold label for every row, assigned cluster by cluster
        self.fold_of_row = np.empty(n, dtype=int)
        position_in_cluster = np.empty(n, dtype=int)
        for j in range(self.q):
            rows = np.flatnonzero(self.cluster == j)
            n_j = rows.size
            if n_j < K:
                raise ValueError(f"Cluster {j} has {n_j} rows, fewer than n_folds={K}.")
            pos = np.arange(n_j)
            if self.contiguous:
                folds_j = (pos * K) // n_j
            else:
                perm = rng.permutation(n_j)
                folds_j = np.empty(n_j, dtype=int)
                folds_j[perm] = (pos * K) // n_j
            self.fold_of_row[rows] = folds_j
            position_in_cluster[rows] = pos

        # 2. roles for each (cluster, fold)
        self.scored = np.zeros(n, dtype=bool)
        for j in range(self.q):
            rows = np.flatnonzero(self.cluster == j)
            pos = position_in_cluster[rows]
            folds_j = self.fold_of_row[rows]
            others = np.flatnonzero(self.cluster != j)
            for k in range(K):
                in_eval = folds_j == k
                near_eval = self._near(pos, in_eval)
                if self.use_calibration:
                    kc = (k + 1) % K
                    in_calib = (folds_j == kc) & ~near_eval
                    near_calib = self._near(pos, folds_j == kc)
                else:
                    in_calib = np.zeros_like(in_eval)
                    near_calib = np.zeros_like(in_eval)
                in_base = ~in_eval & ~in_calib & ~near_eval & ~near_calib
                if self.use_calibration:
                    in_base &= folds_j != (k + 1) % K
                if self.exclude_same_fold:
                    base_other = others[self.fold_of_row[others] != k]
                else:
                    base_other = others
                self.roles.append(FoldRoles(
                    cluster=j,
                    fold=k,
                    eval_idx=rows[in_eval],
                    calib_idx=rows[in_calib],
                    base_target_idx=rows[in_base],
                    base_other_idx=base_other,
                ))
                self.scored[rows[in_eval]] = True

    def _near(self, pos: np.ndarray, in_block: np.ndarray) -> np.ndarray:
        """Rows within `buffer` positions of a contiguous block, excluding the block."""
        if self.buffer == 0 or not in_block.any():
            return np.zeros_like(in_block)
        lo, hi = pos[in_block].min(), pos[in_block].max()
        near = (pos >= lo - self.buffer) & (pos <= hi + self.buffer)
        return near & ~in_block

    def describe(self) -> str:
        lines = [f"FoldPlan: q={self.q} clusters, K={self.n_folds}, "
                 f"calibration={self.use_calibration}, buffer={self.buffer}, "
                 f"contiguous={self.contiguous}"]
        for r in self.roles:
            lines.append(f"  cluster {r.cluster} fold {r.fold}: eval={r.n_eval} "
                         f"calib={r.calib_idx.size} base_target={r.base_target_idx.size} "
                         f"base_other={r.base_other_idx.size}")
        return "\n".join(lines)
