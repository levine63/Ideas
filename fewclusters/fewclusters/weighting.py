"""Experimental weights for S_j=sqrt(n_j)(theta_j-lambda).

Precision stabilization is prespecified, not chosen to minimize p-values.
Data-dependent weights need additional asymptotic justification; this module
makes no finite-sample validity or optimality claim.
"""
import numpy as np


def score_weights(n, tau2=None, kappa=100.0, floor_fraction=0.1):
    n=np.asarray(n,dtype=float)
    if n.ndim!=1 or not np.isfinite(n).all() or np.any(n<=1):
        raise ValueError('Site sizes must be finite and greater than one.')
    if tau2 is None:
        w=np.sqrt(n)
        return w/w.sum(),None
    t=np.asarray(tau2,dtype=float)
    if t.shape!=n.shape or not np.isfinite(t).all() or np.any(t<0):
        raise ValueError('Variances must be finite, nonnegative, and match site sizes.')
    if not np.isfinite(kappa) or kappa<0 or not 0<floor_fraction<=1:
        raise ValueError('Invalid stabilization constants.')
    df=n-1
    pooled=float(np.sum(df*t)/df.sum())
    if pooled<=0:
        raise ValueError('No positive score variance.')
    stabilized=np.maximum((df*t+kappa*pooled)/(df+kappa),floor_fraction*pooled)
    w=np.sqrt(n)/stabilized
    return w/w.sum(),stabilized


def residual_variances(v,ytilde,cluster):
    """IID plug-in Var(S_j); site-centered estimated influence contributions."""
    v,ytilde,cluster=np.asarray(v),np.asarray(ytilde),np.asarray(cluster)
    values=[]
    for j in np.unique(cluster):
        mask=cluster==j
        vv,yy=v[mask],ytilde[mask]
        q=np.mean(vv**2)
        if len(vv)<2 or not q>0 or not np.isfinite(vv).all() or not np.isfinite(yy).all():
            raise ValueError('Invalid residuals or unidentified site.')
        theta=np.sum(vv*yy)/np.sum(vv**2)
        influence=vv*(yy-theta*vv)/q
        values.append(np.var(influence,ddof=1))
    return np.asarray(values)
