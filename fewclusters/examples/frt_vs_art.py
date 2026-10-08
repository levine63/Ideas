"""
frt_vs_art.py -- known individual randomization within six very unequal sites:
the site-level sign test (ARTDML) versus the stratified randomization test
(StratifiedFRT), with fixed and placebo-tuned adjustment and site weights.

Sites of sizes 10, 25, 40, 200, 400, 800; site-specific outcome regressions
(tau_l = 1); treatment Bernoulli with known site-specific probability; true
effect theta = 1 for everyone (so the sharp null holds at theta).
Errors: normal, or lognormal (skewness ~6, like earnings).

Every method is evaluated at the true effect (size) and at theta - 0.15 and
theta - 0.30 (power). ARTDML is fitted once per replication; the FRT refits
its adjustment at each tested value (it must, to stay exact), and the tuned
version re-tunes at each value from placebo worlds only.

Reported fixed FRT configurations come from the same call as the tuned one
(StratifiedFRT reports every configuration's p-value for diagnostics).

Run:  PYTHONPATH=. python examples/frt_vs_art.py --errors normal --reps 300
"""

from __future__ import annotations

import argparse
import time
import warnings
from collections import Counter

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from fewclusters import ARTDML, Design, StratifiedFRT, attainable_size, simulate_plm
from fewclusters.frt import frt_pvalue, linear_coefficients

SIZES = [10, 25, 40, 200, 400, 800]
SHIFTS = (0.0, 0.15, 0.30)
FIXED = [("site_mean", "equal"), ("site_mean", "invvar"), ("local", "equal"),
         ("pooled_id", "invvar"), ("adaptive_shrunk", "equal"), ("adaptive_shrunk", "invvar")]


def poly():
    return make_pipeline(PolynomialFeatures(2, include_bias=False), LinearRegression())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--errors", choices=["normal", "lognormal"], default="normal")
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--seed", type=int, default=777)
    a = ap.parse_args()
    warnings.simplefilter("ignore")

    names = (["ART sign test (adaptive, kappa=20)", "FRT oracle residuals, invvar"]
             + [f"FRT {adj}, {wr}" for adj, wr in FIXED] + ["FRT placebo-tuned"])
    rej = {(m, s, al): 0 for m in names for s in SHIFTS for al in (0.05, 0.10)}
    choices = Counter()
    used = skipped = 0
    t0 = time.time()
    for r in range(a.reps):
        seed = a.seed + r
        data = simulate_plm(q=6, n_j=SIZES, tau_l=1.0, known_propensity=True, error_dist=a.errors, seed=seed)
        y, d, X, cl, m0, th = data["y"], data["d"], data["X"], data["cluster"], data["m0"], data["theta"]
        try:
            art = ARTDML(learner_l=poly(), n_folds=5, pooling_l="adaptive", random_state=seed
                         ).fit(y, d, X, cl, m_known=m0)
        except ValueError:          # a tiny site with no treatment variation
            skipped += 1
            continue
        used += 1
        frt = StratifiedFRT(poly(), B=999, random_state=seed)
        dz = Design(cl, p=m0)
        null_draws = dz.draw(np.random.default_rng(seed + 10**6), 999)
        for s in SHIFTS:
            lam = th - s
            pv = {"ART sign test (adaptive, kappa=20)": art.pvalue(lam)}
            e_or = (y - lam * d) - (data["l0"] - lam * m0)               # true-nuisance residual
            pv["FRT oracle residuals, invvar"] = frt_pvalue(linear_coefficients(e_or, dz, "invvar"), d, dz, null_draws)
            res = frt.test(y, d, X, cl, m0, lam=lam)
            for adj, wr in FIXED:
                pv[f"FRT {adj}, {wr}"] = res.pvalues_all[(adj, wr)]
            pv["FRT placebo-tuned"] = res.p_value
            if s == SHIFTS[-1]:
                choices[res.choice] += 1
            for m in names:
                for al in (0.05, 0.10):
                    rej[(m, s, al)] += pv[m] <= al

    print(f"## Known randomization, sites {SIZES}, {a.errors} errors: {used} replications "
          f"({skipped} skipped: a site with no treatment variation)\n")
    print(f"Sign test attainable size with 6 sites: {attainable_size(6, 0.05):.4f} at 5%, "
          f"{attainable_size(6, 0.10):.4f} at 10%. The FRT is exact at any level.\n")
    print("| method | size 5% | size 10% | power 5%, -0.15 | power 5%, -0.30 | power 10%, -0.30 |")
    print("|---|---:|---:|---:|---:|---:|")
    for m in names:
        f = lambda s, al: rej[(m, s, al)] / max(used, 1)
        print(f"| {m} | {f(0.0, .05):.3f} | {f(0.0, .10):.3f} | {f(0.15, .05):.3f} | {f(0.30, .05):.3f} | "
              f"{f(0.30, .10):.3f} |")
    print("\nPlacebo tuner's choice when testing theta - 0.30 (adjustment, weights): "
          + ", ".join(f"{k[0]}/{k[1]} {v}" for k, v in choices.most_common()))
    print(f"\nMonte Carlo s.e. of a rate near 0.05: {np.sqrt(0.05 * 0.95 / max(used, 1)):.4f}. "
          f"[{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
