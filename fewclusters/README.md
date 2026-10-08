# fewclusters

**Status: research prototype.** Audited once (October 2026; see
[REVIEW_RESPONSE.md](REVIEW_RESPONSE.md)); the ART core matches rART
numerically, but the package has not been validated for published empirical
work.

Approximate randomization tests (ART) with cross-fitted, machine-learned
nuisance functions and a fixed, small number of clusters.

The sign-group test and its weighted-score implementation are from
Cai, Canay, Kim and Shaikh (2023) and Canay, Romano and Shaikh (2017).
This package replaces their OLS residuals by Double/Debiased-ML residuals
(Chernozhukov et al. 2018), cross-fitted within each cluster, with optional
adaptive borrowing from other clusters. Nuisances are fitted once and held
fixed for every sign vector and every hypothesised value.

```
pip install numpy scikit-learn        # the only dependencies
PYTHONPATH=. python -m pytest tests   # 59 tests
PYTHONPATH=. python examples/quickstart.py
PYTHONPATH=. python examples/jtpa_analysis.py --demo --out results/demo.md   # synthetic pipeline check
```

## Usage

```python
from sklearn.ensemble import HistGradientBoostingClassifier as GBC
from sklearn.ensemble import HistGradientBoostingRegressor as GBR
from fewclusters import ARTDML

model = ARTDML(learner_m=GBC(), learner_l=GBR(), n_folds=5,
               pooling_m="adaptive", pooling_l="adaptive", borrow="pooled_id",
               random_state=0)
model.fit(y, d, X, cluster)          # y, d: (n,), X: (n, p), cluster: (n,) labels
model.test(0.0)                      # ARTTestResult with p-value, decision, exactness
model.confint(0.05)                  # (lo, hi) by test inversion
model.summary()                      # per-cluster Q_j, theta_j, pooling weights, warnings
```

Treatment model for binary D: a classifier is used through `predict_proba`,
so `m_hat` is a probability, never a 0/1 label. A regressor also works.

Known treatment probabilities (within-site randomisation): pass them to
`fit(..., m_known=p)` and `learner_m` is not used.

