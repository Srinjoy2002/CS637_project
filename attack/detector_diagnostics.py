"""Independent diagnostics matching REP v1.2, including prefix caveats."""
from dataclasses import dataclass,asdict
import numpy as np
from scipy.stats import binom,chi2
from simulation.closed_loop import parse_schedule

@dataclass(frozen=True)
class Config:
    p: float=.25
    alpha: float=.01
    window: int=10
    amax: int=4
    detector: str='bin'
    windows: tuple=()
    def __post_init__(self):
        if not 0<self.p<1 or not 0<self.alpha<1: raise ValueError('p and alpha must lie strictly between 0 and 1')
        if self.window<1 or self.amax<1 or self.amax>20: raise ValueError('Invalid window or watchdog')
        if self.detector not in ('bin','chi2','bin_chi2','multi'): raise ValueError('Unknown detector')
        if any(w<1 for w in self.windows): raise ValueError('Invalid multiwindow')

def longest_run(z):
    best=run=0
    for b in z:
        run=run+1 if b else 0;best=max(best,run)
    return best

def run_counts(z,amax):
    """Count closed patterns 0 1^k 0. Ignore unfinished run, as REP does."""
    counts=np.zeros(amax+1,dtype=int);previous=None
    for i,b in enumerate(z):
        if not b:
            if previous is not None:
                k=i-previous-1
                if k<=amax:counts[k]+=1
            previous=i
    return counts

def diagnose(z,cfg=Config()):
    z=parse_schedule(z);L=len(z)
    threshold=int(binom.ppf(1-cfg.alpha,cfg.window,cfg.p))
    counts=[int(sum(z[i:i+cfg.window])) for i in range(L-cfg.window+1)] if L>cfg.window else [int(sum(z))]
    ms=run_counts(z,cfg.amax);N=int(ms.sum())
    probabilities=np.r_[(1-cfg.p)*cfg.p**np.arange(cfg.amax),cfg.p**cfg.amax]
    expected=N*probabilities
    statistic=float(np.sum((ms-expected)**2/expected)) if N else None
    limit=float(chi2.ppf(1-cfg.alpha,cfg.amax))
    geo=bool(statistic<=limit+1e-10) if N else None
    wd=longest_run(z)<=cfg.amax;bn=max(counts)<=threshold
    extra=[]
    for w in (cfg.windows or (10,20,40)):
        t=int(binom.ppf(1-cfg.alpha,w,cfg.p))
        cc=[int(sum(z[i:i+w])) for i in range(L-w+1)] if L>w else [int(sum(z))]
        extra.append(dict(window=w,threshold=t,max_count=max(cc),accepted=max(cc)<=t))
    active=bn if cfg.detector=='bin' else geo if cfg.detector=='chi2' else (bn and geo) if cfg.detector=='bin_chi2' else all(a['accepted'] for a in extra)
    return dict(config=asdict(cfg),watchdog=bool(wd),longest_run=longest_run(z),
                binomial=bool(bn),binomial_threshold=threshold,window_counts=counts,
                geometric=geo,chi_square=statistic,chi_threshold=limit,
                run_counts=ms.tolist(),expected=expected.tolist(),N=N,multi=extra,
                accepted=bool(wd and active) if active is not None else None,
                density=float(z.mean()),boundary_hits=bool(z[0]==0 and z[-1]==0),
                expected_counts_small=bool(np.any(expected<5)),
                note='Final finite-schedule REP compatibility; not a guarantee of no prefix alarm.')

def prefix_diagnostics(z,cfg):
    return [diagnose(z[:k],cfg) for k in range(1,len(z)+1)]

def false_alarm_experiment(cfg,length=100,trials=1000,seed=637):
    """IID nominal misses; report any alarm over a session, distinct from alpha."""
    rng=np.random.default_rng(seed);stats=np.zeros(4,dtype=int)
    for _ in range(trials):
        z=rng.binomial(1,cfg.p,length);d=diagnose(np.r_[0,z,0],cfg)
        stats+=np.array([not d['watchdog'],not d['binomial'],d['geometric'] is False,d['accepted'] is False])
    return dict(trials=trials,length=length,seed=seed,nominal_p=cfg.p,
                watchdog_rate=stats[0]/trials,binomial_any_window_rate=stats[1]/trials,
                geometric_end_rate=stats[2]/trials,selected_end_rate=stats[3]/trials,
                note='Monte Carlo with forced boundary hits; geometric checked at end, binomial over all windows.')
