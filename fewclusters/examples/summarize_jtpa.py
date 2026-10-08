"""Summarize all prespecified JTPA pilot runs without selecting a best split."""
import hashlib,json,platform,subprocess
from pathlib import Path
import pandas as pd
from jtpa_analysis import report
root=Path(__file__).resolve().parents[1]; out=root/'results'
records=[]
for mode in ['p23','estimated']:
 for seed in [0,1,2]:
  base=json.loads((out/f'jtpa_{mode}_seed{seed}.json').read_text())
  shrink=json.loads((out/f'shrink_{mode}_seed{seed}.json').read_text())
  base['rows']+=shrink['rows']; base['sites']+=shrink['sites']
  (out/f'comparison_{mode}_seed{seed}.md').write_text(report(base,f'JTPA {mode}, seed {seed}'),encoding='utf-8')
  for row in base['rows']:
   records.append(dict(status='PRELIMINARY - NOT FOR PUBLICATION',mode=mode,seed=seed,
                       length=row['hi']-row['lo'],**row))
df=pd.DataFrame(records)
df.to_csv(out/'jtpa_split_results.csv',index=False)
lines=['# JTPA preliminary estimator comparison','', '**PRELIMINARY - NOT FOR PUBLICATION**','',
       '6,102 women, 16 sites, no rows dropped. Dollar earnings Y as supplied by senseweight; '
       'the exact earnings horizon and sample construction remain unverified. Covariates: '
       'previous earnings, age, marital status, Black and Hispanic indicators, high-school/GED status, years of education.', '',
       'Five folds and three fixed split seeds (0, 1, 2). All 65,536 sign vectors enumerated for each ART. '
       'Intervals are nominal 95% intervals under the stated model, not validated coverage on these data.', '',
       'Four sites are small: MT 38, OH 74, JC 81, OK 87. MT calibration folds have 7-8 observations '
       'and local training folds have 22-23. The 20-row fallback therefore never activates in this sample. '
       'Shrinkage helps stabilize prediction weights; it does not establish normality of site scores.', '',
       'ART aggregates site estimates with sqrt(n_site) weights. Pooled OLS generally targets different '
       'weights when effects are heterogeneous. Do not interpret every estimate difference as estimator bias.', '']
for mode,title in [('p23','Assumed two-thirds propensity'),('estimated','Estimated propensity sensitivity')]:
 lines += [f'## {title}', '',
           'The two-thirds scenario is an explicit design assumption; it is not verified for the selected extract.' if mode=='p23' else
           'Propensities are learned locally by gradient boosting, except methods labeled both, which also adaptively pool the propensity. '
           'These fits do not establish the rate assumptions or resolve outcome selection.', '',
           '| Method | Estimate median [range] | Interval length median [range] | p(0) range |',
           '|---|---:|---:|---:|']
 for name,g in df[df['mode']==mode].groupby('method',sort=False):
  lines.append(f"| {name} | {g.est.median():.0f} [{g.est.min():.0f}, {g.est.max():.0f}] | "
               f"{g.length.median():.0f} [{g.length.min():.0f}, {g.length.max():.0f}] | {g.p0.min():.4f}-{g.p0.max():.4f} |")
 lines+=['']
 p=df[df['mode']==mode].pivot(index='seed',columns='method',values='length')
 pair=('DML adaptive','DML shrink k20')
 gain=100*(1-p[pair[1]]/p[pair[0]])
 lines += [f'Shrinkage reduces interval length relative to the original outcome-adaptive method by '
           f'{gain.min():.1f}% to {gain.max():.1f}% across these splits (negative means lengthening). '
           'This is descriptive; it is not evidence about coverage or power.', '']
lines+=['## Interpretation and next work','',
        'The original adaptive method sets shrink_l=0 and min_local_train=0. Shrinkage uses kappa_l=20, '
        'kappa_m=0 and min_local_train=20. Local matched and pooled matched use the same reduced training '
        'allocation as adaptive fitting. Local full uses all non-evaluation observations.', '',
        'Three split repetitions measure sensitivity to sample splitting, not repeated-sampling uncertainty. '
        'No split was selected for favorable p-values or interval lengths. An empirical dataset has no known '
        'true treatment effect, so this exercise cannot rank coverage or mean squared estimation error.', '',
        'Next scientific checks: reconcile the full JTPA archive and assignment/selection documentation; '
        'simulate common-effect outcomes on the actual site sizes and covariates to measure coverage, power '
        'and RMSE; and separately stress-test heterogeneous effects and heavy-tailed site scores. '
        'The existing theoretical result does not justify arbitrary cross-site treatment-effect heterogeneity.', '',
        'Novelty assessment and prior-work handoff: [JTPA_HANDOFF.md](../JTPA_HANDOFF.md). '
        'Data source: https://www.upjohn.org/data-tools/employment-research-data-center/national-jtpa-study .', '']
(out/'JTPA_COMPARISON.md').write_text('\n'.join(lines),encoding='utf-8')
manifest=dict(status='PRELIMINARY - NOT FOR PUBLICATION',python=platform.python_version(),
              git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
              seeds=[0,1,2],folds=5,shrink_l=20,shrink_m=0,min_local_train=20,
              data_csv_sha256=hashlib.sha256((root/'jtpa_data/jtpa_women.csv').read_bytes()).hexdigest(),
              baseline_core='e4f1794 (baseline process started before merge; equivalent to explicit shrink_l=0, min_local_train=0)',
              shrink_core='3e9fc11 plus matched-training and warning integration',
              code_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [root/'examples/jtpa_analysis.py',root/'examples/jtpa_pilot.py',root/'examples/jtpa_shrink_pilot.py',root/'fewclusters/model.py']})
(out/'pilot_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('\n'.join(lines))
