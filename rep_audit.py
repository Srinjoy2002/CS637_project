"""Audited execution around unchanged REP v1.2 mathematical source.

No credentials are written into result records. Only runtime/solver execution
controls and environment selection are injected; author equations are retained.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom, chi2, geom

from models.paper import get_model
from attack.detector_diagnostics import Config, diagnose
from simulation.closed_loop import simulate

COMMIT = 'd3dbcaa0670bf1d99bf37b3164267b0b9a9398fd'
ROOT = Path(__file__).resolve().parent
SYSTEMS = ('furuta_zero', 'furuta_hold', 'qt_nmp')
DETECTORS = ('bin', 'chi2', 'bin_chi2')


def validate_request(system, ell, cfg):
    if system not in SYSTEMS or cfg.detector not in DETECTORS:
        raise ValueError('Select one original REP system and detector.')
    if not isinstance(ell, (int, np.integer)) or not 1 <= ell <= 25:
        raise ValueError('The interior horizon ell must be an integer from 1 to 25.')


def replay(system, schedule, cfg, solver_objective=None):
    """Score x[L-1], enforce independent diagnostics and replay state bounds."""
    model = get_model(system)
    z = np.asarray(schedule, dtype=int)
    if z.ndim != 1 or len(z) < 3 or any(b not in (0, 1) for b in z):
        raise ValueError('Invalid full binary schedule.')
    if z[0] != 0 or z[-1] != 0:
        raise ValueError('REP schedules require initial and final hits.')
    x = simulate(model, z)
    nominal = simulate(model, np.zeros(len(z), dtype=int))
    j = len(z)-1
    ja = float(x[j] @ model.Q_rep @ x[j])
    jn = float(nominal[j] @ model.Q_rep @ nominal[j])
    diagnostic = diagnose(z, cfg)
    err = None if solver_objective is None else abs(ja-solver_objective)
    tolerance = 1e-7 + 1e-7*abs(ja)
    bounds_ok = bool(np.max(np.abs(x[1:])) <= 1000+1e-6)
    replay_ok = err is None or err <= tolerance
    return dict(schedule=z.tolist(), interior=z[1:-1].tolist(),
                attack_rep=ja, nominal_rep=jn, objective=ja*model.output_scale,
                nominal=jn*model.output_scale, omega=(ja-jn)*model.output_scale,
                objective_index=j, replay_error=err, replay_tolerance=tolerance,
                diagnostics=diagnostic, state_bounds_ok=bounds_ok,
                validation_passed=bool(diagnostic['accepted'] and bounds_ok and replay_ok),
                rep_counter_note=('Author empty-category issue may apply at ell < amax.'
                    if len(z)-2 < cfg.amax and cfg.detector != 'bin' else 'All run categories have observable patterns.'))


def _safe_number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError, AttributeError):
        return None


def _error(exc):
    number = getattr(exc, 'errno', None)
    if number == 10010:
        return 'LICENSE_LIMIT', number, 'Model exceeds the active license size limit. Activate your full local Gurobi license or set GRB_LICENSE_FILE to its gurobi.lic path, then rerun the license cell.'
    # Exclude raw exception messages: license services can put account data there.
    return 'ERROR', number, type(exc).__name__ + ': operation failed; inspect the local solver log without sharing credentials.'


class OfficialRunner:
    """One reusable licensed environment; never fall back silently."""
    def __init__(self, credentials=None, time_limit=60, threads=2):
        import gurobipy as gp
        if time_limit <= 0 or threads < 1:
            raise ValueError('Positive time limit and thread count required.')
        self.gp = gp
        self.time_limit = float(time_limit)
        self.threads = int(threads)
        env = gp.Env(empty=True)
        try:
            env.setParam('OutputFlag', 0)
            for key, value in (credentials or {}).items():
                if key not in ('WLSACCESSID', 'WLSSECRET', 'LICENSEID'):
                    raise ValueError('Unexpected licensing parameter.')
                env.setParam(key, value)
            env.start()
        except BaseException:
            env.dispose()
            raise
        self.env = env
        self.preflight_passed = False

    def preflight(self):
        """A 201-variable quadratic probe rejects the restricted trial license."""
        gp = self.gp
        model = gp.Model(env=self.env)
        try:
            v = model.addMVar(201, lb=0., ub=1.)
            model.setObjective(v @ v, gp.GRB.MINIMIZE)
            model.optimize()
            if model.Status != gp.GRB.OPTIMAL:
                return dict(status='PREFLIGHT_FAILED', full_size_probe=False)
            self.preflight_passed = True
            return dict(status='READY', full_size_probe=True,
                        gurobi_version=list(gp.gurobi.version()))
        except Exception as exc:
            status, number, message = _error(exc)
            return dict(status=status, code=number, message=message, full_size_probe=False)
        finally:
            model.dispose()

    def close(self):
        self.env.dispose()

    def solve(self, system, ell, cfg, store, retry=False):
        validate_request(system, ell, cfg)
        if not self.preflight_passed:
            raise RuntimeError('Full-size license preflight must pass before official experiments.')
        store = Path(store).resolve()
        spec = dict(system=system, ell=int(ell), config=asdict(cfg), commit=COMMIT,
                    time_limit=self.time_limit, threads=self.threads,
                    gurobi_version=list(self.gp.gurobi.version()), python=platform.python_version())
        token = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:20]
        folder = store/token
        folder.mkdir(parents=True, exist_ok=True)
        record_path = folder/'status.json'
        if record_path.exists():
            previous = json.loads(record_path.read_text())
            if previous.get('proven_optimal') or not retry:
                return previous
        source = ROOT/'vendor/REP_v1.2'/f'optimise_{cfg.detector}.py'
        record = dict(spec, method='official REP v1.2, source unchanged', status='RUNNING',
                      source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                      validation_passed=False, proven_optimal=False)
        # Failed or time-limited retries get a fresh subdirectory; earlier output is preserved.
        attempt = folder/f'attempt_{time.time_ns()}'
        (attempt/f'results_{cfg.detector}'/system).mkdir(parents=True)
        gp = self.gp
        real_env = self.env
        created = []
        limit, threads = self.time_limit, self.threads

        class SharedEnv:
            def setParam(self, key, value):
                real_env.setParam(key, value)
            def start(self):
                pass  # authenticated environment has already started

        class GPProxy:
            def __getattr__(self, key):
                return getattr(gp, key)
            def Env(self, *args, **kwargs):
                real_env.setParam('TimeLimit', limit)
                real_env.setParam('Threads', threads)
                return SharedEnv()
            def Model(self, *args, **kwargs):
                kwargs['env'] = real_env
                model = gp.Model(*args, **kwargs)
                created.append(model)
                return model

        model = get_model(system)
        namespace = dict(np=np, gp=GPProxy(), binom=binom, geom=geom, chi2=chi2,
                         system=system, a_length=int(ell)+2, a_max=cfg.amax, a_min=0,
                         p_miss=cfg.p, significance_level=cfg.alpha, window_length=cfg.window,
                         Phi_miss=model.miss, Phi_hit=model.hit, C=model.C, Q=model.Q_rep,
                         x0=model.x0, nx=len(model.x0))
        old = Path.cwd()
        try:
            os.chdir(attempt)
            exec(compile(source.read_text(), str(source), 'exec'), namespace)
            solved = namespace['m']
            labels = {2:'OPTIMAL', 3:'INFEASIBLE', 4:'INF_OR_UNBD', 5:'UNBOUNDED',
                      9:'TIME_LIMIT', 11:'INTERRUPTED', 12:'NUMERIC', 13:'SUBOPTIMAL'}
            record.update(status=labels.get(solved.Status, f'STATUS_{solved.Status}'),
                          solver_status=int(solved.Status), solutions=int(solved.SolCount),
                          runtime=float(solved.Runtime), variables=int(solved.NumVars),
                          constraints=int(solved.NumConstrs), bound=_safe_number(solved.ObjBound))
            if solved.SolCount:
                solved.Params.SolutionNumber = 0
                z = [int(round(v.X)) for v in namespace['zs']]
                record.update(replay(system, z, cfg, float(solved.ObjVal)))
                record.update(solver_objective=float(solved.ObjVal), gap=_safe_number(solved.MIPGap))
            record['proven_optimal'] = bool(solved.Status == gp.GRB.OPTIMAL and record['validation_passed'])
        except KeyboardInterrupt:
            record.update(status='INTERRUPTED', message='User interrupted this optimization.')
            raise
        except Exception as exc:
            status, number, message = _error(exc)
            record.update(status=status, error_code=number, message=message)
        finally:
            os.chdir(old)
            for name in ('filecsv', 'filetxt'):
                if name in namespace:
                    namespace[name].close()
            for created_model in created:
                created_model.dispose()
            temporary = record_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(record, indent=2, allow_nan=False))
            temporary.replace(record_path)
        return record


def experiment_configs(figure):
    from itertools import product
    if figure == 2:
        return [(s, Config(p, .01, 20, a, 'bin_chi2'))
                for s, a, p in product(('qt_nmp','furuta_zero'), range(1,5), (.09,.17,.25))]
    if figure == 3:
        return [(s, Config(p, .01, 20, 4, d))
                for s, d, p in product(('qt_nmp','furuta_zero'), DETECTORS, (.09,.17,.25))]
    if figure == 4:
        return [(s, Config(p, .01, w, 4, 'bin'))
                for s, w, p in product(('furuta_zero','furuta_hold'), (10,12,14,16,18), (.09,.17,.25))]
    raise ValueError('Figure must be 2, 3, or 4.')


def run_grid(runner, configs, horizons, store, retry=False):
    rows = []
    for index, (system, cfg) in enumerate(configs, 1):
        for ell in horizons:
            result = runner.solve(system, int(ell), cfg, store, retry)
            rows.append(result)
            print(f'{index}/{len(configs)} {system} {cfg.detector} w={cfg.window} p={cfg.p} ell={ell}: {result["status"]}', flush=True)
            if result['status'] == 'LICENSE_LIMIT':
                raise RuntimeError(result['message'])
    return rows


def coverage(rows, configs, horizons):
    def key(system, cfg):
        cfg = asdict(cfg) if isinstance(cfg, Config) else cfg
        return system, cfg['detector'], cfg['amax'], cfg['window'], cfg['p'], cfg['alpha']
    requested = set(map(int, horizons))
    output = []
    for system, cfg in configs:
        selected = [r for r in rows if key(r['system'], r['config']) == key(system, cfg)
                    and int(r['ell']) in requested]
        valid = {int(r['ell']) for r in selected if r.get('proven_optimal', False)}
        output.append(dict(system=system, **asdict(cfg), requested=len(requested), solved=len(valid),
                           complete=valid == requested, missing=sorted(requested-valid)))
    return pd.DataFrame(output)


def rank_defender(rows, configs, horizons):
    """Rank only complete, independently validated solver-optimal configurations."""
    report = coverage(rows, configs, horizons)
    ranked = []
    for cfgrow in report.to_dict('records'):
        selected = [r for r in rows if r['system'] == cfgrow['system']
                    and all(r['config'][k] == cfgrow[k] for k in ('p','alpha','window','amax','detector'))
                    and r['ell'] in horizons and r.get('proven_optimal', False)]
        row = dict(cfgrow, worst_omega=None, worst_ell=None,
                   ranking_status='COMPLETE' if cfgrow['complete'] else 'INCOMPLETE — excluded')
        if cfgrow['complete']:
            worst = max(selected, key=lambda r:r['omega'])
            row.update(worst_omega=worst['omega'], worst_ell=worst['ell'])
        ranked.append(row)
    frame = pd.DataFrame(ranked)
    return frame.sort_values(['complete','worst_omega'], ascending=[False,True], na_position='last')


def cached_records(figure):
    path = ROOT/'data/reproductions'/f'figure{figure}_enumeration.json'
    rows = json.loads(path.read_text())['records']
    output = []
    for original in rows:
        row = dict(original)
        row.update(method='cached independent exhaustive enumeration, float64',
                   proven_optimal=False, validation_passed=False)
        # Recompute every cached winner; do not assert official equivalence at short ell.
        check = replay(row['system'], row['schedule'], Config(**row['config']))
        delta = abs(check['omega']-row['omega'])
        row.update(check)
        row['cached_objective_error'] = delta
        row['validation_passed'] = bool(check['validation_passed'] and delta <= 1e-12)
        row['proven_optimal'] = bool(original['status']=='EXHAUSTIVE_OPTIMAL' and row['validation_passed'])
        output.append(row)
    return output


def recover_legacy(root, store):
    """Recover old CSV/TXT winners without inventing missing solver metadata.

    Original REP only writes CSV rows for OPTIMAL status, but status/gap/bound
    is absent from the files themselves. Recovered rows remain explicitly
    uncertified and excluded from the new strict ranking.
    """
    import ast
    import re
    name_pattern=re.compile(r'a(?P<a>\d+)_p(?P<p>[0-9.]+)_alpha(?P<alpha>[0-9.]+)_w(?P<w>\d+)\.csv$')
    row_pattern=re.compile(r'\s*(\d+)\s*,\s*([^,]+),\s*(\[[^\]]*\])')
    records=[]
    for path in Path(root).rglob('*.csv'):
        match=name_pattern.fullmatch(path.name)
        if not match or path.parent.name not in SYSTEMS:continue
        detector=path.parent.parent.name.removeprefix('results_')
        if detector not in DETECTORS:continue
        textpath=path.with_suffix('.txt')
        if not textpath.exists():continue
        cfg=Config(float(match['p']),float(match['alpha']),int(match['w']),int(match['a']),detector)
        frame=pd.read_csv(path,skipinitialspace=True)
        frame.columns=frame.columns.str.strip()
        for line in textpath.read_text().splitlines()[1:]:
            parsed=row_pattern.match(line)
            if not parsed:continue
            length=int(parsed[1]);ell=length-2
            if not 1<=ell<=25:continue
            z=ast.literal_eval(parsed[3])
            if len(z)!=length:continue
            selected=frame[frame['length']==length]
            if selected.empty:continue
            objective=float(parsed[2])
            check=replay(path.parent.name,z,cfg,objective)
            csv_agrees=bool(np.any(np.isclose(selected['attack'],objective,rtol=1e-7,atol=1e-7)))
            check['validation_passed']=bool(check['validation_passed'] and csv_agrees)
            records.append(dict(system=path.parent.name,ell=ell,config=asdict(cfg),**check,
                method='recovered legacy REP CSV/TXT',status='LEGACY_UNCERTIFIED',
                proven_optimal=False,csv_agrees=csv_agrees,
                solver_objective=objective,gap=None,bound=None,
                source_file=str(path),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                note='Schedule/objective replayed; solver status/gap/bound not recorded by legacy files. Excluded from strict optimum rankings.'))
    target=Path(store)/'legacy_recovered.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(records,indent=2,allow_nan=False))
    return records


def trajectory_plot(record, angle_threshold=None):
    import matplotlib.pyplot as plt
    model = get_model(record['system'])
    x = simulate(model, record['schedule'])
    nominal = simulate(model, [0]*len(record['schedule']))
    fig, axes = plt.subplots(2,1,figsize=(10,6),constrained_layout=True)
    k = np.arange(len(x))
    for j in range(1 if model.nplant==3 else 2):
        axes[0].plot(k, model.output(x)[:,j], label=f'attacked output {j+1}')
        axes[0].plot(k, model.output(nominal)[:,j], '--', label=f'nominal output {j+1}')
    axes[0].axvline(record['objective_index'], color='black', ls=':', label='scored sample')
    verdict = None
    if angle_threshold is not None:
        if model.nplant != 3 or not math.isfinite(angle_threshold) or angle_threshold <= 0:
            raise ValueError('Use a positive finite Furuta angle threshold [rad].')
        for sign in (-1,1):
            axes[0].axhline(sign*angle_threshold, ls=':', color='red')
        verdict = dict(criterion=f'max |theta[k]| > {angle_threshold} rad over this replay',
                       violated=bool(np.max(np.abs(x[:,0]))>angle_threshold),
                       note='User-selected performance limit; not validated physical fall criterion.')
    axes[0].set_ylabel('angle [rad]' if model.nplant==3 else 'output deviation [model units]')
    axes[1].step(k, x[:,-model.ninput:], where='post')
    axes[1].set_ylabel('applied input [model units]')
    axes[1].set_xlabel('sample k')
    axes[0].legend()
    for ax in axes: ax.grid(alpha=.25)
    return fig, verdict
