#!/usr/bin/env python3
"""Derive supplementary route transactions and isolated signal validation from raw evidence."""
import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import t

from raw_data import scalars, events
from process_results import CONFIGS, CONFIG_COLORS, write_csv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/supplemental'
DENSITIES = ('low', 'medium', 'high')
SIGNAL_CONFIGS = ('FogCloudAStar', 'MistDynamicFogFallback', 'NoPreemptionBaseline')
LABELS = {'FogCloudAStar': 'Fog/Cloud', 'MistAStar': 'Mist', 'MistDynamicAStar': 'Dynamic Mist',
          'MistDynamicFogFallback': 'Mist + Fog', 'NoPreemptionBaseline': 'No preemption'}
METRICS = {
    'route_requests_per_run': ('Fog route requests', 'requests/run'),
    'route_transaction_ms': ('Fog route transaction turnaround', 'ms'),
    'route_network_roundtrip_ms': ('Fog route network round trip', 'ms'),
}


def continuous(values):
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0
    margin = t.ppf(.975, len(values)-1) * sd / math.sqrt(len(values)) if sd else 0
    return mean, mean-margin, mean+margin


def route_rows(root):
    rows = []
    for c in CONFIGS:
        for d in DENSITIES:
            for seed in range(1, 31):
                path = root / 'results/raw' / f'{c}-{d}-seed{seed}.sca'
                v = scalars(path)
                requests = len(v.get('routeFogRequestTime', []))
                replies = len(v.get('fogProcessingDelay', []))
                assert requests <= 1 and replies <= requests
                # Request scalar is written when EV sends; reply scalar only after
                # the matching valid reply is accepted and its route is applied.
                turnaround = None
                network = None
                if replies:
                    turnaround = (v['routeDecisionLatency'][0] - v['routeWaitBeforeFog'][0]) * 1000
                    network = v['routeCommunicationDelay'][0] * 1000
                    assert math.isclose(turnaround, network + 1000*(v['fogProcessingDelay'][0] + v['cloudBackhaulDelay'][0]), abs_tol=1e-7)
                rows.append(dict(configuration=c, density=d, seed=seed, requests_sent=requests,
                                 replies_accepted=replies, route_transaction_ms=turnaround,
                                 route_network_roundtrip_ms=network, source_scalar=path.relative_to(root).as_posix()))
    return rows


def route_summary(rows):
    result = []
    for c in CONFIGS:
        for d in DENSITIES:
            group = [r for r in rows if r['configuration'] == c and r['density'] == d]
            sent = sum(r['requests_sent'] for r in group)
            received = sum(r['replies_accepted'] for r in group)
            for metric, field in (('route_requests_per_run', 'requests_sent'), ('route_replies_per_run', 'replies_accepted'),
                                  ('route_transaction_ms', 'route_transaction_ms'), ('route_network_roundtrip_ms', 'route_network_roundtrip_ms')):
                vals = [r[field] for r in group if r[field] is not None]
                mean, lo, hi = continuous(vals) if vals else (None, None, None)
                result.append(dict(configuration=c, density=d, metric=metric, n=len(vals), mean=mean,
                                   ci95_lower=lo, ci95_upper=hi, requests_sent=sent, replies_accepted=received))
            # Transaction completion is not EM PDR. Local Mist has no wireless
            # transaction and therefore no denominator; report N/A, not 0%.
            if sent:
                p, z = received / sent, 1.959963984540054
                center = (p + z*z/(2*sent)) / (1+z*z/sent)
                margin = z*math.sqrt(p*(1-p)/sent + z*z/(4*sent*sent))/(1+z*z/sent)
                lo, hi = center-margin, min(1, center+margin)
            else:
                p = lo = hi = None
            result.append(dict(configuration=c, density=d, metric='route_completion_rate', n=sent, mean=p,
                               ci95_lower=lo, ci95_upper=hi, requests_sent=sent, replies_accepted=received))
    return result


