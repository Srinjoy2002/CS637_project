"""Independent exact enumeration of the REP finite binary problem.

No optimizer is imitated: every admissible binary leaf is evaluated. Numba is
optional for short tests and recommended for horizons above 12. Float64 arithmetic
and explicit tolerances apply; this is not an interval-arithmetic certificate.
"""
import time
import numpy as np
from scipy.stats import binom,chi2
from models.paper import get_model
from simulation.closed_loop import simulate
from .detector_diagnostics import Config,diagnose
try:
    from numba import njit
    ACCELERATED=True
except ImportError:
    ACCELERATED=False
    def njit(**kwargs):return lambda f:f

@njit(cache=True)
def _search(H,M,Q,x0,ell,amax,windows,limits,geo,prob,chi_limit,objective):
    n=len(x0);L=ell+2
    x=np.zeros((L+1,n));x[0]=x0;x[1]=H@x0
    z=np.zeros(L,np.int64);next_choice=np.zeros(L,np.int64)
    runs=np.zeros(L,np.int64);sums=np.zeros(L+1,np.int64)
    cum=np.zeros(L+1);peak=np.zeros(L+1)
    peak[0]=x0@Q@x0;v=x[1]@Q@x[1];cum[1]=v;peak[1]=max(peak[0],v)
    best=-np.inf;best_z=z.copy();feasible=0;nodes=0;d=1
    while d>=1:
        if next_choice[d]>1:
            next_choice[d]=0;d-=1;continue
        b=next_choice[d];next_choice[d]+=1;nodes+=1
        run=(runs[d-1]+1) if b else 0
        if run>amax:continue
        z[d]=b;runs[d]=run;sums[d+1]=sums[d]+b
        valid=True
        for j in range(len(windows)):
            w=windows[j]
            if sums[d+1]-sums[max(0,d+1-w)]>limits[j]: valid=False;break
        if not valid:continue
        x[d+1]=(M if b else H)@x[d]
        if np.max(np.abs(x[d+1]))>1000:continue
        v=x[d+1]@Q@x[d+1];cum[d+1]=cum[d]+v;peak[d+1]=max(peak[d],v)
        if d<ell:
            d+=1;next_choice[d]=0;continue
        # Final boundary hit closes the last run and is state-bounded in REP.
        final=H@x[d+1]
        if np.max(np.abs(final))>1000:continue
        if geo:
            ms=np.zeros(amax+1);prev=0
            for k in range(1,L):
                if z[k]==0:
                    ms[k-prev-1]+=1;prev=k
            N=ms.sum();stat=0.
            for j in range(amax+1):stat+=(ms[j]-prob[j]*N)**2/prob[j]
            if stat>chi_limit*N+1e-10:continue
        feasible+=1
        value=v if objective==0 else cum[d+1] if objective==1 else peak[d+1]
        if value>best:
            best=value;best_z=z.copy()
    return best,best_z,feasible,nodes

def optimize(name,ell,cfg=Config(),scale=1.,objective='terminal'):
    if not 1<=ell<=25:raise ValueError('Enumeration supports horizons 1..25')
    if not ACCELERATED and ell>12:raise RuntimeError('Install numba for horizons above 12')
    if objective not in ('terminal','cumulative','peak'):raise ValueError('Unknown objective')
    m=get_model(name);t=time.perf_counter()
    ws=list(cfg.windows or (10,20,40)) if cfg.detector=='multi' else [cfg.window] if cfg.detector in ('bin','bin_chi2') else []
    thresholds=[int(binom.ppf(1-cfg.alpha,w,cfg.p)) for w in ws]
    probs=np.r_[(1-cfg.p)*cfg.p**np.arange(cfg.amax),cfg.p**cfg.amax]
    value,z,feasible,nodes=_search(m.hit,m.miss,m.Q_rep,m.x0*scale,ell,cfg.amax,
        np.array(ws,dtype=np.int64),np.array(thresholds,dtype=np.int64),
        cfg.detector in ('chi2','bin_chi2'),probs,chi2.ppf(1-cfg.alpha,cfg.amax),
        ['terminal','cumulative','peak'].index(objective))
    if not feasible:return dict(status='INFEASIBLE',ell=ell,system=name,nodes=int(nodes))
    xn=simulate(m,np.zeros(ell+2,dtype=int),m.x0*scale)
    costs=np.einsum('bi,ij,bj->b',xn,m.Q_rep,xn)
    nominal=costs[-2] if objective=='terminal' else costs[1:-1].sum() if objective=='cumulative' else costs[:-1].max()
    return dict(status='EXHAUSTIVE_OPTIMAL',method='independent enumeration, float64',
        system=name,ell=ell,rep_counter_note=('Matches REP pattern constraints' if ell>=cfg.amax or cfg.detector not in ('chi2','bin_chi2') else 'Short-horizon REP leaves empty-pattern categories unconstrained; independent enumeration fixes actual counts to zero.'),schedule=z.tolist(),interior=z[1:-1].tolist(),objective_kind=objective,
        attack_rep=float(value),nominal_rep=float(nominal),omega=float((value-nominal)*m.output_scale),
        objective=float(value*m.output_scale),nominal=float(nominal*m.output_scale),
        feasible_leaves=int(feasible),nodes=int(nodes),seconds=time.perf_counter()-t,
        config=cfg.__dict__,diagnostics=diagnose(z,cfg),scale=scale)
