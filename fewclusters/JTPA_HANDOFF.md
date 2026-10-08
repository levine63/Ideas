# Novelty assessment and JTPA handoff

**PRELIMINARY - NOT FOR PUBLICATION**

Assessment date: October 8, 2026. The attached short_note_clearer.docx is the source of the theorem claims. Document instructions were treated as source material, not additional user authorization. The supplement referenced in that note was not present in the repository inspected.

## Is the note novel?

My assessment: potentially a useful, modest methods note, but not yet an established new methodological result. A bounded empirical pilot is worthwhile. Do not claim a new randomization test, a new orthogonal score, or the general invention of adaptive pooling.

Proposition 1 combines a standard cross-fitted partially linear score expansion with the existing approximate-symmetry test. Its useful feature is spelling out how cross-cluster borrowing can become asymptotically negligible with fixed q and growing site samples. It is an application/extension of existing machinery, not a new sign-test theorem. Cai et al. supply the underlying implementation and confidence-set construction: https://home.uchicago.edu/amshaikh/webfiles/usersguide.pdf

Proposition 2 is the strongest novelty candidate: an explicit two-candidate finite-moment risk bound, with disagreement H and variance ratios, and its implication for per-site DML rates. However, a 1/s excess-risk rate for a fixed small convex dictionary is already established under bounded regression. Lecue (2013), Theorem A, gives the M/s rate when M <= sqrt(s); M=2 includes this setting. The note should cite and compare its assumptions, not present the rate itself as new: https://arxiv.org/pdf/1312.4349

Ahrens, Hansen, Schaffer and Wiemann already combine stacking and DML, including short-stacking and pooled stacking. Their pooled stacking concerns common weights across folds; that is different from borrowing observations across heterogeneous sites, but the distinction must be explained precisely: https://doi.org/10.1002/jae.3103

The known-propensity robustness result is a useful specialized corollary, not a new robustness principle. The note correctly requires honest fitting and convergence to a deterministic outcome-prediction limit. Its discussion of estimated propensity combined with a misspecified outcome model is consistent with the issue studied by Dukes, Vansteelandt and Whitney: https://jmlr.org/papers/v25/22-1233.html

The finite-range dependence extension is narrow. The baseline assumes iid observations within each site, unlike a generic promise of arbitrary cluster dependence. The common treatment coefficient is also substantive. A successful JTPA fit cannot verify either assumption, and an interval-length comparison cannot establish coverage or power.

Before a novelty claim is publication-ready: inspect the full supplement, compare the finite-moment aggregation bound with prior aggregation results, obtain an independent proof review, and run coverage/power experiments with the actual algorithm and small-site configurations. The present assessment is a targeted literature comparison, not an exhaustive priority search or proof certification.

## Prior work recovered

- Repository: https://github.com/levine63/Ideas, fewclusters/.
- Baseline main commit e4f1794; REVIEW_RESPONSE.md records the earlier code audit and RESULTS.md the repaired Monte Carlo.
- ChatGPT chat “Review Clustered DRML Literature” pointed to the package and download work. Some older responses were returned only as opaque content references, so their complete text was not visible.
- Draft PR #1 supplies the downloader and the explicit warning that observed assignment shares are not known design probabilities: https://github.com/levine63/Ideas/pull/1
- Claude's commit 3e9fc11 adds shrinkage, the minimum local-training size, small-site warnings, and small_clusters.py. It has been merged into this experiment branch. Its simulation results are a separate upstream workstream.

## Root causes and generalized guardrails

The previous JTPA example computed observed site/stratum treatment shares after dropping missing rows and supplied them as m_known. This confused realized allocations with externally specified design probabilities and overstated applicability of Corollary 2. The revised driver defaults to estimated propensities; supplied probabilities require an explicit source or assumption. Tests ensure changing observed assignments cannot change an externally supplied probability vector. Sibling simulation and quickstart flows use their actual DGP propensities and do not have this error.

The prior ART-DIM and ART-OLS labels described cross-fitted nuisance variants rather than literal difference-in-means and within-site OLS. The driver now computes those benchmarks directly and tests them against their definitions. Cross-fitted linear adjustment is reported separately. ART aggregates site estimates using sqrt(n_site) weights; pooled OLS generally has different weights. With heterogeneous effects, these differences can change the estimand.

Adaptive fitting reserves calibration rows while ordinary local fitting does not. The comparison now includes both ordinary local fitting and local/pooled candidates with matched training allocations. reserve_calibration makes this explicit, with tests checking the row roles. An apparent benefit should not be described as a pure pooling effect without addressing this training-sample cost.

Upstream shrinkage changed the default algorithm. Original pilot methods explicitly set shrink_l=0 and min_local_train=0; separate methods use shrink_l=20, shrink_m=0, min_local_train=20. This prevents a default change from silently relabeling old results. Original adaptive-both and shrinkage-adaptive-both variants are also compared with estimated propensities.

Small sites produce runtime and report warnings, including very small calibration samples. These are heuristic flags, not validated normality cutoffs. Shrinkage can stabilize nuisance prediction but does not establish Gaussian cluster scores. The minimum-training floor applies to both nuisance models; forcing a borrowed propensity in a tiny heterogeneous site remains a concern even when shrink_m=0.

## Data and interpretation

