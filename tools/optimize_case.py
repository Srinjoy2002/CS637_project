"""One local optimization requested by the dashboard; no startup optimization."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rep_audit import Config, OfficialRunner

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--system',required=True);p.add_argument('--ell',type=int,required=True)
    p.add_argument('--detector',default='bin');p.add_argument('--window',type=int,default=10)
    p.add_argument('--p',type=float,default=.25);p.add_argument('--alpha',type=float,default=.01)
    p.add_argument('--amax',type=int,default=4);p.add_argument('--method',choices=['official','enumeration'],default='official')
    p.add_argument('--output',required=True);p.add_argument('--time-limit',type=int,default=20)
    a=p.parse_args();cfg=Config(a.p,a.alpha,a.window,a.amax,a.detector)
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    if a.method=='official':
        output.mkdir(exist_ok=True);runner=None
        try:
            runner=OfficialRunner(time_limit=a.time_limit)
            report=runner.preflight()
            if not report['full_size_probe']:result=report
            else:result=runner.solve(a.system,a.ell,cfg,output/'runs')
        except Exception as exc:
            result=dict(status='ERROR',error=type(exc).__name__+': local solver initialization or execution failed.')
        finally:
            if runner:runner.close()
        (output/'status.json').write_text(json.dumps(result,indent=2))
    else:
        from attack.exhaustive import optimize
        result=optimize(a.system,a.ell,cfg)
        Path(str(output)+'.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
if __name__=='__main__':main()
