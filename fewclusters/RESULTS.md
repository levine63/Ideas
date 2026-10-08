# Monte Carlo results (repaired driver, October 2026)

These replace the earlier numbers, which came from an unseeded driver that
refit each method separately for size and power (see REVIEW_RESPONSE.md).

Common settings: q = 6 clusters, n_j = 400, alpha = 0.05 (attainable size
1/32 = 0.0312), 300 replications, K = 5 folds, learners = degree-2
polynomial least squares, borrowing candidate = pooled with cluster id.
Replication r uses seed 12345 + r for the data, folds and calibration draws.
Each method is fitted once per replication; size (at the true theta) and
power (at theta - 0.3) come from that fit. Monte Carlo standard errors are
about 0.010 near the nominal level.

Reproduce: `PYTHONPATH=. python examples/monte_carlo.py --reps 300 --q 6 --n 400 --experiments <name>`

## Baseline: common nuisance functions (`baseline`)

| method | size | power |
|---|---:|---:|
| oracle | 0.020 | 0.983 |
| local | 0.030 | 0.980 |
| pooled_id | 0.027 | 0.983 |
| adaptive | 0.017 | 0.970 |

## Asymmetry, Section 7.1 (`asymmetry`)

Treatment model differs by cluster (tau_m = 1), outcome model common:

| method | size | power |
|---|---:|---:|
| oracle | 0.013 | 0.953 |
| local m, local ell | 0.017 | 0.927 |
| **pooled m, local ell** | **0.277** | 0.327 |
| adaptive m, adaptive ell | 0.013 | 0.933 |

Outcome model differs by cluster (tau_l = 1), treatment model common:

| method | size | power |
|---|---:|---:|
| oracle | 0.020 | 0.983 |
| local m, local ell | 0.030 | 0.980 |
| **local m, pooled ell** | **0.073** | 0.933 |
| adaptive m, adaptive ell | 0.017 | 0.970 |

Pooling a nuisance that really differs across clusters breaks size, badly for
m and moderately for ell, as Section 7.1 predicts (with estimated m, a
persistent outcome-model error multiplies the treatment-model error).
Adaptive pooling holds size in both designs. In the pooled-m runs the new
`IdentificationWarning` fires: the pooled treatment model predicts D worse
than each cluster's own mean.

## Known propensity, Corollary 2 (`known_m`)

Within-cluster randomisation with known probabilities; outcome model strongly
heterogeneous (tau_l = 1.5):

| method | size | power |
|---|---:|---:|
| oracle | 0.033 | 0.973 |
| known m, local ell | 0.043 | 0.973 |
| known m, pooled ell | 0.027 | 0.680 |
| known m, adaptive ell | 0.040 | 0.980 |

With m known, the badly misspecified pooled outcome model keeps size and
only loses power, as Corollary 2 predicts; adaptive pooling recovers it.
Contrast with the previous table, where the same pooling with an estimated m
over-rejects.

## Effect heterogeneity (`skew`)

Cluster-specific effects theta_j = theta + gamma_j, known m, local ell; null
rejection rate at the mean theta:

| gamma_j | oracle | ARTDML |
|---|---:|---:|
| symmetric (Rademacher x 0.3) | 0.023 | 0.023 |
| skewed (-1 w.p. 2/3, 2 w.p. 1/3, centred, x 0.3) | 0.107 | 0.107 |

Skewed heterogeneity over-rejects (limit 0.089 in the note); the symmetry
assumption is substantive.

## Dependent scores, unequal clusters (`dependence`)

R = 3 dependence in BOTH treatment and outcome shocks (mean lag-1
autocorrelation of the oracle score 0.24); cluster sizes 200, 286, 410, 586,
839, 1200 (ratio 6:1):

| method | size | power |
|---|---:|---:|
| oracle | 0.030 | 0.837 |
| local, random folds (no buffer) | 0.040 | 0.793 |
| local, contiguous folds, no buffer | 0.040 | 0.793 |
| local, contiguous folds, buffer = 3 | 0.043 | 0.787 |

Size holds within Monte Carlo error with serially correlated scores and very
unequal clusters. Buffering makes no visible difference here: low-capacity
polynomial learners cannot exploit neighbouring rows, so this design tests
the within-cluster CLT, not leakage through the nuisance fit. A leakage
stress test needs serially dependent covariates and a flexible learner.


## Very unequal, partly tiny clusters (`examples/small_clusters.py`)

Six clusters of sizes 10, 25, 40, 200, 400, 800; outcome regression differs
by cluster (tau_l = 1); polynomial learners; 500 replications, seed 2026;
size at the true theta, power at theta - 0.3. "sd S(n=10) / oracle" is the
spread of the n = 10 cluster's score relative to the true-nuisance score;
"w_ell" is the mean outcome-model pooling weight (1 = fully borrowed).

