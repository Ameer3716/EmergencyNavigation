"""Publish completed pilot evidence after user cancellation, never partial runs."""
import hashlib
import json
import sys
from pathlib import Path
import next_validation as next

ROOT=Path(__file__).resolve().parents[1]
NATIVE=Path(r'\\wsl.localhost\opp_env\home\opp_env')
OUTPUT=ROOT/'results/next_validation/completed_pilots'

def supervisor_summary():
    text='''# Supervisor summary

The experiment was cancelled on 11 October 2026 before reported seeds 1 to 30 began. Updated CSVs include 109 completed held-out pilot runs only: 60 from the 360 second departure window and 49 from the 120 second window. Eleven unfinished or unstarted runs are excluded, with their seed coverage disclosed. No simulations were restarted.

## Preserved complete matched evidence

Baseline is FogCloudAStarAdvance and proposed is MistDynamicFogFallback. Signal request timing is equal.

| Requirement | Ordinary traffic | Fixed obstruction |
| --- | --- | --- |
| A Faster route decision | Supported | Supported |
| B Clear response margin | 0.3 to 0.7 percent; 20 percent reference unmet | About 40 to 45 percent faster |
| C Two additional improvements | Not established | Full stops and background time loss improve |
| D Lower nonzero signal waiting | Both zero; unmet | Paired intervals include zero; not established |

## New pilots and limits

The first pilot formed queues, but baseline response rose only from 148.25 seconds at 400 trips to 150.00 seconds at 600 trips. Its 1.75 second paired increase missed the predeclared 5 second congestion criterion. The stronger-demand pilot was cancelled before completion; its completed subset is descriptive and may have biased completion patterns. It has no completed 600-trip dynamic Fog cell and cannot establish a final ablation or congestion verdict.

Completed pilot response means are higher for the proposed framework in every demand/window comparison, not a response win. Waiting and secondary measures are mixed; the paired intervals and sample counts must be read alongside the means.

The 900 ms stalls remain controlled injected faults. Zero waiting is not altered. Optional signal-aware cost redesign was not adopted. Baselines and reported seeds were not weakened or selected. Full values, paired intervals, counts, coverage and all completed-pilot graphs are in COMPLETED_PILOT_RESULTS.md and results/next_validation/completed_pilots. Preserved reported measurements remain in POLICY_VALIDATION.md.
'''
    (ROOT/'docs/SUPERVISOR_SUMMARY.md').write_text(text,encoding='utf-8')

def completed_stems(root):
    accepted=set()
    for index in (root/'results/raw').glob('*.vci'):
        stem=index.stem
        files=[index,index.with_suffix('.sca'),index.with_suffix('.vec.gz')]
        if not all(p.is_file() and p.stat().st_size for p in files):continue
        text=(root/f'artifacts/logs/batch/{stem}-stdout.txt').read_text(errors='replace')
        if 'Simulation time limit reached -- at t=900s' in text and text.rstrip().endswith('End.'):
            accepted.add(stem)
    return accepted

