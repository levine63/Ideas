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

* **Size holds** for every method that keeps q = 6 (0.024-0.038 against an
  attainable 0.031 at 5%), even with a 10-observation cluster. The noisy
  small-cluster score is still centred and symmetric because its nuisances
  never see its evaluation rows. Caveat: errors here are Gaussian; skewed
  outcomes such as earnings could make a 10-observation score asymmetric,
  and that is not tested yet.
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
  statistic. Any fixed positive weights chosen before seeing outcomes keep
  validity (`ARTDML(weights=...)`); weights increasing in n_j should help
  here. Not yet tested.


## Known randomization: stratified randomization test vs site-level sign test (`examples/frt_vs_art.py`)

Same six sites (10, 25, 40, 200, 400, 800), site-specific outcome
regressions, treatment Bernoulli with known site-specific probability,
constant effect theta = 1 (the sharp null holds at theta). 400
replications per error distribution, seed 777; FRT p-values from 999
re-randomizations. Power columns test theta - 0.15 and theta - 0.30.
"invvar" = site weights proportional to the inverse design variance of the
site estimate; "placebo-tuned" chooses adjustment and weights from fake
re-randomizations of the design, never seeing the real treatment.

### Normal errors

Sign test attainable size with 6 sites: 0.0312 at 5%, 0.0938 at 10%. The FRT is exact at any level.

| method | size 5% | size 10% | power 5%, -0.15 | power 5%, -0.30 | power 10%, -0.30 |
|---|---:|---:|---:|---:|---:|
| ART sign test (adaptive, kappa=20) | 0.023 | 0.073 | 0.108 | 0.259 | 0.606 |
| FRT oracle residuals, invvar | 0.040 | 0.095 | 0.802 | 1.000 | 1.000 |
| FRT site_mean, equal | 0.053 | 0.106 | 0.088 | 0.188 | 0.289 |
| FRT site_mean, invvar | 0.048 | 0.106 | 0.274 | 0.761 | 0.847 |
| FRT local, equal | 0.035 | 0.083 | 0.053 | 0.143 | 0.209 |
| FRT pooled_id, invvar | 0.053 | 0.101 | 0.784 | 1.000 | 1.000 |
| FRT adaptive_shrunk, equal | 0.038 | 0.068 | 0.113 | 0.319 | 0.420 |
| FRT adaptive_shrunk, invvar | 0.050 | 0.098 | 0.784 | 1.000 | 1.000 |
| FRT placebo-tuned | 0.058 | 0.098 | 0.789 | 1.000 | 1.000 |

Placebo tuner's choice when testing theta - 0.30 (adjustment, weights): pooled_id/invvar 80, pooled_id/size 74, adaptive/invvar 57, local/invvar 51, adaptive/size 48, adaptive_shrunk/size 43, adaptive_shrunk/invvar 35, local/size 10

Monte Carlo s.e. of a rate near 0.05: 0.0109. [1131s]

### Lognormal errors (skewness ~6)

Sign test attainable size with 6 sites: 0.0312 at 5%, 0.0938 at 10%. The FRT is exact at any level.

| method | size 5% | size 10% | power 5%, -0.15 | power 5%, -0.30 | power 10%, -0.30 |
|---|---:|---:|---:|---:|---:|
| ART sign test (adaptive, kappa=20) | 0.023 | 0.083 | 0.148 | 0.317 | 0.661 |
| FRT oracle residuals, invvar | 0.045 | 0.088 | 0.832 | 1.000 | 1.000 |
| FRT site_mean, equal | 0.050 | 0.098 | 0.085 | 0.188 | 0.309 |
| FRT site_mean, invvar | 0.058 | 0.103 | 0.276 | 0.754 | 0.849 |
| FRT local, equal | 0.033 | 0.070 | 0.068 | 0.209 | 0.286 |
| FRT pooled_id, invvar | 0.055 | 0.106 | 0.804 | 1.000 | 1.000 |
| FRT adaptive_shrunk, equal | 0.033 | 0.068 | 0.153 | 0.465 | 0.570 |
| FRT adaptive_shrunk, invvar | 0.048 | 0.106 | 0.814 | 1.000 | 1.000 |
| FRT placebo-tuned | 0.050 | 0.111 | 0.802 | 1.000 | 1.000 |

Placebo tuner's choice when testing theta - 0.30 (adjustment, weights): pooled_id/invvar 127, adaptive_shrunk/invvar 75, adaptive/invvar 73, local/invvar 37, pooled_id/size 32, adaptive_shrunk/size 27, adaptive/size 20, local/size 7

Monte Carlo s.e. of a rate near 0.05: 0.0109. [1136s]

**Reading.**

* **The randomization test is exact**, including with a 10-person site and
  heavily skewed errors: every FRT configuration, tuned or fixed, rejects a
  true null at 0.033-0.058 at 5% (Monte Carlo s.e. 0.011), and at the full
  nominal level, not the sign test's 1/32.
* **Power is transformed.** Against an effect 0.15 below the truth, the
  tuned FRT rejects 79-80% of the time at 5%, essentially the oracle's
  80-83%; the site-level sign test rejects 11-15%. Against 0.30: 100%
  versus 26-32%.
* **Site weighting matters more than the adjustment.** With equal site
  weights even the FRT is weak (0.19-0.47 at -0.30), because the 10-person
  site counts as much as the 800-person site. Inverse-variance weights fix
  this; better covariate adjustment then adds the rest (site means only:
  0.76; adaptive or pooled ML: 1.00).
* **The placebo tuner never chose equal weights or no adjustment**, and
  matched the best fixed configuration (0.79-0.80 vs 0.78-0.81 at -0.15)
  without knowing in advance which that was. In this design a sensible
  fixed default (adaptive_shrunk, invvar) does equally well; tuning is
  insurance against a bad default, not a gain over a good one.
* **Scope.** The FRT tests the sharp null of a constant effect for these
  sites. The sign test answers a different question (inference that holds
  across sites with site-varying effects); its low power here is the price
  of that question plus equal site weights.

## Not covered

* Flexible learners (boosting, forests) in the Monte Carlo; they are used
  only in `quickstart.py` and `jtpa_analysis.py`.
* q other than 6.
* Skewed outcomes with tiny clusters for the sign test with estimated m
  (the known-m design is covered above).
* FRT confidence intervals and the studentized FRT for heterogeneous
  individual effects.
* Leakage through flexible nuisance fits under dependence (see above).
