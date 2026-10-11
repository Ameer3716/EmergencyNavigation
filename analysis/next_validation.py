"""Read immutable next-experiment evidence and reuse the established pipeline."""
import argparse
import gzip
import hashlib
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import process_results as process
import policy_validation as policy
from raw_data import events, scalars

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_next_validation import shortest_route, incident_draw

BASELINE='FogCloudAStarAdvance'
PROPOSED='MistDynamicFogFallback'
DYNAMIC='FogCloudDynamicAdvance'
EXTRA={**policy.EXTRA,'fog_requests':('Fog route requests','requests/run'),
       'fog_completed_reviews':('Completed Fog reviews','reviews/run'),
       'fog_unanswered_reviews':('Unanswered Fog reviews','requests/run')}
METRICS={**process.METRICS,**EXTRA}
OPERATIONAL=('ev_full_stops','ev_below_1_s','ev_mean_speed_mps','ev_green_approach_fraction',
             'background_time_loss_s','route_changes','route_reviews','fog_requests')

def frozen_source(root, scenario):
    source=Path(scenario['source_project'])
    if root.anchor.startswith('\\\\'):
        source=Path(root.anchor)/source.as_posix().lstrip('/')
    return source

def write_rows(path, rows):
    keys=list(dict.fromkeys(key for row in rows for key in row))
    process.write_csv(path,[{key:row.get(key) for key in keys} for row in rows])

def fcd_metrics(path, corridor, incident=None, arrival=None):
    result=dict(fcd_max_queue=0,fcd_corridor_max_queue=0,background_below_1_vehicle_s=0.,
                corridor_below_1_vehicle_s=0.,incident_max_stopped=0,incident_vehicle_s=0.,
                fcd_peak_normal=0,incident_before_arrival_vehicle_s=0.)
    first_seen={};first_stopped={};seen=set();steps=0
    with gzip.open(path,'rb') as handle:
        for _,step in ET.iterparse(handle,events=('end',)):
            if step.tag!='timestep':continue
            steps+=1;queues=defaultdict(int);active=0;blocked=0
            time=float(step.get('time'))
            for vehicle in step:
                identity=vehicle.get('id');speed=float(vehicle.get('speed'))
                lane=vehicle.get('lane','');edge=lane.rsplit('_',1)[0]
                if identity.startswith('normal'):
                    seen.add(identity);active+=1
                    if not edge.startswith(':') and speed<1:
                        queues[edge]+=1
                        result['background_below_1_vehicle_s']+=.5
                        if edge in corridor:result['corridor_below_1_vehicle_s']+=.5
                elif identity.startswith('incidentQueue'):
                    first_seen.setdefault(identity,time)
                    if speed<.1 and (incident is None or edge==incident['edge']):
                        first_stopped.setdefault(identity,time)
                        if incident is None or incident['start_s']<=time<incident['stop_until_s']:
                            blocked+=1;result['incident_vehicle_s']+=.5
                            if arrival is not None and time<=arrival:result['incident_before_arrival_vehicle_s']+=.5
            result['fcd_max_queue']=max(result['fcd_max_queue'],max(queues.values(),default=0))
            result['fcd_corridor_max_queue']=max(result['fcd_corridor_max_queue'],max((v for edge,v in queues.items() if edge in corridor),default=0))
            result['fcd_peak_normal']=max(result['fcd_peak_normal'],active)
            result['incident_max_stopped']=max(result['incident_max_stopped'],blocked)
            step.clear()
    result.update(fcd_inserted_normal=len(seen),fcd_steps=steps,
                  incident_first_seen=json.dumps(first_seen,sort_keys=True),
                  incident_first_stopped=json.dumps(first_stopped,sort_keys=True))
    return result

def fog_review_metrics(value, route):
    """Distinguish sent reviews from replies and route replacements."""
    result=dict(
        fog_requests=sum(value.get('fogRequests',[])),
        fog_completed_reviews=sum(e['action']=='evaluated' and e['reason']=='fog_periodic' for e in route),
        fog_unanswered_reviews=sum(value.get('dynamicFogUnansweredReviews',[])),
        route_changes=sum(e['action']=='applied' and e['reason'] in ('low_speed','cost_improvement') for e in route),
        route_reviews=sum(e['action']=='review_requested' for e in route))
    assert result['fog_completed_reviews']<=result['route_reviews']<=result['fog_requests']
    assert all(delay>=.3-1e-9 for delay in value.get('dynamicFogReplyLatency',[]))
    assert not any(e['action']=='computed' for e in route)
    assert all(e['location']=='fog' for e in route if e['action']=='evaluated')
    return result

