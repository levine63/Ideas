# fewclusters

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
PYTHONPATH=. python -m pytest tests   # 22 tests
PYTHONPATH=. python examples/quickstart.py
```

## Usage

```python
from sklearn.ensemble import GradientBoostingRegressor as GBR
from fewclusters import ARTDML

model = ARTDML(learner_m=GBR(), learner_l=GBR(), n_folds=5,
               pooling_m="adaptive", pooling_l="adaptive", borrow="pooled_id")
model.fit(y, d, X, cluster)          # y, d: (n,), X: (n, p), cluster: (n,) labels
model.test(0.0)                      # ARTTestResult with p-value, decision, exactness
model.confint(0.05)                  # (lo, hi) by test inversion
model.summary()                      # per-cluster Q_j, theta_j, pooling weights, warnings
```

Known treatment probabilities (within-site randomisation): pass them to
`fit(..., m_known=p)` and `learner_m` is not used.

Serially dependent rows within a cluster: pass `buffer=R` (rows must be in
time order within each cluster); folds become contiguous blocks and no row
within `R` positions of a block may train or calibrate the model that scores it.

## How the pieces fit (one module per idea)

| Module | Idea | Note reference |
|---|---|---|
| `folds.py` | evaluation / calibration / base-training roles per (cluster, fold); buffers | Section 2, Corollary 1 |
| `learners.py` | any `fit/predict` estimator; cluster identity as a feature | Section 5.2 |
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
* Treatment must vary within every cluster after adjusting for X
  (`Q_j > 0`); `fit()` raises otherwise.
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
* Validation against rART: `art.ols_cluster_estimates` reproduces the
  cluster-by-cluster OLS estimates so `art_pvalue` can be checked against
  rART's `CRS.test` on the same data.

## References

Cai, Canay, Kim, Shaikh (2023) J. Econometric Methods 12(1): 85-103.
Canay, Romano, Shaikh (2017) Econometrica 85(3): 1013-1030.
Chernozhukov et al. (2018) Econometrics Journal 21(1): C1-C68.
