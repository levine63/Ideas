"""
small_clusters.py -- Monte Carlo with very unequal, partly tiny clusters.

Six clusters of sizes 10, 25, 40, 200, 400, 800 (q = 6, so the attainable
size of the non-randomized test is 1/32 at alpha = 0.05 and 3/32 at 0.10).
The outcome regression differs by cluster (tau_l = 1), so a pooled outcome
model is misspecified and a local one is very noisy in the small clusters:
the setting the shrinkage is designed for.

Two designs:
  known_m  within-cluster randomisation with known probabilities (Corollary 2)
  est_m    treatment probabilities estimated (common treatment model)

Each method is fitted once per replication; p-values at the true theta (size)
and at theta - shift (power) come from that fit and are reported at
alpha = 0.05 and 0.10. Also reported: the standard deviation, across
replications, of the n = 10 cluster's score S_j(theta) relative to the
oracle (variance inflation from a bad nuisance fit), and the mean outcome-
model pooling weight in the n = 10 and n = 800 clusters.

Replications where some cluster has no treatment variation (possible with
n = 10) are skipped for every method and counted.

Run:  PYTHONPATH=. python examples/small_clusters.py --design known_m --reps 500
"""

from __future__ import annotations

import argparse
import time
import warnings
from typing import Callable, Dict

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from fewclusters import ARTDML, attainable_size, simulate_plm
from fewclusters.art import art_pvalue, sign_group
from fewclusters.scores import cluster_scores

SIZES = [10, 25, 40, 200, 400, 800]


def poly():
    return make_pipeline(PolynomialFeatures(2, include_bias=False), LinearRegression())


class Oracle:
    def __init__(self, data: Dict, seed: int):
        cl = data["cluster"]
        labels = np.unique(cl)
        self.scores = cluster_scores(data["d"] - data["m0"], data["y"] - data["l0"], cl,
                                     np.ones(cl.size, bool), labels)
        self.signs, _ = sign_group(labels.size)

    def pvalue(self, lam: float) -> float:
        return art_pvalue(self.scores.S(lam), self.signs)


class Fitted:
    """Adapter: an ARTDML fit exposing pvalue, scores and per-cluster ell weights."""

    def __init__(self, model: ARTDML):
        self.model = model
        self.scores = model.result_.scores
        self.w_l = {r["cluster"]: r["mean_w_l"] for r in model.cluster_table()}

    def pvalue(self, lam: float) -> float:
        return self.model.pvalue(lam)


def method(known_m: bool, pooling_m: str = "adaptive", pooling_l: str = "adaptive",
           shrink_l: float = 20.0, min_local_train: int = 20, regroup: str = "none") -> Callable:
    """regroup: 'none', 'drop10' (drop the n=10 cluster) or 'merge' (merge n=10 and n=25)."""

    def build(data: Dict, seed: int) -> Fitted:
        y, d, X, cl, m0 = data["y"], data["d"], data["X"], data["cluster"].copy(), data["m0"]
        if regroup == "drop10":
            keep = cl != 0
            y, d, X, cl, m0 = y[keep], d[keep], X[keep], cl[keep], m0[keep]
        elif regroup == "merge":
            cl[cl == 0] = 1
        model = ARTDML(learner_m=None if known_m else poly(), learner_l=poly(), n_folds=5,
                       pooling_m=pooling_m, pooling_l=pooling_l, borrow="pooled_id",
                       shrink_l=shrink_l, min_local_train=min_local_train, random_state=seed)
        model.fit(y, d, X, cl, m_known=m0 if known_m else None)
        return Fitted(model)
    return build


def methods_for(design: str) -> Dict[str, Callable]:
    if design == "known_m":
        return {
            "oracle": Oracle,
            "local ell": method(True, pooling_l="local"),
            "pooled_id ell": method(True, pooling_l="pooled_id"),
            "adaptive ell, no shrink, no floor": method(True, shrink_l=0.0, min_local_train=0),
            "adaptive ell, kappa=20 + floor (default)": method(True),
            "default, drop n=10 cluster (q=5)": method(True, regroup="drop10"),
            "default, merge n=10 and n=25 (q=5)": method(True, regroup="merge"),
        }
    return {
        "oracle": Oracle,
        "local m, local ell": method(False, pooling_m="local", pooling_l="local"),
        "pooled_id m, pooled_id ell": method(False, pooling_m="pooled_id", pooling_l="pooled_id"),
        "adaptive, no shrink, no floor": method(False, shrink_l=0.0, min_local_train=0),
        "adaptive, kappa_l=20 + floor (default)": method(False),
        "default, merge n=10 and n=25 (q=5)": method(False, regroup="merge"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", choices=["known_m", "est_m"], default="known_m")
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--shift", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()
    warnings.simplefilter("ignore")

    methods = methods_for(a.design)
    known = a.design == "known_m"
    alphas = (0.05, 0.10)
    p_null = {m: [] for m in methods}
    p_alt = {m: [] for m in methods}
    s10 = {m: [] for m in methods}
    w10 = {m: [] for m in methods}
    w800 = {m: [] for m in methods}
    skipped = 0
    t0 = time.time()
    for r in range(a.reps):
        data = simulate_plm(q=6, n_j=SIZES, tau_l=1.0, known_propensity=known, seed=a.seed + r)
        try:
            fits = {m: build(data, a.seed + r) for m, build in methods.items()}
        except ValueError:
            skipped += 1
            continue
        th = data["theta"]
        for m, f in fits.items():
            p_null[m].append(f.pvalue(th))
            p_alt[m].append(f.pvalue(th - a.shift))
            if f.scores.q == 6:
                s10[m].append(f.scores.S(th)[0])
            if isinstance(f, Fitted):
                if 0 in f.w_l and f.w_l[0] is not None:
                    w10[m].append(f.w_l[0])
                if 5 in f.w_l and f.w_l[5] is not None:
                    w800[m].append(f.w_l[5])

    used = a.reps - skipped
    sd_oracle = np.std(s10["oracle"])
    print(f"## Small clusters, design = {a.design}: sizes {SIZES}, tau_l = 1, "
          f"{used} replications ({skipped} skipped: a cluster with no treatment variation)\n")
    print(f"Attainable size: q=6 -> {attainable_size(6, 0.05):.4f} at 5%, {attainable_size(6, 0.10):.4f} "
          f"at 10%; q=5 -> {attainable_size(5, 0.05):.4f} at 5%, {attainable_size(5, 0.10):.4f} at 10%.\n")
    print("| method | size 5% | size 10% | power 5% | power 10% | sd S(n=10) / oracle | w_ell n=10 | w_ell n=800 |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for m in methods:
        pn, pa = np.array(p_null[m]), np.array(p_alt[m])
        cells = [f"{np.mean(pn <= al):.3f}" for al in alphas] + [f"{np.mean(pa <= al):.3f}" for al in alphas]
        sd = f"{np.std(s10[m]) / sd_oracle:.2f}" if s10[m] else "-"
        wa = f"{np.mean(w10[m]):.2f}" if w10[m] else "-"
        wb = f"{np.mean(w800[m]):.2f}" if w800[m] else "-"
        print(f"| {m} | " + " | ".join(cells) + f" | {sd} | {wa} | {wb} |")
    se = np.sqrt(0.03 * 0.97 / max(used, 1))
    print(f"\nMonte Carlo s.e. of a rejection rate near 0.03: {se:.4f}. [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