Reproducibility: `random_state` seeds the fold partition, calibration draws
and random signs (set the learners' own `random_state` too), or pass explicit
fold labels with `fit(..., folds=f)`. Fit once, then call `test(lam)` and
`confint()` as often as needed; nothing is refit.

Small clusters: in `"adaptive"` mode the outcome-model weight is shrunk
toward full borrowing, `w = (s w_hat + kappa) / (s + kappa)` with `s` the
calibration rows and `shrink_l=20` by default (a cluster of 10 borrows almost
entirely, 400 uses ~80% of its own choice). The treatment model is not
shrunk by default (`shrink_m=0`), because a biased pooled treatment model
breaks size. Below `min_local_train=20` base-training rows the local fit is
skipped and the borrowing model (trained also on the calibration rows) is
used outright. Clusters under `min_cluster_warn=50` rows trigger a
`SmallClusterWarning`: the test relies on each cluster score being roughly
normal. See `examples/small_clusters.py`.

Calibration sample for `"adaptive"`: by default the next fold (needs
`n_folds >= 3`); `calib_fraction=0.2` instead draws 20% of the cluster from
outside the evaluation fold (works with `n_folds = 2`; not with buffers).

Serially dependent rows within a cluster: pass `buffer=R` (rows must be in
time order within each cluster); folds become contiguous blocks and no row
within `R` positions of a block may train or calibrate the model that scores it.

## How the pieces fit (one module per idea)

| Module | Idea | Note reference |
|---|---|---|
| `folds.py` | evaluation / calibration / base-training roles per (cluster, fold); buffers | Section 2, Corollary 1 |
| `learners.py` | any `fit/predict` estimator (classifiers via `predict_proba`); cluster identity as a feature | Section 5.2 |
| `pooling.py` | clipped least-squares mixing weight, local vs borrowing; shrinkage toward borrowing | eq. (7), Proposition 2 |
| `nuisance.py` | cross-fitting loop for one nuisance; pooling modes | Section 3, 5.1 |
| `scores.py` | `Q_j`, `theta_j`, `S_j(lambda) = a_j - b_j lambda` | eq. (2)-(3) |
| `art.py` | sign group, p-value, decision, CI by inversion; pure numpy | eq. (4), Proposition 1 |
| `model.py` | `ARTDML`: fit once, test and invert many times | Section 3 |
| `simulate.py` | DGPs with the knobs of the simulation plan | Sections 4-7 |

Data flow: `FoldPlan` -> `crossfit_nuisance` (twice: m and ell) ->
`cluster_scores` -> `art_test` / `art_confint`. Each stage has a single
input/output contract and can be swapped independently.

## Pooling modes

| `pooling_*` | fitted on |
|---|---|
| `"local"` | the target cluster's base-training rows only |
| `"pooled"` | target base rows + other clusters' allowed rows |
| `"pooled_id"` | as pooled, with one-hot cluster id appended to X |
| `"adaptive"` | local candidate and a borrowing candidate (`borrow`), mixed with the weight chosen on the calibration fold |

Section 7.1 of the note explains why borrowing is riskier for `m` than for
`ell`: with an estimated `m`, a persistent outcome-model error multiplies the
treatment-prediction error and shifts the score. Choose the two modes
separately.

## What the test can and cannot do

* With `q` clusters the non-randomized test's limiting size is
  `floor(alpha 2^(q-1)) / 2^(q-1)`: zero for `q <= 5` at 5%, 1/32 at `q = 6`.
  `summary()` warns when the test can never reject.
* Treatment must vary **within** every cluster. `fit()` raises if D is
  constant in any cluster (e.g. cluster-level treatment); positive
  residual variance `Q_hat_j` alone is not evidence of identification,
  because a poor treatment model leaves residual variance even then. If
  `Q_hat_j` exceeds 1.25 x the raw within-cluster variance of D, `fit()`
  emits an `IdentificationWarning` and `summary()` repeats it. These checks
  are necessary conditions only.
* The treatment coefficient is assumed common across clusters. Skewed
  effect heterogeneity over-rejects (see `examples/monte_carlo.py --experiments skew`).
* The sign group is enumerated exactly for `q <= 20`; beyond that random
  signs are used and results are flagged `exact=False`.

## Extending

* New learner: anything with `fit(X, z)` and `predict(X)`; scikit-learn
  objects are cloned per fit.
* New borrowing candidate: add a builder in `nuisance.py` next to
  `_fit_pooled_id` and a name in `BorrowMode`.
* New pooling rule: replace `ls_pooling_weight` in `pooling.py`; it only
  needs the calibration responses and the two candidate predictions.
* New statistic or weights: `art.py` takes `(a, b, weights)`; `ARTDML(weights=...)`
  passes per-cluster weights through.
* Validation against rART: `tests/rart_port.py` is a line-by-line port of
  rART's `CRS.test` and `CRS.CI`; `tests/test_rart_equivalence.py` checks
  that p-values, critical values and confidence intervals agree on 400
  random cases (they agree exactly, to rounding). This is a port-level
  check; the R package itself was not run.

## References

Cai, Canay, Kim, Shaikh (2023) J. Econometric Methods 12(1): 85-103.
Canay, Romano, Shaikh (2017) Econometrica 85(3): 1013-1030.
Chernozhukov et al. (2018) Econometrics Journal 21(1): C1-C68.


## Preliminary JTPA pilot, October 8, 2026

**PRELIMINARY - NOT FOR PUBLICATION.** See [JTPA_HANDOFF.md](JTPA_HANDOFF.md)
for the novelty assessment, data provenance, corrected benchmark definitions,
and unresolved design questions. The original downloaded data stay in ignored
`jtpa_data/`; results are aggregate summaries only.

The real-data example no longer supplies observed assignment shares as known
probabilities. Its default estimates propensity; `--propensity` or
`--propensity-column` requires `--propensity-source`. A source string records
provenance or an explicit assumption; it does not itself verify the design.

With the working directory set to `fewclusters`, these entry points reproduce
the pilot (install pandas, scipy, requests, pyreadr and tabulate for examples):

```text
python examples/download_jtpa.py --dataset both --output-dir jtpa_data
PYTHONPATH=. python examples/jtpa_pilot.py
PYTHONPATH=. python examples/jtpa_shrink_pilot.py
PYTHONPATH=. python examples/summarize_jtpa.py
```

The `PYTHONPATH=.` prefix is POSIX shell syntax; in PowerShell first run
`$env:PYTHONPATH='.'`. Pilot seeds are 0, 1 and 2. The baseline script resumes
saved pilot JSONs; use a fresh results directory for a new specification or data
version. The shrinkage script recomputes its results.

Original adaptive methods explicitly turn shrinkage and the local-fit floor
off. The new methods use outcome shrinkage kappa=20, treatment shrinkage zero,
and a 20-row local-fit floor. Setting `reserve_calibration=True` on a fixed
local/pooled fit supplies the same training allocation as the adaptive method.
The ordinary local benchmark also appears so the calibration cost is visible.

Small-site warnings do not certify validity for sites above a threshold.
Shrinkage does not establish Gaussian score approximations. With estimated
propensities, cluster identity alone does not guarantee a valid borrowed
propensity model. The floor can force full borrowing for treatment even when
`shrink_m=0`.

### Preliminary test-sample weighting

Follow-up skewed-error simulations found undercoverage with same-sample
precision weights (about 90-91% for nominal 95%). Keep these experimental;
size weighting is the better-supported preliminary primary comparison.

See [the weighting comparison](results/weighting/WEIGHTING_COMPARISON.md).
From `fewclusters`, with `PYTHONPATH=.` (PowerShell: `$env:PYTHONPATH='.'`):

```text
python examples/jtpa_size_weights.py
python examples/jtpa_weighting_fit.py 0
python examples/jtpa_weighting_fit.py 1
python examples/jtpa_weighting_fit.py 2
python examples/summarize_jtpa_weighting.py
```

These scripts require the pilot's saved results and downloaded women data.
Fit scripts stop on an existing ignored residual cache: review provenance and
preserve or move that cache before rerunning. `score_weights` in
`fewclusters.weighting` returns coefficients for scores already scaled by
sqrt(site size). Size weighting therefore passes sqrt(n), not n. Precision
weights are exploratory and need additional inference assumptions; neither
these weights nor nuisance shrinkage establishes small-site normality.

### Preliminary coverage and power stress test

The follow-up uses JTPA site sizes with Gaussian, Student-t(3), and skewed
lognormal errors. It compares current, size, stabilized precision and DGP
oracle-precision weights, with both oracle and fitted shrinkage nuisances.
Coverage is measured by testing the true effect; power by testing zero under
a fixed nonzero common effect. See
[coverage and power results](results/weighting_simulation/COVERAGE_POWER.md)
for the design, uncertainty and scope limitations.

From the repository root, set `PYTHONPATH=fewclusters`, `OMP_NUM_THREADS=1`
and `OPENBLAS_NUM_THREADS=1`. Run `examples/weighting_simulation.py` through
the full package path for each of `normal_equal`, `normal_unequal`,
`t3_unequal`, and `lognormal_unequal`:

```text
python fewclusters/examples/weighting_simulation.py --design normal_equal --oracle-reps 1000 --fitted-reps 500 --output fewclusters/results/weighting_simulation/normal_equal.json
python fewclusters/examples/summarize_weighting_simulation.py
```

Run the summarizer only after all four outputs exist. Existing outputs are
not overwritten. Full sign enumeration is accelerated by using one member
of each positive/negative pair, checked against the production sign test.

After the four main simulations, run
`python fewclusters/examples/independent_weight_diagnostic.py` before the
simulation summarizer. This post hoc oracle diagnostic gives precision weights
an additional independent synthetic sample; it is not an equal-data-budget
proposal. It reproduced the original oracle comparisons and isolated
same-sample weight estimation as a contributor to skewed-error undercoverage.