def signal_rows(root):
    from validate_timing_evidence import audit
    timing = audit(root)
    assert timing['passed'] and timing['runs'] == 18, timing
    rows = []
    scenario = json.loads((root / 'scenario.json').read_text())
    assert scenario['first_phase_state'] == 'rrGGrr' and scenario['preemption_distance_m'] == 10
    for c in SIGNAL_CONFIGS:
        for d in DENSITIES:
            for seed in (1, 4):
                stem = f'{c}-{d}-seed{seed}'
                v = scalars(root / 'results/raw' / f'{stem}.sca')
                first = lambda name: v[name][0] if v.get(name) else None
                tls = events(root / 'artifacts/logs/batch' / f'traffic-light-{stem}.csv')
                red = [r for r in tls if r['trafficLightId'] == 'A1' and r['action'] == 'minimum_green_wait']
                mobility = events(root / 'artifacts/logs/batch' / f'mobility-{stem}.csv')
                stopped = [r for r in mobility if r['edge'] == 'A0A1' and r['event'] == 'position'
                           and float(r['speed']) < .1 and float(r['trafficLightWaiting']) > 0]
                assert first('accidentArrivalConfirmed') == 1, stem
                assert first('evTrafficLightWaitingTime') > 0 and stopped, stem
                assert c == 'NoPreemptionBaseline' or (red and red[0]['originalState'] == 'rrGGrr'), stem
                rows.append(dict(scenario='short_notice_red_signal', configuration=c, density=d, seed=seed,
                                 traffic_light_wait_s=first('evTrafficLightWaitingTime'),
                                 first_signal_wait_s=max(float(r['trafficLightWaiting']) for r in stopped),
                                 first_signal_red_request_time_s=float(red[0]['eventTime']) if red else None,
                                 source_scalar=f'artifacts/signal_validation/results/raw/{stem}.sca'))
    lookup = {(r['configuration'], r['density'], r['seed']): r for r in rows}
    for r in rows:
        control = lookup['NoPreemptionBaseline', r['density'], r['seed']]
        r['waiting_reduction_vs_control_s'] = control['traffic_light_wait_s'] - r['traffic_light_wait_s']
        if r['configuration'] != 'NoPreemptionBaseline':
            assert r['waiting_reduction_vs_control_s'] > 0, r
    return rows, timing


