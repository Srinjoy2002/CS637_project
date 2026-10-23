"""Run byte-verified REP drivers as child processes; audit their raw output.

No mathematical or solver-setting substitution is made on this route. The
authors' files do not record bounds/gaps, so these results stay separate from
the adapter's completeness-aware defender ranking.
"""
from __future__ import annotations

import csv
import hashlib
import json
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from attack.detector_diagnostics import Config
from attack.schedule_loader import parse_rep_txt
from rep_audit import replay

ROOT = Path(__file__).resolve().parent
SCRIPTS = ('main_short.py', 'main_fig2.py', 'main_fig3.py', 'main_fig4.py', 'main.py')
TARGET_HORIZONS = list(range(1, 26))
NAME = re.compile(r'a(?P<a>\d+)_p(?P<p>[0-9.]+)_alpha(?P<alpha>[0-9.]+)_w(?P<w>\d+)\.csv$')


def expected_configs(script):
    """Audited loop domains of the bundled v1.2 drivers; ell=L-2."""
    if script not in SCRIPTS:
        raise ValueError('Select an included author driver: ' + ', '.join(SCRIPTS))
    if script == 'main_short.py':
        return [('furuta_zero', Config(.25, .01, 20, 3, 'bin_chi2'))]
    if script == 'main_fig2.py':
        return [(s, Config(p, .01, 20, a, 'bin_chi2'))
                for s in ('qt_nmp', 'furuta_zero') for a in range(1, 5) for p in (.09, .17, .25)]
    if script == 'main_fig3.py':
        return [(s, Config(p, .01, 20, 4, d)) for s in ('qt_nmp', 'furuta_zero')
                for d in ('bin', 'chi2', 'bin_chi2') for p in (.09, .17, .25)]
    if script == 'main_fig4.py':
        return [(s, Config(p, .01, w, 4, 'bin')) for s in ('furuta_zero', 'furuta_hold')
                for w in (10, 12, 14, 16, 18) for p in (.09, .17, .25)]
    return [(s, Config(p / 100, .01, w, a, d))
            for s in ('furuta_zero', 'furuta_hold', 'qt_nmp') for a in range(1, 6)
            for p in range(1, 26, 2) for w in range(10, 21, 2)
            for d in ('bin', 'bin_chi2', 'chi2') if d != 'chi2' or w == 20]


def _key(system, cfg):
    return (system, cfg['detector'], round(float(cfg['p']), 10),
            round(float(cfg['alpha']), 10), int(cfg['window']), int(cfg['amax']))


def _write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False), encoding='utf-8')


def verify_snapshot(path):
    manifest = json.loads((ROOT / 'docs/vendor_sha256.json').read_text())
    for relative, digest in manifest.items():
        candidate = Path(path) / relative
        if not candidate.is_file() or hashlib.sha256(candidate.read_bytes()).hexdigest() != digest:
            raise ValueError('Author source checksum mismatch: ' + relative)
    return manifest


def prepare_run(script='main_short.py', output=None):
    """Copy untouched source into a fresh working directory, retaining old runs."""
    expected = expected_configs(script)
    source = ROOT / 'vendor/REP_v1.2'
    hashes = verify_snapshot(source)
    output = Path(output or ROOT / 'outputs/author_runs').resolve()
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run = output / (stamp + '_' + Path(script).stem + '_' + uuid.uuid4().hex[:8])
    shutil.copytree(source, run)
    verify_snapshot(run)
    _write(run / 'run_manifest.json', dict(script=script, status='PREPARED',
        created_utc=datetime.now(timezone.utc).isoformat(), python=sys.executable,
        command=[sys.executable, '-u', script], source_sha256=hashes,
        expected_configurations=len(expected), requested_horizons=TARGET_HORIZONS,
        execution='Unmodified author script in a fresh copied source directory. No injected solver settings.',
        solver_metadata='Author CSV rows are written only for OPTIMAL; bound/gap/tolerances are not saved by that code.'))
    return run


