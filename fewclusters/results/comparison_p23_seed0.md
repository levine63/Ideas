# JTPA p23, seed 0

**PRELIMINARY - NOT FOR PUBLICATION**

N=6102; dropped=0; sites=16; split seed=0.
Propensity: ASSUMED p=2/3 sensitivity; overall design ratio documented but extract selection and assignment mechanism not fully verified

Exploratory comparison. ART coverage requires the common-effect and sampling assumptions. Observed interval length is not a measure of coverage or power. Earnings timing and extract selection require source verification.

ART point estimates weight site estimates by sqrt(n_site); pooled OLS generally uses different weights. Differences can reflect effect heterogeneity as well as adjustment.

| Method | Estimate | CI low | CI high | Length | p(0) |
|---|---:|---:|---:|---:|---:|
| OLS site FE CR1 | 1197.8 | 741.6 | 1653.9 | 912.3 | 0.0001 |
| ART difference in means | 953.4 | 86.8 | 1589.8 | 1503.0 | 0.0368 |
| ART within-site OLS | 849.5 | 72.3 | 1394.7 | 1322.4 | 0.0372 |
| DML linear local | 806.8 | 5.7 | 1361.8 | 1356.1 | 0.0489 |
| DML local full | 620.0 | -137.5 | 1250.1 | 1387.7 | 0.0937 |
| DML local matched | 554.2 | -172.1 | 1124.8 | 1296.8 | 0.1128 |
| DML pooled matched | 856.6 | 262.8 | 1301.0 | 1038.2 | 0.0130 |
| DML adaptive | 766.4 | 93.8 | 1266.0 | 1172.2 | 0.0322 |
| DML shrink k20 | 809.7 | 196.1 | 1273.5 | 1077.4 | 0.0184 |

SMALL-SITE WARNING: JC: n=81, MT: n=38, OH: n=74, OK: n=87. Normal approximation may be poor; small calibration folds give noisy weights. Shrinkage alone does not establish normality. The n<100 flag is a diagnostic heuristic.

Local full uses all non-evaluation observations. Local matched, pooled matched, and adaptive reserve the same calibration fold. With estimated m, its local fit uses these respective training allocations too.

Exact sign enumeration means all signs were enumerated; it is not exact finite-sample randomization inference.
