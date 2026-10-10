#!/usr/bin/env python3
"""Run the ordinary matched matrix in an isolated workspace, retaining earlier evidence."""
import argparse
import json
import sys
from pathlib import Path

import run_batch as batch
from run_congestion_validation import prepare


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--seeds', nargs='+', type=int, default=list(range(1, 31)))
    parser.add_argument('--configs', nargs='+', choices=batch.CONFIGS, default=batch.CONFIGS)
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds) or any(not 1 <= s <= 30 for s in args.seeds):
        parser.error('Use distinct seeds from 1 through 30')
    destination = args.workspace.resolve()
    if not args.resume:
        prepare(batch.ROOT, destination, with_incident=False)
    scenario = json.loads((destination / 'scenario.json').read_text())
    assert scenario['scenario'] == 'ordinary_traffic_advance_priority'
    scenario.update(executed_seeds=args.seeds, configurations=args.configs,
                    expected_runs=3 * len(args.seeds) * len(args.configs),
                    dynamic_priority_distance_m=250, dynamic_priority_eta_s=20,
                    baseline_priority_distance_m=100, baseline_priority_eta_s=8)
    (destination / 'scenario.json').write_text(json.dumps(scenario, indent=2) + '\n')
    batch.ROOT = destination
    batch.GRID = destination / 'simulations/grid'
    sys.argv = [sys.argv[0], '--seeds', *map(str, args.seeds), '--configs', *args.configs,
                '--jobs', str(args.jobs), '--artifact-root', str(destination),
                '--sim-time-limit', '900', '--resume-incomplete']
    batch.main()


if __name__ == '__main__':
    main()
