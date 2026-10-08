# JTPA preliminary estimator comparison

**PRELIMINARY - NOT FOR PUBLICATION**

6,102 women, 16 sites, no rows dropped. Dollar earnings Y as supplied by senseweight; the exact earnings horizon and sample construction remain unverified. Covariates: previous earnings, age, marital status, Black and Hispanic indicators, high-school/GED status, years of education.

Five folds and three fixed split seeds (0, 1, 2). All 65,536 sign vectors enumerated for each ART. Intervals are nominal 95% intervals under the stated model, not validated coverage on these data.

Four sites are small: MT 38, OH 74, JC 81, OK 87. MT calibration folds have 7-8 observations and local training folds have 22-23. The 20-row fallback therefore never activates in this sample. Shrinkage helps stabilize prediction weights; it does not establish normality of site scores.

ART aggregates site estimates with sqrt(n_site) weights. Pooled OLS generally targets different weights when effects are heterogeneous. Do not interpret every estimate difference as estimator bias.

## Assumed two-thirds propensity

The two-thirds scenario is an explicit design assumption; it is not verified for the selected extract.

| Method | Estimate median [range] | Interval length median [range] | p(0) range |
|---|---:|---:|---:|
| OLS site FE CR1 | 1198 [1198, 1198] | 912 [912, 912] | 0.0001-0.0001 |
| ART difference in means | 953 [953, 953] | 1503 [1503, 1503] | 0.0368-0.0368 |
| ART within-site OLS | 850 [850, 850] | 1322 [1322, 1322] | 0.0372-0.0372 |
| DML linear local | 807 [794, 824] | 1391 [1356, 1464] | 0.0489-0.0617 |
| DML local full | 705 [620, 783] | 1339 [1305, 1388] | 0.0378-0.0937 |
| DML local matched | 571 [554, 609] | 1326 [1297, 1340] | 0.1009-0.1128 |
| DML pooled matched | 895 [857, 936] | 1013 [1003, 1038] | 0.0065-0.0130 |
| DML adaptive | 766 [723, 873] | 1172 [1128, 1174] | 0.0146-0.0403 |
| DML shrink k20 | 810 [804, 909] | 1048 [1043, 1077] | 0.0081-0.0184 |

Shrinkage reduces interval length relative to the original outcome-adaptive method by 7.6% to 10.7% across these splits (negative means lengthening). This is descriptive; it is not evidence about coverage or power.

## Estimated propensity sensitivity

Propensities are learned locally by gradient boosting, except methods labeled both, which also adaptively pool the propensity. These fits do not establish the rate assumptions or resolve outcome selection.

| Method | Estimate median [range] | Interval length median [range] | p(0) range |
|---|---:|---:|---:|
| OLS site FE CR1 | 1198 [1198, 1198] | 912 [912, 912] | 0.0001-0.0001 |
| ART difference in means | 953 [953, 953] | 1503 [1503, 1503] | 0.0368-0.0368 |
| ART within-site OLS | 850 [850, 850] | 1322 [1322, 1322] | 0.0372-0.0372 |
| DML linear local | 497 [385, 566] | 1398 [1355, 1474] | 0.1396-0.2644 |
| DML local full | 601 [364, 762] | 1538 [1404, 1678] | 0.0548-0.3677 |
| DML local matched | 479 [412, 597] | 1357 [1343, 1433] | 0.0988-0.2403 |
| DML pooled matched | 616 [600, 777] | 1041 [1008, 1054] | 0.0142-0.0512 |
| DML adaptive | 553 [494, 752] | 1163 [1124, 1168] | 0.0255-0.1230 |
| DML adaptive both | 683 [523, 770] | 1186 [1124, 1218] | 0.0218-0.1216 |
| DML shrink k20 | 580 [547, 775] | 1076 [1032, 1093] | 0.0156-0.0746 |
| DML shrink k20 both | 714 [592, 800] | 1098 [1044, 1111] | 0.0121-0.0657 |

Shrinkage reduces interval length relative to the original outcome-adaptive method by 6.5% to 8.2% across these splits (negative means lengthening). This is descriptive; it is not evidence about coverage or power.

## Interpretation and next work

The original adaptive method sets shrink_l=0 and min_local_train=0. Shrinkage uses kappa_l=20, kappa_m=0 and min_local_train=20. Local matched and pooled matched use the same reduced training allocation as adaptive fitting. Local full uses all non-evaluation observations.

Three split repetitions measure sensitivity to sample splitting, not repeated-sampling uncertainty. No split was selected for favorable p-values or interval lengths. An empirical dataset has no known true treatment effect, so this exercise cannot rank coverage or mean squared estimation error.

Next scientific checks: reconcile the full JTPA archive and assignment/selection documentation; simulate common-effect outcomes on the actual site sizes and covariates to measure coverage, power and RMSE; and separately stress-test heterogeneous effects and heavy-tailed site scores. The existing theoretical result does not justify arbitrary cross-site treatment-effect heterogeneity.

Novelty assessment and prior-work handoff: [JTPA_HANDOFF.md](../JTPA_HANDOFF.md). Data source: https://www.upjohn.org/data-tools/employment-research-data-center/national-jtpa-study .