Both sources downloaded successfully. Original Upjohn ZIP: 127,676,441 bytes, 388 members. Women's extract: 6,102 rows, 16 sites, no missing values in the supplied columns. Site sizes range from 38 to 1,392. Four sites have fewer than 100 women. Package documentation says 6,109 rows; the manifest preserves the actual 6,102 without silently reconciling that discrepancy.

The women's file identifies T as assignment and Y as dollar earnings, but does not establish the earnings horizon or the complete extraction/selection process. The original archive contains a final 30-month earnings file, but Y has not been linked to that file. Do not label this extract's Y “30-month earnings” without reconciliation. hrwage is excluded from the pilot because the extract documentation does not sufficiently establish its timing. The seven other adjustment variables are used as provisionally baseline covariates; their exact construction should be verified for publication.

The overall study documentation supports an approximately two-to-one assignment design. The pilot therefore reports p=2/3 as an explicit assumption, not a verified extract-specific randomization mechanism. Estimated-propensity runs are a sensitivity comparison and do not solve attrition or establish the nuisance-rate conditions.

Original data are ignored by Git. Manifests and an archive inventory are under fewclusters/jtpa_data locally. No row-level research records are intended for publication in this branch. Every reported result is preliminary and not for publication.


## Claude's small-cluster simulation update

Commit f2176de arrived during the pilot and has been integrated. It reports
500-replication comparisons with sizes 10, 25, 40, 200, 400, 800. For known
propensity, shrinkage/floor power is 0.308 versus 0.288 unshrunk; for estimated
propensity, 0.301 versus 0.236. Reported 5% null rejection rates for these
variants are 0.032, near the attainable 1/32. These are Claude's supplied
simulation results, not independently rerun in this task.

Two interpretation claims were narrowed in this branch: honest splitting
alone does not establish centering/symmetry with estimated propensities; and
prespecified weights preserve the sign argument only under its assumptions.
Guardrail: separate empirical rejection frequencies in a specified DGP from
a general validity claim. Neither Gaussian errors in one simulation nor
shrinkage eliminates the need for skewed/heavy-tailed small-site tests.


## Shrinkage theory interpretation

The new weight is a convex combination of the empirical calibrated weight
and full borrowing. Convexity gives R(w_shrunk) <= lambda R(w_raw) +
(1-lambda)R(1), where lambda=s/(s+kappa). With fixed kappa, calibration
size proportional to site size, and stochastically bounded borrowing risk,
the extra upper bound is O_p(1/s). The local-fit floor eventually switches
off as every site grows. These are the conditions behind preservation of
large-site learning rates; the bound does not guarantee finite-sample gains.
If some sites remain fixed and tiny as others grow, the original theorem's
min_j n_j -> infinity condition is not met. Shrinkage alone does not extend
the theorem to that different asymptotic regime.

Data QA also checked the binary indicators and numeric ranges: assignment,
marital, race/ethnicity, and high-school indicators are coded 0/1; observed
ages run from 22 to 77 and education from 7 to 17. This does not verify
imputation or extraction rules. Earnings reach 114,739 dollars, reinforcing
the need for an earnings-tail stress test rather than relying only on
Gaussian-error simulations.

## Test-sample weighting follow-up (2026-10-08)

Implemented the user's requested comparison, retaining the PRELIMINARY - NOT
FOR PUBLICATION label. Results and theory are in
[weighting/WEIGHTING_COMPARISON.md](results/weighting/WEIGHTING_COMPARISON.md).
All three splits are retained. Size weights are compared for all saved ART
benchmarks; stabilized precision weights are compared for the shrinkage
known-propensity and adaptive-propensity specifications.

Root cause of the potential weighting error: the ART input already multiplies
site estimates by sqrt(n). Passing n as its weight would produce effective
n^(3/2) weights. The helper and regression test explicitly distinguish score
weights sqrt(n)/tau_squared from effect weights n/tau_squared; constant score
variance must reproduce size weighting. Additional tests cover stabilization,
rescaling, sitewise residual sign changes and invalid variance inputs. The full
suite passed 63 tests. The sign-invariance check is not a validity theorem.

The earlier aggregate files did not preserve influence residuals needed for
precision weighting. Reconstructed nuisance fits match every saved site
estimate, and an ignored residual cache now preserves these fits for further
sensitivity work. Existing caches block silent refitting with changed provenance.
The summary checks 120 unique comparisons, matching reconstructed summaries,
finite intervals/p-values and positive normalized weights. Variance shrinkage
kappa=100, sensitivity kappa=20 and the 0.1 pooled-variance floor were fixed
before inspecting weighting results. They differ from outcome shrinkage kappa=20.
Weights stay fixed across signs and null values.

Median paired width reductions are 7.7% (estimated propensity) and 10.2%
(assumed p=2/3) for size weights, and 14.4% / 14.5% for primary precision
weights. Estimated effects increase with size weighting. Do not interpret
shorter observed intervals as improved coverage/power or unchanged targets
under heterogeneous effects. Plug-in variances assume within-site independence;
additional score/variance-limit assumptions are needed for estimated weights.
Downweighting does not repair the small-site Gaussian approximation. Unequal
sizes, heavy tails, heterogeneity and common nuisance training should enter the
next simulation design before choosing a publication specification.
