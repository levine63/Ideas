"""Prespecified split sensitivity pilot; all results preliminary, not for publication."""
import json
from pathlib import Path
import pandas as pd
from jtpa_analysis import run_all, report

root=Path(__file__).resolve().parents[1]
out=root/'results'; out.mkdir(exist_ok=True)
df=pd.read_csv(root/'jtpa_data/jtpa_women.csv')
xs=['prevearn','age','married','black','hispanic','hsorged','yrs_educ']
for mode in ['p23','estimated']:
    for seed in [0,1,2]:
        path=out/f'jtpa_{mode}_seed{seed}.json'
        if path.exists():
            res=json.loads(path.read_text())
            res['status']='PRELIMINARY - NOT FOR PUBLICATION'
        else:
            kwargs={} if mode=='estimated' else dict(probability=2/3,probability_source=
                'ASSUMED p=2/3 sensitivity; overall design ratio documented but extract selection and assignment mechanism not fully verified')
            print(f'RUN {mode} seed={seed}',flush=True)
            res=run_all(df,'Y','T','site',xs,seed=seed,**kwargs)
        path.write_text(json.dumps(res,indent=2,default=lambda x:x.item())+'\n')
        path.with_suffix('.md').write_text(report(res,'JTPA pilot'),encoding='utf-8')
        print(mode,seed,[(r['method'],round(r['est'],1),round(r['hi']-r['lo'],1)) for r in res['rows']],flush=True)
rows=[]
for path in sorted(out.glob('jtpa_*_seed*.json')):
    res=json.loads(path.read_text())
    for r in res['rows']:
        rows.append(dict(status='PRELIMINARY - NOT FOR PUBLICATION',mode=path.stem.split('_')[1],seed=res['seed'],**r))
pd.DataFrame(rows).to_csv(out/'jtpa_split_results.csv',index=False)