def draw(rows, metric, title, unit, density, folder):
    group = [r for r in rows if r['density'] == density and r['metric'] == metric and r['mean'] is not None]
    means = [r['mean'] for r in group]
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.bar([LABELS[r['configuration']] for r in group], means,
           color=[CONFIG_COLORS[r['configuration']] for r in group],
           yerr=[[max(0, r['mean']-r['ci95_lower']) for r in group], [max(0, r['ci95_upper']-r['mean']) for r in group]],
           capsize=5, edgecolor='#333333')
    ax.set_ylabel(unit)
    ax.set_title(f'{title} — {density.capitalize()} traffic\nSupplementary validation [95% CI]')
    top = max(r['ci95_upper'] for r in group)
    ax.set_ylim(min(0, min(r['ci95_lower'] for r in group)*1.05), top*1.22 if top else 1)
    for i, r in enumerate(group):
        ax.text(i, r['ci95_upper'] + top*.025, f"{r['mean']:.3f}\n(n={r['n']})", ha='center', fontsize=10)
    ax.grid(axis='y', alpha=.25)
    fig.tight_layout()
    fig.savefig(folder / f'{metric}-{density}.png', dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--signal-root', type=Path, default=ROOT / 'artifacts/signal_validation')
    parser.add_argument('--route-only', action='store_true')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'scripts'))
    OUT.mkdir(parents=True, exist_ok=True)
    graphs = OUT / 'graphs'
    graphs.mkdir(exist_ok=True)
    route = route_rows(ROOT)
    summary = route_summary(route)
    write_csv(OUT / 'route_transactions.csv', route)
    write_csv(OUT / 'route_transaction_summary.csv', summary)
    for density in DENSITIES:
        for metric, (title, unit) in METRICS.items():
            draw(summary, metric, title, unit, density, graphs)
    if args.route_only:
        print('Derived 360 route-transaction records and nine supplementary graphs')
        return
    signals, timing = signal_rows(args.signal_root)
    signal_summary = []
    for c in SIGNAL_CONFIGS:
        for d in DENSITIES:
            vals = [r['traffic_light_wait_s'] for r in signals if r['configuration'] == c and r['density'] == d]
            mean, lo, hi = continuous(vals)
            signal_summary.append(dict(configuration=c, density=d, metric='red_signal_wait_s', n=len(vals),
                                       mean=mean, ci95_lower=lo, ci95_upper=hi))
    write_csv(OUT / 'red_signal_runs.csv', signals)
    write_csv(OUT / 'red_signal_summary.csv', signal_summary)
    for d in DENSITIES:
        draw(signal_summary, 'red_signal_wait_s', 'Short notice red signal waiting', 'seconds', d, graphs)
    (OUT / 'validation_report.json').write_text(json.dumps({'passed': True, 'route_runs': len(route),
        'red_signal_runs': len(signals), 'red_signal_timing': timing, 'headline_definitions_changed': False,
        'main_raw_sha256': {r['source_scalar']: hashlib.sha256((ROOT/r['source_scalar']).read_bytes()).hexdigest() for r in route}}, indent=2)+'\n')
    lines = ['# Supplementary route communication and red signal validation', '',
        'The seven headline metrics and their matched batch are unchanged. These checks explain route-specific communication and demonstrate finite waiting under controlled red-signal conditions.', '',
        '## Route transactions', '',
        'A request is counted when the EV sends a Fog RouteRequest. An accepted reply is counted when the matching valid RouteReply is accepted and its route is applied. These counts come from original raw scalars; they are not radio reception counts at every relay. Completion is accepted replies divided by requests sent. Local Mist uses no wireless Fog transaction, so its completion and delay are N/A. EM PDR and EM throughput retain their original definitions.', '',
        'Transaction turnaround starts when the EV sends the Fog request and ends when it applies the reply. It includes Fog or Cloud processing and Cloud backhaul. Network round trip subtracts processing and backhaul, and excludes the 500 ms watchdog wait. No exact route-packet byte counts were recorded, so no route throughput or route-packet PDR is invented.', '',
        '| Density | Configuration | Requests | Accepted replies | Turnaround ms | Network ms |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    for d in DENSITIES:
        for c in CONFIGS:
            g = {r['metric']: r for r in summary if r['density'] == d and r['configuration'] == c}
            fmt = lambda k: f"{g[k]['mean']:.3f}" if g[k]['mean'] is not None else 'N/A'
            lines.append(f"| {d} | {LABELS[c]} | {g['route_requests_per_run']['requests_sent']} | {g['route_requests_per_run']['replies_accepted']} | {fmt('route_transaction_ms')} | {fmt('route_network_roundtrip_ms')} |")
    lines += ['', 'Count and continuous delay intervals use Student-t 95% intervals. Completion-rate intervals use Wilson 95% intervals. Counts include all 30 scheduled runs; delays include completed transactions only. A conditional 100% completion rate does not imply every scheduled run received an EM.', '',
        '## Controlled red signal scenarios', '',
        'Eighteen isolated runs use densities low/medium/high, seeds 1 and 4, and Fog/Cloud, Mist with Fog, and the matched no-preemption control. The existing binary and trip files are reused. Junction A1 starts with a protected conflicting phase rrGGrr for 150 seconds. The original permissive A0A1 green is removed in this validation input so both EV movements from A0A1 are red, including a possible dynamically selected turn. Priority is requested within 10 metres or half a second to test deliberately late notice. The horizon is 400 seconds. All controller safety rules stay in force. These scenarios are supplementary stress tests, not additional samples in the headline batch. Late notice is a controlled boundary case; it is not the default priority algorithm or an estimated real-world frequency.', '',
        '| Density | Configuration | Runs | Mean waiting seconds |', '| --- | --- | ---: | ---: |']
    for r in signal_summary:
        lines.append(f"| {r['density']} | {LABELS[r['configuration']]} | {r['n']} | {r['mean']:.3f} |")
    lines += ['', 'Each priority case must record the conflicting initial phase, a red-priority transition at A1, observed standstill waiting on the approach, confirmed arrival, and less total waiting than its matched no-preemption control. Signal clearance and minimum-green timings are checked from raw event logs.', '',
        'Two seeds per density provide mechanism validation, not a population performance claim. Wide Student-t intervals are retained and can extend below zero; all observed waiting times are positive. Some ordinary green-arrival runs can still correctly have zero waiting, and routing approaches can still share the same initial alert delivery outcomes.', '',
        'Raw validation results, generated network and configurations, scenario provenance, and logs are retained in artifacts/signal_validation/. The reproducible runner is scripts/run_signal_validation.py; the processor is analysis/supplemental_validation.py.', '']
    (ROOT/'docs/SUPPLEMENTAL_VALIDATION.md').write_text('\n'.join(lines))
    print(json.dumps({'route_runs': len(route), 'signal_runs': len(signals), 'supplementary_graphs': len(list(graphs.glob('*.png'))), 'timing_passed': timing['passed']}, indent=2))


if __name__ == '__main__':
    main()
