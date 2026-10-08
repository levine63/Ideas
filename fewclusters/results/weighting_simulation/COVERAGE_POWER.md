# Unequal-site weighting: coverage and power stress test

**PRELIMINARY - NOT FOR PUBLICATION**

## Findings

**Decision for this preliminary analysis:** use size weighting as the primary weighting comparison and keep same-sample estimated precision weighting experimental. In the skewed lognormal design, primary precision weights give only 90.6% fitted-estimator coverage for nominal 95% (Monte Carlo interval 87.7-92.9%); size weights give 95.2% (93.0-96.8%). Apparent power gains from an oversized test are not a fair efficiency comparison. This result does not establish size weighting's validity outside these designs.

- shrink known p, current: coverage 93.8-95.0%; power 57.0-69.0% across the four designs.
- shrink known p, size: coverage 93.6-96.0%; power 71.4-79.4% across the four designs.
- shrink known p, precision k100: coverage 90.6-95.0%; power 72.0-96.0% across the four designs.
- shrink estimated p, current: coverage 93.4-95.6%; power 56.8-70.0% across the four designs.
- shrink estimated p, size: coverage 93.6-95.8%; power 70.6-79.4% across the four designs.
- shrink estimated p, precision k100: coverage 90.6-94.8%; power 71.0-95.8% across the four designs.

Some fitted-method coverage estimates have marginal Monte Carlo intervals entirely below 95%: lognormal_unequal, shrink known p, precision k100; lognormal_unequal, shrink known p, precision k20; lognormal_unequal, shrink estimated p, precision k100; lognormal_unequal, shrink estimated p, precision k20. These are diagnostic flags, not multiplicity-adjusted findings.

## Design and interpretation

Independent observations within each of 16 sites, with the JTPA sizes 38, 74, 81, 87, 177, 179, 190, 234, 353, 401, 463, 485, 524, 636, 788, 1392 (6,102 total). Treatment is independent Bernoulli(2/3). The common true treatment effect is 0.08 in standardized simulation units, not JTPA dollars. Outcomes follow Y=0.08D+g_g(X)+sigma_g*epsilon. Two independent standard-normal covariates enter a linear outcome function with site-specific intercepts and slopes. Local outcome models can learn these slopes; the pooled site-intercept model cannot represent all of them.

Four prespecified error designs:

- `normal_equal`: independent standard Gaussian errors, sigma_g=1.
- `normal_unequal`: Gaussian errors, sigma_g=(median(n)/n_g)^(1/4). Small sites are noisier per observation as well as having fewer observations.
- `t3_unequal`: Student-t(3) errors divided by sqrt(3), with the same unequal site scales. Variance is finite but the fourth moment is not.
- `lognormal_unequal`: lognormal errors with log-standard-deviation 1.5, centered and scaled using population moments, with the same unequal site scales. This is a skewness/heavy-tail stress test, not a fitted earnings distribution.

Each design has 1,000 oracle-nuisance replications, with fitted nuisances on the first 500. Each replication fits once at the true effect and tests both the true value (coverage) and zero (power). Coverage equals acceptance of the true value by the inverted 5% sign test; endpoints need not be computed. All sign pairs are enumerated, using 32,768 representatives of the 65,536 signs. A regression test verifies the accelerated calculation against the production full enumeration, including ties.

Fitted outcome nuisances use five-fold adaptive local/pooled-site-intercept Ridge(alpha=1), outcome weight shrinkage kappa=20 and the 20-row local-training floor. The estimated-propensity version uses adaptively calibrated local and pooled sample means (DummyRegressor), with treatment shrinkage zero and the same floor. This is appropriate to the simulated constant propensity and keeps the comparison focused; it does not validate the JTPA gradient-boosting implementation or observational propensity misspecification. Shared cross-site nuisance training is included. Oracle outcome and treatment means provide a separate baseline.

Weight rules match the JTPA exercise: current equal score weights, size score weights sqrt(n), and stabilized precision score weights sqrt(n)/tauhat_squared with variance kappa=100 (primary) or 20 (sensitivity), floored at 0.1 times the pooled variance. The final rule uses the DGP oracle variance sigma_g^2/[p(1-p)], without shrinkage. For fitted nuisances that final variance omits nuisance estimation error, so it is a reference rather than the true finite-sample optimal weight. All weights remain fixed over signs and nulls.

The intervals in the tables are Monte Carlo uncertainty for the estimated coverage/power rates, not effect confidence intervals. Wilson intervals are marginal and are not adjusted for the many comparisons. At 500 replications, a rejection probability of 5% has Monte Carlo standard error about 1 percentage point. Full enumeration removes sign-sampling error, not simulation uncertainty or failures of score symmetry. Paired changes versus current weighting, including their Monte Carlo standard errors, are in `paired_differences.csv`. Raw replication p-values and estimates are retained in each design JSON. There were no skipped or failed replications.

