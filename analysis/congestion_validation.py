#!/usr/bin/env python3
"""Report controlled incident outcomes and matched fault recovery from raw evidence."""
import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import process_results as process
from raw_data import events, incident_observation
from supplemental_validation import continuous, draw, LABELS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/congestion_validation'
DENSITIES = ('low', 'medium', 'high')


def collect(root, require_all=True, ordinary_root=None):
    ordinary_root = ordinary_root or ROOT
    scenario = json.loads((root / 'scenario.json').read_text())
    assert scenario['scenario'] == 'post_decision_lane_obstruction'
    paths = sorted((root / 'results/raw').glob('*.sca'))
    if require_all:
        assert len(paths) == 360, len(paths)
    records, proof = [], []
    old_root = process.ROOT
    process.ROOT = root
    try:
        for path in paths:
            config, density, suffix = path.stem.split('-')
            seed = int(suffix.removeprefix('seed'))
            assert config in process.CONFIGS and density in DENSITIES and 1 <= seed <= 30
            logs = root / 'artifacts/logs/batch'
            record = process.one_run(config, path, density, seed, logs / f'emergency-{path.stem}.csv')
            try:
                record['source_scalar'] = path.relative_to(ROOT).as_posix()
            except ValueError:
                record['source_scalar'] = path.as_posix()
            route = events(logs / f'routing-{path.stem}.csv')
            applications = [r for r in route if r['action'] == 'applied']
            changes = [r for r in applications if r['reason'] in ('cost_improvement', 'low_speed')]
            record['initial_route_edges'] = applications[0]['selectedEdges'] if applications else ''
            avoided = False
            for previous, current in zip(applications, applications[1:]):
                old = previous['selectedEdges'].split('|')
                edge = current['currentEdge']
                remaining = old[old.index(edge):] if edge in old else []
                avoided |= (90 <= float(current['time']) < 250 and 'C1C2' in remaining
                            and 'C1C2' not in current['selectedEdges'].split('|'))
            record['incident_avoided_by_reroute'] = int(avoided)
            observed, maximum = incident_observation(logs / f'incident-fcd-{path.stem}.xml')
            assert maximum >= 1, (path.stem, 'no realised incident', observed)
            assert all(v['first_seen_s'] is not None and v['first_seen_s'] >= v['requested_departure_s'] for v in observed.values()), (path.stem, observed)
            assert any(v['incident_last_s'] is not None and v['incident_last_s'] >= 249 for v in observed.values()), (path.stem, 'no blocker at end of incident', observed)
            record['maximum_stopped_incident_vehicles'] = maximum
            record['incident_vehicles_inserted_after_stop_period'] = sum(v['first_seen_s'] >= 250 for v in observed.values())
            if record['delivered_messages']:
                assert record['arrival_confirmed'] == 1, (path.stem, 'arrival not confirmed')
                assert applications and float(applications[0]['time']) < 90, (path.stem, 'incident must follow initial route')
            for change in changes:
                assert float(change['estimatedCost']) < float(change['currentRemainingCost']), path.stem
            manifest = json.loads((logs / f'manifest-{path.stem}.json').read_text())
            directory = root / 'simulations/batch' / f'{density}-seed{seed}' / config
            special = directory / 'special.rou.xml'
            assert hashlib.sha256(special.read_bytes()).hexdigest() == scenario['incident_special_sha256']
            demand_name = f'normal-{density}-seed{seed}.rou.xml'
            original_demand = ROOT / 'simulations/batch' / f'{density}-seed{seed}' / demand_name
            demand_hash = hashlib.sha256(original_demand.read_bytes()).hexdigest()
            assert hashlib.sha256((directory / demand_name).read_bytes()).hexdigest() == demand_hash
            assert (directory / 'grid.net.xml').read_bytes() == (ROOT / 'simulations/grid/grid.net.xml').read_bytes()
            original_case = json.loads((ordinary_root / 'artifacts/logs/batch' / f'manifest-{path.stem}.json').read_text())
            assert manifest['controlled_mist_stall_ms'] == original_case['controlled_mist_stall_ms']
            proof.append(dict(run=path.stem, source_scalar=record['source_scalar'], incident_observations=observed, maximum_stopped_incident_vehicles=maximum,
                              binary_sha256=manifest['binary_sha256'], demand_sha256=demand_hash,
                              scalar_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            records.append(record)
    finally:
        process.ROOT = old_root
    assert len({(r['configuration'], r['density'], r['seed']) for r in records}) == len(records)
    assert len({r['binary_sha256'] for r in proof}) == 1
    original_manifest = json.loads((ordinary_root / 'artifacts/logs/batch/manifest-FogCloudAStar-low-seed1.json').read_text())
    assert proof[0]['binary_sha256'] == original_manifest['binary_sha256'], 'Incident suite must reuse the original binary'
    if require_all:
        assert {(r['configuration'], r['density'], r['seed']) for r in records} == {
            (c, d, s) for c in process.CONFIGS for d in DENSITIES for s in range(1, 31)}
        # Match requested demand and obstruction inputs. Different signal
        # policies can change subsequent insertion/queue states; retain those
        # outcomes and disclose them instead of selecting matching trajectories.
    return records, proof


def recovery():
    rows = events(ROOT / 'results/processed/individual_runs-batch.csv')
    lookup = {(r['configuration'], r['density'], r['seed']): r for r in rows}
    records = []
    for row in rows:
        if row['configuration'] != 'MistDynamicFogFallback' or row['fallback_triggered'] != '1':
            continue
        counterpart = lookup['MistDynamicAStar', row['density'], row['seed']]
        a, b = float(counterpart['route_decision_ms']), float(row['route_decision_ms'])
        records.append(dict(density=row['density'], seed=row['seed'], mist_decision_ms=a,
                            fallback_decision_ms=b, recovery_saved_ms=a-b, recovery_saved_percent=100*(a-b)/a))
    assert records, 'No matched controlled-stall fallback evidence'
    return records


def paired_plot(rows, density, graphs):
    group = [r for r in rows if r['density'] == density and r['metric'] == 'ev_response_s']
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.errorbar(range(len(group)), [r['mean_paired_diff'] for r in group],
                yerr=[[r['mean_paired_diff']-r['ci95_lower'] for r in group],
                      [r['ci95_upper']-r['mean_paired_diff'] for r in group]], fmt='o', capsize=5)
    ax.axhline(0, color='gray', linewidth=1)
    ax.set_xticks(range(len(group)), [f"{LABELS[r['config_A']]}\nminus {LABELS[r['config_B']]}" for r in group])
    ax.set_ylabel('Response difference (s); negative means faster')
    ax.set_title(f'Controlled incident matched response differences — {density.capitalize()} traffic [95% CI]')
    ax.grid(axis='y', alpha=.25)
    fig.tight_layout()
    fig.savefig(graphs / f'incident_paired_response_s-{density}.png', dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--incident-root', type=Path, default=ROOT / 'artifacts/congestion_validation')
    parser.add_argument('--pilot', action='store_true', help='Print incomplete pilot measurements without producing final deliverables')
    parser.add_argument('--ordinary-root', type=Path, default=ROOT, help='Reference ordinary experiment for binary and stall provenance')
    args = parser.parse_args()
    root = args.incident_root.resolve()
    rows, proof = collect(root, not args.pilot, args.ordinary_root.resolve())
    if args.pilot:
        print(json.dumps([{k: r[k] for k in ('configuration', 'density', 'seed', 'ev_response_s', 'route_changes', 'incident_avoided_by_reroute')} for r in rows], indent=2))
        return
    sys.path.insert(0, str(ROOT / 'scripts'))
    from validate_timing_evidence import audit
    timing = audit(root)
    assert timing['passed'] and timing['runs'] == 360, timing
    graphs = OUT / 'graphs'
    graphs.mkdir(parents=True, exist_ok=True)
    summary, paired = process.summarize(rows), process.paired_comparisons(rows)
    process.write_csv(OUT / 'individual_runs.csv', rows)
    process.write_csv(OUT / 'summary.csv', summary)
    process.write_csv(OUT / 'paired_comparisons.csv', paired)
    faults = recovery()
    process.write_csv(OUT / 'fault_recovery_runs.csv', faults)
    recovered = []
    for density in DENSITIES:
        values = [r['recovery_saved_ms'] for r in faults if r['density'] == density]
        mean, lo, hi = continuous(values)
        recovered.append(dict(configuration='MistDynamicFogFallback', density=density, metric='recovery_saved_ms',
                              n=len(values), mean=mean, ci95_lower=lo, ci95_upper=hi))
        for metric, title, unit in [('ev_response_s', 'Controlled incident EV response', 'seconds'),
                                    ('route_changes', 'Controlled incident route changes', 'changes/run')]:
            draw(summary, metric, title, unit, density, graphs)
        paired_plot(paired, density, graphs)
    process.write_csv(OUT / 'fault_recovery_summary.csv', recovered)
    for density in DENSITIES:
        draw(recovered, 'recovery_saved_ms', 'Controlled fault route decision time saved', 'milliseconds', density, graphs)
    exposure_matches = sum(len({(r['maximum_stopped_incident_vehicles'], r['incident_vehicles_inserted_after_stop_period'])
                                for r in rows if r['density'] == d and r['seed'] == s}) == 1
                           for d in DENSITIES for s in range(1, 31))
    report = dict(passed=True, runs=len(rows), timing=timing, incident_evidence=proof,
                  matched_realised_exposure_groups=exposure_matches, input_matched_groups=90,
                  fault_recovery_pairs=len(faults), headline_definitions_changed=False)
    (OUT / 'validation_report.json').write_text(json.dumps(report, indent=2)+'\n')
    lines = ['# Requirements evidence and controlled incident comparison', '',
             'The ordinary 450-run batch, the 18 signal validation runs, and this separate 360-run incident comparison answer different questions. The incident experiment tests route adaptation after the initial decision. It does not replace ordinary traffic results or establish how often incidents occur in practice.', '',
             '## Fixed incident design', '',
             'All four algorithms use the same 30 seeds at each density, original background trips, frozen binary, safety controller and stall assignment. Dynamic Mist uses advance signal requests (250 m or 20 s); Fog/Cloud and static Mist use reactive requests (100 m or 8 s). All may retry every five seconds without extending an active hold. The comparison therefore measures routing and signal policy together. The input requests three passenger vehicles on C1C2 at 90, 91 and 92 seconds, with stops until 250 seconds. SUMO safety checks may delay insertion; requested times are not assumed to be actual entry times. There is no injected routing cost or privileged incident notification: ordinary beacons and RSU reports provide observations. FCD verifies the realised obstruction in every run, with at least one incident vehicle still stopped at the end of the planned interval. Initial routes must be applied before the incident. All runs have a 900 second horizon.', '',
             'Routing retains its existing minimum of three observed vehicles for a congestion adjustment. Incident vehicles and ordinary queued vehicles can provide those observations. The incident vehicles are additional to the 72/144/200 generated background trips. Demand counts are not simultaneous occupancy. Every delivered-alert run must reach the destination. Undelivered alerts remain in the matrix; delivery-dependent means exclude them and report their sample sizes.', '',
             'The seed labels vary demand generation and OMNeT++ streams. Veins launchd retains the original manager default, using SUMO driving seed 0 for run number zero. Driving randomness is common across cases; route-generation seeds still vary routes and entry edges. This preserves the original experiment and does not claim independently varied SUMO driver seeds. The [retained launchd history](../artifacts/congestion_validation/launchd_history.log) records the effective seed; it includes previous suites and startup attempts as well as this matrix.', '',
             'The advance-priority framework was screened on seeds 1, 4, 22 and 27 at all densities before the fixed full matrix. Screening checks mechanism operation, not an acceptance threshold for favourable results. Previous evidence and pilot workspaces are retained. Neither effect size nor significance is a pass criterion.', '',
             '## Measured incident response', '',
             '| Density | Algorithm | Arrived samples | Mean response s | Mean route changes per scheduled run |',
             '| --- | --- | ---: | ---: | ---: |']
    lookup = {(r['configuration'], r['density'], r['metric']): r for r in summary}
    for d in DENSITIES:
        for c in process.CONFIGS:
            r = lookup[c, d, 'ev_response_s']
            changes = lookup.get((c, d, 'route_changes'))
            lines.append(f"| {d} | {LABELS[c]} | {r['n']} | {r['mean']:.3f} | {changes['mean']:.3f} |" if changes else
                         f"| {d} | {LABELS[c]} | {r['n']} | {r['mean']:.3f} | N/A |")
    lines += ['', '## Realised obstruction and insertion delays', '',
              f'FCD measures simultaneous stopped incident vehicles during 90 to 250 seconds. All cases remain in the input-matched comparison; no input was retuned after this observation. Realised obstruction and late insertion counts match across algorithms in {exposure_matches} of 90 density/seed groups. Different routing and signal policies can alter subsequent traffic and insertion states. The effect estimate includes those consequences; it does not condition on identical downstream trajectories. Every case must still realise at least one blocker through the end of the incident. Complete per-vehicle first-seen times and stopped samples are in validation_report.json.', '',
              '| Density | Algorithm | Runs with 3 stopped vehicles | Runs with 2 | Runs with 1 | Vehicles inserted after 250 s |',
              '| --- | --- | ---: | ---: | ---: | ---: |']
    for d in DENSITIES:
        for c in process.CONFIGS:
            group = [r for r in rows if r['density'] == d and r['configuration'] == c]
            counts = [sum(r['maximum_stopped_incident_vehicles'] == n for r in group) for n in (3, 2, 1)]
            lines.append(f"| {d} | {LABELS[c]} | {counts[0]} | {counts[1]} | {counts[2]} | {sum(r['incident_vehicles_inserted_after_stop_period'] for r in group)} |")
    lines += ['', '## Observed incident avoidance', '',
              'A run counts here only when its routing log applies a replacement during the incident that removes C1C2 from its remaining route. Reviews alone do not count.', '',
              '| Density | Dynamic approach | Delivered alerts | Runs avoiding incident by reroute | Scheduled runs |',
              '| --- | --- | ---: | ---: | ---: |']
    for d in DENSITIES:
        for c in process.CONFIGS[2:]:
            group = [r for r in rows if r['density'] == d and r['configuration'] == c]
            lines.append(f"| {d} | {LABELS[c]} | {sum(r['delivered_messages'] for r in group)} | {sum(r['incident_avoided_by_reroute'] for r in group)} | {len(group)} |")
    lines += ['', '## Matched response differences', '',
              'Differences are algorithm A minus B; negative means A is faster. Intervals are Student-t 95% paired intervals. The exploratory comparisons are not corrected for multiple testing.', '',
              '| Density | A | B | Paired samples | Difference s | 95% interval s |',
              '| --- | --- | --- | ---: | ---: | --- |']
    for r in paired:
        if r['metric'] == 'ev_response_s':
            lines.append(f"| {r['density']} | {LABELS[r['config_A']]} | {LABELS[r['config_B']]} | {r['n_pairs']} | {r['mean_paired_diff']:.3f} | {r['ci95_lower']:.3f} to {r['ci95_upper']:.3f} |")
    lines += ['', '## Controlled fallback benefit', '',
              f'These values use the ordinary batch, not the incident matrix. On the {len(faults)} delivered matched controlled-stall cases, compare Mist + Fog against Dynamic Mist with the same 900 ms stall. Time saved is the difference between their actual initial route application delays. This measures recovery latency; it is not a claim of a comparable journey-time reduction or organic failure.', '',
              '| Density | Matched stalled cases | Mean route decision time saved ms | 95% interval ms |',
              '| --- | ---: | ---: | --- |']
    for r in recovered:
        lines.append(f"| {r['density']} | {r['n']} | {r['mean']:.3f} | {r['ci95_lower']:.3f} to {r['ci95_upper']:.3f} |")
    lines += ['', '## Metric scope and remaining limits', '',
              'EM PDR, throughput and end-to-end delay concern the shared alert-delivery mechanism before route computation. Identical results across routing algorithms are expected for those definitions and cannot establish routing superiority. EM throughput uses a fixed payload and window. The separate request/reply metrics describe routing communication; local Mist has no wireless Fog transaction. No absent packet measurements are inferred.', '',
              'Normal Mist decision latency is 326 ms in this grid; Fog/Cloud is about 626.54 ms. The equality between normal Mist variants reflects the same initial computation model. Fallback adds recovery only when a controlled stall occurs. A controlled obstacle can expose adaptation benefits but does not guarantee them on uncongested roads.', '',
              'Main response labels now retain three decimal places to expose small numerical differences. Underlying SUMO movement resolution remains 500 ms; the decimal display is not a claim of millisecond movement accuracy. Paired graphs show differences with confidence intervals without exaggerating bar heights.', '',
              'Continuous incident response and route-change intervals are Student-t; fault recovery uses paired differences with Student-t intervals. The full incident summary also retains the established Wilson intervals for PDR/fallback and bootstrap intervals for waiting. Every graph retains a generic 95% CI label.', '',
              'SUMO model references: [vehicle stops](https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#stops) and [vehicle insertion safety](https://sumo.dlr.de/docs/Simulation/VehicleInsertion.html).']
    (ROOT / 'docs/REQUIREMENTS_EVIDENCE.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(f'Validated {len(rows)} incident runs and {len(faults)} matched fault recoveries; {OUT}')


if __name__ == '__main__':
    main()
