#!/usr/bin/env python3
"""Compare every Mist approach directly with Fog/Cloud using retained raw scalars."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import process_results as process
from raw_data import events, scalars
from supplemental_validation import continuous, LABELS

ROOT = Path(__file__).resolve().parents[1]
METRICS = {
    'route_decision_ms': ('Route decision latency', 'ms'),
    'ev_response_s': ('EV response time', 's'),
    'traffic_light_wait_s': ('EV traffic-light waiting time', 's'),
    'ev_delay_vs_freeflow_s': ('Excess travel delay above free flow', 's'),
    'fog_route_requests': ('Fog route requests per scheduled run', 'requests/run'),
}
DENSITIES = ('low', 'medium', 'high')


def read_runs(path):
    records, hashes = [], {}
    for source in events(path):
        if source['configuration'] not in process.CONFIGS:
            continue
        row = dict(source)
        for field in ('seed', 'delivered_messages', *METRICS):
            if field != 'fog_route_requests':
                row[field] = float(row[field]) if row[field] else None
        scalar = ROOT / source['source_scalar'].replace('\\', '/')
        values = scalars(scalar)
        # Validate reported headline values independently against raw scalars.
        for field, name, scale in (
            ('route_decision_ms', 'routeDecisionLatency', 1000),
            ('ev_response_s', 'evResponseTime', 1),
            ('traffic_light_wait_s', 'evTrafficLightWaitingTime', 1),
        ):
            expected = values[name][0] * scale if values[name] else None
            assert (row[field] is None and expected is None) or (
                row[field] is not None and expected is not None
                and math.isclose(row[field], expected, abs_tol=1e-8)), (scalar, field)
        expected = (max(0., values['evTravelTime'][0] - values['evDistance'][0] / 13.9)
                    if values['evTravelTime'] and values['evDistance'] else None)
        assert (row['ev_delay_vs_freeflow_s'] is None and expected is None) or (
            expected is not None and math.isclose(row['ev_delay_vs_freeflow_s'], expected, abs_tol=1e-8))
        row['fog_route_requests'] = len(values['routeFogRequestTime'])
        hashes[source['source_scalar']] = hashlib.sha256(scalar.read_bytes()).hexdigest()
        records.append(row)
    expected = {(c, d, s) for c in process.CONFIGS for d in DENSITIES for s in range(1, 31)}
    assert len(records) == 360 and {(r['configuration'], r['density'], int(r['seed'])) for r in records} == expected
    return records, hashes


def compare(rows):
    pairs = process.paired_comparisons(rows, [
        (c, 'FogCloudAStar', list(METRICS)) for c in process.CONFIGS[1:]])
    for row in pairs:
        baseline, proposed = row['mean_B'], row['mean_A']
        row['reduction_percent'] = 100 * (baseline - proposed) / baseline if baseline else None
    return pairs


def draw(rows, metric, context, folder):
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for offset, config in ((-.18, 'FogCloudAStar'), (.18, 'MistDynamicFogFallback')):
        means, lows, highs, ns = [], [], [], []
        for density in DENSITIES:
            values = [r[metric] for r in rows if r['configuration'] == config
                      and r['density'] == density and r[metric] is not None]
            mean, low, high = continuous(values)
            if metric == 'traffic_light_wait_s':
                low, high = process.bootstrap_ci(values)
            means.append(mean)
            lows.append(max(0., mean - low))
            highs.append(max(0., high - mean))
            ns.append(len(values))
        xs = [i + offset for i in range(3)]
        ax.bar(xs, means, width=.34, label=LABELS[config], color=process.CONFIG_COLORS[config],
               yerr=[lows, highs], capsize=5, edgecolor='#333333')
        for x, mean, high, n in zip(xs, means, highs, ns):
            ax.annotate(f'{mean:.3f}\n(n={n})', (x, mean + high), xytext=(0, 5),
                        textcoords='offset points', ha='center', fontsize=9)
    ax.set_xticks(range(3), [d.capitalize() for d in DENSITIES])
    ax.set_ylabel(METRICS[metric][1])
    ax.set_title(f'{METRICS[metric][0]}\n{context} [95% CI]')
    bottom, top = ax.get_ylim()
    ax.set_ylim(min(0, bottom), top * 1.2 if top else 1)
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.01), ncol=2, fontsize=9)
    ax.grid(axis='y', alpha=.2)
    fig.tight_layout()
    fig.savefig(folder / f'{metric}-{context.lower().replace(" ", "_")}.png', dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ordinary-csv', type=Path, default=ROOT / 'results/processed/individual_runs-batch.csv')
    parser.add_argument('--incident-csv', type=Path, default=ROOT / 'results/congestion_validation/individual_runs.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'results/client_review')
    args = parser.parse_args()
    graphs = args.output / 'graphs'
    graphs.mkdir(parents=True, exist_ok=True)
    paired, hashes = [], {}
    for context, path in (('Ordinary traffic', args.ordinary_csv), ('Controlled obstruction', args.incident_csv)):
        rows, proof = read_runs(path)
        hashes.update(proof)
        result = compare(rows)
        paired.extend(dict(context=context, **r) for r in result)
        for metric in METRICS:
            draw(rows, metric, context, graphs)
    process.write_csv(args.output / 'baseline_comparisons.csv', paired)
    (args.output / 'provenance.json').write_text(json.dumps(dict(
        baseline='FogCloudAStar', proposed='MistDynamicFogFallback', raw_scalar_sha256=hashes,
        source_matrices=2, primary_runs_per_matrix=360,
        note='Evidence checks do not require a winning effect. Ordinary and obstruction cases remain separate.'), indent=2) + '\n')
    lines = ['# Client baseline comparisons', '',
             'FogCloudAStar is the baseline. The proposed framework is MistDynamicFogFallback. All three Mist approaches are retained in the comparison CSV. Ordinary traffic and controlled obstruction are separate experiments.', '',
             'Positive reduction percentages mean a lower proposed value. Confidence intervals use matched seeds, including zero differences. Missing arrivals are excluded from time metrics. Fog request counts include all 30 scheduled runs, including runs without alert delivery.', '',
             '| Scenario | Density | Metric | Paired runs | Fog baseline | Proposed | Reduction % | Proposed minus baseline 95% interval |',
             '| --- | --- | --- | ---: | ---: | ---: | ---: | --- |']
    for r in paired:
        if r['config_A'] != 'MistDynamicFogFallback':
            continue
        reduction = f"{r['reduction_percent']:.2f}" if r['reduction_percent'] is not None else 'N/A'
        lines.append(f"| {r['context']} | {r['density']} | {METRICS[r['metric']][0]} ({METRICS[r['metric']][1]}) | {r['n_pairs']} | {r['mean_B']:.3f} | {r['mean_A']:.3f} | {reduction} | {r['ci95_lower']:.3f} to {r['ci95_upper']:.3f} |")
    lines += ['', '## Supporting metric definitions', '',
              'Excess travel delay is max(0, actual EV travel time minus traveled distance / 13.9 m/s). This reuses collected travel-time and distance scalars. It measures delay relative to a reference speed and is correlated with response time. It does not isolate congestion from signals.', '',
              'Fog route requests count actual initial RouteRequest send events recorded by the EV. Local Mist needs zero requests; fallback needs one only when it switches to Fog. These are requests at the sender, not total relay transmissions or EM packet delivery. A scheduled case without an EM has zero requests.', '',
              'Bar intervals use Student-t, except signal waiting uses the existing bootstrap percentile method. Paired intervals use Student-t and are exploratory without multiple-comparison correction. All graph labels use generic 95% CI.', '',
              'The framework comparison includes live routing and advance signal requests in dynamic Mist. Fog/Cloud and static Mist use reactive requests. All use the same safety controller and bounded retry mechanism. Journey differences therefore do not isolate A* computation alone.', '',
              '## Measured assessment', '',
              'A paired interval wholly below zero supports a lower proposed value in this experiment. An interval crossing zero is inconclusive. The client selected a 20 percent response-time target after these runs were measured. The obstruction experiment exceeds that target at every density; ordinary traffic does not. This is an exploratory assessment, not a prospectively registered success test. See CLIENT_20_PERCENT_FEASIBILITY.md for the physical limits of the ordinary grid.']
    for context in ('Ordinary traffic', 'Controlled obstruction'):
        for metric in ('ev_response_s', 'traffic_light_wait_s', 'ev_delay_vs_freeflow_s', 'fog_route_requests'):
            group = [r for r in paired if r['context'] == context and r['config_A'] == 'MistDynamicFogFallback' and r['metric'] == metric]
            supported = [r['density'] for r in group if r['ci95_upper'] < 0]
            lines += ['', f"{context}, {METRICS[metric][0].lower()}: lower proposed values supported in {', '.join(supported) if supported else 'none of the three densities'}. Read the percentage reductions and intervals above for the size and uncertainty of each effect."]
    (ROOT / 'docs/CLIENT_BASELINE_COMPARISON.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(dict(raw_scalars_verified=len(hashes), paired_comparisons=len(paired), graphs=10), indent=2))


if __name__ == '__main__':
    main()
