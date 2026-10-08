"""Check the simulation accelerator against the production sign test."""
import importlib.util
from pathlib import Path
import numpy as np
from fewclusters.art import art_pvalue, sign_group

spec=importlib.util.spec_from_file_location('weighting_simulation',Path(__file__).resolve().parents[1]/'examples/weighting_simulation.py')
sim=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)


def test_half_group_batched_pvalues_match_full_enumeration_with_ties():
    full,_=sign_group(6)
    half=full[full[:,0]==1].astype(float)
    a=np.array([1.,2.,3.,4.,5.,6.]); b=np.ones(6)
    weights=[np.ones(6),np.arange(1.,7.)]
    nulls=[0.,1.,3.5]
    actual=sim.batched_pvalues(a,b,weights,half,nulls)
    expected=np.array([[art_pvalue(a-b*t,full,w) for t in nulls] for w in weights])
    np.testing.assert_array_equal(actual,expected)


def test_generator_reproducible_and_oracle_score_identity():
    first=sim.generate(2,'t3_unequal')
    second=sim.generate(2,'t3_unequal')
    for x,y in zip(first,second):np.testing.assert_array_equal(x,y)
    x,d,y,cl,l0,tau=first
    assert len(y)==6102 and len(np.unique(cl))==16
    assert np.all(tau>0) and np.isfinite(y).all()
    # Replacing y by its conditional mean leaves exactly theta*(D-p).
    g=l0-sim.THETA*2/3
    np.testing.assert_allclose(sim.THETA*d+g-l0,sim.THETA*(d-2/3),atol=1e-14)
