# JTPA test-sample weighting comparison

**PRELIMINARY - NOT FOR PUBLICATION**

Three fixed splits (seeds 0, 1, 2), 6,102 women, 16 sites. All 65,536 sign vectors are enumerated. These are nominal 95% ART intervals: exact enumeration is not evidence of exact finite-sample coverage. Outcomes are earnings in dollars; the extract's precise earnings horizon and selection rules remain unverified. See [data and model caveats](../JTPA_COMPARISON.md).

## Findings

Giving small sites less weight reduces observed interval widths, and raises the estimated effect in these data. Stabilized precision weights reduce widths further. This is an empirical sensitivity exercise, not a coverage or power comparison. Larger-site weighting also changes the estimand if site effects differ.

The table summarizes separate runs; its medians and ranges are not a combined estimate or confidence interval. `p23` assumes assignment probability 2/3; `estimated` uses adaptively pooled propensity fits. Outcome nuisance fits use Claude's kappa=20 shrinkage and 20-row local-training floor in both cases.

| Propensity   | Method              | Weight rule               |   Median effect | Effect range   |   Median CI width | CI width range   | p(0) range       |
|:-------------|:--------------------|:--------------------------|----------------:|:---------------|------------------:|:-----------------|:-----------------|
| estimated    | DML shrink k20 both | current                   |             714 | 592 to 800     |             1,098 | 1,044 to 1,111   | 0.0121 to 0.0657 |
| estimated    | DML shrink k20 both | size                      |             888 | 833 to 924     |               993 | 992 to 1,026     | 0.0032 to 0.0162 |
| estimated    | DML shrink k20 both | precision k100            |             870 | 786 to 899     |               951 | 934 to 969       | 0.0035 to 0.0132 |
| estimated    | DML shrink k20 both | precision k20 sensitivity |             871 | 780 to 899     |               940 | 923 to 964       | 0.0038 to 0.0130 |
| p23          | DML shrink k20      | current                   |             810 | 804 to 909     |             1,048 | 1,043 to 1,077   | 0.0081 to 0.0184 |
| p23          | DML shrink k20      | size                      |           1,003 | 1,003 to 1,058 |               936 | 935 to 967       | 0.0023 to 0.0052 |
| p23          | DML shrink k20      | precision k100            |             972 | 960 to 1,031   |               900 | 895 to 909       | 0.0025 to 0.0051 |
| p23          | DML shrink k20      | precision k20 sensitivity |             969 | 953 to 1,029   |               897 | 886 to 908       | 0.0027 to 0.0052 |

Paired reductions relative to the current rule, using the same split and site estimates:

- estimated, size: median paired width reduction 7.7% (range 5.0% to 9.6%).
- estimated, precision k100: median paired width reduction 14.4% (range 7.2% to 14.9%).
- estimated, precision k20 sensitivity: median paired width reduction 15.4% (range 7.7% to 15.9%).
- p23, size: median paired width reduction 10.2% (range 7.7% to 13.2%).
- p23, precision k100: median paired width reduction 14.5% (range 12.8% to 16.4%).
- p23, precision k20 sensitivity: median paired width reduction 15.4% (range 12.9% to 16.7%).

## Weight definitions and restricted optimality

The code's score is S_g(theta) = sqrt(n_g) * (theta_hat_g - theta). The point estimate solves sum_g w_g S_g(theta)=0, so its effective weight on theta_hat_g is proportional to w_g sqrt(n_g).

| Rule | Score weight w_g, up to normalization | Effective effect weight |
|---|---|---|
| Current | 1 | sqrt(n_g) |
| Size | sqrt(n_g) | n_g |
| Stabilized precision | sqrt(n_g) / stabilized_tau_g_squared | n_g / stabilized_tau_g_squared |

