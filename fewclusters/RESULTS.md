# Monte Carlo checks run during development

q = 6 clusters, n_j = 400, alpha = 0.05 (attainable size 1/32 = 0.0312),
nuisance learners: degree-2 polynomial least squares, K = 5 folds, borrow = pooled_id.
Power is against theta - 0.3. Monte Carlo standard errors are roughly 0.015.

Baseline, common nuisances (120 reps)

| method     | size   | power |
|------------|--------|-------|
| oracle     | 0.025  | 0.983 |
| local      | 0.033  | 0.975 |
| pooled_id  | 0.017  | 0.983 |
| adaptive   | 0.008  | 0.983 |

Known propensity (Corollary 2), outcome regressions strongly heterogeneous (tau_l = 1.5), 150 reps

| method                 | size   | power |
|------------------------|--------|-------|
| oracle                 | 0.033  | 0.967 |
| known m, local ell     | 0.053  | 0.960 |
| known m, pooled ell    | 0.020  | 0.613 |
| known m, adaptive ell  | 0.027  | 0.960 |

The misspecified pooled outcome model keeps size but loses a third of its power,
exactly the variance-inflation-without-shift prediction of Corollary 2; adaptive
pooling recovers the local power.

Effect heterogeneity (300 reps, known propensity, local ell), null rejection:

| gamma_j        | oracle | ARTDML |
|----------------|--------|--------|
| symmetric +-   | 0.023  | 0.023  |
| skewed {-1, 2} | 0.107  | 0.107  |

Skewed heterogeneity over-rejects (theory: 0.089 in the limit), confirming
the symmetry assumption is substantive.

Run `PYTHONPATH=. python examples/monte_carlo.py --help` to reproduce.