### Known treatment probabilities

Attainable size: q=6 -> 0.0312 at 5%, 0.0938 at 10%; q=5 -> 0.0000 at 5%, 0.0625 at 10%.

| method | size 5% | size 10% | power 5% | power 10% | sd S(n=10) / oracle | w_ell n=10 | w_ell n=800 |
|---|---:|---:|---:|---:|---:|---:|---:|
| oracle | 0.026 | 0.105 | 0.435 | 0.786 | 1.00 | - | - |
| local ell | 0.034 | 0.083 | 0.192 | 0.415 | 3.19 | - | - |
| pooled_id ell | 0.034 | 0.085 | 0.302 | 0.665 | 2.18 | - | - |
| adaptive ell, no shrink, no floor | 0.032 | 0.085 | 0.288 | 0.597 | 2.50 | 0.45 | 0.72 |
| adaptive ell, kappa=20 + floor (default) | 0.032 | 0.079 | 0.308 | 0.645 | 2.18 | 1.00 | 0.75 |
| default, drop n=10 cluster (q=5) | 0.000 | 0.077 | 0.000 | 0.552 | - | - | 0.75 |
| default, merge n=10 and n=25 (q=5) | 0.000 | 0.075 | 0.000 | 0.571 | - | - | 0.75 |

Monte Carlo s.e. of a rejection rate near 0.03: 0.0077. [500s]

### Estimated treatment probabilities

Attainable size: q=6 -> 0.0312 at 5%, 0.0938 at 10%; q=5 -> 0.0000 at 5%, 0.0625 at 10%.

| method | size 5% | size 10% | power 5% | power 10% | sd S(n=10) / oracle | w_ell n=10 | w_ell n=800 |
|---|---:|---:|---:|---:|---:|---:|---:|
| oracle | 0.024 | 0.094 | 0.425 | 0.760 | 1.00 | - | - |
| local m, local ell | 0.038 | 0.106 | 0.220 | 0.499 | 2.72 | - | - |
| pooled_id m, pooled_id ell | 0.028 | 0.088 | 0.325 | 0.647 | 1.98 | - | - |
| adaptive, no shrink, no floor | 0.032 | 0.096 | 0.236 | 0.511 | 2.02 | 0.46 | 0.72 |
| adaptive, kappa_l=20 + floor (default) | 0.032 | 0.100 | 0.301 | 0.597 | 1.98 | 1.00 | 0.75 |
| default, merge n=10 and n=25 (q=5) | 0.000 | 0.064 | 0.000 | 0.469 | - | - | 0.75 |

Monte Carlo s.e. of a rejection rate near 0.03: 0.0076. [824s]

**Reading.**

* **Observed rejection rates are near the attainable level** for methods
  keeping q = 6 in this simulation (0.024-0.038 against 0.031 at 5%).
  This is not a general small-cluster validity result. Honest sample splitting
  avoids own-observation leakage; it does not by itself establish score
  centering or symmetry, especially with estimated propensities and nuisance
  error drift. Errors here are Gaussian; skewed earnings and heavy tails
  require separate stress tests.
* **The cost is power.** The equal-weighted statistic gives the n = 10
  cluster the same weight as the n = 800 cluster, and its score is 2-3x
  noisier than the oracle's. Power at 5% falls from 0.43 (oracle) to 0.19
  (local), 0.29 (adaptive, no shrinkage) and 0.31 (shrinkage + floor).
* **Shrinkage helps where it should.** With estimated m, power at 5% rises
  from 0.236 to 0.301 (at 10%: 0.511 to 0.597); with known m, 0.288 to
  0.308. The default borrows fully in the n = 10 cluster (w = 1.00) and
  keeps most of the data's choice in the n = 800 cluster (0.75 vs 0.72
  unshrunk). It essentially matches always borrowing with cluster
  intercepts (pooled_id), while still adapting in large clusters.
* **Merging or dropping small clusters is not a fix at q = 6.** It leaves
  q = 5, where the test cannot reject at 5% at all, and at 10% it has less
  power (0.47-0.57) than keeping the clusters with shrinkage (0.60-0.65).
* **What would recover more power:** down-weighting small clusters in the
  statistic. Prespecified deterministic positive weights preserve the sign-invariance
  argument when its original assumptions hold (`ARTDML(weights=...)`).
  They do not repair non-Gaussian small-site scores. Whether weights increasing
  in n_j improve power is an untested conjecture in this design.

## Not covered

* Flexible learners (boosting, forests) in the Monte Carlo; they are used
  only in `quickstart.py` and `jtpa_analysis.py`.
* q other than 6.
* Skewed or heavy-tailed outcomes with tiny clusters.
* Leakage through flexible nuisance fits under dependence (see above).
