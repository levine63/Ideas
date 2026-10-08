# JTPA estimated, seed 1

**PRELIMINARY - NOT FOR PUBLICATION**

N=6102; dropped=0; sites=16; split seed=1.
Propensity: Estimated separately within site by cross-fitted boosted classifier; not known

Exploratory comparison. ART coverage requires the common-effect and sampling assumptions. Observed interval length is not a measure of coverage or power. Earnings timing and extract selection require source verification.

ART point estimates weight site estimates by sqrt(n_site); pooled OLS generally uses different weights. Differences can reflect effect heterogeneity as well as adjustment.

| Method | Estimate | CI low | CI high | Length | p(0) |
|---|---:|---:|---:|---:|---:|
| OLS site FE CR1 | 1197.8 | 741.6 | 1653.9 | 912.3 | 0.0001 |
| ART difference in means | 953.4 | 86.8 | 1589.8 | 1503.0 | 0.0368 |
| ART within-site OLS | 849.5 | 72.3 | 1394.7 | 1322.4 | 0.0372 |
| DML linear local | 566.3 | -252.7 | 1145.7 | 1398.4 | 0.1396 |
| DML local full | 762.4 | -18.7 | 1385.0 | 1403.8 | 0.0548 |
| DML local matched | 479.3 | -302.7 | 1054.7 | 1357.4 | 0.1889 |
| DML pooled matched | 599.6 | -3.5 | 1050.1 | 1053.5 | 0.0512 |
| DML adaptive | 494.4 | -182.8 | 980.1 | 1162.9 | 0.1230 |
| DML adaptive both | 522.7 | -191.3 | 1026.9 | 1218.3 | 0.1216 |
| DML shrink k20 | 547.0 | -72.4 | 1004.0 | 1076.4 | 0.0746 |
| DML shrink k20 both | 592.4 | -52.4 | 1059.0 | 1111.4 | 0.0657 |

SMALL-SITE WARNING: JC: n=81, MT: n=38, OH: n=74, OK: n=87. Normal approximation may be poor; small calibration folds give noisy weights. Shrinkage alone does not establish normality. The n<100 flag is a diagnostic heuristic.

Local full uses all non-evaluation observations. Local matched, pooled matched, and adaptive reserve the same calibration fold. With estimated m, its local fit uses these respective training allocations too.

Exact sign enumeration means all signs were enumerated; it is not exact finite-sample randomization inference.
