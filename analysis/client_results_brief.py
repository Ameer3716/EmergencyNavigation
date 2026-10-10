"""Build a compact client review from measured matched comparisons; no simulation edits."""
import base64
import csv
import hashlib
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/client_review/baseline_comparisons.csv'
CONTEXTS = ('Ordinary traffic', 'Controlled obstruction')
DENSITIES = ('low', 'medium', 'high')


def main():
    with SOURCE.open(newline='', encoding='utf-8') as handle:
        rows = [r for r in csv.DictReader(handle) if r['config_A'] == 'MistDynamicFogFallback']
    lookup = {(r['context'], r['density'], r['metric']): r for r in rows}
    assert len(lookup) == 30, 'Expected all two-context, three-density, five-metric comparisons'
    # Display the paired difference directly; negation reverses the CI endpoints.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharex=True, sharey=True)
    for ax, context in zip(axes, CONTEXTS):
        group = [lookup[context, d, 'ev_response_s'] for d in DENSITIES]
        means = [-float(r['mean_paired_diff']) for r in group]
        lows = [-float(r['ci95_upper']) for r in group]
        highs = [-float(r['ci95_lower']) for r in group]
        ax.barh(range(3), means, xerr=[[m-l for m,l in zip(means,lows)],
                     [h-m for h,m in zip(highs,means)]], capsize=5,
                color='#247b78' if context == 'Controlled obstruction' else '#526986')
        for i, (r, value, high) in enumerate(zip(group, means, highs)):
            ax.text(high+2, i, f"{value:.1f} s saved\n{float(r['reduction_percent']):.1f}% lower · n={r['n_pairs']}",
                    va='center', fontsize=9)
        ax.set_title(context + '\n[95% CI]')
        ax.set_yticks(range(3), [d.capitalize() for d in DENSITIES])
        ax.set_xlim(0, 190)
        ax.set_xlabel('EV response time saved versus Fog/Cloud (seconds)')
        ax.grid(axis='x', alpha=.2)
    axes[0].invert_yaxis()
    fig.suptitle('Where dynamic Mist produces a large measured benefit', fontsize=15)
    fig.tight_layout()
    output = ROOT / 'docs/client_brief'
    output.mkdir(exist_ok=True)
    chart = output / 'response_time_saved.png'
    fig.savefig(chart, dpi=160)
    plt.close(fig)
    encoded = base64.b64encode(chart.read_bytes()).decode('ascii')
    sections = []
    for context in CONTEXTS:
        body = []
        for d in DENSITIES:
            r = lookup[context,d,'ev_response_s']
            body.append(f"<tr><td>{d.capitalize()}</td><td>{float(r['mean_B']):.3f}</td>"
                        f"<td>{float(r['mean_A']):.3f}</td><td>{-float(r['mean_paired_diff']):.3f}</td>"
                        f"<td><strong>{float(r['reduction_percent']):.2f}%</strong></td>"
                        f"<td>{r['n_pairs']}</td></tr>")
        sections.append(f'<h2>{html.escape(context)}</h2><table><thead><tr><th>Density</th>'
                        '<th>Fog/Cloud (s)</th><th>Proposed (s)</th><th>Saved (s)</th>'
                        '<th>Reduction</th><th>Matched runs</th></tr></thead><tbody>'
                        + ''.join(body) + '</tbody></table>')
    supporting = []
    for metric, label, unit in (
        ('route_decision_ms', 'Route decision latency', 'ms'),
        ('traffic_light_wait_s', 'Traffic-light waiting', 's'),
        ('ev_delay_vs_freeflow_s', 'Excess travel delay', 's'),
        ('fog_route_requests', 'Fog route requests per scheduled run', 'requests/run')):
        group = [lookup['Ordinary traffic', d, metric] for d in DENSITIES]
        percentages = [float(r['reduction_percent']) for r in group]
        supporting.append(f"<tr><td>{label}</td><td>{min(percentages):.1f}–{max(percentages):.1f}% lower</td>"
                          f"<td>{'; '.join(d.capitalize()+': '+format(float(r['mean_B']),'.3f')+' → '+format(float(r['mean_A']),'.3f') for d,r in zip(DENSITIES,group))} {unit}</td></tr>")
    content = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Emergency navigation — measured client comparison</title><style>
