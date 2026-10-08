"""
jtpa_analysis.py -- re-analysis of the National JTPA Study with site clusters.

The JTPA experiment randomized applicants to treatment or control (about 2:1)
WITHIN each of 16 sites, so (i) treatment varies within every cluster and
(ii) the assignment probability is known by design. That makes it the
textbook case for Corollary 2 of the note: with m known, the outcome model
may be pooled across sites, or even misspecified, without affecting the
validity of the site-level randomization test; only precision changes.

Estimand: intent-to-treat effect of ASSIGNMENT on the chosen outcome
(e.g. 30-month earnings), assumed common across sites.

Methods reported (all ART methods use the 16 sites as clusters, the
sign-group test of Cai, Canay, Kim and Shaikh 2023, and the same weights):

  CRVE      OLS with site fixed effects, site-clustered SE, t(q-1) critical value
  ART-DIM   ART, no covariates: within-site difference in means
  ART-OLS   ART, known m, linear outcome model fitted within site (Cai et al. style)
  DML-loc   ART, known m, gradient boosting outcome model, local to each site
  DML-pool  ART, known m, gradient boosting fitted on all sites with site id
  DML-adapt ART, known m, adaptive mixture of local and pooled (eq. (7))
  DML-mhat  ART, m ESTIMATED by a boosted classifier (adaptive) -- what one would do
            without using the design; included for contrast

Usage
-----
  # real data (column names as in your file):
  PYTHONPATH=. python examples/jtpa_analysis.py --data path/to/file.dta \
      --y earn30 --d assign --site site --x age,female,black,hisp,hsged,married,prevearn \
      [--strata strategy] [--subset "female == 1"] [--out jtpa_results.md]

  # synthetic JTPA-shaped data, to check the pipeline:
  PYTHONPATH=. python examples/jtpa_analysis.py --demo

The known propensity is the treated share within site (x strata, if given),
which equals the design assignment ratio up to sampling noise in the realized
allocation. Rows with missing outcome, assignment, site or covariates are
dropped and the counts are reported.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression

from fewclusters import ARTDML, attainable_size


# --------------------------------------------------------------------- data
def load_table(path: str) -> pd.DataFrame:
    p = path.lower()
    if p.endswith(".dta"):
        return pd.read_stata(path, convert_categoricals=False)
    if p.endswith(".csv"):
        return pd.read_csv(path)
    if p.endswith(".xpt"):
        return pd.read_sas(path, format="xport")
    if p.endswith(".sas7bdat"):
        return pd.read_sas(path)
    raise ValueError(f"Unrecognized file type: {path}")


def demo_data(seed: int = 0) -> pd.DataFrame:
    """Synthetic data shaped like the JTPA adult sample: 16 sites, 2:1 assignment."""
    rng = np.random.default_rng(seed)
    sizes = rng.integers(150, 1500, size=16)
    rows = []
    for s, n in enumerate(sizes):
        age = rng.integers(22, 60, n)
        female = rng.integers(0, 2, n)
        black = rng.random(n) < 0.3
        hsged = rng.random(n) < 0.6
        prev = np.maximum(0, rng.gamma(1.5, 2500, n))
        base = 6000 + 3000 * rng.standard_normal()              # site level
        assign = (rng.random(n) < 2 / 3).astype(int)
        y = (base + 0.8 * prev + 2000 * hsged - 1500 * female + 40 * (age - 35)
             - 0.6 * (age - 35) ** 2 + 1100 * assign + rng.gamma(2, 4000, n) - 8000)
        rows.append(pd.DataFrame(dict(site=s, age=age, female=female, black=black.astype(int),
                                      hsged=hsged.astype(int), prevearn=prev, assign=assign,
                                      earn30=np.maximum(0, y))))
    return pd.concat(rows, ignore_index=True)


# --------------------------------------------------------------------- CRVE benchmark
def crve_site_fe(y: np.ndarray, d: np.ndarray, X: np.ndarray, site: np.ndarray, alpha: float):
    """OLS of y on d, X and site dummies; site-clustered CR1 SE; t(q-1) CI."""
    from scipy import stats
    labels, s = np.unique(site, return_inverse=True)
    q = labels.size
    Z = np.column_stack([d, X, np.eye(q)[s]])
    beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
    e = y - Z @ beta
    bread = np.linalg.pinv(Z.T @ Z)
    meat = np.zeros((Z.shape[1], Z.shape[1]))
    for j in range(q):
        g = Z[s == j].T @ e[s == j]
        meat += np.outer(g, g)
    n, k = Z.shape
    adj = q / (q - 1) * (n - 1) / (n - k)
    V = adj * bread @ meat @ bread
    se = float(np.sqrt(V[0, 0]))
    tcrit = stats.t.ppf(1 - alpha / 2, q - 1)
    est = float(beta[0])
    p = float(2 * (1 - stats.t.cdf(abs(est / se), q - 1)))
    return est, (est - tcrit * se, est + tcrit * se), p


# --------------------------------------------------------------------- methods
def gbc():
    """Classifier for the binary assignment; fewclusters uses its predict_proba."""
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                                          min_samples_leaf=30, random_state=0)


def gbr():
    return HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                                         min_samples_leaf=30, random_state=0)


def method_specs() -> Dict[str, dict]:
    return {
        "ART-DIM":   dict(learner_l=DummyRegressor(), pooling_l="local", known_m=True),
        "ART-OLS":   dict(learner_l=LinearRegression(), pooling_l="local", known_m=True),
        "DML-loc":   dict(learner_l=gbr(), pooling_l="local", known_m=True),
        "DML-pool":  dict(learner_l=gbr(), pooling_l="pooled_id", known_m=True),
        "DML-adapt": dict(learner_l=gbr(), pooling_l="adaptive", known_m=True),
        "DML-mhat":  dict(learner_l=gbr(), pooling_l="adaptive", known_m=False,
                          learner_m=gbc(), pooling_m="adaptive"),
    }


def run_all(df: pd.DataFrame, y: str, d: str, site: str, xs: List[str], strata: Optional[str],
            alpha: float, n_folds: int, seed: int) -> Dict:
    data = df[[y, d, site] + xs + ([strata] if strata else [])].dropna()
    dropped = len(df) - len(data)
    yv = data[y].to_numpy(float)
    dv = data[d].to_numpy(float)
    X = data[xs].to_numpy(float)
    sv = data[site].to_numpy()
    cells = data[[site, strata]].astype(str).agg("|".join, axis=1) if strata else data[site].astype(str)
    m_known = data.groupby(cells)[d].transform("mean").to_numpy(float)
    bad = (m_known <= 0) | (m_known >= 1)
    if bad.any():
        raise ValueError(f"{int(bad.sum())} rows sit in site/strata cells with no treated or no controls.")

    q = np.unique(sv).size
    out = {"n": len(data), "dropped": dropped, "q": q, "alpha": alpha,
           "attainable": attainable_size(q, alpha), "rows": [], "sites": None, "weights": None}

    est, ci, p = crve_site_fe(yv, dv, X, sv, alpha)
    out["rows"].append(dict(method="CRVE (site FE, t(q-1))", est=est, lo=ci[0], hi=ci[1], p0=p))

    site_tab = None
    for name, spec in method_specs().items():
        t0 = time.time()
        known = spec.pop("known_m")
        model = ARTDML(n_folds=n_folds, random_state=seed, **spec)
        model.fit(yv, dv, X, sv, m_known=m_known if known else None)
        lo, hi = model.confint(alpha)
        out["rows"].append(dict(method=name, est=model.pooled_estimate(), lo=lo, hi=hi,
                                p0=model.pvalue(0.0), secs=time.time() - t0))
        tab = pd.DataFrame(model.cluster_table()).set_index("cluster")
        if site_tab is None:
            site_tab = tab[["n_scored"]].copy()
        site_tab[name] = tab["theta_hat"]
        if name == "DML-adapt":
            out["weights"] = tab["mean_w_l"]
    out["sites"] = site_tab
    return out


# --------------------------------------------------------------------- report
def report(res: Dict, title: str) -> str:
    L = [f"## {title}", "",
         f"n = {res['n']} (dropped {res['dropped']} rows with missing values), q = {res['q']} sites; "
         f"alpha = {res['alpha']}, attainable ART size = {res['attainable']:.4f}.", "",
         "| method | estimate | CI low | CI high | CI length | p (theta=0) |",
         "|---|---:|---:|---:|---:|---:|"]
    for r in res["rows"]:
        L.append(f"| {r['method']} | {r['est']:.1f} | {r['lo']:.1f} | {r['hi']:.1f} | "
                 f"{r['hi'] - r['lo']:.1f} | {r['p0']:.4f} |")
    L += ["", "Per-site estimates (theta_j):", "",
          res["sites"].round(1).to_markdown()]
    if res["weights"] is not None:
        w = res["weights"].dropna()
        L += ["", f"DML-adapt outcome-model pooling weights across sites: mean {w.mean():.2f}, "
                  f"range [{w.min():.2f}, {w.max():.2f}] (0 = local only, 1 = pooled only)."]
    return "\n".join(L)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data")
    ap.add_argument("--y", default="earn30")
    ap.add_argument("--d", default="assign")
    ap.add_argument("--site", default="site")
    ap.add_argument("--x", default="age,female,black,hsged,prevearn")
    ap.add_argument("--strata", default=None)
    ap.add_argument("--subset", default=None, help='pandas query, e.g. "female == 1"')
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args(argv)

    if a.demo:
        df, title = demo_data(a.seed), "Synthetic JTPA-shaped data (latent effect 1100; censoring at zero lowers the observed ITT)"
    elif a.data:
        df, title = load_table(a.data), f"JTPA: {a.y} on {a.d}" + (f", subset {a.subset}" if a.subset else "")
    else:
        ap.error("give --data or --demo")
    if a.subset:
        df = df.query(a.subset)
    xs = [c for c in a.x.split(",") if c]
    res = run_all(df, a.y, a.d, a.site, xs, a.strata, a.alpha, a.folds, a.seed)
    text = report(res, title)
    print(text)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
