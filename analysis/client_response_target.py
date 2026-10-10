#!/usr/bin/env python3
"""Audit the client's response target without changing simulation outcomes."""
import argparse
import csv
import hashlib
import heapq
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def optimistic_route_distance(network, start, destination):
    """Shortest legal external-edge distance; omit all internal junction lanes."""
    tree = ET.parse(network)
    lengths = {e.attrib['id']: min(float(l.attrib['length']) for l in e.findall('lane'))
               for e in tree.findall('edge') if e.get('function') != 'internal'}
    successors = {edge: set() for edge in lengths}
    for connection in tree.findall('connection'):
        source, target = connection.get('from'), connection.get('to')
        if source in lengths and target in lengths:
            successors[source].add(target)
    queue, best = [(lengths[start], start)], {start: lengths[start]}
    while queue:
        distance, edge = heapq.heappop(queue)
        if distance != best[edge]:
            continue
        if edge == destination:
            return distance
        for target in successors[edge]:
            candidate = distance + lengths[target]
            if candidate < best.get(target, float('inf')):
                best[target] = candidate
                heapq.heappush(queue, (candidate, target))
    raise ValueError('No legal route')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target-percent', type=float, default=20)
    args = parser.parse_args()
    if not 0 < args.target_percent < 100:
        parser.error('Target must be between 0 and 100 percent')
    comparison_path = ROOT / 'results/client_review/baseline_comparisons.csv'
    comparisons = list(csv.DictReader(comparison_path.open(encoding='utf-8')))
    selected = [r for r in comparisons if r['config_A'] == 'MistDynamicFogFallback'
                and r['metric'] == 'ev_response_s']
    assert len(selected) == 6
    network = ROOT / 'simulations/grid/grid.net.xml'
    distance = optimistic_route_distance(network, 'A0A1', 'D2D3')
    # Current EV release speed is a hard cap, including lane speed factors.
    ned_text = (ROOT / 'src/emergencynavigation/apps/EmergencyVehicleApp.ned').read_text()
    cap = float(re.search(r'releaseSpeed.*?default\(([\d.]+)mps\)', ned_text).group(1))
    ini = (ROOT / 'simulations/grid/omnetpp.ini').read_text()
    assert not re.search(r'^\s*[^#\n]*\.releaseSpeed\s*=', ini, re.M), 'Audit effective speed override first'
    positions = []
    for path in sorted((ROOT / 'artifacts/logs/batch').glob('routing-MistDynamicFogFallback-*.csv')):
        route_rows = list(csv.DictReader(path.open()))
        initial = next((r for r in route_rows if r['action'] == 'computed' and r['reason'] == 'initial'), None)
        if initial is None:
            continue
        mobility_path = path.with_name(path.name.replace('routing-', 'mobility-', 1))
        last = None
        with mobility_path.open() as handle:
            for row in csv.DictReader(handle):
                if float(row['time']) > float(initial['time']):
                    break
                if row['event'] == 'position':
                    last = row
        assert last and last['edge'] == 'A0A1', path
        positions.append(float(last['lanePosition']))
    expected_delivered = sum(int(r['n_pairs']) for r in selected if r['context'] == 'Ordinary traffic')
    assert len(positions) == expected_delivered and max(positions) < 1e-6, positions
    bound = (distance - max(positions)) / cap
    records = []
    lines = [f'# Audit of the {args.target_percent:g} percent EV response target', '',
             f'The acceptance target is at least {args.target_percent:g} percent lower mean EV response time in each density. '
             'Ordinary traffic and controlled obstruction remain separate experiments.', '',
             '| Experiment | Density | Baseline s | Proposed s | Reduction percent | Target s | Target met |',
             '| --- | --- | ---: | ---: | ---: | ---: | --- |']
    for row in selected:
        baseline, proposed = float(row['mean_B']), float(row['mean_A'])
        target = baseline * (1 - args.target_percent / 100)
        passed = proposed <= target
        record = dict(experiment=row['context'], density=row['density'], baseline_s=baseline,
                      proposed_s=proposed, target_s=target, target_met=passed,
                      reduction_percent=float(row['reduction_percent']))
        records.append(record)
        lines.append(f"| {row['context']} | {row['density']} | {baseline:.3f} | {proposed:.3f} | "
                     f"{record['reduction_percent']:.2f} | {target:.3f} | {'Yes' if passed else 'No'} |")
    impossible = [r['density'] for r in records if r['experiment'] == 'Ordinary traffic' and r['target_s'] < bound]
    lines += ['', '## Physical feasibility in the current ordinary grid', '',
              f'The shortest legal path contains at least {distance:.3f} m of external road lanes. '
              f'All {len(positions)} delivered proposed runs start route computation at lane position zero. '
              f'At the current {cap:.3f} m/s EV speed cap, external road travel alone takes at least {bound:.3f} s.', '',
              'This is an optimistic lower bound. It omits junction connector travel, acceleration, '
              'message delivery, route computation and every traffic delay. Those factors can only increase response time.', '',
              f'Ordinary densities whose targets fall below this optimistic bound: {", ".join(impossible) or "none"}. '
              'A target below this bound cannot be met by routing and signal timing changes '
              'while preserving the current trip, speed cap and measured baseline. A target above this bound '
              'is not guaranteed achievable because the bound omits unavoidable delays.', '',
              'A different demand scenario or vehicle policy would be a new experiment. Apply common input changes '
              'to every compared configuration, justify them before running, retain every scheduled seed, '
              'and keep the current ordinary results. Do not slow the baseline or select seeds to manufacture the target.', '',
              f'Final verdict: {sum(r["target_met"] for r in records)} of {len(records)} experiment and density combinations meet the target.', '']
    report = ROOT / 'docs/CLIENT_20_PERCENT_FEASIBILITY.md'
    report.write_text('\n'.join(lines), encoding='utf-8')
    evidence = dict(target_percent=args.target_percent, external_distance_lower_bound_m=distance,
                    speed_cap_mps=cap, optimistic_response_lower_bound_s=bound,
                    verified_start_positions=len(positions), comparisons=records,
                    comparison_sha256=hashlib.sha256(comparison_path.read_bytes()).hexdigest(),
                    network_sha256=hashlib.sha256(network.read_bytes()).hexdigest())
    (ROOT / 'artifacts/client_response_target_audit.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
