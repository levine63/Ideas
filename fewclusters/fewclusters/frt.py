"""
frt.py -- stratified Fisher randomization test (FRT) with ML covariate
adjustment, and a placebo tuner that chooses the adjustment and the site
weights from fake re-randomizations of the known design.

When to use this instead of ARTDML
----------------------------------
When treatment was randomized at the INDIVIDUAL level within sites with
KNOWN assignment probabilities, inference does not need site-level
clustering: the score terms (D_i - p_i) e_i are uncorrelated across people
even if outcomes are correlated within a site. The randomization test below
is then exact in finite samples under the sharp null of a constant effect,
needs no normal approximation, has no 2^(q-1) resolution floor, and lets a
10-person site contribute its own re-randomizations. ARTDML remains the
tool for cluster-level or unknown assignment, or for inference that must
generalize across sites with site-varying effects.

The test of H0: Y_i(1) - Y_i(0) = lam for all i
-----------------------------------------------
1. Null-adjusted outcome R = Y - lam D. Under H0, R does not depend on D.
2. Residualize R on X WITHOUT using D (Rosenbaum 2002): e = R - g_hat(X),
   g_hat cross-fitted within sites, with local / pooled / adaptive borrowing
   across sites (reusing nuisance.py). e is a function of (R, X) only.
3. Per-site effect estimates tau_j = sum_{i in j} (D_i - p_i) e_i / Q_j with
   Q_j = sum_{i in j} p_i (1 - p_i), and the statistic
   T(D) = | sum_j w_j tau_j | = | (D - p) @ a |, a_i = w_j e_i / Q_j,
   with site weights w (sum 1) computed from e only:
       "equal"   w_j = 1/S
       "size"    w_j proportional to n_j
       "invvar"  w_j proportional to 1 / Var_design(tau_j | e)
                 = Q_j^2 / sum_{i in j} p_i (1 - p_i) e_i^2
4. p-value = (1 + #{b : |T(D*_b)| >= |T(D)|}) / (B + 1), D*_b drawn from the
   design. Exact (finite-sample valid) for any choice of adjustment and
   weights that is a function of (R, X, design) only.

Placebo tuning (the "fake treatment" idea)
------------------------------------------
Choose (adjustment, weights) by simulated power on the same data: draw fake
treatments D' from the design, add a known effect delta, R' = R + delta D',
and record how often each configuration rejects. Because E[R' | X] =
E[R | X] + delta p(X), the adjusted placebo residual is e + delta (D' - p):
no refitting per draw or per delta. The tuner only ever sees (R, X, design),
never the real D, so the selected configuration is ancillary under H0 and
the final test stays exact. (The tuner's power estimate for the chosen
configuration is optimistic; that does not affect validity.)

Scope: the sharp null (constant effect). With individual effect
heterogeneity the unstudentized FRT tests the sharp null, not the average
effect; a studentized version (Wu & Ding 2021) is future work. Confidence
intervals by inversion are not implemented yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .folds import FoldPlan
from .nuisance import NuisanceSpec, crossfit_nuisance

WEIGHT_RULES: Tuple[str, ...] = ("equal", "size", "invvar")
DEFAULT_ADJUSTMENTS: Tuple[str, ...] = ("site_mean", "local", "pooled_id", "adaptive", "adaptive_shrunk")


# =========================================================================== design
@dataclass
class Design:
    """
    Known individual-level assignment within strata (sites).

    kind = "bernoulli": D_i ~ Bernoulli(p_i) independently.
    kind = "complete" : exactly n_treated[s] treated in stratum s, all subsets
                        equally likely; p_i = n_treated[s] / n_s.
    """

    strata: np.ndarray
    p: Optional[np.ndarray] = None
    kind: str = "bernoulli"
    n_treated: Optional[np.ndarray] = None

    def __post_init__(self) -> None:
        self.strata = np.asarray(self.strata).astype(int).ravel()
        n = self.strata.size
        self.S = int(self.strata.max()) + 1
        self.n_s = np.bincount(self.strata, minlength=self.S)
        if np.any(self.n_s == 0):
            raise ValueError("Strata must be coded 0..S-1 with no empty stratum.")
        if self.kind == "complete":
            if self.n_treated is None:
                raise ValueError("A complete design needs n_treated per stratum.")
            self.n_treated = np.asarray(self.n_treated, dtype=int)
            if np.any((self.n_treated <= 0) | (self.n_treated >= self.n_s)):
                raise ValueError("Each stratum needs at least one treated and one control unit.")
            self.p = (self.n_treated / self.n_s)[self.strata]
        elif self.kind == "bernoulli":
            if self.p is None:
                raise ValueError("A Bernoulli design needs p.")
            self.p = np.asarray(self.p, dtype=float).ravel()
            if self.p.size != n or np.any((self.p <= 0) | (self.p >= 1)) or not np.all(np.isfinite(self.p)):
                raise ValueError("p must have one entry per unit, strictly between 0 and 1.")
        else:
            raise ValueError("kind must be 'bernoulli' or 'complete'.")
        self.var_d = self.p * (1 - self.p)
        self.Q = np.bincount(self.strata, weights=self.var_d, minlength=self.S)
        self._onehot = np.zeros((n, self.S))
        self._onehot[np.arange(n), self.strata] = 1.0

    @property
    def n(self) -> int:
        return int(self.strata.size)

    def stratum_sums(self, v: np.ndarray) -> np.ndarray:
        """Sum v over each stratum; v is (n,) or (B, n) -> (S,) or (B, S)."""
        return v @ self._onehot

    def draw(self, rng: np.random.Generator, B: int) -> np.ndarray:
        """B independent assignments from the design, as a (B, n) float 0/1 array."""
        if self.kind == "bernoulli":
            return (rng.random((B, self.n)) < self.p).astype(float)
        out = np.zeros((B, self.n))
        for s in range(self.S):
            rows = np.flatnonzero(self.strata == s)
            keys = rng.random((B, rows.size))
            ranks = np.argsort(np.argsort(keys, axis=1), axis=1)
            out[:, rows] = (ranks < self.n_treated[s]).astype(float)
        return out


# =========================================================================== statistic
def site_weights(e: np.ndarray, design: Design, rule: str) -> np.ndarray:
    """Site weights (sum 1) from residuals e of shape (n,) or (B, n)."""
    two_d = e.ndim == 2
    B = e.shape[0] if two_d else 1
    if rule == "equal":
        w = np.ones((B, design.S))
    elif rule == "size":
        w = np.tile(design.n_s.astype(float), (B, 1))
    elif rule == "invvar":
        v = design.stratum_sums(design.var_d * np.atleast_2d(e) ** 2) / design.Q ** 2
        v = np.maximum(v, 1e-12 * max(float(np.max(v)), 1e-300))
        w = 1.0 / v
    else:
        raise ValueError(f"Unknown weight rule {rule!r}; choose from {WEIGHT_RULES}.")
    w = w / w.sum(axis=1, keepdims=True)
    return w if two_d else w[0]


def linear_coefficients(e: np.ndarray, design: Design, rule: str) -> np.ndarray:
    """a with T(D) = (D - p) @ a = sum_j w_j tau_j; same shape as e."""
    w = site_weights(e, design, rule)
    if e.ndim == 2:
        return w[:, design.strata] * e / design.Q[design.strata]
    return w[design.strata] * e / design.Q[design.strata]


def frt_pvalue(a: np.ndarray, d: np.ndarray, design: Design, null_draws: np.ndarray) -> float:
    """Monte Carlo randomization p-value (1 + #{|T*| >= |T|}) / (B + 1)."""
    t_obs = abs(float((d - design.p) @ a))
    t_null = np.abs((null_draws - design.p) @ a)
    tol = 1e-12 * max(t_obs, 1e-300)
    return float((1 + np.sum(t_null >= t_obs - tol)) / (null_draws.shape[0] + 1))


# =========================================================================== adjustment
def residualize(R: np.ndarray, X: np.ndarray, strata: np.ndarray, learner: Any,
                adjustments: Sequence[str] = DEFAULT_ADJUSTMENTS, n_folds: int = 5,
                random_state: Optional[int] = None) -> Dict[str, np.ndarray]:
    """
    Residuals e = R - g_hat(X) for each adjustment. Uses (R, X, strata) only;
    the treatment is deliberately not an argument.

      site_mean        R minus its site mean (no covariates)
      local            learner cross-fitted within each site
      pooled_id        learner on all sites, site identity as features
      adaptive         local/pooled_id mixture, weight chosen on calibration folds
      adaptive_shrunk  as adaptive, weight shrunk toward borrowing (kappa = 20),
                       local fit skipped below 20 training rows
    """
    R = np.asarray(R, dtype=float)
    X = np.asarray(X, dtype=float)
    strata = np.asarray(strata).astype(int)
    out: Dict[str, np.ndarray] = {}
    plans: Dict[bool, FoldPlan] = {}

    def plan(calib: bool) -> FoldPlan:
        if calib not in plans:
            plans[calib] = FoldPlan(strata, n_folds=n_folds, use_calibration=calib, random_state=random_state)
        return plans[calib]

    for name in adjustments:
        if name == "site_mean":
            means = np.bincount(strata, weights=R) / np.bincount(strata)
            out[name] = R - means[strata]
            continue
        if name == "local":
            spec, calib = NuisanceSpec(learner, "local", name="g"), False
        elif name == "pooled_id":
            spec, calib = NuisanceSpec(learner, "pooled_id", name="g"), False
        elif name == "adaptive":
            spec, calib = NuisanceSpec(learner, "adaptive", "pooled_id", name="g"), True
        elif name == "adaptive_shrunk":
            spec, calib = NuisanceSpec(learner, "adaptive", "pooled_id", name="g",
                                       shrink_kappa=20.0, min_local_train=20), True
        else:
            raise ValueError(f"Unknown adjustment {name!r}.")
        out[name] = R - crossfit_nuisance(R, X, strata, plan(calib), spec).predictions
    return out


# =========================================================================== placebo tuner
@dataclass
class TuneResult:
    choice: Tuple[str, str]
    delta: float
    table: List[Dict[str, Any]] = field(default_factory=list)   # adj, weights, power, mean_p, sd

    def __str__(self) -> str:
        lines = [f"placebo tuning at delta = {self.delta:.4g}; chosen {self.choice}"]
        for r in sorted(self.table, key=lambda r: (-r["power"], r["mean_p"])):
            lines.append(f"  {r['adjustment']:16s} {r['weights']:7s} power={r['power']:.3f} "
                         f"mean p={r['mean_p']:.3f} null sd={r['sd']:.4g}")
        return "\n".join(lines)


def placebo_tune(residuals: Dict[str, np.ndarray], design: Design, weight_rules: Sequence[str] = WEIGHT_RULES,
                 alpha: float = 0.05, delta: Optional[float] = None, B_tune: int = 100, B_null: int = 200,
                 rng: Optional[np.random.Generator] = None, delta_multiple: float = 2.0) -> TuneResult:
    """
    Simulated power of each (adjustment, weights) on placebo data built from
    fake assignments D' ~ design and a known effect delta. Takes residuals
    and the design only; never the real treatment.

    delta defaults to delta_multiple x the smallest design-based null standard
    deviation of T among the configurations, so the best one has moderate
    (not saturated) power and the comparison is informative.
    """
    rng = np.random.default_rng(rng)
    configs = [(adj, wr) for adj in residuals for wr in weight_rules]
    sds = {}
    for adj, wr in configs:
        a = linear_coefficients(residuals[adj], design, wr)
        sds[(adj, wr)] = float(np.sqrt(np.sum(design.var_d * a ** 2)))
    if delta is None:
        delta = delta_multiple * min(sds.values())
    Dp = design.draw(rng, B_tune)
    Zp = Dp - design.p
    Z0 = design.draw(rng, B_null) - design.p
    table = []
    for adj, wr in configs:
        E = residuals[adj][None, :] + delta * Zp            # placebo residuals, one row per fake world
        A = linear_coefficients(E, design, wr)              # (B_tune, n)
        t_obs = np.abs(np.sum(Zp * A, axis=1))              # (B_tune,)
        t_null = np.abs(Z0 @ A.T)                           # (B_null, B_tune)
        pv = (1 + np.sum(t_null >= t_obs[None, :] * (1 - 1e-12), axis=0)) / (B_null + 1)
        table.append({"adjustment": adj, "weights": wr, "power": float(np.mean(pv <= alpha)),
                      "mean_p": float(np.mean(pv)), "sd": sds[(adj, wr)]})
    best = min(table, key=lambda r: (-r["power"], r["mean_p"]))
    return TuneResult(choice=(best["adjustment"], best["weights"]), delta=float(delta), table=table)


# =========================================================================== user-facing test
@dataclass
class FRTResult:
    lam: float
    p_value: float
    estimate: float                      # sum_j w_j tau_j for the chosen configuration, + lam
    choice: Tuple[str, str]
    B: int
    tuning: Optional[TuneResult]
    pvalues_all: Dict[Tuple[str, str], float]   # diagnostics ONLY: picking the smallest is invalid

    def __str__(self) -> str:
        return (f"Stratified FRT of effect = {self.lam:g}: p = {self.p_value:.4f} (B = {self.B}), "
                f"estimate = {self.estimate:.4g}, configuration = {self.choice}")


class StratifiedFRT:
    """
    Exact randomization test for individually randomized multi-site data.

    Parameters
    ----------
    learner : regressor with fit/predict, for g(x) = E[Y - lam D | X]
    adjustments : subset of DEFAULT_ADJUSTMENTS to consider
    weight_rules : subset of WEIGHT_RULES to consider
    tune : bool
        Choose (adjustment, weights) by placebo power. If False, use `fixed`.
    fixed : (adjustment, weights) used when tune=False
    n_folds : folds for cross-fitting g within sites
    B : null draws for the reported p-value
    B_tune, B_null_tune : placebo worlds and null draws per world in tuning
    delta : placebo effect size (default: data-scaled, see placebo_tune)
    alpha_tune : level at which placebo power is measured
    random_state : int or None
    """

    def __init__(self, learner: Any = None, adjustments: Sequence[str] = DEFAULT_ADJUSTMENTS,
                 weight_rules: Sequence[str] = WEIGHT_RULES, tune: bool = True,
                 fixed: Tuple[str, str] = ("adaptive_shrunk", "invvar"), n_folds: int = 5,
                 B: int = 1000, B_tune: int = 100, B_null_tune: int = 200, delta: Optional[float] = None,
                 alpha_tune: float = 0.05, random_state: Optional[int] = None):
        self.learner = learner
        self.adjustments = tuple(adjustments)
        self.weight_rules = tuple(weight_rules)
        self.tune = tune
        self.fixed = fixed
        self.n_folds = n_folds
        self.B = B
        self.B_tune = B_tune
        self.B_null_tune = B_null_tune
        self.delta = delta
        self.alpha_tune = alpha_tune
        self.random_state = random_state
        needs_learner = any(a != "site_mean" for a in self.adjustments) or fixed[0] != "site_mean"
        if needs_learner and learner is None:
            raise ValueError("A learner is required unless only 'site_mean' adjustment is used.")
        if not tune and (fixed[0] not in self.adjustments or fixed[1] not in self.weight_rules):
            raise ValueError("fixed configuration must be among adjustments x weight_rules.")

    def test(self, y: np.ndarray, d: np.ndarray, X: np.ndarray, strata: np.ndarray,
             p: Optional[np.ndarray] = None, lam: float = 0.0, design: str = "bernoulli") -> FRTResult:
        """
        Test H0: every unit's effect equals lam.

        design="bernoulli" needs p (known assignment probabilities). design=
        "complete" uses the realized number treated per stratum (fixed by a
        complete-randomization design) and ignores p.
        """
        y = np.asarray(y, dtype=float).ravel()
        d = np.asarray(d, dtype=float).ravel()
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X[:, None]
        labels, codes = np.unique(np.asarray(strata).ravel(), return_inverse=True)
        n = y.size
        if not (d.size == n and X.shape[0] == n and codes.size == n):
            raise ValueError("y, d, X and strata must have the same number of rows.")
        for name, arr in (("y", y), ("d", d), ("X", X)):
            if not np.all(np.isfinite(arr)):
                raise ValueError(f"{name} contains missing or non-finite values.")
        if not np.all(np.isin(d, [0.0, 1.0])):
            raise ValueError("The randomization test needs a binary 0/1 treatment.")
        if design == "complete":
            dz = Design(codes, kind="complete", n_treated=np.bincount(codes, weights=d).astype(int))
        else:
            dz = Design(codes, p=p, kind="bernoulli")

        ss = np.random.SeedSequence(self.random_state)
        rng_tune, rng_test = (np.random.default_rng(s) for s in ss.spawn(2))
        R = y - lam * d                                         # null-adjusted outcome
        adjustments = self.adjustments if self.tune else (self.fixed[0],)
        res = residualize(R, X, codes, self.learner, adjustments, self.n_folds, self.random_state)

        tuning = None
        if self.tune:
            tuning = placebo_tune(res, dz, self.weight_rules, self.alpha_tune, self.delta,
                                  self.B_tune, self.B_null_tune, rng_tune)
            choice = tuning.choice
        else:
            choice = self.fixed

        draws = dz.draw(rng_test, self.B)
        pvals: Dict[Tuple[str, str], float] = {}
        rules = self.weight_rules if self.tune else (self.fixed[1],)
        for adj in res:
            for wr in rules:
                a = linear_coefficients(res[adj], dz, wr)
                pvals[(adj, wr)] = frt_pvalue(a, d, dz, draws)
        a = linear_coefficients(res[choice[0]], dz, choice[1])
        estimate = lam + float((d - dz.p) @ a)
        return FRTResult(lam=float(lam), p_value=pvals[choice], estimate=estimate, choice=choice,
                         B=self.B, tuning=tuning, pvalues_all=pvals)
