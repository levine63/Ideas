"""
Monte Carlo driver for the simulation plan.

Reproducibility contract
    replication r uses data seed  seed + r  and fold/sign seed  seed + r
    for every method; learners are deterministic (polynomial least squares).
    Each method is FITTED ONCE per replication; the size p-value (at the true
    theta) and the power p-value (at theta - shift) both come from that one
    fit, exactly as the package is meant to be used.

A method is a callable (data, seed) -> object with pvalue(lam). The oracle
plugs in the true nuisances and is the benchmark for every other method.

Run:  PYTHONPATH=. python examples/monte_carlo.py --reps 300 --q 6 --n 400 \\
          --experiments baseline,asymmetry,known_m,skew,dependence
"""

from __future__ import annotations

import argparse
import time
from typing import Callable, Dict

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from fewclusters import ARTDML, attainable_size, simulate_plm
from fewclusters.art import art_pvalue, sign_group
from fewclusters.scores import cluster_scores
from fewclusters.simulate import lag1_autocorr, oracle_scores, skewed_gamma, symmetric_gamma


def poly_learner(degree: int = 2):
    return make_pipeline(PolynomialFeatures(degree, include_bias=False), LinearRegression())


# ---------------------------------------------------------------- methods
class Oracle:
    """ART with the true nuisances; fitted once, then pvalue(lam) is cheap."""

    def __init__(self, data: Dict, seed: int):
        cl = data["cluster"]
        labels = np.unique(cl)
        self.sc = cluster_scores(data["d"] - data["m0"], data["y"] - data["l0"], cl,
                                 np.ones(cl.size, bool), labels)
        self.signs, _ = sign_group(labels.size)

    def pvalue(self, lam: float) -> float:
        return art_pvalue(self.sc.S(lam), self.signs)


def artdml(pooling_m: str, pooling_l: str, n_folds: int = 5, known_m: bool = False,
           buffer: int = 0, contiguous: bool = False) -> Callable:
    def build(data: Dict, seed: int) -> ARTDML:
        model = ARTDML(learner_m=None if known_m else poly_learner(), learner_l=poly_learner(),
                       n_folds=n_folds, pooling_m=pooling_m, pooling_l=pooling_l, borrow="pooled_id",
                       buffer=buffer, contiguous=contiguous, random_state=seed)
        return model.fit(data["y"], data["d"], data["X"], data["cluster"],
                         m_known=data["m0"] if known_m else None)
    return build


# ---------------------------------------------------------------- runner
def run_experiment(name: str, dgp: Callable[[int], Dict], methods: Dict[str, Callable], reps: int,
                   alpha: float, shift: float, seed: int, q: int, power: bool = True) -> None:
    print(f"\n=== {name}: q={q}, alpha={alpha}, attainable size={attainable_size(q, alpha):.4f}, "
          f"reps={reps}" + (f", power shift={shift}" if power else ""))
    rej_size = {m: 0 for m in methods}
    rej_pow = {m: 0 for m in methods}
    ac = []
    t0 = time.time()
    for r in range(reps):
        data = dgp(seed + r)
        ac.append(lag1_autocorr(oracle_scores(data), data["cluster"]))
        for m, build in methods.items():
            fitted = build(data, seed + r)
            theta0 = data["theta"]
            rej_size[m] += fitted.pvalue(theta0) <= alpha
            if power:
                rej_pow[m] += fitted.pvalue(theta0 - shift) <= alpha
    print(f"  mean lag-1 autocorrelation of the oracle score: {np.mean(ac):.3f}")
    for m in methods:
        s = rej_size[m] / reps
        se = np.sqrt(max(s * (1 - s), 1e-9) / reps)
        line = f"  {m:34s} size={s:.4f} (MC se {se:.4f})"
        if power:
            line += f"   power={rej_pow[m] / reps:.4f}"
        print(line)
    print(f"  [{time.time() - t0:.1f}s]")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--q", type=int, default=6)
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--shift", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--experiments", type=str, default="baseline,asymmetry,known_m",
                    help="comma-separated subset of: baseline,asymmetry,known_m,skew,dependence")
    a = ap.parse_args()
    chosen = set(a.experiments.split(","))
    q, n = a.q, a.n
    run = lambda name, dgp, methods, power=True: run_experiment(
        name, dgp, methods, a.reps, a.alpha, a.shift, a.seed, q, power)

    if "baseline" in chosen:
        run("baseline: common nuisances", lambda s: simulate_plm(q=q, n_j=n, seed=s), {
            "oracle": Oracle,
            "local": artdml("local", "local"),
            "pooled_id": artdml("pooled_id", "pooled_id"),
            "adaptive": artdml("adaptive", "adaptive"),
        })

    if "asymmetry" in chosen:
        run("asymmetry: heterogeneous m (tau_m=1), common ell",
            lambda s: simulate_plm(q=q, n_j=n, tau_m=1.0, seed=s), {
                "oracle": Oracle,
                "local m, local ell": artdml("local", "local"),
                "pooled m, local ell": artdml("pooled", "local"),
                "adaptive m, adaptive ell": artdml("adaptive", "adaptive"),
            })
        run("asymmetry: common m, heterogeneous ell (tau_l=1)",
            lambda s: simulate_plm(q=q, n_j=n, tau_l=1.0, seed=s), {
                "oracle": Oracle,
                "local m, local ell": artdml("local", "local"),
                "local m, pooled ell": artdml("local", "pooled"),
                "adaptive m, adaptive ell": artdml("adaptive", "adaptive"),
            })

    if "known_m" in chosen:
        run("known propensity (Corollary 2): misspecified pooled ell",
            lambda s: simulate_plm(q=q, n_j=n, known_propensity=True, tau_l=1.5, seed=s), {
                "oracle": Oracle,
                "known m, local ell": artdml("local", "local", known_m=True),
                "known m, pooled ell": artdml("local", "pooled", known_m=True),
                "known m, adaptive ell": artdml("local", "adaptive", known_m=True),
            })

    if "skew" in chosen:
        for label, gfun in [("symmetric", symmetric_gamma), ("skewed", skewed_gamma)]:
            run(f"effect heterogeneity ({label} gamma_j), known m",
                lambda s, g=gfun: simulate_plm(q=q, n_j=n, known_propensity=True,
                                               gamma=g(q, np.random.default_rng(s)), seed=s), {
                    "oracle": Oracle,
                    "known m, local ell": artdml("local", "local", known_m=True),
                }, power=False)

    if "dependence" in chosen:
        sizes = np.round(np.geomspace(n / 2, 3 * n, q)).astype(int)   # unequal, ratio 6:1
        R = 3
        print(f"\n(dependence: R = {R}, cluster sizes {list(sizes)})")
        run(f"dependent oracle scores (R={R}), unequal clusters",
            lambda s: simulate_plm(q=q, n_j=sizes, dependence_R=R, dependence_share=0.9, seed=s), {
                "oracle": Oracle,
                "local, random folds (no buffer)": artdml("local", "local"),
                "local, contiguous, no buffer": artdml("local", "local", contiguous=True),
                f"local, contiguous, buffer={R}": artdml("local", "local", buffer=R),
            })


if __name__ == "__main__":
    main()