## Shrinkage estimator, known propensity

| Design            | Weight           |   Reps |   Coverage % | Coverage MC 95%   |   Power % | Power MC 95%   |    Bias |   RMSE |
|:------------------|:-----------------|-------:|-------------:|:------------------|----------:|:---------------|--------:|-------:|
| normal_equal      | current          |    500 |         93.8 | 91.3-95.6         |      64.8 | 60.5-68.9      | -0.0014 | 0.0305 |
| normal_equal      | size             |    500 |         94.2 | 91.8-95.9         |      71.4 | 67.3-75.2      | -0.0016 | 0.0277 |
| normal_equal      | precision k100   |    500 |         94   | 91.6-95.8         |      72   | 67.9-75.8      | -0.0017 | 0.0279 |
| normal_equal      | precision k20    |    500 |         94   | 91.6-95.8         |      71.6 | 67.5-75.4      | -0.0017 | 0.0279 |
| normal_equal      | oracle precision |    500 |         94.2 | 91.8-95.9         |      71.4 | 67.3-75.2      | -0.0016 | 0.0277 |
| normal_unequal    | current          |    500 |         93.8 | 91.3-95.6         |      57   | 52.6-61.3      | -0.0011 | 0.0334 |
| normal_unequal    | size             |    500 |         93.6 | 91.1-95.4         |      75   | 71.0-78.6      | -0.0013 | 0.0247 |
| normal_unequal    | precision k100   |    500 |         94.2 | 91.8-95.9         |      78.6 | 74.8-82.0      | -0.0014 | 0.0233 |
| normal_unequal    | precision k20    |    500 |         94   | 91.6-95.8         |      78.6 | 74.8-82.0      | -0.0014 | 0.0232 |
| normal_unequal    | oracle precision |    500 |         94.2 | 91.8-95.9         |      78.4 | 74.6-81.8      | -0.0014 | 0.023  |
| t3_unequal        | current          |    500 |         95   | 92.7-96.6         |      58.4 | 54.0-62.6      | -0.0001 | 0.0329 |
| t3_unequal        | size             |    500 |         96   | 93.9-97.4         |      77.8 | 74.0-81.2      |  0.0002 | 0.025  |
| t3_unequal        | precision k100   |    500 |         95   | 92.7-96.6         |      84.4 | 81.0-87.3      |  0.0005 | 0.0215 |
| t3_unequal        | precision k20    |    500 |         94.2 | 91.8-95.9         |      84   | 80.5-87.0      |  0.0007 | 0.0215 |
| t3_unequal        | oracle precision |    500 |         96   | 93.9-97.4         |      80.8 | 77.1-84.0      |  0.0006 | 0.0235 |
| lognormal_unequal | current          |    500 |         94.6 | 92.3-96.3         |      69   | 64.8-72.9      |  0.001  | 0.0319 |
| lognormal_unequal | size             |    500 |         95.2 | 93.0-96.8         |      79.4 | 75.6-82.7      |  0.0005 | 0.0245 |
| lognormal_unequal | precision k100   |    500 |         90.6 | 87.7-92.9         |      96   | 93.9-97.4      |  0.0089 | 0.0207 |
| lognormal_unequal | precision k20    |    500 |         90   | 87.1-92.3         |      97.8 | 96.1-98.8      |  0.0105 | 0.0213 |
| lognormal_unequal | oracle precision |    500 |         95.4 | 93.2-96.9         |      81.8 | 78.2-84.9      |  0.0004 | 0.0226 |

## Shrinkage estimator, estimated propensity

