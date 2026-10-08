# JTPA pilot

**PRELIMINARY - NOT FOR PUBLICATION**

N=6102; dropped=0; sites=16; split seed=2.
Propensity: Estimated separately within site by cross-fitted boosted classifier; not known

Exploratory comparison. ART coverage requires the common-effect and sampling assumptions. Observed interval length is not a measure of coverage or power. Earnings timing and extract selection require source verification.

ART point estimates weight site estimates by sqrt(n_site); pooled OLS generally uses different weights. Differences can reflect effect heterogeneity as well as adjustment.

| Method | Estimate | CI low | CI high | Length | p(0) |
|---|---:|---:|---:|---:|---:|
| OLS site FE CR1 | 1197.8 | 741.6 | 1653.9 | 912.3 | 0.0001 |
| ART difference in means | 953.4 | 86.8 | 1589.8 | 1503.0 | 0.0368 |
| ART within-site OLS | 849.5 | 72.3 | 1394.7 | 1322.4 | 0.0372 |
| DML linear local | 497.4 | -333.8 | 1140.2 | 1474.0 | 0.1876 |
| DML local full | 601.4 | -224.1 | 1313.4 | 1537.6 | 0.1291 |
| DML local matched | 596.9 | -149.6 | 1193.1 | 1342.7 | 0.0988 |
| DML pooled matched | 776.7 | 217.0 | 1224.8 | 1007.8 | 0.0142 |
| DML adaptive | 752.4 | 126.5 | 1250.8 | 1124.4 | 0.0255 |
| DML adaptive both | 770.4 | 151.5 | 1275.8 | 1124.3 | 0.0218 |

SMALL-SITE WARNING: JC: n=81, MT: n=38, OH: n=74, OK: n=87. Normal approximation may be poor; small calibration folds give noisy weights. Shrinkage alone does not establish normality. The n<100 flag is a diagnostic heuristic.

Local full uses all non-evaluation observations. Local matched, pooled matched, and adaptive reserve the same calibration fold. With estimated m, its local fit uses these respective training allocations too.

Exact sign enumeration means all signs were enumerated; it is not exact finite-sample randomization inference.
