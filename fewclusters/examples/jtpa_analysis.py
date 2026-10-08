"""JTPA pilot. Explicit propensity provenance; literal OLS/DIM comparisons.

Real data default to estimated propensity. Supply --propensity only with an
explicit --propensity-source; an assumption is reported as such. No observed
allocation fraction is ever passed as known. ART intervals assume a common
site effect and the note's sampling conditions, not arbitrary heterogeneity.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from fewclusters import ARTDML, attainable_size
from fewclusters.art import sign_group, art_test, art_confint


def load_table(path):
    if str(path).lower().endswith('.dta'):
        return pd.read_stata(path, convert_categoricals=False)
    return pd.read_csv(path)


def propensity_vector(data, probability=None, probability_column=None, source=None):
    if probability is not None and probability_column is not None:
        raise ValueError('Choose a constant probability OR a probability column.')
    if probability is None and probability_column is None:
        return None
    if not source or not source.strip():
        raise ValueError('An explicit propensity source or assumption is required.')
    p = (np.full(len(data), probability, dtype=float) if probability_column is None
         else data[probability_column].to_numpy(float))
    if not np.all(np.isfinite(p)) or np.any((p <= 0) | (p >= 1)):
        raise ValueError('Supplied probabilities must be finite and strictly inside (0,1).')
    return p


def demo_data(seed=0):
    rng = np.random.default_rng(seed)
    s = np.repeat(np.arange(8), 150)
    x = rng.normal(size=(len(s), 2))
    d = rng.binomial(1, 2/3, len(s))
    y = 1000*d + 2000*x[:, 0] + 500*x[:, 1]**2 + 100*s + rng.normal(0, 3000, len(s))
    return pd.DataFrame(dict(site=s, T=d, Y=y, x0=x[:, 0], x1=x[:, 1]))


def crve_site_fe(y, d, X, site, alpha):
    labels, s = np.unique(site, return_inverse=True)
    Z = np.column_stack([d, X, np.eye(len(labels))[s]])
    rank = np.linalg.matrix_rank(Z)
    if rank != Z.shape[1]:
        raise ValueError('Pooled OLS design is rank deficient; review covariates.')
    beta = np.linalg.lstsq(Z, y, rcond=None)[0]
    e = y - Z @ beta
    # pinv(Z) avoids squaring the condition number of earnings covariates.
    A = np.linalg.pinv(Z)
    influence = np.column_stack([A[:, s == j] @ e[s == j] for j in range(len(labels))])
    q, n = len(labels), len(y)
    V = influence @ influence.T * q/(q-1) * (n-1)/(n-rank)
    se = np.sqrt(V[0, 0])
    crit = stats.t.ppf(1-alpha/2, q-1)
    return dict(method='OLS site FE CR1', est=float(beta[0]), lo=float(beta[0]-crit*se),
                hi=float(beta[0]+crit*se), p0=float(2*stats.t.sf(abs(beta[0]/se), q-1)))


def classical_site_estimates(y, d, X, site, linear=False):
    theta, ns = [], []
    for lab in np.unique(site):
        rows = site == lab
        yy, dd = y[rows], d[rows]
        if np.unique(dd).size != 2:
            raise ValueError('Both assignment arms required in every site.')
        if linear:
            xx = X[rows]
            # Site-constant controls are collinear with the intercept, drop them.
            xx = xx[:, np.std(xx, axis=0) > 1e-12]
            z = np.column_stack([np.ones(len(dd)), dd, xx])
            if np.linalg.matrix_rank(z) < z.shape[1]:
                raise ValueError(f'Nonconstant OLS covariates collinear in site {lab}.')
            est = np.linalg.lstsq(z, yy, rcond=None)[0][1]
        else:
            est = yy[dd == 1].mean()-yy[dd == 0].mean()
        theta.append(est)
        ns.append(len(yy))
    return np.asarray(theta), np.asarray(ns)


def gbr():
    return HistGradientBoostingRegressor(max_iter=200, learning_rate=.05,
        max_leaf_nodes=15, min_samples_leaf=30, random_state=0)


def gbc():
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=.05,
        max_leaf_nodes=15, min_samples_leaf=30, random_state=0)


def method_specs():
    return {
        'DML linear local': dict(learner_l=LinearRegression(), pooling_l='local'),
        'DML local full': dict(learner_l=gbr(), pooling_l='local'),
        'DML local matched': dict(learner_l=gbr(), pooling_l='local', reserve_calibration=True),
        'DML pooled matched': dict(learner_l=gbr(), pooling_l='pooled_id', reserve_calibration=True),
        'DML adaptive': dict(learner_l=gbr(), pooling_l='adaptive'),
        'DML adaptive both': dict(learner_l=gbr(), pooling_l='adaptive', pooling_m='adaptive'),
    }


def run_all(df, y, d, site, xs, strata=None, alpha=.05, n_folds=5, seed=0,
            probability=None, probability_column=None, probability_source=None):
    if strata and strata not in xs:
        raise ValueError('Include design strata in covariates after appropriate encoding.')
    cols = list(dict.fromkeys([y, d, site]+xs+([probability_column] if probability_column else [])))
    data = df[cols].dropna()
    yv, dv, X, sv = data[y].to_numpy(float), data[d].to_numpy(float), data[xs].to_numpy(float), data[site].to_numpy()
    if not set(np.unique(dv)).issubset({0, 1}):
        raise ValueError('Treatment column must be binary ASSIGNMENT, not service receipt.')
    if not np.isfinite(np.column_stack([yv, dv, X])).all():
        raise ValueError('Nonfinite data values.')
    p = propensity_vector(data, probability, probability_column, probability_source)
    labels = np.unique(sv)
    q = len(labels)
    result = dict(status='PRELIMINARY - NOT FOR PUBLICATION', n=len(data), dropped=len(df)-len(data), q=q, seed=seed, alpha=alpha,
                  attainable=attainable_size(q, alpha),
                  propensity=probability_source if p is not None else 'Estimated separately within site by cross-fitted boosted classifier; not known',
                  xs=xs, rows=[], diagnostics=[], sites=[])
    result['rows'].append(crve_site_fe(yv, dv, X, sv, alpha))
    signs, exact = sign_group(q)
    for linear, name in [(False, 'ART difference in means'), (True, 'ART within-site OLS')]:
        theta, ns = classical_site_estimates(yv, dv, X, sv, linear)
        b = np.sqrt(ns)
        a = b*theta
        lo, hi = art_confint(a, b, signs, alpha)
        result['rows'].append(dict(method=name, est=float(a.sum()/b.sum()), lo=lo, hi=hi,
                                  p0=art_test(a, b, 0., signs, exact, alpha).p_value))
        result['sites'].extend(dict(method=name, cluster=str(lab), theta_hat=float(th), n_scored=int(n))
                               for lab, th, n in zip(labels, theta, ns))
    for name, spec in method_specs().items():
        if p is not None and name == 'DML adaptive both':
            continue
        spec.setdefault('pooling_m', 'local')
        spec.setdefault('shrink_l', 0.0)
        spec.setdefault('min_local_train', 0)
        model = ARTDML(learner_m=gbc(), n_folds=n_folds, random_state=seed, **spec)
        model.fit(yv, dv, X, sv, m_known=p)
        lo, hi = model.confint(alpha)
        r = model.result_
        result['rows'].append(dict(method=name, est=model.pooled_estimate(), lo=lo, hi=hi,
                                  p0=model.pvalue(0), outcome_mse=float(np.mean((yv-r.lhat)**2))))
        for row in model.cluster_table():
            result['sites'].append(dict(method=name, **row))
        for diag in r.diagnostics_l:
            result['diagnostics'].append(dict(method=name, **diag.as_dict()))
    return result


def report(res, title):
    lines = [f'# {title}', '', '**PRELIMINARY - NOT FOR PUBLICATION**', '', f"N={res['n']}; dropped={res['dropped']}; sites={res['q']}; split seed={res['seed']}.",
             f"Propensity: {res['propensity']}", '',
             'Exploratory comparison. ART coverage requires the common-effect and sampling assumptions. '
             'Observed interval length is not a measure of coverage or power. Earnings timing and extract selection require source verification.', '',
             'ART point estimates weight site estimates by sqrt(n_site); pooled OLS generally uses different weights. '
             'Differences can reflect effect heterogeneity as well as adjustment.', '',
             '| Method | Estimate | CI low | CI high | Length | p(0) |', '|---|---:|---:|---:|---:|---:|']
    for r in res['rows']:
        lines.append(f"| {r['method']} | {r['est']:.1f} | {r['lo']:.1f} | {r['hi']:.1f} | {r['hi']-r['lo']:.1f} | {r['p0']:.4f} |")
    site_rows = [r for r in res['sites'] if r['method'] == 'ART difference in means']
    small = [(str(r['cluster']), r['n_scored']) for r in site_rows if r['n_scored'] < 100]
    if small:
        lines += ['', 'SMALL-SITE WARNING: ' + ', '.join(f'{j}: n={n}' for j,n in small)
                  + '. Normal approximation may be poor; small calibration folds give noisy weights. '
                    'Shrinkage alone does not establish normality. The n<100 flag is a diagnostic heuristic.']
    lines.extend(['', 'Local full uses all non-evaluation observations. Local matched, pooled matched, and adaptive reserve '
                  'the same calibration fold. With estimated m, its local fit uses these respective training allocations too.', '',
                  'Exact sign enumeration means all signs were enumerated; it is not exact finite-sample randomization inference.'])
    return '\n'.join(lines)+'\n'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data'); ap.add_argument('--demo', action='store_true')
    ap.add_argument('--y', default='Y'); ap.add_argument('--d', default='T'); ap.add_argument('--site', default='site')
    ap.add_argument('--x', default='prevearn,age,married,black,hispanic,hsorged,yrs_educ')
    ap.add_argument('--strata'); ap.add_argument('--subset'); ap.add_argument('--alpha', type=float, default=.05)
    ap.add_argument('--folds', type=int, default=5); ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--propensity', type=float); ap.add_argument('--propensity-column'); ap.add_argument('--propensity-source')
    ap.add_argument('--out', required=True)
    a=ap.parse_args()
    if a.demo:
        df=demo_data(a.seed); a.x='x0,x1'; a.propensity=2/3; a.propensity_source='Known synthetic Bernoulli DGP p=2/3'
    elif a.data:
        df=load_table(a.data)
    else:
        ap.error('Supply --data or --demo')
    if a.subset: df=df.query(a.subset)
    res=run_all(df,a.y,a.d,a.site,a.x.split(','),a.strata,a.alpha,a.folds,a.seed,
                a.propensity,a.propensity_column,a.propensity_source)
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(report(res,'Synthetic pipeline check' if a.demo else 'JTPA pilot'),encoding='utf-8')
    out.with_suffix('.json').write_text(json.dumps(res,indent=2,default=lambda x:x.item())+'\n')
    print(report(res,'Synthetic pipeline check' if a.demo else 'JTPA pilot'),flush=True)

if __name__=='__main__': main()
