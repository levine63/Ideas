"""Summarize coverage/power with Monte Carlo intervals and paired differences."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

root=Path(__file__).resolve().parents[1]
out=root/'results/weighting_simulation'
DESIGNS=['normal_equal','normal_unequal','t3_unequal','lognormal_unequal']
RULES=['current','size','precision k100','precision k20','oracle precision']


def wilson(success,n):
    z=1.959963984540054; p=success/n; den=1+z*z/n
    center=(p+z*z/(2*n))/den
    radius=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return center-radius,center+radius


def main():
    frames=[]; metadata=[]
    for design in DESIGNS:
        path=out/f'{design}.json'
        obj=json.loads(path.read_text(encoding='utf-8-sig'))
        assert obj['status']=='PRELIMINARY - NOT FOR PUBLICATION'
        assert obj['design']==design
        assert not obj['failures'],obj['failures']
        data=pd.DataFrame(obj.pop('rows'))
        assert not data.duplicated(['rep','method','weighting']).any()
        assert np.isfinite(data[['p_true','p_zero','estimate']]).all().all()
        assert data[['p_true','p_zero']].ge(0).all().all() and data[['p_true','p_zero']].le(1).all().all()
        for (method,rule),g in data.groupby(['method','weighting']):
            assert len(g)==obj['oracle_reps' if method=='oracle' else 'fitted_reps']
        assert len(data)==5*(obj['oracle_reps']+2*obj['fitted_reps'])
        frames.append(data)
        metadata.append({**obj,'result_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    df=pd.concat(frames,ignore_index=True)
    records=[]; differences=[]
    for (design,method,rule),g in df.groupby(['design','method','weighting'],sort=False):
        n=len(g); covered=(g.p_true>.05); power=(g.p_zero<=.05)
        clo,chi=wilson(int(covered.sum()),n); plo,phi=wilson(int(power.sum()),n)
        records.append(dict(design=design,method=method,weighting=rule,reps=n,coverage=covered.mean(),
            coverage_mc_lo=clo,coverage_mc_hi=chi,power=power.mean(),power_mc_lo=plo,power_mc_hi=phi,
            bias=(g.estimate-.08).mean(),rmse=np.sqrt(np.mean((g.estimate-.08)**2))))
        current=df[(df.design==design)&(df.method==method)&(df.weighting=='current')].set_index('rep')
        other=g.set_index('rep')
        for metric,column,op in [('coverage','p_true','gt'),('power','p_zero','le')]:
            base=getattr(current[column],op)(.05).astype(float)
            new=getattr(other[column],op)(.05).astype(float)
            delta=new-base
            se=delta.std(ddof=1)/np.sqrt(n)
            differences.append(dict(design=design,method=method,weighting=rule,metric=metric,
                difference=delta.mean(),mc_se=se,mc_lo=delta.mean()-1.96*se,mc_hi=delta.mean()+1.96*se))
    summary=pd.DataFrame(records)
    summary.to_csv(out/'summary.csv',index=False)
    pd.DataFrame(differences).to_csv(out/'paired_differences.csv',index=False)
    (out/'manifest.json').write_text(json.dumps(dict(status='PRELIMINARY - NOT FOR PUBLICATION',runs=metadata),indent=2)+'\n',encoding='utf-8')
    def render(method):
        selected=summary[summary.method==method]
        rows=[]
        for design in DESIGNS:
            for rule in RULES:
                g=selected[(selected.design==design)&(selected.weighting==rule)].iloc[0]
                rows.append({'Design':design,'Weight':rule,'Reps':int(g.reps),
                    'Coverage %':f'{100*g.coverage:.1f}',
                    'Coverage MC 95%':f'{100*g.coverage_mc_lo:.1f}-{100*g.coverage_mc_hi:.1f}',
                    'Power %':f'{100*g.power:.1f}',
                    'Power MC 95%':f'{100*g.power_mc_lo:.1f}-{100*g.power_mc_hi:.1f}',
                    'Bias':f'{g.bias:.4f}','RMSE':f'{g.rmse:.4f}'})
        return pd.DataFrame(rows).to_markdown(index=False)
    findings=[]
    for method in ['shrink known p','shrink estimated p']:
        for rule in ['current','size','precision k100']:
            z=summary[(summary.method==method)&(summary.weighting==rule)]
            findings.append(f'- {method}, {rule}: coverage {100*z.coverage.min():.1f}-{100*z.coverage.max():.1f}%; power {100*z.power.min():.1f}-{100*z.power.max():.1f}% across the four designs.')
    flags=summary[(summary.method!='oracle') & (summary.coverage_mc_hi < .95)]
    if len(flags):
        findings.append('\nSome fitted-method coverage estimates have marginal Monte Carlo intervals entirely below 95%: '+ '; '.join(f'{r.design}, {r.method}, {r.weighting}' for r in flags.itertuples())+'. These are diagnostic flags, not multiplicity-adjusted findings.')
    else:
        findings.append('\nNo fitted-method coverage estimate has a marginal Monte Carlo interval entirely below 95%. This does not prove correct coverage or equivalence of the rules.')
    ablation_path=out/'independent_weights.json'
    ablation=json.loads(ablation_path.read_text())
    ad=pd.DataFrame(ablation['rows'])
    assert len(ad)==5000 and not ad.duplicated(['rep','weighting']).any()
    assert np.isfinite(ad[['p_true','p_zero','estimate']]).all().all()
    ar=[]
    for rule,g in ad.groupby('weighting',sort=False):
        assert len(g)==1000
        coverage=(g.p_true>.05).mean(); power=(g.p_zero<=.05).mean()
        clo,chi=wilson(int((g.p_true>.05).sum()),len(g))
        ar.append({'Rule':rule,'Coverage %':100*coverage,'Coverage MC 95%':f'{100*clo:.1f}-{100*chi:.1f}',
                   'Power %':100*power,'Mean estimate':g.estimate.mean()})
    at=pd.DataFrame(ar)
    at.to_csv(out/'independent_weights_summary.csv',index=False)
    manifest=json.loads((out/'manifest.json').read_text())
    manifest['posthoc_diagnostic']={k:v for k,v in ablation.items() if k!='rows'}
    manifest['posthoc_diagnostic']['result_sha256']=hashlib.sha256(ablation_path.read_bytes()).hexdigest()
    manifest['source_sha256']={name:hashlib.sha256((root/'examples'/name).read_bytes()).hexdigest() for name in
        ['weighting_simulation.py','independent_weight_diagnostic.py','summarize_weighting_simulation.py']}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    text='''# Unequal-site weighting: coverage and power stress test

**PRELIMINARY - NOT FOR PUBLICATION**

## Findings

**Decision for this preliminary analysis:** use size weighting as the primary weighting comparison and keep same-sample estimated precision weighting experimental. In the skewed lognormal design, primary precision weights give only 90.6% fitted-estimator coverage for nominal 95% (Monte Carlo interval 87.7-92.9%); size weights give 95.2% (93.0-96.8%). Apparent power gains from an oversized test are not a fair efficiency comparison. This result does not establish size weighting's validity outside these designs.

'''+ '\n'.join(findings) + '''

## Design and interpretation

Independent observations within each of 16 sites, with the JTPA sizes 38, 74, 81, 87, 177, 179, 190, 234, 353, 401, 463, 485, 524, 636, 788, 1392 (6,102 total). Treatment is independent Bernoulli(2/3). The common true treatment effect is 0.08 in standardized simulation units, not JTPA dollars. Outcomes follow Y=0.08D+g_g(X)+sigma_g*epsilon. Two independent standard-normal covariates enter a linear outcome function with site-specific intercepts and slopes. Local outcome models can learn these slopes; the pooled site-intercept model cannot represent all of them.

Four prespecified error designs:

- `normal_equal`: independent standard Gaussian errors, sigma_g=1.
- `normal_unequal`: Gaussian errors, sigma_g=(median(n)/n_g)^(1/4). Small sites are noisier per observation as well as having fewer observations.
- `t3_unequal`: Student-t(3) errors divided by sqrt(3), with the same unequal site scales. Variance is finite but the fourth moment is not.
- `lognormal_unequal`: lognormal errors with log-standard-deviation 1.5, centered and scaled using population moments, with the same unequal site scales. This is a skewness/heavy-tail stress test, not a fitted earnings distribution.

Each design has 1,000 oracle-nuisance replications, with fitted nuisances on the first 500. Each replication fits once at the true effect and tests both the true value (coverage) and zero (power). Coverage equals acceptance of the true value by the inverted 5% sign test; endpoints need not be computed. All sign pairs are enumerated, using 32,768 representatives of the 65,536 signs. A regression test verifies the accelerated calculation against the production full enumeration, including ties.

Fitted outcome nuisances use five-fold adaptive local/pooled-site-intercept Ridge(alpha=1), outcome weight shrinkage kappa=20 and the 20-row local-training floor. The estimated-propensity version uses adaptively calibrated local and pooled sample means (DummyRegressor), with treatment shrinkage zero and the same floor. This is appropriate to the simulated constant propensity and keeps the comparison focused; it does not validate the JTPA gradient-boosting implementation or observational propensity misspecification. Shared cross-site nuisance training is included. Oracle outcome and treatment means provide a separate baseline.

Weight rules match the JTPA exercise: current equal score weights, size score weights sqrt(n), and stabilized precision score weights sqrt(n)/tauhat_squared with variance kappa=100 (primary) or 20 (sensitivity), floored at 0.1 times the pooled variance. The final rule uses the DGP oracle variance sigma_g^2/[p(1-p)], without shrinkage. For fitted nuisances that final variance omits nuisance estimation error, so it is a reference rather than the true finite-sample optimal weight. All weights remain fixed over signs and nulls.

The intervals in the tables are Monte Carlo uncertainty for the estimated coverage/power rates, not effect confidence intervals. Wilson intervals are marginal and are not adjusted for the many comparisons. At 500 replications, a rejection probability of 5% has Monte Carlo standard error about 1 percentage point. Full enumeration removes sign-sampling error, not simulation uncertainty or failures of score symmetry. Paired changes versus current weighting, including their Monte Carlo standard errors, are in `paired_differences.csv`. Raw replication p-values and estimates are retained in each design JSON. There were no skipped or failed replications.

## Shrinkage estimator, known propensity

'''+render('shrink known p')+'''

## Shrinkage estimator, estimated propensity

'''+render('shrink estimated p')+'''

## Oracle nuisances

'''+render('oracle')+'''

## Post hoc diagnostic: source of the skewed-error failure

After observing undercoverage, we reran the lognormal oracle-nuisance case with the same 1,000 evaluation datasets, changing only where variance weights were estimated. The additional independent weight-training sample has 6,102 observations, the same site sizes and DGP, and independent seed=20261010. Original evaluation seed=20261009. Recomputed original results match the main simulation. This is a diagnostic ablation, not a prespecified comparison or a fair equal-data-budget proposal.

'''+at.to_markdown(index=False,floatfmt='.4f')+'''

With a true effect of 0.08, same-sample precision weights produce a mean estimate of 0.08913 and coverage of 91.3%, despite oracle nuisances. Independent-sample precision weights give a mean of 0.07996 and coverage of 94.5%; fixed DGP precision weights give 94.7% coverage. This isolates same-sample weight estimation as a contributor to the failure in this design, rather than nuisance fitting alone. Dependence between skewed estimation errors and their estimated variances can create biased weighting and spoil the required joint sign symmetry. Merely holding weights fixed during enumeration does not remove that dependence. The independent-sample diagnostic costs extra data and does not prove that an ordinary holdout or cross-fit version is universally valid; it also has lower power than simple size weights here.

The generalized guardrail is to retain this skewed-error case and oracle/independent-weight controls in future weighting evaluations. Any proposed precision-weight fix must report coverage as well as power before replacing the primary size-weight sensitivity.

## Limits and reproduction

The designs have a common effect and independent within-site errors. They do not establish validity for heterogeneous effects, common site shocks or arbitrary within-site dependence. Small sites remain small. Neither variance shrinkage nor small-site downweighting is a theorem repairing their Gaussian approximation. Conclusions from these four designs cannot establish universal optimality.

From the repository root set PYTHONPATH=fewclusters, OMP_NUM_THREADS=1 and OPENBLAS_NUM_THREADS=1. For each design run:

```text
python fewclusters/examples/weighting_simulation.py --design DESIGN --oracle-reps 1000 --fitted-reps 500 --output fewclusters/results/weighting_simulation/DESIGN.json
python fewclusters/examples/summarize_weighting_simulation.py
```

After all four designs finish, run `python fewclusters/examples/independent_weight_diagnostic.py`, then the summarizer. The simulation refuses to overwrite existing results. Seed=20261009; replication-indexed random streams are reproducible. Warnings are counted and retained in manifests. Any fitting/scoring failure is recorded; the summarizer refuses to silently produce the no-failure report if a failure occurred. Synthetic replication summaries contain no person-level JTPA data.
'''
    (out/'COVERAGE_POWER.md').write_text(text,encoding='utf-8')
    print(summary[['design','method','weighting','coverage','power']].to_string(index=False))

if __name__=='__main__':main()
