"""Reproduce the final PPT's saved cases without Gurobi; no network access."""
from pathlib import Path
import csv,hashlib,json,math,io
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def replay_cases(make_plots=False):
 from models.paper import get_model
 from simulation.closed_loop import simulate
 from attack.detector_diagnostics import Config,diagnose
 output=ROOT/'outputs/ppt_replay';output.mkdir(parents=True,exist_ok=True)
 rows=list(csv.DictReader(io.StringIO((ROOT/'data/ppt/case_results.csv').read_text(encoding='utf-8'))));results=[];traces=[]
 for row in rows:
  bits=[int(b) for b in row['schedule']];z=[0]+bits+[0];tank=row['system']=='tank'
  audit=diagnose(z,Config(p=.25,alpha=.01,window=int(row['window']),amax=4,detector=row['detector']))
  item=dict(case=row['case'],ell=len(bits),schedule=row['schedule'],diagnostics=audit)
  for pol in ['hold','zero']:
   name=('qt_nmp' if pol=='hold' else 'qt_zero') if tank else 'furuta_'+pol
   m=get_model(name);x=simulate(m,z);nom=simulate(m,[0]*len(z));Q=m.Q_output
   omega=float(x[-2]@Q@x[-2]-nom[-2]@Q@nom[-2]);key='hold_omega' if pol=='hold' else 'zero_same_schedule_omega'
   assert math.isclose(omega,float(row[key]),rel_tol=2e-10,abs_tol=1e-12),(row['case'],pol,omega,row[key])
   item[pol+'_omega']=omega
   # After the first hit, before the final hit: precisely the slide convention.
   xx=x[1:-1];yy=m.output(xx);y=yy[:,1] if tank else np.degrees(xx[:,0]);time=np.arange(len(y))*m.dt
   traces.append((row['case'],row['system'],pol,time,y))
  assert math.isclose(audit['chi_square'],float(row['chi2']),rel_tol=1e-12,abs_tol=1e-12)
  assert audit['accepted'],row['case']
  results.append(item)
 (output/'replayed_cases.json').write_text(json.dumps(results,indent=2))
 if make_plots:
  import matplotlib
  matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  for system in ['furuta','tank']:
   selected=[r for r in rows if r['system']==system];fig,axs=plt.subplots(len(selected),1,figsize=(10,2.5*len(selected)),squeeze=False)
   for ax,row in zip(axs[:,0],selected):
    for case,sys,pol,t,y in traces:
     if case==row['case']:ax.plot(t,y,label=pol.upper(),ls='-' if pol=='hold' else '--')
    ax.set_title(row['case']);ax.set_ylabel('angle (deg)' if system=='furuta' else 'lower-tank output y2');ax.grid(alpha=.25);ax.legend()
   axs[-1,0].set_xlabel('Seconds after first forced hit');fig.tight_layout();fig.savefig(output/(system+'_replays.png'),dpi=160);plt.close(fig)
 print('PASS: all 10 cases / 20 policy replays and chi-square values match the final PPT source CSV.')
 return results
def verify():
 manifest=json.loads((ROOT/'docs/vendor_sha256.json').read_text())
 for name,digest in manifest.items():assert hashlib.sha256((ROOT/'vendor/REP_v1.2'/name).read_bytes()).hexdigest()==digest,name
 assert len(list(csv.DictReader(io.StringIO((ROOT/'data/ppt/omega_main_short.csv').read_text(encoding='utf-8')))))==25
 assert len(list(csv.DictReader(io.StringIO((ROOT/'data/ppt/defender_available_summary.csv').read_text(encoding='utf-8')))))==18
 replay_cases()
 print('PASS: author hashes, 25-point curve and 18-row partial summary present.')
def enumerate_curve(max_ell=10):
 from attack.exhaustive import optimize
 from attack.detector_diagnostics import Config
 if not 1<=max_ell<=25:raise ValueError('Use a maximum horizon from 1 through 25')
 results=[]
 for ell in range(1,max_ell+1):
  r=optimize('furuta_zero',ell,Config(p=.25,alpha=.01,window=20,amax=3,detector='bin_chi2'));results.append(r);print(ell,r['status'],r.get('omega'),flush=True)
 output=ROOT/'outputs/independent_enumeration';output.mkdir(parents=True,exist_ok=True)
 (output/'curve.json').write_text(json.dumps(results,indent=2))
 print('Saved independent results. This does not replace the historical CSV automatically.')
