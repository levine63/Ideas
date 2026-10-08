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

## Not covered

* Flexible learners (boosting, forests) in the Monte Carlo; they are used
  only in `quickstart.py` and `jtpa_analysis.py`.
* q other than 6, and n_j other than 400 (except the dependence design).
* Leakage through flexible nuisance fits under dependence (see above).