body{font:17px/1.55 system-ui,sans-serif;color:#172a3a;max-width:1100px;margin:40px auto;padding:0 24px}h1{font-size:34px;line-height:1.2}h2{margin-top:32px}img{width:100%;height:auto}table{border-collapse:collapse;width:100%;font-size:15px}td,th{padding:10px;border-bottom:1px solid #ccd6de;text-align:left}th{background:#edf3f7}.lead{padding:20px;background:#e9f5f0;border-left:5px solid #247b78;font-size:21px}.note{background:#f3f5f7;padding:18px}small{color:#435665}@media print{body{font-size:12px;margin:0}h1{font-size:24px}table{font-size:11px}img{max-height:300px;object-fit:contain}tr{break-inside:avoid}}
</style><h1>Emergency vehicle navigation: measured improvements</h1>
<p>Baseline: FogCloudAStar. Proposed framework: MistDynamicFogFallback. Results use matched seeds at low, medium and high traffic.</p>
<p class="lead"><strong>Under controlled congestion, the proposed framework arrives 114–122 seconds earlier: a 41.9–45.8% reduction in EV response time.</strong></p>
<h2>Why the difference occurs</h2><p>The same three stopped passenger vehicles create a road queue in every compared configuration. Dynamic Mist reviews live road costs and can reroute around the obstruction; the fixed-route approaches keep their initial route. The framework also requests signal priority earlier. This comparison measures the complete framework, not A* computation alone.</p>
'''
    content += f'<img alt="Paired response time savings with 95 percent confidence intervals, using the same zero-based scale for both scenarios" src="data:image/png;base64,{encoded}">'
    content += ''.join(sections)
    content += '<h2>Additional measured improvements in ordinary traffic</h2><table><thead><tr><th>Metric</th><th>Reduction</th><th>Baseline → proposed, by density</th></tr></thead><tbody>' + ''.join(supporting) + '</tbody></table>'
    content += '''<h2>What the results establish</h2><div class="note"><ul>
<li>The congestion experiment demonstrates a substantial response benefit at every density. All three paired 95% intervals exclude zero.</li>
<li>Ordinary traffic shows a smaller 4.0–6.1% response benefit. A universal 20% improvement is not established.</li>
<li>Ordinary signal waiting improves at all densities. Under obstruction, waiting averages improve at all densities, but only high density has a paired interval excluding zero.</li>
<li>Excess travel delay is related to response time. Fog request counts measure remote routing transactions, not total radio overhead.</li>
<li>Initial routing failures remain in delivery metrics. Arrival-time comparisons use 24, 29 and 30 matched delivered runs. Request counts include all 30 scheduled runs.</li>
<li>Eight seeds receive an explicitly controlled Mist stall uniformly across Mist configurations. These tests do not demonstrate naturally occurring fallback.</li>
</ul></div><p><a href="CLIENT_BASELINE_COMPARISON.md">Full comparison and confidence intervals</a> · <a href="Emergency_Vehicle_Navigation_Final_Submission.docx">Full Word report with all graphs</a></p>'''
    content += '<p><small>Generated from results/client_review/baseline_comparisons.csv; source SHA-256: ' + hashlib.sha256(SOURCE.read_bytes()).hexdigest() + '</small></p></html>'
    (ROOT / 'docs/CLIENT_RESULTS.html').write_text(content, encoding='utf-8')
    (ROOT / 'artifacts/client_brief_provenance.json').write_text(json.dumps({
        'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'comparisons': len(rows), 'new_simulation_runs': 0,
        'chart': 'docs/client_brief/response_time_saved.png',
        'interpretation': 'Measured congestion benefit; ordinary results retained on the same scale.'}, indent=2)+'\n')
    print('Generated client results page and paired response savings figure from 30 measured comparisons.')


if __name__ == '__main__':
    main()
