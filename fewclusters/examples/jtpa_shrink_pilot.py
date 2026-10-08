"""Run Claude's 3e9fc11 shrinkage alongside the saved unshrunk pilot."""
import json
from pathlib import Path
import pandas as pd
import numpy as np
from fewclusters import ARTDML
from jtpa_analysis import gbr,gbc
root=Path(__file__).resolve().parents[1]
df=pd.read_csv(root/'jtpa_data/jtpa_women.csv')
X=df[['prevearn','age','married','black','hispanic','hsorged','yrs_educ']].to_numpy()
y,d,site=df['Y'].to_numpy(),df['T'].to_numpy(),df['site'].to_numpy()
for mode in ['p23','estimated']:
 for seed in [0,1,2]:
  res=dict(status='PRELIMINARY - NOT FOR PUBLICATION',seed=seed,mode=mode,
           upstream_commit='3e9fc113ffadb157e8130da408eeb32d32229e3c',rows=[],sites=[],diagnostics=[])
  m=np.full(len(df),2/3) if mode=='p23' else None
  specs=[('DML shrink k20','local')]
  if mode=='estimated': specs.append(('DML shrink k20 both','adaptive'))
  for name,pm in specs:
   print('RUN SHRINK',mode,seed,name,flush=True)
   model=ARTDML(learner_l=gbr(),learner_m=gbc(),pooling_l='adaptive',pooling_m=pm,
                shrink_l=20.,shrink_m=0.,min_local_train=20,random_state=seed,n_folds=5)
   model.fit(y,d,X,site,m_known=m)
   lo,hi=model.confint(.05)
   r=model.result_
   row=dict(method=name,est=model.pooled_estimate(),lo=lo,hi=hi,p0=model.pvalue(0),outcome_mse=float(np.mean((y-r.lhat)**2)))
   res['rows'].append(row)
   res['sites'].extend(dict(method=name,**x) for x in model.cluster_table())
   res['diagnostics'].extend(dict(method=name,**x.as_dict()) for x in r.diagnostics_l)
   print(row,flush=True)
  path=root/'results'/f'shrink_{mode}_seed{seed}.json'
  path.write_text(json.dumps(res,indent=2,default=lambda x:x.item())+'\n')
