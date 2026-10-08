# JTPA pilot

**PRELIMINARY - NOT FOR PUBLICATION**

N=6102; dropped=0; sites=16; split seed=0.
Propensity: Estimated separately within site by cross-fitted boosted classifier; not known

Exploratory comparison. ART coverage requires the common-effect and sampling assumptions. Observed interval length is not a measure of coverage or power. Earnings timing and extract selection require source verification.

ART point estimates weight site estimates by sqrt(n_site); pooled OLS generally uses different weights. Differences can reflect effect heterogeneity as well as adjustment.

| Method | Estimate | CI low | CI high | Length | p(0) |
|---|---:|---:|---:|---:|---:|
| OLS site FE CR1 | 1197.8 | 741.6 | 1653.9 | 912.3 | 0.0001 |
| ART difference in means | 953.4 | 86.8 | 1589.8 | 1503.0 | 0.0368 |
| ART within-site OLS | 849.5 | 72.3 | 1394.7 | 1322.4 | 0.0372 |
| DML linear local | 385.0 | -390.5 | 964.2 | 1354.7 | 0.2644 |
| DML local full | 363.8 | -533.5 | 1144.6 | 1678.1 | 0.3677 |
| DML local matched | 411.6 | -351.3 | 1082.2 | 1433.5 | 0.2403 |
| DML pooled matched | 615.5 | 52.5 | 1093.5 | 1041.0 | 0.0367 |
| DML adaptive | 553.1 | -79.8 | 1088.7 | 1168.4 | 0.0771 |
| DML adaptive both | 683.2 | 12.3 | 1198.1 | 1185.8 | 0.0470 |

SMALL-SITE WARNING: JC: n=81, MT: n=38, OH: n=74, OK: n=87. Normal approximation may be poor; small calibration folds give noisy weights. Shrinkage alone does not establish normality. The n<100 flag is a diagnostic heuristic.

Local full uses all non-evaluation observations. Local matched, pooled matched, and adaptive reserve the same calibration fold. With estimated m, its local fit uses these respective training allocations too.

Exact sign enumeration means all signs were enumerated; it is not exact finite-sample randomization inference.
