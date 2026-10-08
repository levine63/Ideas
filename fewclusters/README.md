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
PYTHONPATH=. python -m pytest tests   # 48 tests
PYTHONPATH=. python examples/quickstart.py
PYTHONPATH=. python examples/jtpa_analysis.py --demo   # JTPA pipeline on synthetic data
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
| `pooling.py` | clipped least-squares mixing weight, local vs borrowing | eq. (7), Proposition 2 |
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
