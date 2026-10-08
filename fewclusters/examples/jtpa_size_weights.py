"""Size-weight all saved site estimates without refitting nuisance models."""
import json
from pathlib import Path
import numpy as np
from fewclusters.art import sign_group,art_confint,art_test
from fewclusters.weighting import score_weights
root=Path(__file__).resolve().parents[1]; out=root/'results/weighting'; out.mkdir(exist_ok=True)
rows=[]; signs,exact=sign_group(16)
for prefix in ['jtpa','shrink']:
 for mode in ['p23','estimated']:
  for seed in [0,1,2]:
   data=json.loads((root/'results'/f'{prefix}_{mode}_seed{seed}.json').read_text())
   for old in data['rows']:
    sites=sorted([s for s in data['sites'] if s['method']==old['method']],key=lambda x:str(x['cluster']))
    if not sites:continue
    n=np.array([s['n_scored'] for s in sites]);theta=np.array([s['theta_hat'] for s in sites]);b=np.sqrt(n);a=b*theta
    rows.append(dict(mode=mode,seed=seed,method=old['method'],weighting='current',est=old['est'],lo=old['lo'],hi=old['hi'],length=old['hi']-old['lo'],p0=old['p0']))
    w,_=score_weights(n)
    lo,hi=art_confint(a,b,signs,weights=w)
    rows.append(dict(mode=mode,seed=seed,method=old['method'],weighting='size',est=float(np.sum(w*a)/np.sum(w*b)),lo=lo,hi=hi,length=hi-lo,p0=art_test(a,b,0,signs,exact,weights=w).p_value))
   print(prefix,mode,seed,'complete',flush=True)
(out/'size_comparison.json').write_text(json.dumps(dict(status='PRELIMINARY - NOT FOR PUBLICATION',rows=rows),indent=2)+'\n')
