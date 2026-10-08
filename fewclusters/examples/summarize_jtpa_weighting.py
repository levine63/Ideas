"""Validate and summarize prespecified preliminary JTPA weighting comparisons."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
out = root / 'results/weighting'
base = json.loads((out / 'size_comparison.json').read_text())['rows']
rows = list(base)
site_frames = []
for seed in range(3):
    run = json.loads((out / f'seed{seed}.json').read_text())
    for row in run['rows']:
        if row['weighting'] in ('current', 'size'):
            old = [x for x in base if all(x[k] == row[k] for k in ('mode', 'seed', 'method', 'weighting'))]
            assert len(old) == 1
            np.testing.assert_allclose([row[k] for k in ('est','lo','hi','p0')],
                                       [old[0][k] for k in ('est','lo','hi','p0')], rtol=1e-9, atol=1e-6)
        else:
            rows.append(row)
    sites = pd.DataFrame(run['sites']).assign(seed=seed)
    for _, group in sites.groupby(['mode', 'weighting']):
        assert len(group) == 16
        assert (group[['score_weight','effect_weight']] > 0).all().all()
        np.testing.assert_allclose(group[['score_weight','effect_weight']].sum(), 1)
    site_frames.append(sites)
df = pd.DataFrame(rows)
assert len(df) == 120 and not df.duplicated(['mode','seed','method','weighting']).any()
assert np.isfinite(df[['est','lo','hi','length','p0']]).all().all()
assert (df.lo < df.hi).all() and df.p0.between(0,1).all()
df.to_csv(out / 'all_weighting_results.csv', index=False)
site_df = pd.concat(site_frames, ignore_index=True)
site_df.to_csv(out / 'shrinkage_site_weights.csv', index=False)

main = df[((df['mode'] == 'p23') & (df.method == 'DML shrink k20')) |
          ((df['mode'] == 'estimated') & (df.method == 'DML shrink k20 both'))]
order = ['current','size','precision k100','precision k20 sensitivity']
def table(frame):
    records = []
    for (mode, method, weighting), g in frame.groupby(['mode','method','weighting'], sort=False):
        records.append({'Propensity':mode, 'Method':method, 'Weight rule':weighting,
                        'Median effect':f'{g.est.median():,.0f}',
                        'Effect range':f'{g.est.min():,.0f} to {g.est.max():,.0f}',
                        'Median CI width':f'{g.length.median():,.0f}',
                        'CI width range':f'{g.length.min():,.0f} to {g.length.max():,.0f}',
                        'p(0) range':f'{g.p0.min():.4f} to {g.p0.max():.4f}'})
    return pd.DataFrame(records).to_markdown(index=False)
main = main.assign(weighting=pd.Categorical(main.weighting, order, ordered=True)).sort_values(['mode','weighting','seed'])
changes=[]
for mode,g in main.groupby('mode'):
    p=g.pivot(index='seed',columns='weighting',values='length')
    for rule in order[1:]:
        pct=100*(1-p[rule]/p['current'])
        changes.append(f'- {mode}, {rule}: median paired width reduction {pct.median():.1f}% (range {pct.min():.1f}% to {pct.max():.1f}%).')
weight_rows=[]
for (mode,rule),g in site_df.groupby(['mode','weighting']):
    for site in ['MT','IN']:
        z=g[g.site==site]
        weight_rows.append({'Propensity':mode,'Rule':rule,'Site':site,'N':int(z.n.iloc[0]),'Median effect weight (%)':round(100*z.effect_weight.median(),2)})
text='''# JTPA test-sample weighting comparison

**PRELIMINARY - NOT FOR PUBLICATION**

Three fixed splits (seeds 0, 1, 2), 6,102 women, 16 sites. All 65,536 sign vectors are enumerated. These are nominal 95% ART intervals: exact enumeration is not evidence of exact finite-sample coverage. Outcomes are earnings in dollars; the extract's precise earnings horizon and selection rules remain unverified. See [data and model caveats](../JTPA_COMPARISON.md).

## Findings

Giving small sites less weight reduces observed interval widths, and raises the estimated effect in these data. Stabilized precision weights reduce widths further. This is an empirical sensitivity exercise, not a coverage or power comparison. Larger-site weighting also changes the estimand if site effects differ.

The table summarizes separate runs; its medians and ranges are not a combined estimate or confidence interval. `p23` assumes assignment probability 2/3; `estimated` uses adaptively pooled propensity fits. Outcome nuisance fits use Claude's kappa=20 shrinkage and 20-row local-training floor in both cases.

'''+table(main)+'\n\nPaired reductions relative to the current rule, using the same split and site estimates:\n\n'+'\n'.join(changes)+'''

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

'''+pd.DataFrame(weight_rows).to_markdown(index=False)+'''

## Same size-weight comparison for the benchmarks

Precision weighting was run only for the two shrinkage specifications above. Current and size weights were compared for every saved ART benchmark, including the fixed pooled fit. Ordinary pooled OLS with clustered standard errors is not an ART site-score method and is excluded from this reweighting exercise.

'''+table(df[df.weighting.isin(['current','size'])])+'''

## Reproduction and validation

Run `jtpa_size_weights.py`, then `jtpa_weighting_fit.py 0`, `1`, and `2`, then `summarize_jtpa_weighting.py`, with `PYTHONPATH` pointing to the package directory. Fit scripts deliberately stop if an old residual cache exists; preserve or move it after checking provenance before refitting. Individual residual predictions stay in ignored `jtpa_data/`; only aggregate site diagnostics are tracked.

Each reconstructed shrinkage site estimate matched its saved counterpart (rtol=1e-10, atol=1e-7). Recomputed current and size summaries also matched saved results. The summarizer validates 120 unique finite method/split/weight combinations and normalized positive weights. Four new weight tests check the score-versus-effect normalization, constant-variance equivalence, scale/sign transformations, and invalid inputs; the full suite passed 63 tests.

Next evidence needed before choosing a publication specification: simulated null coverage and power with unequal sizes, earnings-like heavy tails, heterogeneous effects and shared nuisance training. Keep all specified weight rules visible; do not select the smallest p-value.
'''
(out/'WEIGHTING_COMPARISON.md').write_text(text,encoding='utf-8')
paths=[root/'jtpa_data/jtpa_women.csv',root/'fewclusters/weighting.py',root/'examples/jtpa_weighting_fit.py',root/'examples/jtpa_size_weights.py']
manifest={'status':'PRELIMINARY - NOT FOR PUBLICATION','base_commit':'6c949b7','seeds':[0,1,2],'primary_variance_kappa':100,'sensitivity_variance_kappa':20,'variance_floor_fraction':.1,'outcome_shrink_kappa':20,'rows':len(df),'sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(table(main))
print('\n'.join(changes))
print('Validated 120 unique rows and all site weight vectors.')
