#!/usr/bin/env python3
"""Run a matched, post-decision lane-obstruction experiment in an isolated workspace."""
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
        raise SystemExit(f'Use a new workspace: {destination}')
    (destination / 'simulations/grid').mkdir(parents=True)
    (destination / 'scripts').mkdir()
    (destination / 'src').symlink_to(source / 'src', target_is_directory=True)
    shutil.copy2(source / 'scripts/generate_demand.py', destination / 'scripts')
    for path in (source / 'simulations/grid').iterdir():
        if path.is_file():
            shutil.copy2(path, destination / 'simulations/grid' / path.name)
    special = destination / 'simulations/grid/special.rou.xml'
    tree = ET.parse(special)
    routes = tree.getroot()
    kind = ET.Element('vType', id='incidentQueue', vClass='passenger', color='0.7,0,0.8')
    ET.SubElement(kind, 'param', key='has.fcd.device', value='true')
    routes.insert(0, kind)
    routes.insert(1, ET.Element('route', id='incidentQueueRoute', edges='C1C2 C2D2'))
    # Three physical vehicles provide an observable stopped queue, not a fabricated
    # routing cost. All algorithms receive exactly the same SUMO incident input.
    for index, position in enumerate((70, 55, 40)):
        vehicle = ET.SubElement(routes, 'vehicle', id=f'incidentQueue{index}',
                                type='incidentQueue', route='incidentQueueRoute',
                                depart=str(90 + index), departPos=str(position), departSpeed='0')
        ET.SubElement(vehicle, 'stop', lane='C1C2_0', endPos=str(position + 5), until='250')
    tree.write(special, encoding='utf-8', xml_declaration=True)
    for density in ('low', 'medium', 'high'):
        for seed in range(1, 31):
            name = f'{density}-seed{seed}'
            target = destination / 'simulations/batch' / name
            target.mkdir(parents=True)
            for suffix in ('rou.xml', 'trips.xml'):
                path = source / 'simulations/batch' / name / f'normal-{name}.{suffix}'
                shutil.copy2(path, target / path.name)
    scenario = dict(scenario='post_decision_lane_obstruction', incident_edge='C1C2',
                    incident_vehicle_ids=[f'incidentQueue{i}' for i in range(3)],
                    requested_departures_s=[90, 91, 92], stop_until_s=250, horizon_s=900,
                    source_project=str(source),
                    source_special_sha256=hashlib.sha256((source / 'simulations/grid/special.rou.xml').read_bytes()).hexdigest(),
                    incident_special_sha256=hashlib.sha256(special.read_bytes()).hexdigest(),
                    interpretation='Controlled incident experiment, separate from ordinary traffic; no guarantee of improvement.')
    (destination / 'scenario.json').write_text(json.dumps(scenario, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--densities', nargs='+', choices=('low', 'medium', 'high'), default=['low', 'medium', 'high'])
    parser.add_argument('--seeds', nargs='+', type=int, default=list(range(1, 31)))
    args = parser.parse_args()
    if not args.seeds or len(set(args.seeds)) != len(args.seeds) or any(s < 1 or s > 30 for s in args.seeds):
        parser.error('Use distinct seeds from 1 through 30')
    destination = args.workspace.resolve()
    if not args.resume:
        prepare(batch.ROOT, destination)
    scenario_path = destination / 'scenario.json'
    scenario = json.loads(scenario_path.read_text())
    assert scenario['scenario'] == 'post_decision_lane_obstruction'
    scenario.update(executed_densities=args.densities, executed_seeds=args.seeds,
                    expected_runs=4 * len(args.densities) * len(args.seeds))
    scenario_path.write_text(json.dumps(scenario, indent=2) + '\n')
    original = batch.one_sumo_config

    def with_evidence(directory, route_name, seed, summary_path=None):
        original(directory, route_name, seed, summary_path)
        if summary_path is not None:
            path = directory / 'grid.sumocfg'
            tree = ET.parse(path)
            output = tree.getroot().find('output')
            ET.SubElement(output, 'fcd-output', value=str(summary_path).replace('sumo-summary-', 'incident-fcd-'))
            ET.SubElement(output, 'tripinfo-output', value=str(summary_path).replace('sumo-summary-', 'tripinfo-'))
            ET.SubElement(output, 'device.fcd.probability', value='0')
            tree.write(path, encoding='utf-8', xml_declaration=True)

    batch.one_sumo_config = with_evidence
    batch.ROOT = destination
    batch.GRID = destination / 'simulations/grid'
    sys.argv = [sys.argv[0], '--seeds', *map(str, args.seeds), '--densities', *args.densities,
                '--configs', *batch.CONFIGS[:4], '--jobs', str(args.jobs), '--artifact-root', str(destination),
                '--sim-time-limit', '900', '--resume-incomplete']
    batch.main()


if __name__ == '__main__':
    main()
