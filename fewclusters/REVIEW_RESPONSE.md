# Response to the October 2026 code audit

The audit's architecture verdict is accepted (keep the modules, fix the
defects). Every finding was first reproduced against the audited code, then
fixed, then pinned by a regression test. Test count went from 22 to 48.

| # | Audit finding | Reproduced? | Fix | Test |
|---|---|---|---|---|
| 1 | Classifier `.predict()` used as E[D\|X] | Yes: `LogisticRegression` gave 0/1 labels | Every fitted nuisance is wrapped in `FittedNuisance`; classifiers return `predict_proba[:, class 1]`, single-class fits return the constant, non-0/1 responses are rejected | `test_review_fixes.py::test_classifier_*`, `test_fitted_classifier_matches_predict_proba` |
| 2 | Cluster-level treatment passes the identification check (Q_hat = 0.25) | Yes, exactly as reported | `fit()` raises if D is constant within any cluster. New `IdentificationWarning` when Q_hat_j > 1.25 x raw within-cluster Var(D) (the treatment model predicts D worse than the cluster mean, so Q_hat reflects between-cluster variation). `var_D` reported per cluster. Docs state these are necessary conditions only | `test_cluster_level_treatment_is_rejected`, `test_one_constant_cluster_is_rejected`, `test_spurious_residual_variance_triggers_warning` |
| 3 | Monte Carlo folds unseeded; ML refit separately for size and power | Yes: two unseeded fits gave 0.954 vs 0.987 | Each method is fitted once per replication with `random_state = seed + r`; size and power p-values come from that single fit. Folds are seeded per cluster via `SeedSequence.spawn`, independent of processing order | `test_same_seed_same_answer_different_seed_different_folds` |
| 4 | Dependence DGP correlates U but not the oracle score V*U | Yes: lag-1 corr 0.665 for U, -0.0005 for V*U | Root cause: V i.i.d., mean zero, independent of U, so Cov(V_iU_i, V_jU_j) = E[V_iV_j] E[U_iU_j] = 0. New DGP adds an MA(R) latent shock to treatment (probit, so m_0 = Phi(index) stays exact) independent of the MA(R) outcome error; then Cov = Cov(V_i,V_j) Cov(U_i,U_j) != 0. Lag-1 autocorrelation of V*U is now 0.14-0.30. Driver reports it every run | `test_dependent_dgp_correlates_the_oracle_score_and_keeps_propensity_correct` |
| 5 | No numerical comparison with rART | — | `tests/rart_port.py`: line-by-line Python port of rART `CRS.test` and `CRS.CI` (fetched from mwt/rART). p-values agree exactly, critical values to 1e-14 (after the sqrt(q) scale difference in rART's statistic), CIs on 300/300 random cases including infinite endpoints. Limitation: R was not available, so this compares against a port, not the R package | `test_rart_equivalence.py` |
| 6 | Input validation; advertised calibration fraction not implemented | Yes | Non-finite y/d/X/m_known, m_known outside (0,1) for binary D, non-positive weights, alpha outside (0,1), infinite lambda, bad fold specs now raise. `calib_fraction` implemented (random share outside the evaluation fold; works with K = 2; refused with buffered folds) | `test_invalid_inputs_raise`, `test_alpha_and_lambda_validated`, `test_calib_fraction_*` |
| — | Suggested metamorphic tests | — | Added: order-preserving and order-changing cluster relabelling, row permutation with explicit folds, cluster order in the ART core, outcome rescaling (theta and CI scale, p(c*lam) = p(lam)), score scale invariance | `test_metamorphic.py` |

Also added: `fit(..., folds=...)` for explicit fold labels (exact reproducibility
across machines; used by the metamorphic tests).

## Re-run simulations

All earlier simulation numbers are superseded by [RESULTS.md](RESULTS.md),
produced by the repaired driver (seeded folds, one fit per replication,
dependent oracle scores, unequal cluster sizes). Headlines:

* Size holds near the attainable 1/32 for local, pooled and adaptive fits
  when nuisances are common across clusters, and with serially dependent
  oracle scores and 6:1 cluster sizes (0.030-0.043).
* New and important: pooling a treatment model that differs by cluster
  over-rejects badly (0.277); pooling a cluster-specific outcome model with
  an estimated m over-rejects moderately (0.073); with known m it does not
  (0.027). Adaptive pooling holds size in all three designs.
* The dependence design confirms the within-cluster CLT but does not
  stress-test buffering (low-capacity learners cannot leak); stated as a
  limitation.

## Known limits that remain

* Folds are seeded by cluster *index*, so an order-changing relabelling of
  clusters changes the random partition (results are identical given explicit
  `folds`).
* The rART check is against a port, not the R package.
* The Monte Carlo uses polynomial least-squares learners for speed; flexible
  learners (boosting, forests) are exercised only in the JTPA script and the
  quickstart.
* Finite-range dependence is the only dependence covered by theory; the
  simulation does not test data-driven buffer choice.
