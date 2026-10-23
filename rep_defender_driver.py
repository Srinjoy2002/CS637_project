#!/usr/bin/env python3
"""Defender-parameter sweep using UNMODIFIED official REP v1.2 optimizer scripts.

Run through main.py defender --run in the consolidated repository.
Author scripts live in vendor/REP_v1.2; config is config/defender_config.json.
Results live in outputs/defender_official/results_{detector}/{system}/...
"""
import ast
import csv
import json
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import gurobipy as gp
from scipy.stats import binom, geom, chi2

ROOT = Path(__file__).resolve().parent
AUTHOR = ROOT/'vendor/REP_v1.2'
CFG = json.loads((ROOT/'config/defender_config.json').read_text())
OUT = ROOT/'outputs/defender_official'
OUT.mkdir(parents=True,exist_ok=True)
os.chdir(OUT)

source=ast.parse((AUTHOR/'main_short.py').read_text())
fun=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='define_system']
assert len(fun)==1
exec(compile(ast.Module(body=fun,type_ignores=[]),str(AUTHOR/'main_short.py'),'exec'),globals())

FILE = {'bin':'optimise_bin.py', 'chi2':'optimise_chi2.py',
        'bin_chi2':'optimise_bin_chi2.py'}

def result_path(det,system,amax,p,alpha,window):
    return OUT/f'results_{det}'/system/f'a{amax}_p{p}_alpha{alpha}_w{window}.csv'

def has_length(path,n):
    if not path.exists():
        return False
    try:
        with path.open(newline='') as f:
            for row in csv.DictReader(f):
                try:
                    if int(row['length'])==n:
                        return True
                except (ValueError, KeyError, TypeError):
                    pass
    except Exception:
        return False
    return False

logs=[]
for detector in CFG['detectors']:
    if detector not in FILE:
        raise ValueError(detector)
    original = AUTHOR / FILE[detector]
    compiled=compile(original.read_text(),str(original),'exec')
    for system in CFG['systems']:
        Phi_miss, Phi_hit, C, Q, x0, nx = define_system(system)
        for a_max in CFG['a_max']:
            for significance_level in CFG['alpha']:
                for window_length in ([20] if detector=='chi2' else CFG['windows']):
                    for p_miss in CFG['p_miss']:
                        out_folder = OUT/f'results_{detector}'/system
                        out_folder.mkdir(parents=True,exist_ok=True)
                        csvp=result_path(detector,system,a_max,p_miss,significance_level,window_length)
                        for ell in CFG['ells']:
                            a_length=int(ell)+2
                            start=time.perf_counter()
                            status='SKIPPED' if has_length(csvp,a_length) else 'STARTED'
                            details=''
                            if status=='STARTED':
                                try:
                                    # Same globals that the original main_short.py sets.
                                    # Official optimizer source is executed verbatim.
                                    exec(compiled,globals())
                                    status='SOLVED' if has_length(csvp,a_length) else 'NO_OPTIMAL_ROW'
                                except Exception as exc:
                                    status='ERROR'
                                    details=f'{type(exc).__name__}: {exc}'
                                    traceback.print_exc()
                                finally:
                                    # Only close handles left open by exceptional paths.
                                    for var in ('filecsv','filetxt'):
                                        obj=globals().get(var)
                                        if obj is not None and not obj.closed:
                                            try: obj.close()
                                            except Exception: pass
                            secs=time.perf_counter()-start
                            row=dict(detector=detector,system=system,a_max=a_max,
                                     alpha=significance_level,window_length=window_length,
                                     p_miss=p_miss,ell=ell,status=status,
                                     elapsed_seconds=round(secs,3),notes=details)
                            logs.append(row)
                            print(f'{status:14s} {detector:8s} {system:12s}'
                                  f' w={window_length:2d} p={p_miss:.2f} '
                                  f'alpha={significance_level} ell={ell:2d}  {secs:.2f}s',
                                  flush=True)
                            if status in ('ERROR','NO_OPTIMAL_ROW'):
                                print('  Check Gurobi status, feasibility and license, before claiming completeness.')
                            # flush a simple progress manifest for interrupted sessions
                            with (OUT/'defender_run_manifest.csv').open('w',newline='') as mf:
                                wr=csv.DictWriter(mf,fieldnames=list(row))
                                wr.writeheader();wr.writerows(logs)
print('Sweep complete. Inspect defender_run_manifest.csv for non-optimal runs.')
