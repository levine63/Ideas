"""
Monte Carlo driver for the simulation plan.

Each experiment is a dict of simulate_plm arguments plus a list of methods.
A method is a callable (data, rng) -> p-value at the true theta (size) or at
theta + shift (power). The oracle method plugs in the true nuisances and is
the benchmark every other method is compared with.

Run:  python examples/monte_carlo.py --reps 300 --q 6 --n 400
"""

from __future__ import annotations

import argparse
import time
from typing import Callable, Dict, List

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from fewclusters import ARTDML, attainable_size, simulate_plm
from fewclusters.art import art_pvalue, sign_group
from fewclusters.scores import cluster_scores


def poly_learner(degree: int = 2):
    return make_pipeline(PolynomialFeatures(degree, include_bias=False), LinearRegression())


# ---------------------------------------------------------------- methods
def oracle(data: Dict, lam: float) -> float:
    cl = data["cluster"]
    labels = np.unique(cl)
    sc = cluster_scores(data["d"] - data["m0"], data["y"] - data["l0"], cl, np.ones(cl.size, bool), labels)
    signs, _ = sign_group(labels.size)
    return art_pvalue(sc.S(lam), signs)


def make_artdml(pooling_m: str, pooling_l: str, n_folds: int = 5, known_m: bool = False) -> Callable:
    def run(data: Dict, lam: float) -> float:
        model = ARTDML(learner_m=None if known_m else poly_learner(), learner_l=poly_learner(),
                       n_folds=n_folds, pooling_m=pooling_m, pooling_l=pooling_l, borrow="pooled_id")
        model.fit(data["y"], data["d"], data["X"], data["cluster"], m_known=data["m0"] if known_m else None)
        return model.pvalue(lam)
    return run


# ---------------------------------------------------------------- experiment runner
def run_experiment(name: str, dgp_kwargs: Dict, methods: Dict[str, Callable], reps: int,
                   alpha: float, shift: float, seed: int) -> None:
    q = dgp_kwargs["q"]
    print(f"\n=== {name}: q={q}, alpha={alpha}, attainable size={attainable_size(q, alpha):.4f}, "
          f"reps={reps}, power shift={shift}")
    rej_size = {m: 0 for m in methods}
    rej_pow = {m: 0 for m in methods}
    t0 = time.time()
    for r in range(reps):
        data = simulate_plm(seed=seed + r, **dgp_kwargs)
        for m, fn in methods.items():
            rej_size[m] += fn(data, data["theta"]) <= alpha
            rej_pow[m] += fn(data, data["theta"] - shift) <= alpha
    for m in methods:
        s, p = rej_size[m] / reps, rej_pow[m] / reps
        se = np.sqrt(max(s * (1 - s), 1e-9) / reps)
        print(f"  {m:28s} size={s:.4f} (MC se {se:.4f})   power={p:.4f}")
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
                    help="comma-separated subset of: baseline,asymmetry,known_m,skew")
    args = ap.parse_args()
    chosen = set(args.experiments.split(","))
    base = dict(q=args.q, n_j=args.n)

    if "baseline" in chosen:
        run_experiment("baseline: common nuisances", dict(base, tau_m=0.0, tau_l=0.0), {
            "oracle": oracle,
            "local": make_artdml("local", "local"),
            "pooled_id": make_artdml("pooled_id", "pooled_id"),
            "adaptive": make_artdml("adaptive", "adaptive"),
        }, args.reps, args.alpha, args.shift, args.seed)

    if "asymmetry" in chosen:
        run_experiment("asymmetry: heterogeneous m (tau_m=1), common ell",
                       dict(base, tau_m=1.0, tau_l=0.0), {
            "oracle": oracle,
            "local m, local ell": make_artdml("local", "local"),
            "pooled m, local ell": make_artdml("pooled", "local"),
            "adaptive m, adaptive ell": make_artdml("adaptive", "adaptive"),
        }, args.reps, args.alpha, args.shift, args.seed)
        run_experiment("asymmetry: common m, heterogeneous ell (tau_l=1)",
                       dict(base, tau_m=0.0, tau_l=1.0), {
            "oracle": oracle,
            "local m, local ell": make_artdml("local", "local"),
            "local m, pooled ell": make_artdml("local", "pooled"),
            "adaptive m, adaptive ell": make_artdml("adaptive", "adaptive"),
        }, args.reps, args.alpha, args.shift, args.seed)

    if "known_m" in chosen:
        run_experiment("known propensity (Corollary 2): misspecified pooled ell is still valid",
                       dict(base, known_propensity=True, tau_l=1.5), {
            "oracle": oracle,
            "known m, local ell": make_artdml("local", "local", known_m=True),
            "known m, pooled ell": make_artdml("local", "pooled", known_m=True),
            "known m, adaptive ell": make_artdml("local", "adaptive", known_m=True),
        }, args.reps, args.alpha, args.shift, args.seed)

    if "skew" in chosen:
        from fewclusters.simulate import skewed_gamma, symmetric_gamma
        rng = np.random.default_rng(args.seed)
        for label, gfun in [("symmetric", symmetric_gamma), ("skewed", skewed_gamma)]:
            kw = dict(base, known_propensity=True)
            methods = {"oracle": oracle, "known m, local ell": make_artdml("local", "local", known_m=True)}
            print(f"\n=== effect heterogeneity ({label} gamma): expect ~{attainable_size(args.q, args.alpha):.3f} "
                  f"if symmetric, larger if skewed")
            rej = {m: 0 for m in methods}
            for r in range(args.reps):
                g = gfun(args.q, np.random.default_rng(args.seed + r))
                data = simulate_plm(seed=args.seed + r, gamma=g, **kw)
                for m, fn in methods.items():
                    rej[m] += fn(data, data["theta"]) <= args.alpha
            for m in methods:
                print(f"  {m:28s} null rejection = {rej[m] / args.reps:.4f}")


if __name__ == "__main__":
    main()
