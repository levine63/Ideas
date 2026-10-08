import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
from jtpa_analysis import propensity_vector, classical_site_estimates, demo_data
from fewclusters import ARTDML


def test_empirical_shares_are_never_implicitly_known():
    df=pd.DataFrame({'T':[0,1,1,1]})
    assert propensity_vector(df) is None
    with pytest.raises(ValueError,match='source'):
        propensity_vector(df,2/3)
    assert np.all(propensity_vector(df,2/3,source='Explicit design assumption')==2/3)
    # Assignment changes cannot change externally supplied probabilities.
    df['T']=0
    assert np.all(propensity_vector(df,2/3,source='Explicit design assumption')==2/3)


def test_propensity_column_and_invalid_values():
    df=pd.DataFrame({'p':[.3,.7]})
    np.testing.assert_array_equal(propensity_vector(df,probability_column='p',source='Protocol'),df.p)
    for bad in [0,1,float('nan')]:
        with pytest.raises(ValueError): propensity_vector(df,bad,source='Protocol')
    with pytest.raises(ValueError): propensity_vector(df,.5,'p','Protocol')


def test_benchmarks_reproduce_dim_and_direct_ols():
    df=demo_data()
    y,d,x,s=df.Y.to_numpy(),df['T'].to_numpy(),df[['x0','x1']].to_numpy(),df.site.to_numpy()
    theta,_=classical_site_estimates(y,d,x,s)
    ols,_=classical_site_estimates(y,d,x,s,True)
    for j in range(8):
        rows=s==j
        assert theta[j]==pytest.approx(y[rows&(d==1)].mean()-y[rows&(d==0)].mean())
        Z=np.column_stack([np.ones(rows.sum()),d[rows],x[rows]])
        assert ols[j]==pytest.approx(np.linalg.lstsq(Z,y[rows],rcond=None)[0][1])


def test_matched_candidates_have_identical_training_and_evaluation_roles():
    df=demo_data()
    args=(df.Y.to_numpy(),df['T'].to_numpy(),df[['x0','x1']].to_numpy(),df.site.to_numpy())
    models=[]
    for mode in ['local','pooled_id','adaptive']:
        model=ARTDML(learner_l=LinearRegression(),pooling_l=mode,reserve_calibration=True,random_state=19)
        model.fit(*args,m_known=np.full(len(df),2/3))
        models.append(model)
    for candidate in models[1:]:
        for a,b in zip(models[0].result_.plan.roles,candidate.result_.plan.roles):
            for field in ['eval_idx','calib_idx','base_target_idx','base_other_idx']:
                np.testing.assert_array_equal(getattr(a,field),getattr(b,field))
            assert not np.intersect1d(b.eval_idx,b.calib_idx).size
            assert not np.intersect1d(b.calib_idx,b.base_target_idx).size


def test_small_cluster_warning_is_retained_in_summary():
    from fewclusters.model import SmallClusterWarning
    df=demo_data().groupby('site').head(38)
    model=ARTDML(learner_l=LinearRegression(),pooling_l='adaptive',random_state=1)
    with pytest.warns(SmallClusterWarning,match='does not establish normality'):
        model.fit(df['Y'],df['T'],df[['x0','x1']],df['site'],m_known=np.full(len(df),2/3))
    assert 'Small-sample warning' in model.summary()
