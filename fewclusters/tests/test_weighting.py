import numpy as np
import pytest
from fewclusters.weighting import score_weights,residual_variances


def test_size_weights_give_n_weighted_effect_not_n_to_three_halves():
    n=np.array([38,1392])
    w,_=score_weights(n)
    effective=w*np.sqrt(n)
    np.testing.assert_allclose(effective/effective.sum(),n/n.sum())


def test_equal_variances_recover_size_weights_and_scaling_cancels():
    n=np.array([38,74,400])
    a,_=score_weights(n,np.ones(3)*7)
    b,_=score_weights(n)
    np.testing.assert_allclose(a,b)
    t=np.array([0.,2.,10.])
    a,s=score_weights(n,t)
    b,_=score_weights(n,t*1e8)
    np.testing.assert_allclose(a,b)
    assert np.all(a>0) and np.isfinite(a).all() and np.all(s>0)


def test_influence_variances_and_weights_ignore_site_sign_reversals():
    rng=np.random.default_rng(9)
    c=np.repeat(np.arange(3),50)
    v=rng.normal(size=150); y=rng.normal(size=150)
    t=residual_variances(v,y,c)
    signed=y*np.array([-1,1,-1])[c]
    np.testing.assert_allclose(t,residual_variances(v,signed,c))
    np.testing.assert_allclose(residual_variances(v,10*y,c),100*t)


def test_invalid_variances_are_rejected():
    for t in [[-1,2],[np.nan,2],[0,0]]:
        with pytest.raises(ValueError):score_weights([20,30],t)