def collect_results(run):
    """Check CSV/TXT pairs independently; never infer a missing schedule or value."""
    run = Path(run).resolve()
    records, issues = [], []
    for path in sorted(run.glob('results_*/*/*.csv')):
        match = NAME.fullmatch(path.name)
        if match is None:
            issues.append(dict(file=str(path.relative_to(run)), error='Unrecognized result filename'))
            continue
        textpath = path.with_suffix('.txt')
        try:
            cfg = Config(float(match['p']), float(match['alpha']), int(match['w']),
                         int(match['a']), path.parent.parent.name.removeprefix('results_'))
            with path.open(newline='', encoding='utf-8') as handle:
                csvrows = [{k.strip(): v.strip() for k, v in row.items()}
                           for row in csv.DictReader(handle, skipinitialspace=True)]
            schedules = parse_rep_txt(textpath)
        except Exception as exc:
            issues.append(dict(file=str(path.relative_to(run)), error=f'{type(exc).__name__}: {exc}'))
            continue
        csv_by_length, txt_by_length = {}, {}
        for row in csvrows:
            try:
                length = int(row['length'])
                csv_by_length.setdefault(length, []).append(row)
            except (KeyError, ValueError) as exc:
                issues.append(dict(file=str(path.relative_to(run)), error=f'Malformed CSV row: {exc}'))
        for row in schedules:
            txt_by_length.setdefault(row['length'], []).append(row)
        for length in sorted(set(csv_by_length) | set(txt_by_length)):
            if length - 2 not in TARGET_HORIZONS:
                continue  # Authors also attempt L=1,2, outside plotted ell=1..25.
            csvitems, txtitems = csv_by_length.get(length, []), txt_by_length.get(length, [])
            if len(csvitems) != 1 or len(txtitems) != 1:
                issues.append(dict(file=str(path.relative_to(run)), length=length,
                    error='Missing or duplicate CSV/TXT row; not accepted or arbitrarily deduplicated.'))
                continue
            raw, txt = csvitems[0], txtitems[0]
            try:
                attack, nominal = float(raw['attack']), float(raw['nominal'])
                if not np.isfinite([attack, nominal, txt['objective']]).all():
                    raise ValueError('Nonfinite objective')
                checked = replay(path.parent.name, txt['schedule'], cfg, txt['objective'])
                agree = bool(np.isclose(attack, txt['objective'], rtol=1e-7, atol=1e-7)
                             and np.isclose(nominal, checked['nominal_rep'], rtol=1e-7, atol=1e-7))
                checked['validation_passed'] = bool(checked['validation_passed'] and agree)
                scale = .25 if path.parent.name == 'qt_nmp' else 1.
                records.append(dict(system=path.parent.name, ell=length-2, config=asdict(cfg),
                    **checked, method='Direct unmodified REP driver CSV/TXT',
                    status='AUTHOR_OPTIMAL_WRITE_POLICY', proven_optimal=False,
                    solver_objective=attack, csv_nominal_rep=nominal, csv_agrees=agree,
                    csv_omega_output=(attack-nominal)*scale, gap=None, bound=None,
                    source_file=str(path.relative_to(run)),
                    source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    note='CSV written only for OPTIMAL by verified author code. Independent replay shown; bound/gap absent from original files. Excluded from strict defender ranking.'))
            except Exception as exc:
                issues.append(dict(file=str(path.relative_to(run)), length=length,
                                   error=f'{type(exc).__name__}: {exc}'))
    return records, issues


