# JTPA p23, seed 2

**PRELIMINARY - NOT FOR PUBLICATION**

N=6102; dropped=0; sites=16; split seed=2.
Propensity: ASSUMED p=2/3 sensitivity; overall design ratio documented but extract selection and assignment mechanism not fully verified

Exploratory comparison. ART coverage requires the common-effect and sampling assumptions. Observed interval length is not a measure of coverage or power. Earnings timing and extract selection require source verification.

ART point estimates weight site estimates by sqrt(n_site); pooled OLS generally uses different weights. Differences can reflect effect heterogeneity as well as adjustment.

| Method | Estimate | CI low | CI high | Length | p(0) |
|---|---:|---:|---:|---:|---:|
| OLS site FE CR1 | 1197.8 | 741.6 | 1653.9 | 912.3 | 0.0001 |
| ART difference in means | 953.4 | 86.8 | 1589.8 | 1503.0 | 0.0368 |
| ART within-site OLS | 849.5 | 72.3 | 1394.7 | 1322.4 | 0.0372 |
| DML linear local | 794.3 | -62.9 | 1400.8 | 1463.7 | 0.0617 |
| DML local full | 704.8 | -35.5 | 1303.5 | 1339.1 | 0.0589 |
| DML local matched | 570.6 | -176.8 | 1163.3 | 1340.1 | 0.1098 |
| DML pooled matched | 935.9 | 372.1 | 1384.6 | 1012.5 | 0.0065 |
| DML adaptive | 872.8 | 238.4 | 1366.6 | 1128.2 | 0.0146 |
| DML shrink k20 | 909.1 | 329.7 | 1372.3 | 1042.6 | 0.0081 |

SMALL-SITE WARNING: JC: n=81, MT: n=38, OH: n=74, OK: n=87. Normal approximation may be poor; small calibration folds give noisy weights. Shrinkage alone does not establish normality. The n<100 flag is a diagnostic heuristic.

Local full uses all non-evaluation observations. Local matched, pooled matched, and adaptive reserve the same calibration fold. With estimated m, its local fit uses these respective training allocations too.

Exact sign enumeration means all signs were enumerated; it is not exact finite-sample randomization inference.
