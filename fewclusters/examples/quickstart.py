"""
Quickstart: simulate a few-cluster dataset, run ARTDML with adaptive pooling,
test theta = 0, and build a 95% confidence interval.

Run from the package root:  PYTHONPATH=. python examples/quickstart.py
"""

from sklearn.ensemble import GradientBoostingRegressor

from fewclusters import ARTDML, simulate_plm

data = simulate_plm(q=8, n_j=600, theta=1.0, tau_m=0.5, tau_l=0.5, seed=7)

learner = lambda: GradientBoostingRegressor(n_estimators=150, max_depth=2, learning_rate=0.1)

model = ARTDML(learner_m=learner(), learner_l=learner(), n_folds=5,
               pooling_m="adaptive", pooling_l="adaptive", borrow="pooled_id",
               random_state=0)
model.fit(data["y"], data["d"], data["X"], data["cluster"])

print(model.summary(alpha=0.05))
print()
print(model.test(0.0))         # H0: no effect
print(model.test(1.0))         # H0: the true value

# Reading the per-cluster table matters. If every theta_hat_j sits on the same
# side of the truth, the nuisance learners are biased in a common direction and
# the product-rate condition (eq. (5)) is not yet met at this cluster size; the
# sign test cannot see a shift shared by all clusters. Compare learners, enlarge
# n_j, or inspect the calibration MSEs in model.result_.diagnostics_*.

# Known propensities (Corollary 2): pass m_known and skip learner_m
data2 = simulate_plm(q=8, n_j=600, known_propensity=True, tau_l=1.0, seed=8)
model2 = ARTDML(learner_l=learner(), n_folds=5, pooling_l="pooled")
model2.fit(data2["y"], data2["d"], data2["X"], data2["cluster"], m_known=data2["m0"])
print()
print(model2.summary())
