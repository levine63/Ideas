# JTPA pilot

**PRELIMINARY - NOT FOR PUBLICATION**

N=6102; dropped=0; sites=16; split seed=1.
Propensity: ASSUMED p=2/3 sensitivity; overall design ratio documented but extract selection and assignment mechanism not fully verified

Exploratory comparison. ART coverage requires the common-effect and sampling assumptions. Observed interval length is not a measure of coverage or power. Earnings timing and extract selection require source verification.

ART point estimates weight site estimates by sqrt(n_site); pooled OLS generally uses different weights. Differences can reflect effect heterogeneity as well as adjustment.

| Method | Estimate | CI low | CI high | Length | p(0) |
|---|---:|---:|---:|---:|---:|
| OLS site FE CR1 | 1197.8 | 741.6 | 1653.9 | 912.3 | 0.0001 |
| ART difference in means | 953.4 | 86.8 | 1589.8 | 1503.0 | 0.0368 |
| ART within-site OLS | 849.5 | 72.3 | 1394.7 | 1322.4 | 0.0372 |
| DML linear local | 824.1 | 4.1 | 1394.7 | 1390.6 | 0.0493 |
| DML local full | 783.0 | 57.3 | 1362.7 | 1305.3 | 0.0378 |
| DML local matched | 608.7 | -148.6 | 1177.3 | 1325.8 | 0.1009 |
| DML pooled matched | 895.3 | 326.7 | 1330.0 | 1003.4 | 0.0075 |
| DML adaptive | 723.2 | 44.4 | 1218.0 | 1173.6 | 0.0403 |

SMALL-SITE WARNING: JC: n=81, MT: n=38, OH: n=74, OK: n=87. Normal approximation may be poor; small calibration folds give noisy weights. Shrinkage alone does not establish normality. The n<100 flag is a diagnostic heuristic.

Local full uses all non-evaluation observations. Local matched, pooled matched, and adaptive reserve the same calibration fold. With estimated m, its local fit uses these respective training allocations too.

Exact sign enumeration means all signs were enumerated; it is not exact finite-sample randomization inference.