| Design            | Weight           |   Reps |   Coverage % | Coverage MC 95%   |   Power % | Power MC 95%   |    Bias |   RMSE |
|:------------------|:-----------------|-------:|-------------:|:------------------|----------:|:---------------|--------:|-------:|
| normal_equal      | current          |    500 |         93.6 | 91.1-95.4         |      64   | 59.7-68.1      | -0.0014 | 0.0305 |
| normal_equal      | size             |    500 |         94.4 | 92.0-96.1         |      70.6 | 66.5-74.4      | -0.0017 | 0.0277 |
| normal_equal      | precision k100   |    500 |         94   | 91.6-95.8         |      71   | 66.9-74.8      | -0.0017 | 0.0279 |
| normal_equal      | precision k20    |    500 |         94   | 91.6-95.8         |      71.8 | 67.7-75.6      | -0.0017 | 0.0279 |
| normal_equal      | oracle precision |    500 |         94.4 | 92.0-96.1         |      70.6 | 66.5-74.4      | -0.0017 | 0.0277 |
| normal_unequal    | current          |    500 |         93.4 | 90.9-95.3         |      56.8 | 52.4-61.1      | -0.0011 | 0.0334 |
| normal_unequal    | size             |    500 |         93.6 | 91.1-95.4         |      75.4 | 71.4-79.0      | -0.0013 | 0.0247 |
| normal_unequal    | precision k100   |    500 |         94.2 | 91.8-95.9         |      77.8 | 74.0-81.2      | -0.0014 | 0.0233 |
| normal_unequal    | precision k20    |    500 |         94.4 | 92.0-96.1         |      77.8 | 74.0-81.2      | -0.0014 | 0.0232 |
| normal_unequal    | oracle precision |    500 |         94.2 | 91.8-95.9         |      78   | 74.2-81.4      | -0.0014 | 0.023  |
| t3_unequal        | current          |    500 |         95.6 | 93.4-97.1         |      58.8 | 54.4-63.0      | -0.0001 | 0.0331 |
| t3_unequal        | size             |    500 |         95.8 | 93.7-97.2         |      77.8 | 74.0-81.2      |  0.0002 | 0.0251 |
| t3_unequal        | precision k100   |    500 |         94.8 | 92.5-96.4         |      83.6 | 80.1-86.6      |  0.0005 | 0.0215 |
| t3_unequal        | precision k20    |    500 |         94.2 | 91.8-95.9         |      83.8 | 80.3-86.8      |  0.0007 | 0.0215 |
| t3_unequal        | oracle precision |    500 |         95.8 | 93.7-97.2         |      80.8 | 77.1-84.0      |  0.0006 | 0.0235 |
| lognormal_unequal | current          |    500 |         94.6 | 92.3-96.3         |      70   | 65.8-73.9      |  0.0009 | 0.032  |
| lognormal_unequal | size             |    500 |         95.2 | 93.0-96.8         |      79.4 | 75.6-82.7      |  0.0005 | 0.0245 |
| lognormal_unequal | precision k100   |    500 |         90.6 | 87.7-92.9         |      95.8 | 93.7-97.2      |  0.009  | 0.0207 |
| lognormal_unequal | precision k20    |    500 |         90.6 | 87.7-92.9         |      97.8 | 96.1-98.8      |  0.0106 | 0.0213 |
| lognormal_unequal | oracle precision |    500 |         95.6 | 93.4-97.1         |      81.4 | 77.8-84.6      |  0.0004 | 0.0226 |

## Oracle nuisances

| Design            | Weight           |   Reps |   Coverage % | Coverage MC 95%   |   Power % | Power MC 95%   |    Bias |   RMSE |
|:------------------|:-----------------|-------:|-------------:|:------------------|----------:|:---------------|--------:|-------:|
| normal_equal      | current          |   1000 |         94.6 | 93.0-95.8         |      66.1 | 63.1-69.0      | -0.0008 | 0.03   |
| normal_equal      | size             |   1000 |         94.1 | 92.5-95.4         |      72.3 | 69.4-75.0      | -0.0008 | 0.0278 |
| normal_equal      | precision k100   |   1000 |         94   | 92.4-95.3         |      72.4 | 69.5-75.1      | -0.0008 | 0.0279 |
| normal_equal      | precision k20    |   1000 |         94   | 92.4-95.3         |      72   | 69.1-74.7      | -0.0008 | 0.0279 |
| normal_equal      | oracle precision |   1000 |         94.1 | 92.5-95.4         |      72.3 | 69.4-75.0      | -0.0008 | 0.0278 |
| normal_unequal    | current          |   1000 |         94.2 | 92.6-95.5         |      59.3 | 56.2-62.3      | -0.0008 | 0.0328 |
| normal_unequal    | size             |   1000 |         93.9 | 92.2-95.2         |      76.5 | 73.8-79.0      | -0.0006 | 0.0247 |
| normal_unequal    | precision k100   |   1000 |         93.9 | 92.2-95.2         |      80   | 77.4-82.4      | -0.0007 | 0.0234 |
| normal_unequal    | precision k20    |   1000 |         93.7 | 92.0-95.0         |      80.9 | 78.3-83.2      | -0.0007 | 0.0234 |
| normal_unequal    | oracle precision |   1000 |         93.5 | 91.8-94.9         |      80.9 | 78.3-83.2      | -0.0006 | 0.0233 |
| t3_unequal        | current          |   1000 |         95.7 | 94.3-96.8         |      60   | 56.9-63.0      | -0.0002 | 0.0316 |
| t3_unequal        | size             |   1000 |         96.2 | 94.8-97.2         |      78   | 75.3-80.5      | -0      | 0.0242 |
| t3_unequal        | precision k100   |   1000 |         95.2 | 93.7-96.4         |      83.4 | 81.0-85.6      |  0      | 0.0211 |
| t3_unequal        | precision k20    |   1000 |         95   | 93.5-96.2         |      84.3 | 81.9-86.4      |  0.0001 | 0.021  |
| t3_unequal        | oracle precision |   1000 |         95.5 | 94.0-96.6         |      82.5 | 80.0-84.7      |  0.0001 | 0.0228 |
| lognormal_unequal | current          |   1000 |         94.4 | 92.8-95.7         |      68.3 | 65.4-71.1      | -0.0001 | 0.0325 |
| lognormal_unequal | size             |   1000 |         94.4 | 92.8-95.7         |      80.3 | 77.7-82.6      |  0.0001 | 0.0242 |
| lognormal_unequal | precision k100   |   1000 |         91.3 | 89.4-92.9         |      96.8 | 95.5-97.7      |  0.0091 | 0.0202 |
| lognormal_unequal | precision k20    |   1000 |         90.7 | 88.7-92.3         |      97.7 | 96.6-98.5      |  0.0109 | 0.0208 |
| lognormal_unequal | oracle precision |   1000 |         94.7 | 93.1-95.9         |      82.6 | 80.1-84.8      |  0.0002 | 0.0223 |

