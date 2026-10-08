"""End-to-end tests for ARTDML with simple learners."""

import numpy as np
import pytest
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from fewclusters import ARTDML, simulate_plm
from fewclusters.learners import ConstantPredictor


def poly_learner():
    return make_pipeline(PolynomialFeatures(2, include_bias=False), LinearRegression())


@pytest.mark.parametrize("pooling", ["local", "pooled", "pooled_id", "adaptive"])
def test_pipeline_runs_in_every_pooling_mode(pooling):
    data = simulate_plm(q=6, n_j=200, seed=0)
    model = ARTDML(learner_m=poly_learner(), learner_l=poly_learner(), n_folds=4,
                   pooling_m=pooling, pooling_l=pooling, random_state=0)
    model.fit(data["y"], data["d"], data["X"], data["cluster"])
    res = model.test(data["theta"])
    assert 0 < res.p_value <= 1 and res.exact
    lo, hi = model.confint(0.05)
    assert lo < model.pooled_estimate() < hi
    assert res.q == 6
    table = model.cluster_table()
    assert len(table) == 6 and all(r["Q_hat"] > 0 for r in table)
    if pooling == "adaptive":
        assert all(0.0 <= r["mean_w_m"] <= 1.0 and 0.0 <= r["mean_w_l"] <= 1.0 for r in table)
    else:
        assert all(r["mean_w_m"] is None for r in table)


def test_known_propensity_skips_learner_m():
    data = simulate_plm(q=6, n_j=200, known_propensity=True, seed=1)
    model = ARTDML(learner_m=None, learner_l=poly_learner(), n_folds=4, pooling_l="local")
    model.fit(data["y"], data["d"], data["X"], data["cluster"], m_known=data["m0"])
    assert np.allclose(model.result_.vhat, data["d"] - data["m0"])
    assert model.result_.diagnostics_m == []
    assert 0 < model.pvalue(data["theta"]) <= 1


def test_fit_once_scores_are_affine_in_lambda():
    data = simulate_plm(q=6, n_j=150, seed=2)
    model = ARTDML(learner_m=poly_learner(), learner_l=poly_learner(), n_folds=4,
                   pooling_m="local", pooling_l="local").fit(data["y"], data["d"], data["X"], data["cluster"])
    sc = model.result_.scores
    lam = np.array([-1.0, 0.0, 2.0])
    for l in lam:
        assert np.allclose(sc.S(l), sc.a - sc.b * l)
    # p-value at the pooled estimate is 1
    assert model.pvalue(model.pooled_estimate()) == 1.0


def test_oracle_scores_match_true_nuisance_plugin():
    """With constant learners replaced by the true functions, vhat and ytilde are the oracle residuals."""
    data = simulate_plm(q=4, n_j=100, seed=3)
    # oracle: pass m_known = m0 and make learner_l reproduce l0 exactly via a lookup trick
    class Lookup:
        def __init__(self, table): self.table = table
        def fit(self, X, z): return self
        def predict(self, X):
            key = [tuple(row) for row in X]
            return np.array([self.table[k] for k in key])
    table = {tuple(row): v for row, v in zip(data["X"], data["l0"])}
    model = ARTDML(learner_l=Lookup(table), n_folds=3, pooling_l="local")
    model.fit(data["y"], data["d"], data["X"], data["cluster"], m_known=data["m0"])
    assert np.allclose(model.result_.ytilde, data["y"] - data["l0"])


def test_buffered_dependence_mode_runs():
    data = simulate_plm(q=6, n_j=240, dependence_R=2, seed=5)
    model = ARTDML(learner_m=poly_learner(), learner_l=poly_learner(), n_folds=4,
                   pooling_m="local", pooling_l="local", buffer=2)
    model.fit(data["y"], data["d"], data["X"], data["cluster"])
    assert model.result_.scored.all()
    for r in model.result_.plan.roles:   # buffer rows never train the model scoring their block
        lo, hi = r.eval_idx.min(), r.eval_idx.max()
        assert not np.any((r.base_target_idx >= lo - 2) & (r.base_target_idx <= hi + 2))
    assert 0 < model.pvalue(1.0) <= 1


def test_constant_predictor():
    assert np.all(ConstantPredictor(0.3).predict(np.zeros((5, 2))) == 0.3)