def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    combined=[];stats=[];contrasts=[];coverage=[];evidence=[]
    for window in (360,120):
        root=NATIVE/f'next_pilot_{window}_20261011'
        accepted=completed_stems(root)
        next.verify_vectors(root)
        rows,audit,scenario=next.collect(root,accepted_stems=accepted)
        label=f'pilot_{window}'
        for row in rows:row.update(context=label,pilot_window_s=window,evidence_role='held_out_pilot_only')
        summary=next.summarize(rows)
        pairs=(next.paired(rows,next.PROPOSED,next.BASELINE,'main_matched')+
               next.paired(rows,next.PROPOSED,next.DYNAMIC,'local_vs_dynamic_fog')+
               next.paired(rows,next.DYNAMIC,next.BASELINE,'dynamic_vs_static_fog'))
        for row in summary+pairs:row.update(context=label,pilot_window_s=window)
        for config in scenario['configurations']:
            for density in scenario['executed_densities']:
                seeds=sorted(r['seed'] for r in rows if r['configuration']==config and r['density']==density)
                coverage.append(dict(context=label,pilot_window_s=window,configuration=config,density=density,
                    scheduled_runs=10,completed_runs=len(seeds),included_seeds=' '.join(map(str,seeds)),
                    excluded_seeds=' '.join(map(str,sorted(set(range(101,111))-set(seeds))))))
        folder=OUTPUT/label
        next.write_rows(folder/'individual_runs.csv',rows)
        next.write_rows(folder/'summary.csv',summary)
        next.write_rows(folder/'graph_plot_data.csv',summary)
        next.write_rows(folder/'paired_comparisons.csv',pairs)
        next.graphs(summary,folder/'graphs')
        combined+=rows;stats+=summary;contrasts+=pairs;evidence+=audit
    next.write_rows(OUTPUT/'individual_runs.csv',combined)
    next.write_rows(OUTPUT/'summary.csv',stats)
    next.write_rows(OUTPUT/'paired_comparisons.csv',contrasts)
    next.write_rows(OUTPUT/'coverage.csv',coverage)
    cancellation=json.loads((ROOT/'artifacts/next_validation/cancellation.json').read_text())
    expected=sum(cancellation['cancellation'][key] for key in ('completed_first_pilot','completed_second_pilot'))
    assert len(combined)==expected==109
    audit=dict(passed=True,complete_runs=len(combined),scheduled_pilot_runs=120,excluded_runs=11,
        reported_batch_started=False,evidence_role='Held-out pilot only; cancelled before reported seeds',
        completion_rule='Nonempty scalar, compressed vector and index; normal 900 s termination; verified vector checksum',
        scope='Validity of included completed evidence; NOT full matrix completeness or supervisor performance success',
        coverage=coverage,evidence=evidence)
    (OUTPUT/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    lines=['# Completed pilot results after cancellation','',
        'The experiment was cancelled on 11 October 2026. This update includes 109 fully completed held-out pilot runs only. Eleven unfinished or unstarted runs are excluded from every table, CSV and graph. The reported seeds 1 to 30 were never launched. These pilot observations do not replace the preserved matched ordinary and fixed-obstruction results.','',
        'The first pilot used a 360 second departure window. All 60 runs completed. The stronger-demand pilot used a 120 second window; 49 of 60 runs completed. Partial cells can have biased completion patterns, so comparisons are descriptive pilot evidence and cannot establish general performance.','',
        '## Coverage','', '| Window s | Trips | Configuration | Complete | Scheduled |',
        '| ---: | --- | --- | ---: | ---: |']
    for r in coverage:lines.append(f"| {r['pilot_window_s']} | {r['density']} | {r['configuration']} | {r['completed_runs']} | 10 |")
    lines+=['','## Completed matched pilot measurements','',
        'Baseline is FogCloudAStarAdvance; proposed is MistDynamicFogFallback. Both use the same advance signal requests. Intervals are paired proposed minus baseline bootstrap 95% intervals. Counts disclose available completed pairs; no partial run is assigned a result.','',
        '| Window s | Trips | Requirement and metric | Baseline | Proposed | Change % | Paired difference 95% CI | Pairs |',
        '| ---: | --- | --- | ---: | ---: | ---: | --- | ---: |']
    labels={'route_decision_ms':'A decision ms','ev_response_s':'B response s','ev_full_stops':'C full stops',
        'ev_green_approach_fraction':'C green approach share','background_time_loss_s':'C background loss s',
        'traffic_light_wait_s':'D signal waiting s'}
    f=next.format_value
    for p in contrasts:
        if p['contrast']=='main_matched' and p['metric'] in labels:
            lines.append(f"| {p['pilot_window_s']} | {p['density']} | {labels[p['metric']]} | {f(p['baseline_mean'])} | {f(p['proposed_mean'])} | {f(p['percent_change'])} | [{f(p['ci95_lower'])}, {f(p['ci95_upper'])}] | {p['n_pairs']} |")
    lines+=['','## Interpretation','',
        'The completed first pilot produced queues, but the baseline response rose only from 148.25 s at 400 trips to 150.00 s at 600 trips. The paired increase was 1.75 s, below the predeclared 5 s congestion qualification. Stronger demand was therefore piloted, but that matrix was cancelled before completion. No final congestion qualification or reported-sample A to D verdict is claimed.','',
        'Dynamic Fog uses real network requests. Existing Mist periodic reviews compute synchronously without scheduling another initial processing delay; the ablation is not a hardware CPU benchmark. The 900 ms stalls remain labelled controlled fault injection. Zero waiting is retained when measured. Mean speed is correlated with journey time; background loss is not a pure causal measure of preemption harm.','',
        'Primary metrics are PDR, NRL, EM throughput, EM end-to-end delay, route decision latency, EV response and signal waiting. Completed-run secondary metrics and ablations are retained in summary.csv and paired_comparisons.csv. No existing historical result was replaced.','',
        '## Graphs','']
    for path in sorted(OUTPUT.glob('pilot_*/graphs/*.png')):
        lines += [f'### {path.parent.parent.name} {path.stem}','',f'![{path.stem}](../results/next_validation/completed_pilots/{path.relative_to(OUTPUT).as_posix()})','']
    (ROOT/'docs/COMPLETED_PILOT_RESULTS.md').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8')
    supervisor_summary()
    for name in ('METHODOLOGY.md','VERIFICATION.md','PROGRESS.md'):
        path=ROOT/'docs'/name;marker='## Cancelled experiment completed evidence'
        text=path.read_text(encoding='utf-8').split(marker)[0].rstrip()
        path.write_text(text+'\n\n'+marker+'\n\nThe new experiment was cancelled before reported seeds began. COMPLETED_PILOT_RESULTS.md and results/next_validation/completed_pilots contain only 109 completed held-out pilot runs, with 11 unfinished or unstarted cases excluded and coverage disclosed. The audit validates included evidence, not a complete scheduled matrix or performance success. Preserved reported results remain in POLICY_VALIDATION.md.\n',encoding='utf-8')
    print(json.dumps(dict(completed=len(combined),excluded=11,graphs=len(list(OUTPUT.glob('pilot_*/graphs/*.png')))),indent=2))

if __name__=='__main__':main()