def collect(root, include_fcd=True, accepted_stems=None):
    rows,audit,scenario=policy.collect(root,accepted_stems=accepted_stems)
    if 'execution_started_at' in scenario:
        assert hashlib.sha256((root/'plan.snapshot.md').read_bytes()).hexdigest()==scenario['plan_sha256']
    corridor=shortest_route(root/'simulations/grid/grid.net.xml')
    for r in rows:
        stem=f"{r['configuration']}-{r['density']}-seed{r['seed']}"
        logs=root/'artifacts/logs/batch'
        value=scalars(root/f'results/raw/{stem}.sca')
        route=events(logs/f'routing-{stem}.csv')
        r['fog_requests']=sum(value['fogRequests']) if value['fogRequests'] else len(value['routeFogRequestTime'])
        r['fog_completed_reviews']=sum(e['action']=='evaluated' and e['reason']=='fog_periodic' for e in route) if r['configuration']==DYNAMIC else None
        r['fog_unanswered_reviews']=sum(value['dynamicFogUnansweredReviews']) if r['configuration']==DYNAMIC else None
        if r['configuration']==DYNAMIC:
            r.update(fog_review_metrics(value,route))
        incident=scenario['incident_draws'].get(str(r['seed']))
        r['incident_edge']=incident['edge'] if incident else ''
        r['incident_start_s']=incident['start_s'] if incident else None
        r['incident_requested_vehicles']=incident['vehicles'] if incident else None
        if include_fcd:
            arrival=value['emGenerationTime'][0]+r['ev_response_s'] if value['emGenerationTime'] and r['ev_response_s'] is not None else None
            r.update(fcd_metrics(logs/f'traffic-fcd-{stem}.xml.gz',corridor,incident,arrival))
        r['scheduled_normal_trips']=len(ET.parse(root/f"simulations/batch/{r['density']}-seed{r['seed']}/normal-{r['density']}-seed{r['seed']}.rou.xml").getroot().findall('vehicle'))
    source=frozen_source(root,scenario)
    assert {a['binary_sha256'] for a in audit}=={hashlib.sha256((source/'src/out/clang-release/libsrc.so').read_bytes()).hexdigest()}
    assert scenario['source_model_sha256']==json.loads((root/'scenario.json').read_text())['source_model_sha256']
    return rows,audit,scenario

def archive_vectors(root):
    """Losslessly archive completed copies from the initial, older pilot runner."""
    saved=0
    for index in (root/'results/raw').glob('*.vci'):
        source=index.with_suffix('.vec')
        target=index.with_suffix('.vec.gz')
        if not source.exists():continue
        config,density,seed=index.stem.rsplit('-',2)
        duplicate=root/f'simulations/batch/{density}-{seed}/{config}/results/Batch-#0.vec'
        temporary=target.with_name(target.name+'.archiving')
        checksum=hashlib.sha256()
        with source.open('rb') as stream,gzip.open(temporary,'wb',compresslevel=1) as compressed:
            while block:=stream.read(1024*1024):
                checksum.update(block);compressed.write(block)
        temporary.replace(target)
        manifest=root/f'artifacts/logs/batch/manifest-{index.stem}.json'
        metadata=json.loads(manifest.read_text())
        metadata.update(vector_uncompressed_sha256=checksum.hexdigest(),vector_uncompressed_bytes=source.stat().st_size)
        manifest.write_text(json.dumps(metadata,indent=2)+'\n')
        saved+=source.stat().st_size-target.stat().st_size
        # Both exact paths are completed outputs within this experiment root.
        if duplicate.exists():
            assert hashlib.sha256(duplicate.read_bytes()).hexdigest()==checksum.hexdigest()
            duplicate.unlink()
        source.unlink()
    return saved

