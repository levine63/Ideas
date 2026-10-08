"""Reconstruct shrinkage residuals for one split; all outputs preliminary."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from fewclusters import ARTDML
from fewclusters.nuisance import NuisanceSpec,crossfit_nuisance
from fewclusters.scores import cluster_scores
from fewclusters.art import sign_group,art_test,art_confint
from fewclusters.weighting import score_weights,residual_variances
from jtpa_analysis import gbr,gbc
root=Path(__file__).resolve().parents[1]
seed=int(sys.argv[1]); out=root/'results/weighting'; out.mkdir(exist_ok=True)
df=pd.read_csv(root/'jtpa_data/jtpa_women.csv')
y,d=df['Y'].to_numpy(),df['T'].to_numpy()
X=df[['prevearn','age','married','black','hispanic','hsorged','yrs_educ']].to_numpy()
labels,cl=np.unique(df.site,return_inverse=True)
cache=root/'jtpa_data'/f'weight_residuals_seed{seed}.npz'
if cache.exists():
    raise FileExistsError('Residual cache exists; review provenance before recomputing.')
print('Reconstruct outcome fits',seed,flush=True)
model=ARTDML(learner_l=gbr(),pooling_l='adaptive',shrink_l=20,shrink_m=0,min_local_train=20,random_state=seed)
model.fit(y,d,X,cl,m_known=np.full(len(d),2/3))
r=model.result_
print('Reconstruct adaptive propensity fits',seed,flush=True)
mfit=crossfit_nuisance(d,X,cl,r.plan,NuisanceSpec(gbc(),'adaptive','pooled_id',name='m',shrink_kappa=0,min_local_train=20))
np.savez_compressed(cache,lhat=r.lhat,mhat=mfit.predictions,folds=r.plan.fold_of_row)
result=dict(status='PRELIMINARY - NOT FOR PUBLICATION',seed=seed,kappa=100,floor_fraction=.1,rows=[],sites=[])
signs,exact=sign_group(len(labels))
for mode,mhat,name in [('p23',np.full(len(d),2/3),'DML shrink k20'),('estimated',mfit.predictions,'DML shrink k20 both')]:
    v,yt=d-mhat,y-r.lhat
    scores=cluster_scores(v,yt,cl,np.ones(len(y),dtype=bool),labels)
    saved=json.loads((root/'results'/f'shrink_{mode}_seed{seed}.json').read_text())
    expected={x['cluster']:x['theta_hat'] for x in saved['sites'] if x['method']==name}
    np.testing.assert_allclose(scores.theta,[expected[x] for x in labels],rtol=1e-10,atol=1e-7)
    tau=residual_variances(v,yt,cl)
    for kind,kappa in [('current',None),('size',None),('precision k100',100.),('precision k20 sensitivity',20.)]:
        if kind=='current':w=np.ones(len(labels))/len(labels); stabilized=tau
        elif kind=='size':w,stabilized=score_weights(scores.n)
        else:w,stabilized=score_weights(scores.n,tau,kappa=kappa)
        lo,hi=art_confint(scores.a,scores.b,signs,.05,w)
        row=dict(mode=mode,seed=seed,method=name,weighting=kind,est=scores.pooled_theta(w),lo=lo,hi=hi,length=hi-lo,p0=art_test(scores.a,scores.b,0,signs,exact,.05,w).p_value)
        result['rows'].append(row)
        effective=w*scores.b; effective/=effective.sum()
        for j,lab in enumerate(labels):
            result['sites'].append(dict(mode=mode,method=name,weighting=kind,site=str(lab),n=int(scores.n[j]),tau2=float(tau[j]),stabilized_tau2=None if stabilized is None else float(stabilized[j]),score_weight=float(w[j]),effect_weight=float(effective[j])))
        print(seed,row,flush=True)
(out/f'seed{seed}.json').write_text(json.dumps(result,indent=2)+'\n')
