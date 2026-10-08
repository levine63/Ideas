"""Preliminary coverage/power stress tests for unequal-site ART weights."""
import argparse
import hashlib
import json
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from fewclusters import ARTDML
from fewclusters.art import sign_group
from fewclusters.nuisance import NuisanceSpec, crossfit_nuisance
from fewclusters.scores import cluster_scores
from fewclusters.weighting import score_weights, residual_variances

SIZES = np.array([38,74,81,87,177,179,190,234,353,401,463,485,524,636,788,1392])
DESIGNS = ['normal_equal','normal_unequal','t3_unequal','lognormal_unequal']
RULES = ['current','size','precision k100','precision k20','oracle precision']
THETA = .08


def generate(rep, design, seed=20261009):
    rng = np.random.default_rng(np.random.SeedSequence([seed,rep]))
    cl = np.repeat(np.arange(len(SIZES)), SIZES)
    x = rng.normal(size=(len(cl),2))
    d = rng.binomial(1,2/3,len(cl)).astype(float)
    if design.startswith('t3'):
        e = rng.standard_t(3,len(cl))/np.sqrt(3)
    elif design.startswith('lognormal'):
        s = 1.5
        e = (rng.lognormal(0,s,len(cl))-np.exp(s*s/2))/np.sqrt((np.exp(s*s)-1)*np.exp(s*s))
    else:
        e = rng.normal(size=len(cl))
    sigma = np.ones(len(SIZES)) if design=='normal_equal' else (np.median(SIZES)/SIZES)**.25
    g = (.5+.4*np.sin(cl))*x[:,0]+.25*x[:,1]+.5*np.cos(cl)
    y = THETA*d+g+sigma[cl]*e
    return x,d,y,cl,g+THETA*2/3,sigma**2/(2/9)


def batched_pvalues(a,b,weights,signs,lambdas):
    """Exact two-sided enumeration using one representative of each +/- pair."""
    columns = np.column_stack([w*(a-b*lam) for w in weights for lam in lambdas])
    observed = np.abs(columns.sum(axis=0))
    randomized = np.abs(signs @ columns)
    # Identity is evaluated by the same summation as the observed statistic.
    randomized[0,:] = observed
    return np.mean(randomized >= observed,axis=0).reshape(len(weights),len(lambdas))


def evaluate(v,yt,cl,oracle_tau,signs):
    scores=cluster_scores(v,yt,cl,np.ones(len(cl),bool),np.arange(len(SIZES)))
    tau=residual_variances(v,yt,cl)
    weights=[np.ones(len(SIZES))/len(SIZES),score_weights(SIZES)[0],
             score_weights(SIZES,tau,kappa=100)[0],score_weights(SIZES,tau,kappa=20)[0],
             score_weights(SIZES,oracle_tau,kappa=0,floor_fraction=1e-12)[0]]
    p=batched_pvalues(scores.a,scores.b,weights,signs,[THETA,0.])
    return [dict(weighting=rule,p_true=float(pp[0]),p_zero=float(pp[1]),
                 estimate=float(scores.pooled_theta(w))) for rule,pp,w in zip(RULES,p,weights)]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--design',choices=DESIGNS,required=True)
    parser.add_argument('--oracle-reps',type=int,default=1000)
    parser.add_argument('--fitted-reps',type=int,default=500)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    assert 0<=args.fitted_reps<=args.oracle_reps
    path=Path(args.output)
    if path.exists(): raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    full,_=sign_group(len(SIZES)); signs=full[full[:,0]==1].astype(float)
    rows=[]; failures=[]; warning_counts={}; start=time.time()
    for rep in range(args.oracle_reps):
        x,d,y,cl,l0,tau0=generate(rep,args.design)
        fits={'oracle':(d-2/3,y-l0)}
        if rep<args.fitted_reps:
            try:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    model=ARTDML(learner_l=Ridge(alpha=1),pooling_l='adaptive',shrink_l=20,
                                 shrink_m=0,min_local_train=20,random_state=20261009+rep)
                    model.fit(y,d,x,cl,m_known=np.full(len(d),2/3))
                    r=model.result_
                    mf=crossfit_nuisance(d,x,cl,r.plan,NuisanceSpec(DummyRegressor(strategy='mean'),
                        'adaptive','pooled_id',name='m',shrink_kappa=0,min_local_train=20))
                for warning in caught:
                    msg=str(warning.message)
                    warning_counts[msg]=warning_counts.get(msg,0)+1
                fits['shrink known p']=(d-2/3,y-r.lhat)
                fits['shrink estimated p']=(d-mf.predictions,y-r.lhat)
            except Exception as exc:
                failures.append(dict(rep=rep,stage='fit',error=repr(exc)))
        for method,(v,yt) in fits.items():
            try:
                for row in evaluate(v,yt,cl,tau0,signs):
                    rows.append(dict(design=args.design,rep=rep,method=method,**row))
            except Exception as exc:
                failures.append(dict(rep=rep,stage=method,error=repr(exc)))
        if (rep+1)%25==0 or rep+1==args.oracle_reps:
            print(args.design,rep+1,'/',args.oracle_reps,'elapsed',round(time.time()-start,1),'failures',len(failures),flush=True)
    payload=dict(status='PRELIMINARY - NOT FOR PUBLICATION',design=args.design,theta=THETA,
        sizes=SIZES.tolist(),oracle_reps=args.oracle_reps,fitted_reps=args.fitted_reps,
        seed=20261009,variance_kappas=[100,20],variance_floor_fraction=.1,
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        seconds=time.time()-start,warnings=warning_counts,failures=failures,rows=rows)
    path.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print('Saved',path,flush=True)

if __name__=='__main__': main()