def verify_vectors(root):
    for index in (root/'results/raw').glob('*.vci'):
        metadata=json.loads((root/f'artifacts/logs/batch/manifest-{index.stem}.json').read_text())
        vector=index.with_suffix('.vec.gz')
        if not vector.exists():raise AssertionError(f'Missing lossless vector: {vector}')
        size=0;checksum=hashlib.sha256()
        with gzip.open(vector,'rb') as stream:
            while block:=stream.read(1024*1024):checksum.update(block);size+=len(block)
        assert checksum.hexdigest()==metadata['vector_uncompressed_sha256'],index.stem
        assert size==metadata['vector_uncompressed_bytes'],index.stem

def regression(root, old):
    a=scalars(root/'results/raw/MistDynamicFogFallback-high-seed102.sca')
    b=scalars(old/'results/raw/MistTuningReference-high-seed102.sca')
    common=a.keys() & b.keys()
    differences={key:(a[key],b[key]) for key in common if a[key]!=b[key]}
    assert common and not differences,differences
    return dict(passed=True,seed=102,density='high',shared_scalar_fields=len(common),differences=differences)

def historical_rows(context, new_rows, new_root, native):
    original='ordinary' if context=='ordinary_ablation' else 'obstruction'
    root=native/f'policy_report_{original}_20261010'
    rows,_,_=policy.collect(root)
    for r in rows:
        stem=f"{r['configuration']}-{r['density']}-seed{r['seed']}"
        value=scalars(root/f'results/raw/{stem}.sca')
        r['fog_requests']=len(value['routeFogRequestTime'])
        r['fog_completed_reviews']=None;r['fog_unanswered_reviews']=None
    rows+=new_rows
    # Include the added ablation in the same observed background cohort.
    for density in {r['density'] for r in new_rows}:
        for seed in range(1,31):
            group=[r for r in rows if r['density']==density and r['seed']==seed]
            samples={}
            for r in group:
                folder=new_root if r['configuration']==DYNAMIC else root
                path=folder/f"artifacts/logs/batch/tripinfo-{r['configuration']}-{density}-seed{seed}.xml"
                samples[r['configuration']]={v.get('id'):float(v.get('timeLoss')) for v in ET.parse(path).getroot()
                    if v.tag=='tripinfo' and v.get('id','').startswith('normal')}
            ids=set.intersection(*(set(sample) for config,sample in samples.items() if config!='NoPreemptionBaseline'))
            for r in group:
                common=ids & samples[r['configuration']].keys()
                r['background_matched_count']=len(common)
                r['background_time_loss_s']=statistics.mean(samples[r['configuration']][i] for i in common) if common else None
    return rows

def format_value(value):
    return 'undefined' if value is None else f'{value:.3f}'