If independent site estimates share a common effect and Var(theta_hat_g) = tau_g_squared/n_g, minimizing the variance among linear unbiased combinations gives inverse-variance effect weights n_g/tau_g_squared. This implies score weights sqrt(n_g)/tau_g_squared, not n_g/tau_g_squared. With independent Gaussian scores and known variances, the same weights arise from the conditional likelihood ratio against a fixed common shift (or an equally weighted mixture of its positive and negative versions). This is a restricted oracle argument, not a universal optimum for all alternatives, heterogeneity or estimated weights. See [Canay, Romano and Shaikh, Appendix A](https://home.uchicago.edu/amshaikh/webfiles/weakrand.pdf).

For the plug-in rule we calculate each site's influence contributions as v_i * (ytilde_i - theta_hat_g*v_i) / mean_g(v_i^2), and take their sample variance tauhat_g_squared. This assumes independent observations within sites for this variance calculation. It does not estimate a general within-site long-run variance.

The pooled target is the (n_g-1)-weighted average of these variances. Stabilization is ((n_g-1)*tauhat_g_squared + kappa*pooled)/(n_g-1+kappa), floored at 0.1*pooled. Kappa=100 is primary and kappa=20 is a prespecified sensitivity. These constants were fixed before viewing these weighting results. This kappa differs from the outcome-regression shrinkage kappa=20.

Weights are computed once and held fixed across sign permutations and tested null values. Precision weights use scoring residuals, so they are not independent of the scores. An asymptotic validity claim requires consistent variance estimation and joint score-limit conditions; this pilot does not establish them. The sign-invariance unit check alone does not prove conditional sign symmetry. Cross-site nuisance borrowing also needs the original theorem's conditions. Small-site downweighting and shrinkage do not establish normality, especially for the 38-row site.

## How much the smallest and largest sites count

These are effective weights on site effects, not the coefficients passed directly to the sign test. The current smallest-to-largest ratio is sqrt(38/1392)=0.165; size weighting reduces it to 38/1392=0.0273.

| Propensity   | Rule                      | Site   |    N |   Median effect weight (%) |
|:-------------|:--------------------------|:-------|-----:|---------------------------:|
| estimated    | current                   | MT     |   38 |                       2.17 |
| estimated    | current                   | IN     | 1392 |                      13.1  |
| estimated    | precision k100            | MT     |   38 |                       0.58 |
| estimated    | precision k100            | IN     | 1392 |                      17.73 |
| estimated    | precision k20 sensitivity | MT     |   38 |                       0.53 |
| estimated    | precision k20 sensitivity | IN     | 1392 |                      17.24 |
| estimated    | size                      | MT     |   38 |                       0.62 |
| estimated    | size                      | IN     | 1392 |                      22.81 |
| p23          | current                   | MT     |   38 |                       2.17 |
| p23          | current                   | IN     | 1392 |                      13.1  |
| p23          | precision k100            | MT     |   38 |                       0.57 |
| p23          | precision k100            | IN     | 1392 |                      18.04 |
| p23          | precision k20 sensitivity | MT     |   38 |                       0.52 |
| p23          | precision k20 sensitivity | IN     | 1392 |                      17.54 |
| p23          | size                      | MT     |   38 |                       0.62 |
| p23          | size                      | IN     | 1392 |                      22.81 |

## Same size-weight comparison for the benchmarks

Precision weighting was run only for the two shrinkage specifications above. Current and size weights were compared for every saved ART benchmark, including the fixed pooled fit. Ordinary pooled OLS with clustered standard errors is not an ART site-score method and is excluded from this reweighting exercise.

| Propensity   | Method                  | Weight rule   |   Median effect | Effect range   |   Median CI width | CI width range   | p(0) range       |
|:-------------|:------------------------|:--------------|----------------:|:---------------|------------------:|:-----------------|:-----------------|
| p23          | ART difference in means | current       |             953 | 953 to 953     |             1,503 | 1,503 to 1,503   | 0.0368 to 0.0368 |
| p23          | ART difference in means | size          |           1,247 | 1,247 to 1,247 |             1,293 | 1,293 to 1,293   | 0.0109 to 0.0109 |
| p23          | ART within-site OLS     | current       |             850 | 850 to 850     |             1,322 | 1,322 to 1,322   | 0.0372 to 0.0372 |
| p23          | ART within-site OLS     | size          |           1,141 | 1,141 to 1,141 |               966 | 966 to 966       | 0.0054 to 0.0054 |
| p23          | DML linear local        | current       |             807 | 794 to 824     |             1,391 | 1,356 to 1,464   | 0.0489 to 0.0617 |
| p23          | DML linear local        | size          |           1,110 | 1,103 to 1,140 |             1,018 | 985 to 1,056     | 0.0065 to 0.0084 |
| p23          | DML local full          | current       |             705 | 620 to 783     |             1,339 | 1,305 to 1,388   | 0.0378 to 0.0937 |
| p23          | DML local full          | size          |             893 | 787 to 982     |             1,220 | 1,167 to 1,302   | 0.0048 to 0.0374 |
| p23          | DML local matched       | current       |             571 | 554 to 609     |             1,326 | 1,297 to 1,340   | 0.1009 to 0.1128 |
| p23          | DML local matched       | size          |             768 | 766 to 872     |             1,147 | 1,137 to 1,178   | 0.0154 to 0.0280 |
| p23          | DML pooled matched      | current       |             895 | 857 to 936     |             1,013 | 1,003 to 1,038   | 0.0065 to 0.0130 |
| p23          | DML pooled matched      | size          |           1,071 | 1,048 to 1,087 |               903 | 878 to 912       | 0.0023 to 0.0036 |
| p23          | DML adaptive            | current       |             766 | 723 to 873     |             1,172 | 1,128 to 1,174   | 0.0146 to 0.0403 |
| p23          | DML adaptive            | size          |             987 | 968 to 1,048   |               962 | 955 to 1,011     | 0.0030 to 0.0076 |
| estimated    | ART difference in means | current       |             953 | 953 to 953     |             1,503 | 1,503 to 1,503   | 0.0368 to 0.0368 |
| estimated    | ART difference in means | size          |           1,247 | 1,247 to 1,247 |             1,293 | 1,293 to 1,293   | 0.0109 to 0.0109 |
| estimated    | ART within-site OLS     | current       |             850 | 850 to 850     |             1,322 | 1,322 to 1,322   | 0.0372 to 0.0372 |
| estimated    | ART within-site OLS     | size          |           1,141 | 1,141 to 1,141 |               966 | 966 to 966       | 0.0054 to 0.0054 |
| estimated    | DML linear local        | current       |             497 | 385 to 566     |             1,398 | 1,355 to 1,474   | 0.1396 to 0.2644 |
| estimated    | DML linear local        | size          |             738 | 637 to 890     |             1,174 | 1,116 to 1,232   | 0.0168 to 0.0711 |
| estimated    | DML local full          | current       |             601 | 364 to 762     |             1,538 | 1,404 to 1,678   | 0.0548 to 0.3677 |
| estimated    | DML local full          | size          |             754 | 502 to 985     |             1,501 | 1,316 to 1,735   | 0.0101 to 0.3008 |
| estimated    | DML local matched       | current       |             479 | 412 to 597     |             1,357 | 1,343 to 1,433   | 0.0988 to 0.2403 |
| estimated    | DML local matched       | size          |             767 | 535 to 790     |             1,185 | 1,185 to 1,333   | 0.0226 to 0.1446 |
| estimated    | DML pooled matched      | current       |             616 | 600 to 777     |             1,041 | 1,008 to 1,054   | 0.0142 to 0.0512 |
| estimated    | DML pooled matched      | size          |             809 | 728 to 923     |               937 | 924 to 943       | 0.0033 to 0.0107 |
| estimated    | DML adaptive            | current       |             553 | 494 to 752     |             1,163 | 1,124 to 1,168   | 0.0255 to 0.1230 |
| estimated    | DML adaptive            | size          |             751 | 679 to 913     |               988 | 953 to 1,025     | 0.0034 to 0.0210 |
| estimated    | DML adaptive both       | current       |             683 | 523 to 770     |             1,186 | 1,124 to 1,218   | 0.0218 to 0.1216 |
| estimated    | DML adaptive both       | size          |             879 | 802 to 918     |             1,010 | 1,010 to 1,063   | 0.0040 to 0.0241 |
| p23          | DML shrink k20          | current       |             810 | 804 to 909     |             1,048 | 1,043 to 1,077   | 0.0081 to 0.0184 |
| p23          | DML shrink k20          | size          |           1,003 | 1,003 to 1,058 |               936 | 935 to 967       | 0.0023 to 0.0052 |
| estimated    | DML shrink k20          | current       |             580 | 547 to 775     |             1,076 | 1,032 to 1,093   | 0.0156 to 0.0746 |
| estimated    | DML shrink k20          | size          |             772 | 689 to 916     |               961 | 935 to 1,006     | 0.0030 to 0.0172 |
| estimated    | DML shrink k20 both     | current       |             714 | 592 to 800     |             1,098 | 1,044 to 1,111   | 0.0121 to 0.0657 |
| estimated    | DML shrink k20 both     | size          |             888 | 833 to 924     |               993 | 992 to 1,026     | 0.0032 to 0.0162 |

## Reproduction and validation

Run `jtpa_size_weights.py`, then `jtpa_weighting_fit.py 0`, `1`, and `2`, then `summarize_jtpa_weighting.py`, with `PYTHONPATH` pointing to the package directory. Fit scripts deliberately stop if an old residual cache exists; preserve or move it after checking provenance before refitting. Individual residual predictions stay in ignored `jtpa_data/`; only aggregate site diagnostics are tracked.

Each reconstructed shrinkage site estimate matched its saved counterpart (rtol=1e-10, atol=1e-7). Recomputed current and size summaries also matched saved results. The summarizer validates 120 unique finite method/split/weight combinations and normalized positive weights. Four new weight tests check the score-versus-effect normalization, constant-variance equivalence, scale/sign transformations, and invalid inputs; the full suite passed 63 tests.

Next evidence needed before choosing a publication specification: simulated null coverage and power with unequal sizes, earnings-like heavy tails, heterogeneous effects and shared nuisance training. Keep all specified weight rules visible; do not select the smallest p-value.