## Post hoc diagnostic: source of the skewed-error failure

After observing undercoverage, we reran the lognormal oracle-nuisance case with the same 1,000 evaluation datasets, changing only where variance weights were estimated. The additional independent weight-training sample has 6,102 observations, the same site sizes and DGP, and independent seed=20261010. Original evaluation seed=20261009. Recomputed original results match the main simulation. This is a diagnostic ablation, not a prespecified comparison or a fair equal-data-budget proposal.

| Rule                    |   Coverage % | Coverage MC 95%   |   Power % |   Mean estimate |
|:------------------------|-------------:|:------------------|----------:|----------------:|
| current                 |      94.4000 | 92.8-95.7         |   68.3000 |          0.0799 |
| size                    |      94.4000 | 92.8-95.7         |   80.3000 |          0.0801 |
| same sample k100        |      91.3000 | 89.4-92.9         |   96.8000 |          0.0891 |
| independent sample k100 |      94.5000 | 92.9-95.8         |   76.7000 |          0.0800 |
| DGP oracle precision    |      94.7000 | 93.1-95.9         |   82.6000 |          0.0802 |

With a true effect of 0.08, same-sample precision weights produce a mean estimate of 0.08913 and coverage of 91.3%, despite oracle nuisances. Independent-sample precision weights give a mean of 0.07996 and coverage of 94.5%; fixed DGP precision weights give 94.7% coverage. This isolates same-sample weight estimation as a contributor to the failure in this design, rather than nuisance fitting alone. Dependence between skewed estimation errors and their estimated variances can create biased weighting and spoil the required joint sign symmetry. Merely holding weights fixed during enumeration does not remove that dependence. The independent-sample diagnostic costs extra data and does not prove that an ordinary holdout or cross-fit version is universally valid; it also has lower power than simple size weights here.

The generalized guardrail is to retain this skewed-error case and oracle/independent-weight controls in future weighting evaluations. Any proposed precision-weight fix must report coverage as well as power before replacing the primary size-weight sensitivity.

## Limits and reproduction

The designs have a common effect and independent within-site errors. They do not establish validity for heterogeneous effects, common site shocks or arbitrary within-site dependence. Small sites remain small. Neither variance shrinkage nor small-site downweighting is a theorem repairing their Gaussian approximation. Conclusions from these four designs cannot establish universal optimality.

From the repository root set PYTHONPATH=fewclusters, OMP_NUM_THREADS=1 and OPENBLAS_NUM_THREADS=1. For each design run:

```text
python fewclusters/examples/weighting_simulation.py --design DESIGN --oracle-reps 1000 --fitted-reps 500 --output fewclusters/results/weighting_simulation/DESIGN.json
python fewclusters/examples/summarize_weighting_simulation.py
```

After all four designs finish, run `python fewclusters/examples/independent_weight_diagnostic.py`, then the summarizer. The simulation refuses to overwrite existing results. Seed=20261009; replication-indexed random streams are reproducible. Warnings are counted and retained in manifests. Any fitting/scoring failure is recorded; the summarizer refuses to silently produce the no-failure report if a failure occurred. Synthetic replication summaries contain no person-level JTPA data.
