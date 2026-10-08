"""Oracle ablation: same-sample versus independent-sample precision weights."""
import json
from pathlib import Path
import numpy as np
from fewclusters.art import sign_group
from fewclusters.scores import cluster_scores
from fewclusters.weighting import residual_variances,score_weights
from weighting_simulation import generate,SIZES,THETA,batched_pvalues
root=Path(__file__).resolve().parents[1]
out=root/'results/weighting_simulation/independent_weights.json'
if out.exists():raise FileExistsError(out)
old=json.loads((out.parent/'lognormal_unequal.json').read_text())
expected={(r['rep'],r['weighting']):r for r in old['rows'] if r['method']=='oracle'}
full,_=sign_group(16);signs=full[full[:,0]==1].astype(float)
rows=[]
for rep in range(1000):
    _,d,y,cl,l0,tau0=generate(rep,'lognormal_unequal')
    v,yt=d-2/3,y-l0
    s=cluster_scores(v,yt,cl,np.ones(len(cl),bool),np.arange(16))
    _,di,yi,cli,l0i,_=generate(rep,'lognormal_unequal',seed=20261010)
    same=residual_variances(v,yt,cl)
    independent=residual_variances(di-2/3,yi-l0i,cli)
    rules=['current','size','same sample k100','independent sample k100','DGP oracle precision']
    weights=[np.ones(16)/16,score_weights(SIZES)[0],score_weights(SIZES,same)[0],
             score_weights(SIZES,independent)[0],score_weights(SIZES,tau0,kappa=0,floor_fraction=1e-12)[0]]
    ps=batched_pvalues(s.a,s.b,weights,signs,[THETA,0.])
    for k,rule in enumerate(rules):
        row=dict(rep=rep,weighting=rule,p_true=float(ps[k,0]),p_zero=float(ps[k,1]),estimate=s.pooled_theta(weights[k]))
        check={'current':'current','size':'size','same sample k100':'precision k100','DGP oracle precision':'oracle precision'}.get(rule)
        if check:
            prior=expected[rep,check]
            np.testing.assert_allclose([row[x] for x in ['p_true','p_zero','estimate']],
                [prior[x] for x in ['p_true','p_zero','estimate']],rtol=1e-12,atol=1e-12)
        rows.append(row)
out.write_text(json.dumps(dict(status='PRELIMINARY - NOT FOR PUBLICATION',design='lognormal_unequal',
    diagnostic='Oracle nuisances; extra independent sample of 6102 observations used only for variance weights',
    evaluation_seed=20261009,independent_seed=20261010,reps=1000,rows=rows),indent=2)+'\n')
print('Saved',out)
