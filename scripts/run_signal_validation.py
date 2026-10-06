#!/usr/bin/env python3
"""Run isolated short-notice red-signal cases with the existing simulation binary."""
import argparse
import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import run_batch as batch


def prepare(source, destination):
    if destination.exists():
        raise SystemExit(f'Use a new validation workspace: {destination}')
    (destination / 'simulations/grid').mkdir(parents=True)
    (destination / 'scripts').mkdir()
    (destination / 'src').symlink_to(source / 'src', target_is_directory=True)
    shutil.copy2(source / 'scripts/generate_demand.py', destination / 'scripts')
    for path in (source / 'simulations/grid').iterdir():
        if path.is_file():
            shutil.copy2(path, destination / 'simulations/grid' / path.name)
    grid = destination / 'simulations/grid'
    tree = ET.parse(grid / 'grid.net.xml')
    light = tree.getroot().find("tlLogic[@id='A1']")
    phases = list(light)
    assert [p.get('state') for p in phases] == ['GgrrGG', 'yyrryy', 'rrGGGr', 'rryyyr']
    # Start with protected conflicting green for 150 s. Remove the permissive
    # A0A1 green so both possible EV movements on that incoming edge are red.
    for phase in phases:
        light.remove(phase)
    phases[2].set('duration', '150')
    phases[2].set('state', 'rrGGrr')
    for i in (2, 3, 0, 1):
        light.append(phases[i])
    tree.write(grid / 'grid.net.xml', encoding='utf-8', xml_declaration=True)
    ini = (grid / 'omnetpp.ini').read_text()
    ini = ini.replace('*.node[*].appl.preemptionDistance = 100m', '*.node[*].appl.preemptionDistance = 10m')
    ini = ini.replace('*.node[*].appl.preemptionEta = 8s', '*.node[*].appl.preemptionEta = 0.5s')
    (grid / 'omnetpp.ini').write_text(ini)
    # Retain the original matched trips; the validation changes signal timing only.
    for density in ('low', 'medium', 'high'):
        for seed in (1, 4):
            name = f'{density}-seed{seed}'
            target = destination / 'simulations/batch' / name
            target.mkdir(parents=True)
            for suffix in ('rou.xml', 'trips.xml'):
                route = source / 'simulations/batch' / name / f'normal-{name}.{suffix}'
                shutil.copy2(route, target / route.name)
    (destination / 'scenario.json').write_text(json.dumps({
        'scenario': 'short_notice_red_signal', 'source_project': str(source),
        'first_signal': 'A1', 'first_phase_state': 'rrGGrr', 'first_phase_duration_s': 150,
        'ev_turn': 'A0A1 -> A1B1', 'preemption_distance_m': 10, 'preemption_eta_s': .5,
        'horizon_s': 400, 'seeds': [1, 4], 'densities': ['low', 'medium', 'high'],
        'source_network_sha256': hashlib.sha256((source / 'simulations/grid/grid.net.xml').read_bytes()).hexdigest(),
        'validation_network_sha256': hashlib.sha256((grid / 'grid.net.xml').read_bytes()).hexdigest(),
        'interpretation': 'Controlled signal validation only; not part of the headline matched batch.'
    }, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--densities', nargs='+', choices=('low', 'medium', 'high'), default=['low', 'medium', 'high'])
    parser.add_argument('--seeds', nargs='+', type=int, choices=(1, 4), default=[1, 4])
    args = parser.parse_args()
    source = batch.ROOT
    destination = args.workspace.resolve()
    if args.resume:
        scenario = json.loads((destination / 'scenario.json').read_text())
        assert scenario['scenario'] == 'short_notice_red_signal' and scenario['preemption_distance_m'] == 10 and scenario['first_phase_state'] == 'rrGGrr'
    else:
        prepare(source, destination)
    scenario_path = destination / 'scenario.json'
    scenario = json.loads(scenario_path.read_text())
    scenario.update(executed_densities=args.densities, executed_seeds=args.seeds,
                    expected_runs=3 * len(args.densities) * len(args.seeds))
    scenario_path.write_text(json.dumps(scenario, indent=2) + '\n')
    batch.ROOT = destination
    batch.GRID = destination / 'simulations/grid'
    sys.argv = [sys.argv[0], '--seeds', *map(str, args.seeds), '--densities', *args.densities, '--configs', 'FogCloudAStar',
                'MistDynamicFogFallback', 'NoPreemptionBaseline', '--jobs', str(args.jobs),
                '--artifact-root', str(destination), '--sim-time-limit', '400', '--resume-incomplete']
    batch.main()


if __name__ == '__main__':
    main()