def audit_run(run, return_code=None, interrupted=False):
    """Report coverage even when the original driver caught exceptions and exited 0."""
    run = Path(run).resolve()
    manifest = json.loads((run / 'run_manifest.json').read_text())
    verify_snapshot(run)
    records, issues = collect_results(run)
    coverage = []
    expected_keys = set()
    for system, cfg in expected_configs(manifest['script']):
        key = _key(system, asdict(cfg)); expected_keys.add(key)
        selected = [r for r in records if _key(r['system'], r['config']) == key]
        written = sorted({r['ell'] for r in selected})
        valid = sorted({r['ell'] for r in selected if r['validation_passed']})
        coverage.append(dict(system=system, **asdict(cfg), requested=25, written=len(written),
            validated=len(valid), missing=[h for h in TARGET_HORIZONS if h not in written],
            invalid=[h for h in written if h not in valid]))
    unexpected = [r for r in records if _key(r['system'], r['config']) not in expected_keys]
    if unexpected:
        issues.append(dict(error=f'{len(unexpected)} rows outside expected driver configuration.'))
    log = (run / 'driver.log').read_text(encoding='utf-8', errors='replace') if (run / 'driver.log').exists() else ''
    caught = log.count('There was a problem for length=')
    complete = all(c['written'] == 25 for c in coverage)
    validated = complete and all(c['validated'] == 25 for c in coverage) and not issues
    status = ('INTERRUPTED_PARTIAL' if interrupted else 'PROCESS_FAILED' if return_code not in (None, 0)
              else 'COMPLETE_REPLAY_VALIDATED' if validated
              else 'COMPLETE_WITH_VALIDATION_FLAGS' if complete else 'INCOMPLETE')
    report = dict(status=status, return_code=return_code, interrupted=interrupted,
        script=manifest['script'], source_verified=True, expected_points=25*len(coverage),
        written_points=len(records), validated_points=sum(r['validation_passed'] for r in records),
        complete=complete, independent_validation_passed=validated,
        author_caught_problem_messages=caught, coverage=coverage, issues=issues,
        warning='Exit 0 alone does not establish successful optimization. Driver exceptions may be caught. Missing horizons are gaps; no stored data substitution.',
        solver_metadata='Original output lacks explicit bound/gap. See status/write policy in each record.')
    _write(run / 'parsed_results.json', records)
    _write(run / 'coverage.json', report)
    fields = ['system','p','alpha','window','amax','detector','windows','requested','written','validated','missing','invalid']
    with (run / 'coverage.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(coverage)
    manifest.update(status=status, finished_utc=datetime.now(timezone.utc).isoformat(),
                    return_code=return_code, interrupted=interrupted)
    _write(run / 'run_manifest.json', manifest)
    _write(run.parent / ('latest_' + Path(manifest['script']).stem + '.json'),
           dict(run_directory=str(run), status=status))
    return report, records


def plot_results(run, records=None):
    """Python version of author plot expressions, keeping missing points as NaNs."""
    import matplotlib.pyplot as plt
    run = Path(run)
    script = json.loads((run / 'run_manifest.json').read_text())['script']
    if records is None:
        records = json.loads((run / 'parsed_results.json').read_text())
    if script in ('main_fig2.py','main_fig3.py','main_fig4.py'):
        # Plot only independently valid raw rows; expose the legacy-metadata label.
        # This temporary plotting flag is never saved or used for defender ranking.
        from rep_plots import plot_figure
        plotrows = [dict(r, omega=r['csv_omega_output'], proven_optimal=r['validation_passed']) for r in records]
        number = int(script[-4])
        figure, _ = plot_figure(number, plotrows, TARGET_HORIZONS,
            'DIRECT author CSV; replay-validated; solver gaps unavailable')
    else:
        figure, axis = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
        for system, cfg in expected_configs(script):
            key = _key(system, asdict(cfg))
            selected = {r['ell']: r for r in records if _key(r['system'], r['config']) == key}
            if script == 'main.py' and not selected:
                continue
            axis.plot(TARGET_HORIZONS,
                [selected[h]['csv_omega_output'] if h in selected and selected[h]['validation_passed']
                 else np.nan for h in TARGET_HORIZONS], color='#a26422' if script=='main_short.py' else None,
                marker='x', markersize=5, label=f'{system}; {cfg.detector}; p={cfg.p}; w={cfg.window}; amax={cfg.amax}')
        axis.set(xlabel='attack horizon ell = CSV length - 2 [periods]',
                 ylabel='physical-output attack effectiveness omega', xlim=(1, 25),
                 title='Direct unmodified ' + script + '\nCSV values; independent replay; bounds/gaps unavailable')
        axis.grid(alpha=.3)
        if script != 'main.py' or len(records) < 150:
            axis.legend(fontsize=8)
        figure.text(.5, -.015, 'Separate optimization at each marker. Missing or replay-invalid points are gaps. Tank raw REP omega is divided by 4.',
                    ha='center', fontsize=8)
    figure.savefig(run / (Path(script).stem + '_python_plot.png'), dpi=160, bbox_inches='tight')
    return figure


def run_author(script='main_short.py', output=None, echo=True, wall_seconds=None):
    """Execute the actual driver. Stop/interrupt preserves partial files and audit.

    wall_seconds is an optional process deadline, not an injected Gurobi limit.
    The default is unlimited, preserving the authors' execution behavior.
    """
    if wall_seconds is not None and wall_seconds <= 0:
        raise ValueError('wall_seconds must be positive or None.')
    run = prepare_run(script, output)
    manifest = json.loads((run / 'run_manifest.json').read_text())
    manifest['status'] = 'RUNNING'; _write(run / 'run_manifest.json', manifest)
    if echo:
        print('Running unchanged author driver:', script, '\nWorking directory:', run, flush=True)
    process = None
    interrupted = False
    try:
        process = subprocess.Popen([sys.executable, '-u', script], cwd=run,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding='utf-8', errors='replace', bufsize=1)
        lines = queue.Queue()
        def reader():
            try:
                for line in process.stdout:
                    lines.put(line)
            finally:
                process.stdout.close()
                lines.put(None)
        thread = threading.Thread(target=reader, daemon=True); thread.start()
        start = time.monotonic()
        with (run / 'driver.log').open('w', encoding='utf-8') as log:
            while True:
                if wall_seconds is not None and time.monotonic()-start > wall_seconds:
                    interrupted = True
                    break
                try:
                    line = lines.get(timeout=.2)
                except queue.Empty:
                    continue
                if line is None:
                    break
                log.write(line); log.flush()
                if echo:
                    print(line, end='', flush=True)
        if not interrupted:
            process.wait()
    except KeyboardInterrupt:
        interrupted = True
    except Exception as exc:
        with (run / 'driver.log').open('a', encoding='utf-8') as log:
            log.write(f'Runner exception: {type(exc).__name__}: {exc}\n')
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait()
        return_code = process.returncode if process is not None else -1
        report, records = audit_run(run, return_code, interrupted)
        figure = plot_results(run, records)
        import matplotlib.pyplot as plt
        plt.close(figure)
    if echo:
        print('\nAuthor driver:', report['status'],
              f"({report['validated_points']}/{report['expected_points']} independently valid points)", flush=True)
        print('Results, log, coverage and plot:', run, flush=True)
    return run, report, records


def latest_run(script='main_short.py', output=None):
    expected_configs(script)
    pointer = Path(output or ROOT / 'outputs/author_runs') / ('latest_' + Path(script).stem + '.json')
    if not pointer.exists():
        return None
    stored = Path(json.loads(pointer.read_text())['run_directory'])
    if not stored.is_dir():
        raise FileNotFoundError('Last-run directory was moved. Supply its new path to audit_run().')
    return stored
