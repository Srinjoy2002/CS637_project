"""Native command-line entry point for unchanged REP author drivers."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from author_drivers import SCRIPTS, audit_run, plot_results, prepare_run, run_author


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script', choices=SCRIPTS, default='main_short.py')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/author_runs')
    parser.add_argument('--prepare-only', action='store_true', help='Copy and verify sources without optimization.')
    parser.add_argument('--audit', type=Path, help='Recheck and plot an existing run without solving.')
    parser.add_argument('--wall-seconds', type=float, default=None,
                        help='Optional process stop deadline; preserves partial results. No injected solver settings.')
    args = parser.parse_args()
    if args.prepare_only and args.audit:
        parser.error('Choose either --prepare-only or --audit.')
    if args.audit:
        manifest = json.loads((args.audit/'run_manifest.json').read_text())
        report, records = audit_run(args.audit, manifest.get('return_code'), manifest.get('interrupted', False))
        plot_results(args.audit, records)
        print(json.dumps(report, indent=2))
        return 0 if report['independent_validation_passed'] else 2
    if args.prepare_only:
        print('Prepared and checksum-verified:', prepare_run(args.script, args.output))
        return 0
    _, report, _ = run_author(args.script, args.output, wall_seconds=args.wall_seconds)
    return 0 if report['independent_validation_passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
