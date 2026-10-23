import numpy as np
from models.paper import get_model

def parse_schedule(value):
    if isinstance(value,str):
        s=''.join(value.split()).replace(',','')
        if any(c not in '01' for c in s): raise ValueError('Sequence must contain only 0 and 1')
        value=list(map(int,s))
    a=np.asarray(value)
    if a.ndim!=1 or not len(a) or not np.all((a==0)|(a==1)):
        raise ValueError('A nonempty one-dimensional binary schedule is required')
    return a.astype(np.int8)

def simulate(model, schedule, x0=None):
    if isinstance(model,str): model=get_model(model)
    z=parse_schedule(schedule)
    initial=model.x0 if x0 is None else np.asarray(x0,dtype=float)
    if initial.shape!=model.x0.shape or not np.all(np.isfinite(initial)): raise ValueError('Invalid initial state')
    x=np.empty((len(z)+1,len(initial)));x[0]=initial
    for k,miss in enumerate(z): x[k+1]=(model.miss if miss else model.hit)@x[k]
    if not np.all(np.isfinite(x)): raise ValueError('Numerical overflow: shorten the replay')
    return x

def objectives(model,x,index):
    costs=np.einsum('bi,ij,bj->b',x,model.Q_output,x)
    return dict(terminal=float(costs[index]),cumulative=float(costs[1:index+1].sum()),
                peak=float(costs[:index+1].max()),rep_terminal=float(x[index]@model.Q_rep@x[index]))

def compare(system,interior,tail=0,scale=1.0,safety=None):
    """REP boundary convention: z=[0]+interior+[0]; objective x[len(z)-1]."""
    if system not in ('furuta','tank'): raise ValueError('Unknown system')
    if not isinstance(tail,(int,np.integer)) or not 0<=tail<=1000: raise ValueError('Invalid tail')
    if not np.isfinite(scale) or not 0<scale<=10: raise ValueError('Scale must be finite and in (0,10]')
    if safety is not None and (not np.isfinite(safety) or safety<=0): raise ValueError('Threshold must be positive and finite')
    interior=parse_schedule(interior)
    z=np.r_[0,interior,0,np.zeros(tail,dtype=np.int8)]
    objective_index=len(interior)+1
    names=['furuta_hold','furuta_zero'] if system=='furuta' else ['qt_nmp','qt_zero']
    result=dict(system=system,z=z.tolist(),ell=len(interior),objective_index=objective_index,series=[])
    for name in names:
        m=get_model(name); x0=m.x0*scale
        x=simulate(m,z,x0); nominal=simulate(m,np.zeros(len(z),dtype=int),x0)
        ma=objectives(m,x,objective_index);mn=objectives(m,nominal,objective_index)
        ma.update(nominal=mn['terminal'],omega=ma['terminal']-mn['terminal'],
                  rep_omega=ma['rep_terminal']-mn['rep_terminal'])
        threshold=float(safety if safety is not None else (.2 if system=='furuta' else .5))
        physical=np.abs(x[:,:1] if system=='furuta' else x[:,:2])
        crossings=np.flatnonzero(np.any(physical>threshold,axis=1))
        # Arm position is absent in REP; integrate its velocity ONLY for drawing.
        arm=np.r_[0,np.cumsum((x[:-1,2]+x[1:,2])*.5*m.dt)] if system=='furuta' else []
        result['series'].append(dict(name=name,x=x.tolist(),nominal=nominal.tolist(),
            y=m.output(x).tolist(),u=x[:,-m.ninput:].tolist(),metrics=ma,arm=list(arm),
            safety=dict(threshold=threshold,violated=bool(len(crossings)),
                        first_index=int(crossings[0]) if len(crossings) else None,
                        criterion='user-defined absolute plant deviation; not a certified physical limit')))
    result['dt']=m.dt;result['labels']=m.labels
    return result