def report(manifest_path, output):
    manifest=json.loads(manifest_path.read_text())
    native=Path(manifest['native_root'])
    output.mkdir(parents=True,exist_ok=True)
    all_pairs=[];all_rows=[];matrices=[];evidence=[]
    for name,path in manifest['workspaces'].items():
        root=Path(path)
        verify_vectors(root)
        rows,audit,scenario=collect(root)
        assert scenario['executed_seeds']==list(range(1,31))
        matrices.append(dict(context=name,seeds=scenario['executed_seeds'],expected_runs=scenario['expected_runs'],actual_runs=len(rows),
            binary_sha256=audit[0]['binary_sha256'],source_model_sha256=scenario['source_model_sha256']))
        if name in ('ordinary_ablation','fixed_ablation'):
            rows=historical_rows(name,rows,root,native)
        label={'ordinary_ablation':'ordinary','fixed_ablation':'fixed_incident'}.get(name,name)
        for r in rows:r['context']=label
        summary=summarize(rows)
        pairs=paired(rows,PROPOSED,BASELINE,'main_matched')+paired(rows,PROPOSED,DYNAMIC,'local_vs_dynamic_fog')+paired(rows,DYNAMIC,BASELINE,'dynamic_vs_static_fog')
        for p in pairs:p['context']=label
        write_rows(output/label/'individual_runs.csv',rows)
        process.write_csv(output/label/'summary.csv',summary)
        process.write_csv(output/label/'graph_plot_data.csv',summary)
        process.write_csv(output/label/'paired_comparisons.csv',pairs)
        cohorts=[]
        for condition in ('normal','controlled_stall'):
            for p in paired([r for r in rows if r['scenario_condition']==condition],PROPOSED,BASELINE,'main_matched'):
                p.update(context=label,scenario_condition=condition);cohorts.append(p)
        process.write_csv(output/label/'paired_cohorts.csv',cohorts)
        graphs(summary,output/label/'graphs')
        all_rows+=rows;all_pairs+=pairs;evidence+=audit
    write_rows(output/'individual_runs.csv',all_rows)
    process.write_csv(output/'paired_comparisons.csv',all_pairs)
    result=dict(passed=True,matrices=matrices,regression=manifest['regression'],new_runs=sum(m['actual_runs'] for m in matrices),
                retained_and_new_rows=len(all_rows),graphs=len(list(output.glob('*/graphs/*.png'))),evidence=evidence,
                scope='Every scheduled seed, inputs, provenance, scalar reconciliation, signal safety and vector checksums; no outcome gates',
                provenance='Historical e3178f2 outputs retained; new ablation binary adds only a separate Fog dynamic branch and counters. Regression shared scalars exact.')
    (output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    requirements={'route_decision_ms':'A: decision latency (ms)','ev_response_s':'B: response (s)',
        'ev_full_stops':'C: full stops','ev_green_approach_fraction':'C: green approach share',
        'background_time_loss_s':'C: background loss (s)','traffic_light_wait_s':'D: signal waiting (s)'}
    table=['| Scenario | Density | Requirement / metric | Baseline | Proposed | Change % | Paired difference 95% CI | Pairs |',
           '| --- | --- | --- | ---: | ---: | ---: | --- | ---: |']
    for p in all_pairs:
        if p['contrast']!='main_matched' or p['metric'] not in requirements:continue
        table.append(f"| {p['context']} | {p['density']} | {requirements[p['metric']]} | {format_value(p['baseline_mean'])} | {format_value(p['proposed_mean'])} | {format_value(p['percent_change'])} | [{format_value(p['ci95_lower'])}, {format_value(p['ci95_upper'])}] | {p['n_pairs']} |")
    verdicts=[]
    for context,density in sorted({(p['context'],p['density']) for p in all_pairs if p['contrast']=='main_matched'}):
        group={p['metric']:p for p in all_pairs if p['context']==context and p['density']==density and p['contrast']=='main_matched'}
        decision=group['route_decision_ms'];response=group['ev_response_s'];wait=group['traffic_light_wait_s']
        wins=sum((group[m]['ci95_upper'] is not None and group[m]['ci95_upper']<0) if m!='ev_green_approach_fraction' else (group[m]['ci95_lower'] is not None and group[m]['ci95_lower']>0)
                 for m in ('ev_full_stops','ev_green_approach_fraction','background_time_loss_s'))
        verdicts.append(dict(scenario=context,density=density,A='Met' if decision['ci95_upper'] is not None and decision['ci95_upper']<0 else 'Not established',
            B='Met' if response['percent_change'] is not None and response['percent_change']<=-20 and response['ci95_upper']<0 else '20% reference not met',
            C=f'{"Met" if wins>=2 else "Not met"}: {wins}/3 supported wins',D='Not established: no matched arrivals' if wait['proposed_mean'] is None else 'Met' if wait['proposed_mean']>0 and wait['ci95_upper']<0 else
              'Not met: zero proposed waiting' if wait['proposed_mean']==0 else 'Improvement not established'))
    process.write_csv(output/'requirement_verdicts.csv',verdicts)
    lines=['# Extended matched-framework results','',
        'Baseline: FogCloudAStarAdvance. Proposed: MistDynamicFogFallback. Both request signal priority at 250 m / 20 s. FogCloudDynamicAdvance adds remote dynamic routing with actual radio delay and the same A* costs and review thresholds. A small local-computing advantage is not overstated.','',
        'All reported cells keep seeds 1-30. Non-delivery and non-arrival remain in individual results; time comparisons use available pairs. Controlled 900 ms stalls are injected faults. Ordinary, heavy demand, fixed incidents and random incidents remain separate. Mean EV speed is related to journey time; it does not establish requirement C by itself.','',
        '## Main A-D measurements','',*table,'','Intervals are paired proposed-minus-baseline bootstrap percentile 95% intervals (10000 resamples, fixed seed 42). A zero baseline gives an undefined percent change. No effect size controls data acceptance. The prior 20% target is a reporting reference.','',
        '## Verdicts','', '| Scenario | Density | A | B | C | D |','| --- | --- | --- | --- | --- | --- |']
    for v in verdicts:lines.append('| '+' | '.join(str(v[k]) for k in ('scenario','density','A','B','C','D'))+' |')
    lines+=['','## Computing versus dynamic rerouting','',
        '| Scenario | Density | Contrast | Baseline response s | Compared response s | Change % | Paired difference 95% CI s | Pairs |',
        '| --- | --- | --- | ---: | ---: | ---: | --- | ---: |']
    for p in all_pairs:
        if p['metric']=='ev_response_s' and p['contrast']!='main_matched':
            lines.append(f"| {p['context']} | {p['density']} | {p['contrast']} | {format_value(p['baseline_mean'])} | {format_value(p['proposed_mean'])} | {format_value(p['percent_change'])} | [{format_value(p['ci95_lower'])}, {format_value(p['ci95_upper'])}] | {p['n_pairs']} |")
    lines+=['','These contrasts separate static versus dynamic Fog routing and dynamic Fog versus Mist. The local contrast also includes different initial cloud/Mist routing and controlled fallback; it is not a pure processor benchmark. Radio losses, unavailable reviews and stale replies are retained. No optional signal/queue-aware cost redesign was adopted.','',
        '## Physical queues and incident realization','',
        '| Scenario | Density | Configuration | Runs | Mean max corridor queue | Mean corridor slow vehicle-s | Mean incident vehicle-s before EV arrival |','| --- | --- | --- | ---: | ---: | ---: | ---: |']
    for context,density,config in sorted({(r['context'],r['density'],r['configuration']) for r in all_rows if 'fcd_max_queue' in r and r['configuration']!='NoPreemptionBaseline'}):
        group=[r for r in all_rows if r['context']==context and r['density']==density and r['configuration']==config]
        lines.append(f"| {context} | {density} | {config} | {len(group)} | {statistics.mean(r['fcd_corridor_max_queue'] for r in group):.3f} | {statistics.mean(r['corridor_below_1_vehicle_s'] for r in group):.3f} | {statistics.mean(r['incident_before_arrival_vehicle_s'] for r in group):.3f} |")
    lines+=['','All assignment and realization details, uninserted/unfinished background counts, operational metrics and Fog requests are in individual_runs.csv. Background loss uses the same observed IDs across compared configurations at 900 s and is not a pure causal measure of preemption harm. First green approach and crossing phases are sampled at 500 ms. Whole-route slow time includes the shared scheduled start stop. Zero waiting is never replaced with an artificial value.','',
        '## Pilot, runtime and scope','',f"Frozen decision: `{json.dumps(manifest['decision'],sort_keys=True)}`",'',
        'Historical rows retain their original binary and raw provenance. New rows use the frozen extension binary; model equivalence of the proposed framework was checked on held-out seed 102 with every shared scalar equal. Existing results and reports remain available.','',
        'Existing Mist periodic reviews compute synchronously, without scheduling the initial Mist processing delay again. Dynamic Fog reviews include modeled remote service and radio delay. The ablation therefore compares the modeled frameworks, including initial routing and review delivery; it does not isolate physical OBU CPU performance.','',
        '## Graphs','']
    for path in sorted(output.glob('*/graphs/*.png')):
        lines += [f'### {path.parent.parent.name}: {path.stem}','',f'![{path.stem}]({Path("../results/next_validation")/path.relative_to(output)})','']
    (ROOT/'docs/NEXT_RESULTS.md').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8')
    summary=['# Supervisor summary','',
        'We compared the proposed Mist framework with Fog/Cloud using the same advance signal requests. An additional dynamic-Fog control tests whether remote rerouting achieves the same benefit. All 30 scheduled seeds in every reported cell were retained. Ordinary traffic, heavier demand and incidents were analysed separately.','',
        '| Scenario | Density | Faster decisions (A) | Clear response margin (B) | Extra metrics (C) | Lower nonzero waiting (D) |',
        '| --- | --- | --- | --- | --- | --- |']
    for v in verdicts:summary.append('| '+' | '.join(str(v[k]) for k in ('scenario','density','A','B','C','D'))+' |')
    summary+=['','B uses the previously requested 20% reference; C requires two supported improvements among full stops, green approach share and background time loss. All losses are reported. Zero waiting or an interval spanning zero leaves D unmet. The road lower bound limits gains in uncongested ordinary traffic. Random incidents may happen after an EV passes; these runs remain included.','',
        'Full baseline/proposed values, percent changes, paired confidence intervals and sample sizes appear in NEXT_RESULTS.md and results/next_validation/paired_comparisons.csv. Dynamic-Fog comparisons show how much benefit remains after both frameworks can reroute.','',
        'The 900 ms stalls are controlled injected faults. Optional queue/signal-aware cost changes were not adopted. No baseline was weakened and no result was accepted or rejected for its effect size.']
    (ROOT/'docs/SUPERVISOR_SUMMARY.md').write_text('\n'.join(summary)+'\n',encoding='utf-8')
    for name in ('METHODOLOGY.md','VERIFICATION.md','PROGRESS.md'):
        path=ROOT/'docs'/name
        marker='## Next experiment extension (2026-10-11)'
        text=path.read_text(encoding='utf-8').split(marker)[0].rstrip()
        path.write_text(text+'\n\n'+marker+'\n\nThe predeclared design is in NEXT_PLAN.md. NEXT_RESULTS.md contains matched-framework, dynamic-Fog, heavier-demand and random-incident results with paired bootstrap intervals. All new matrices passed input, source, binary, signal-safety and lossless-vector checks; effect sizes do not gate data. Optional cost redesign was not adopted. See SUPERVISOR_SUMMARY.md for explicit unmet requirements.\n',encoding='utf-8')
    print(f'Generated {len(all_rows)} rows and {result["graphs"]} graphs; all scheduled new runs audited.',flush=True)

def bootstrap(values):
    if not values:return None,None
    x=np.array(values,dtype=float)
    draws=np.random.default_rng(42).integers(0,len(x),size=(10000,len(x)))
    lo,hi=np.percentile(x[draws].mean(axis=1),[2.5,97.5])
    return float(lo),float(hi)

def paired(rows, left, right, contrast):
    output=[]
    for density in sorted({r['density'] for r in rows}):
        group={c:{r['seed']:r for r in rows if r['density']==density and r['configuration']==c} for c in (left,right)}
        for metric in METRICS:
            pairs=[(group[left][s].get(metric),group[right][s].get(metric)) for s in sorted(group[left].keys() & group[right].keys())]
            pairs=[(float(a),float(b)) for a,b in pairs if a is not None and b is not None]
            if not pairs:
                if metric in ('route_decision_ms','ev_response_s','traffic_light_wait_s','ev_full_stops','ev_green_approach_fraction','background_time_loss_s'):
                    output.append(dict(contrast=contrast,density=density,metric=metric,baseline=right,proposed=left,
                        baseline_mean=None,proposed_mean=None,percent_change=None,paired_difference=None,
                        ci95_lower=None,ci95_upper=None,n_pairs=0,ci_method='Unavailable: no valid matched observations'))
                continue
            diffs=[a-b for a,b in pairs];a=statistics.mean(a for a,b in pairs);b=statistics.mean(b for a,b in pairs)
            lo,hi=bootstrap(diffs)
            output.append(dict(contrast=contrast,density=density,metric=metric,baseline=right,proposed=left,
                baseline_mean=b,proposed_mean=a,percent_change=100*(a-b)/b if b else None,
                paired_difference=statistics.mean(diffs),ci95_lower=lo,ci95_upper=hi,n_pairs=len(pairs),
                ci_method='Paired bootstrap percentile 95%, 10000 resamples, seed 42'))
    return output

def summarize(rows):
    result=[]
    for density in sorted({r['density'] for r in rows}):
        for config in sorted({r['configuration'] for r in rows}):
            group=[r for r in rows if r['configuration']==config and r['density']==density]
            for metric in METRICS:
                if config=='NoPreemptionBaseline' and metric!='traffic_light_wait_s':continue
                values=[float(r[metric]) for r in group if r.get(metric) is not None]
                if not values:continue
                if metric in ('pdr','fallback_triggered'):
                    lo,hi=process.wilson_interval(int(sum(values)),len(values))
                else:lo,hi=bootstrap(values)
                result.append(dict(configuration=config,density=density,metric=metric,n=len(values),
                    mean=statistics.mean(values),ci95_lower=lo,ci95_upper=hi,unit=METRICS[metric][1],
                    ci_method='Wilson 95%' if metric in ('pdr','fallback_triggered') else 'Bootstrap percentile 95%, 10000 resamples, seed 42'))
    return result

def graphs(summary, folder):
    folder.mkdir(parents=True,exist_ok=True)
    for density in sorted({r['density'] for r in summary}):
        for metric,(label,unit) in METRICS.items():
            group=[r for r in summary if r['density']==density and r['metric']==metric]
            if not group:continue
            fig,ax=plt.subplots(figsize=(11,5.5))
            for i,r in enumerate(group):
                ax.errorbar(i,r['mean'],yerr=[[max(0,r['mean']-r['ci95_lower'])],[max(0,r['ci95_upper']-r['mean'])]],fmt='o',capsize=4,color='#234f75')
            ax.set_xticks(range(len(group)),[r['configuration'] for r in group],rotation=25,ha='right',fontsize=8)
            ax.set_ylabel(f'{label} ({unit})');ax.set_title(f'{label}: {density} [95% CI]')
            ax.grid(axis='y',alpha=.2);fig.tight_layout()
            fig.savefig(folder/f'{metric}-{density}.png',dpi=130);plt.close(fig)

def pilot(root, output):
    rows,audit,scenario=collect(root)
    output.mkdir(parents=True,exist_ok=True)
    process.write_csv(output/'individual_runs.csv',rows)
    groups=[]
    for density in scenario['executed_densities']:
        for config in scenario['configurations']:
            group=[r for r in rows if r['density']==density and r['configuration']==config]
            valid=[r['ev_response_s'] for r in group if r['ev_response_s'] is not None]
            groups.append(dict(density=density,configuration=config,scheduled=len(group),arrivals=len(valid),
                mean_response_s=statistics.mean(valid) if valid else None,
                mean_corridor_queue=statistics.mean(r['fcd_corridor_max_queue'] for r in group),
                mean_corridor_slow_vehicle_s=statistics.mean(r['corridor_below_1_vehicle_s'] for r in group),
                mean_background_slow_vehicle_s=statistics.mean(r['background_below_1_vehicle_s'] for r in group),
                mean_inserted=statistics.mean(r['fcd_inserted_normal'] for r in group)))
    process.write_csv(output/'summary.csv',groups)
    baseline={g['density']:g for g in groups if g['configuration']==BASELINE}
    low,high=baseline['heavy400'],baseline['heavy600']
    common={c:{r['seed']:r for r in rows if r['configuration']==BASELINE and r['density']==c} for c in ('heavy400','heavy600')}
    changes=[common['heavy600'][s]['ev_response_s']-common['heavy400'][s]['ev_response_s'] for s in range(101,111)
             if common['heavy600'][s]['ev_response_s'] is not None and common['heavy400'][s]['ev_response_s'] is not None]
    delta=statistics.mean(changes) if changes else None
    qualified=bool(delta is not None and delta>=5 and high['mean_corridor_queue']>=3 and high['mean_corridor_slow_vehicle_s']>low['mean_corridor_slow_vehicle_s'])
    record=dict(passed=True,congestion_qualified=qualified,paired_response_rise_s=delta,departure_end_s=scenario['departure_end_s'],
                rows=len(rows),groups=groups,execution=json.loads((root/'execution.json').read_text()),evidence=audit)
    (output/'pilot_audit.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='evidence'},indent=2))

def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('command',choices=('pilot','report'))
    parser.add_argument('--workspace',type=Path)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='pilot':pilot(args.workspace,args.output)
    else:report(args.manifest,args.output)

if __name__=='__main__':main()
