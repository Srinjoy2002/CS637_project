"""Execute authors' optimizer unchanged in an isolated result directory.

Only execution controls (time/thread limit and logging) are injected into Env.
The mathematical source, objective, bounds and parameters are not rewritten.
Run in a dedicated subprocess: this function temporarily changes working directory.
"""
import json,os,time
from pathlib import Path
import numpy as np
from scipy.stats import binom,geom,chi2
from models.official_definition import define_system
from simulation.closed_loop import simulate
from models.paper import get_model
from .detector_diagnostics import Config,diagnose
ROOT=Path(__file__).resolve().parents[1]

def run_official(system,ell,cfg,output,time_limit=60):
    import gurobipy as gp
    if cfg.detector not in ('bin','chi2','bin_chi2'):raise ValueError('Official REP supports three original detectors')
    if system not in ('furuta_hold','furuta_zero','qt_nmp'):raise ValueError('Not an official system')
    if not 1<=ell<=25:raise ValueError('Use attack horizon 1..25')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    (output/f'results_{cfg.detector}'/system).mkdir(parents=True)
    class GPProxy:
        def __getattr__(self,k):return getattr(gp,k)
        def Env(self,*args,**kw):
            env=gp.Env(*args,**kw);env.setParam('TimeLimit',time_limit);env.setParam('Threads',2)
            return env
    miss,hit,C,Q,x0,nx=define_system(system)
    ns=dict(np=np,gp=GPProxy(),binom=binom,geom=geom,chi2=chi2,
            system=system,a_length=ell+2,a_max=cfg.amax,a_min=0,p_miss=cfg.p,
            significance_level=cfg.alpha,window_length=cfg.window,Phi_miss=miss,Phi_hit=hit,
            C=C,Q=Q,x0=x0,nx=nx)
    old=Path.cwd();result=dict(system=system,ell=ell,config=cfg.__dict__,gurobi_version=gp.gurobi.version())
    try:
        os.chdir(output)
        source=ROOT/'vendor/REP_v1.2'/f'optimise_{cfg.detector}.py'
        exec(compile(source.read_text(),str(source),'exec'),ns)
        m=ns['m'];result.update(status=int(m.Status),solutions=int(m.SolCount),runtime=m.Runtime,
                               status_label='GUROBI_OPTIMAL' if m.Status==gp.GRB.OPTIMAL else 'NOT_PROVEN_OPTIMAL')
        if m.SolCount:
            z=[int(round(v.X)) for v in ns['zs']];model=get_model(system)
            x=simulate(model,z);J=float(x[-2]@Q@x[-2]);nom=simulate(model,[0]*len(z))
            Jn=float(nom[-2]@Q@nom[-2])
            result.update(schedule=z,interior=z[1:-1],solver_objective=float(m.ObjVal),
                          attack_rep=J,nominal_rep=Jn,omega=(J-Jn)*model.output_scale,
                          replay_error=abs(J-m.ObjVal),bound=float(m.ObjBound),gap=float(m.MIPGap),
                          diagnostics=diagnose(z,cfg))
    except Exception as exc:
        result.update(status_label='ERROR',error=f'{type(exc).__name__}: {exc}')
    finally:
        os.chdir(old)
        for name in ('filecsv','filetxt'):
            if name in ns:ns[name].close()
        if 'm' in ns:ns['m'].dispose()
        if 'env' in ns:ns['env'].dispose()
    (output/'status.json').write_text(json.dumps(result,indent=2));return result
