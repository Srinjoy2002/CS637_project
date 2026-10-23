"""Single entry point. No optimisation runs without an explicit command."""
from pathlib import Path
import argparse, json, subprocess, sys, webbrowser
ROOT=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser(description='CPS final-PPT project: start here')
 sub=p.add_subparsers(dest='command')
 sub.add_parser('info');sub.add_parser('verify');sub.add_parser('replay')
 d=sub.add_parser('dashboard');d.add_argument('--system',choices=['furuta','tank'],default='furuta')
 a=sub.add_parser('author');a.add_argument('--script',choices=['main_short.py','main_fig2.py','main_fig3.py','main_fig4.py','main.py'],default='main_short.py');a.add_argument('--run',action='store_true')
 e=sub.add_parser('enumerate');e.add_argument('--max-ell',type=int,default=10)
 f=sub.add_parser('defender');f.add_argument('--run',action='store_true')
 x=p.parse_args()
 if x.command in (None,'info'):
  print('Final PPT: presentations/final/main.pdf and main.tex')
  print('Original main.py: vendor/REP_v1.2/main.py (full, expensive campaign)')
  print('PPT numerical evidence: data/ppt/; read docs/PPT_FILE_MAP.md')
  print('Commands: verify | replay | dashboard --system furuta|tank | enumerate --max-ell 10')
  print('Solver commands require explicit --run: author | defender')
  return
 if x.command=='dashboard':
  file='furuta_table1_dashboard.html' if x.system=='furuta' else 'tank_verified_replay.html'
  webbrowser.open((ROOT/'visualisations'/file).as_uri());return
 if x.command=='defender':
  cfg=json.loads((ROOT/'config/defender_config.json').read_text());count=0
  for det in cfg['detectors']:
   count+=len(cfg['systems'])*len(cfg['a_max'])*len(cfg['alpha'])*(1 if det=='chi2' else len(cfg['windows']))*len(cfg['p_miss'])*len(cfg['ells'])
  print('Requested original-optimizer calls:',count)
  print('The PPT saved sweep is partial; running this command is a NEW campaign.')
  if not x.run: print('Preview only. Use --run to start Gurobi.');return
  raise SystemExit(subprocess.call([sys.executable,str(ROOT/'rep_defender_driver.py')],cwd=ROOT))
 if x.command=='author':
  args=[sys.executable,str(ROOT/'tools/run_author_driver.py'),'--script',x.script]
  if not x.run:args.append('--prepare-only')
  raise SystemExit(subprocess.call(args,cwd=ROOT))
 if x.command=='enumerate':
  from tools.ppt_evidence import enumerate_curve
  enumerate_curve(x.max_ell);return
 from tools.ppt_evidence import replay_cases,verify
 if x.command=='verify':verify()
 else:replay_cases(make_plots=True)
if __name__=='__main__':main()
