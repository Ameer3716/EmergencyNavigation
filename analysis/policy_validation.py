"""Extend the existing scalar/statistics pipeline for matched signal-policy experiments."""
import argparse
import hashlib
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import process_results as process
from raw_data import events, scalars, incident_observation

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_timing_evidence import audit as timing_audit
EXTRA={
 'ev_full_stops':('EV full stops','stops/run'),
 'ev_below_1_s':('EV time below 1 m/s','s'),
 'ev_whole_stopped_s':('Whole-route EV standstill','s'),
 'ev_green_fraction':('Signals entered on green (sampled)','share'),
 'ev_green_count':('Signals entered on green (sampled)','signals/run'),
 'ev_green_approach_fraction':('Green on first arrival within 20 m','share'),
 'background_time_loss_s':('Matched background time loss at 900 s','s/vehicle'),
 'ev_mean_speed_mps':('Mean EV journey speed','m/s'),
}
SCALAR_FIELDS={'ev_full_stops':'evFullStops','ev_below_1_s':'evTimeBelow1Mps',
 'ev_whole_stopped_s':'evWholeRouteStoppedTime','ev_green_fraction':'evGreenCrossingFraction',
 'ev_green_count':'evSignalsPassedOnGreen'}
REPORTED=('FogCloudAStar','MistAStar','MistDynamicAStar','MistDynamicFogFallback','NoPreemptionBaseline','FogCloudAStarAdvance','MistAStarAdvance')


def effective_parameters(path):
    result={}
    for line in path.read_text().splitlines():
        fields=line.split()
        if len(fields)==4 and fields[0]=='par':result.setdefault(fields[2],set()).add(fields[3])
    return result


def first_approach_states(mobility,release):
    """A red arrival followed by a green crossing remains a red arrival."""
    if release is None:return []
    result=[];previous_edge=None;recorded=False
    for row in mobility:
        edge=row['edge']
        if edge!=previous_edge:recorded=False;previous_edge=edge
        if not edge or edge.startswith(':') or not row['nextTls'] or recorded:continue
        if float(row['time'])+1e-9<release:continue
        distance=float(row['tlsDistance'])
        if 0<=distance<=20:
            result.append(dict(time=float(row['time']),edge=edge,tls=row['nextTls'],state=row['linkState']))
            recorded=True
    return result


def collect(root, accepted_stems=None):
    scenario=json.loads((root/'scenario.json').read_text())
    source=Path(scenario['source_project'])
    if root.anchor.startswith('\\\\'):
        source=Path(root.anchor)/source.as_posix().lstrip('/')
    model_files=[p for p in (source/'src').rglob('*')
                 if p.is_file() and p.suffix in ('.cc','.h','.ned','.msg') and 'out' not in p.relative_to(source).parts]
    assert model_files,(source,'missing frozen model source')
    scenario['source_model_sha256']={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted(model_files)}
    if scenario['phase']=='report':
        assert scenario['source_model_sha256']==scenario['selection']['source_model_sha256'],'Model source changed after held-out selection'
    densities=scenario.get('executed_densities',('low','medium','high'))
    expected={(c,d,s) for c in scenario['configurations'] for d in densities for s in scenario['executed_seeds']}
    if accepted_stems is not None:
        expected={key for key in expected if f'{key[0]}-{key[1]}-seed{key[2]}' in accepted_stems}
        assert len(expected)==len(accepted_stems),'Unknown completed-run key'
    rows=[];audit=[];seen=set();input_groups={};background_samples={};oldroot=process.ROOT;process.ROOT=root
    try:
        for path in sorted((root/'results/raw').glob('*.sca')):
            if accepted_stems is not None and path.stem not in accepted_stems:continue
            c,d,suffix=path.stem.split('-');seed=int(suffix.removeprefix('seed'))
            key=(c,d,seed);assert key in expected and key not in seen,key;seen.add(key)
            logs=root/'artifacts/logs/batch'
            r=process.one_run(c,path,d,seed,logs/f'emergency-{path.stem}.csv')
            if c.startswith('MistTuning'):
                routes=events(logs/f'routing-{path.stem}.csv')
                r['route_changes']=sum(e['action']=='applied' and e['reason'] in ('low_speed','cost_improvement') for e in routes)
                r['route_reviews']=sum(e['action']=='evaluated' for e in routes)
            values=scalars(path)
            for field,name in SCALAR_FIELDS.items():r[field]=values[name][0] if values[name] else None
            r['ev_mean_speed_mps']=r['ev_distance_m']/r['ev_travel_s'] if r['ev_travel_s'] else None
            trips=ET.parse(logs/f'tripinfo-{path.stem}.xml').getroot()
            background=[t for t in trips if t.tag=='tripinfo' and t.get('id','').startswith('normal')]
            loss=[float(t.get('timeLoss')) for t in background]
            background_samples[key]={t.get('id'):float(t.get('timeLoss')) for t in background}
            r['background_time_loss_s']=statistics.mean(loss) if loss else None
            r['background_tripinfo_count']=len(loss)
            r['background_unfinished_count']=sum(float(t.get('arrival'))<0 for t in background)
            r['context']=scenario['context']
            r['incident_maximum_stopped']=None
            r['incident_inserted_by_250']=None
            if scenario['context']=='obstruction':
                observed,maximum=incident_observation(logs/f'incident-fcd-{path.stem}.xml')
                r['incident_maximum_stopped']=maximum
                r['incident_inserted_by_250']=sum(v['first_seen_s'] is not None and v['first_seen_s']<250 for v in observed.values())
            mobility=events(logs/f'mobility-{path.stem}.csv')
            assert mobility and 'nextTls' in mobility[0],(path.stem,'missing extended mobility schema')
            junctions=[e for e in mobility if e['junctionEvent']=='junction_entry']
            approach=first_approach_states(mobility,values['evNavigationReleaseTime'][0] if values['evNavigationReleaseTime'] else None)
            release=values['evNavigationReleaseTime'][0] if values['evNavigationReleaseTime'] else None
            observed_motion=[e for e in mobility if release is not None and e['speed']
                             and float(e['time'])+1e-9>=release]
            r['ev_near_signal_below_1_s']=sum(.1 for e in observed_motion
                if float(e['speed'])<1 and e['tlsDistance'] and 0<=float(e['tlsDistance'])<=20)
            previous_stops=0;stop_events=[]
            for e in observed_motion:
                count=int(e['fullStops'])
                if count>previous_stops:stop_events.extend([e]*(count-previous_stops))
                previous_stops=count
            r['ev_full_stops_at_scheduled_start']=sum(e['edge']=='A0A1' and abs(float(e['lanePosition'])-30)<.2 for e in stop_events)
            r['ev_approach_count']=len(approach)
            r['ev_green_approach_count']=sum(e['state'] in ('G','g') for e in approach)
            r['ev_green_approach_fraction']=r['ev_green_approach_count']/len(approach) if approach and r['ev_response_s'] is not None else None
            if r['ev_response_s'] is not None:
                assert values['evNavigationReleaseTime'],path.stem
                assert r['ev_below_1_s']+1e-6>=r['ev_whole_stopped_s']>=r['traffic_light_wait_s']-1e-6,path.stem
                assert int(values['evSignalCrossings'][0])==len(junctions),path.stem
                assert int(r['ev_green_count'])==sum(e['crossingLinkState'] in ('G','g') for e in junctions),path.stem
                assert int(r['ev_full_stops'])==len(stop_events),path.stem
                assert all(e['crossingState'] and e['crossingTls'] for e in junctions),path.stem
            manifest=json.loads((logs/f'manifest-{path.stem}.json').read_text())
            ini=root/f'simulations/batch/{d}-seed{seed}/{c}/omnetpp.ini'
            assert hashlib.sha256(ini.read_bytes()).hexdigest()==manifest['ini_sha256'],path.stem
            assert manifest['controlled_mist_stall_ms']==(900 if c.startswith('Mist') and seed in process.STALL_SEEDS else 0),path.stem
            assert r['generated_messages']==1,path.stem
            parameters=effective_parameters(path)
            advance=c not in ('FogCloudAStar','MistAStar','NoPreemptionBaseline')
            assert parameters['preemptionDistance']=={'250m' if advance else '100m'},path.stem
            assert parameters['preemptionEta']=={'20s' if advance else '8s'},path.stem
            assert parameters['releaseSpeed']=={'13.9mps'},path.stem
            for parameter,expected_value in {'maxInterfDist':'400m','telemetryValidationDelay':'0s',
                  'watchdogThreshold':'0.5s','pollInterval':'0.1s','minimumGreen':'10s','updateInterval':'0.5s'}.items():
                assert parameters[parameter]=={expected_value},(path.stem,parameter,parameters[parameter])
            inputs={name:hashlib.sha256((ini.parent/name).read_bytes()).hexdigest()
                    for name in ('grid.net.xml','special.rou.xml','antenna.xml','config.xml',f'normal-{d}-seed{seed}.rou.xml')}
            groupkey=(d,seed)
            if groupkey in input_groups:assert inputs==input_groups[groupkey],(path.stem,'unequal inputs')
            else:input_groups[groupkey]=inputs
            if scenario['phase']=='report':
                assert manifest['binary_sha256']==scenario['selection']['binary_sha256'],path.stem
                if c=='MistDynamicFogFallback':
                    selected=scenario['selection']['settings']
                    assert parameters['dynamicUpdateInterval']=={f"{selected['review_s']}s"},path.stem
                    assert parameters['minimumRerouteGap']=={f"{selected['gap_s']}s"},path.stem
                    for parameter,setting in (('minimumRouteImprovement','improvement'),
                                              ('slowRouteImprovement','slow_improvement')):
                        assert {float(v) for v in parameters[parameter]}=={selected[setting]},path.stem
            audit.append(dict(run=path.stem,scalar_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         binary_sha256=manifest['binary_sha256'],junction_entries=len(junctions),
                         arrived=bool(r['ev_response_s'] is not None),background_count=len(loss),input_sha256=inputs))
            rows.append(r)
    finally:process.ROOT=oldroot
    assert seen==expected,(len(seen),len(expected),sorted(expected-seen)[:10])
    assert len({r['binary_sha256'] for r in audit})==1,'Mixed binaries'
    safety=timing_audit(root,accepted_stems=accepted_stems)
    assert safety['passed'],safety['failures'][:10]
    audit[0]['suite_timing_audit']=safety
    # Prevent changes in insertion/completion composition from creating an
    # apparent background benefit. Use common observed IDs at the same horizon.
    # Still disclose original observed and unfinished counts for every run.
    for density in densities:
        for seed in scenario['executed_seeds']:
            group=[r for r in rows if r['density']==density and r['seed']==seed]
            compared=[r for r in group if r['configuration']!='NoPreemptionBaseline']
            common=set.intersection(*(set(background_samples[r['configuration'],density,seed]) for r in compared))
            for r in group:
                sample=background_samples[r['configuration'],density,seed]
                ids=common & sample.keys()
                r['background_matched_count']=len(ids)
                r['background_time_loss_s']=statistics.mean(sample[i] for i in ids) if ids else None
    return rows,audit,scenario


def summarize(rows,configs):
    oldconfigs,oldmetrics=process.ALL_CONFIGS,process.METRICS
    try:
        process.ALL_CONFIGS=configs;process.METRICS={**oldmetrics,**EXTRA}
        return process.summarize(rows)
    finally:process.ALL_CONFIGS=oldconfigs;process.METRICS=oldmetrics


def tune(ordinary,obstruction,out):
    rows=[];evidence=[];candidates=None;source_hashes=None
    for root in (ordinary,obstruction):
        data,audit,scenario=collect(root)
        assert len(data)==90
        assert scenario['phase']=='tuning' and scenario['executed_seeds']==list(range(101,111))
        if source_hashes is not None:assert source_hashes==scenario['source_model_sha256'],'Tuning source differs across contexts'
        source_hashes=scenario['source_model_sha256']
        rows+=data;evidence+=audit;candidates=scenario['tuning_candidates']
    groups={c:[r for r in rows if r['configuration']==c] for c in candidates}
    delivered={c:{(r['context'],r['density'],r['seed']) for r in group if r['ev_response_s'] is not None} for c,group in groups.items()}
    assert len({frozenset(v) for v in delivered.values()})==1,'Held-out delivery sets differ; diagnose before selecting'
    scores=[]
    for c,group in groups.items():
        valid=[r for r in group if r['ev_response_s'] is not None]
        assert valid
        # All cells count equally; report every valid cell and every scheduled case.
        scores.append(dict(candidate=c,scheduled=len(group),arrivals=len(valid),
                           mean_response_s=statistics.mean(r['ev_response_s'] for r in valid),
                           mean_route_changes=statistics.mean(r['route_changes'] or 0 for r in valid)))
    best=min(s['mean_response_s'] for s in scores)
    tied=[s for s in scores if s['mean_response_s']<=best+.5]
    chosen=min(tied,key=lambda s:(s['mean_route_changes'],s['candidate']!='MistTuningReference',s['mean_response_s']))
    selection=dict(training_seeds=list(range(101,111)),reported_seeds_used_for_selection=[],
        candidate=chosen['candidate'],settings=candidates[chosen['candidate']],scores=scores,
        selection_rule='Smallest mean response; within 0.5 s prefer fewer reroutes then reference.',
        binary_sha256=evidence[0]['binary_sha256'],input_roots=[str(ordinary),str(obstruction)])
    selection['source_model_sha256']=source_hashes
    out.mkdir(parents=True,exist_ok=True)
    process.write_csv(out/'held_out_runs.csv',rows);process.write_csv(out/'held_out_scores.csv',scores)
    (out/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    (out/'held_out_audit.json').write_text(json.dumps(dict(passed=True,runs=len(rows),evidence=evidence),indent=2)+'\n')
    print(json.dumps(selection,indent=2))


def comparisons(rows):
    metrics=['route_decision_ms','ev_response_s','traffic_light_wait_s',*EXTRA]
    definitions=[('original_policy','MistDynamicFogFallback','FogCloudAStar'),
                 ('matched_policy','MistDynamicFogFallback','FogCloudAStarAdvance'),
                 ('fog_signal_policy','FogCloudAStarAdvance','FogCloudAStar'),
                 ('static_mist_signal_policy','MistAStarAdvance','MistAStar'),
                 ('matched_static_routing','MistDynamicFogFallback','MistAStarAdvance')]
    result=[]
    for label,a,b in definitions:
        paired=process.paired_comparisons(rows,[(a,b,metrics)])
        for r in paired:
            r['comparison']=label
            r['percent_change']=100*(r['mean_A']-r['mean_B'])/r['mean_B'] if r['mean_B'] else None
        result+=paired
    return result


def draw(summary,context,folder):
    metrics={**process.METRICS,**EXTRA};configs=REPORTED
    colors={**process.CONFIG_COLORS,'FogCloudAStarAdvance':'#305c8d','MistAStarAdvance':'#236b45'}
    folder.mkdir(parents=True,exist_ok=True)
    for metric,(label,unit) in metrics.items():
        for density in ('low','medium','high'):
            group=[r for r in summary if r['metric']==metric and r['density']==density]
            if not group:continue
            fig,ax=plt.subplots(figsize=(10,5))
            for i,r in enumerate(group):
                mean=r['mean'];lo=r['ci95_lower'];hi=r['ci95_upper']
                ax.bar(i,mean,yerr=[[max(0,mean-lo)],[max(0,hi-mean)]],capsize=4,color=colors[r['configuration']])
                ax.annotate(f"{mean:.3f}\nn={r['n']}",(i,max(mean,hi)),xytext=(0,4),textcoords='offset points',ha='center',fontsize=8)
            names={'FogCloudAStar':'Fog reactive','MistAStar':'Mist reactive','MistDynamicAStar':'Dynamic Mist',
                   'MistDynamicFogFallback':'Proposed','FogCloudAStarAdvance':'Fog advance','MistAStarAdvance':'Mist advance',
                   'NoPreemptionBaseline':'No preemption'}
            ax.set_xticks(range(len(group)),[names[r['configuration']] for r in group],rotation=15)
            ax.set_title(f'{label} — {context}, {density} [95% CI]');ax.set_ylabel(unit)
            bottom,top=ax.get_ylim();ax.set_ylim(min(0,bottom),top*1.25 if top else 1)
            ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(folder/f'{metric}-{density}.png',dpi=140);plt.close(fig)


def report(ordinary,obstruction,out):
    allrows=[];allaudit=[];allpairs=[];allsummaries=[]
    out.mkdir(parents=True,exist_ok=True)
    for root in (ordinary,obstruction):
        rows,audit,scenario=collect(root);context=scenario['context']
        assert scenario['phase']=='report' and scenario['executed_seeds']==list(range(1,31))
        assert len(rows)==(630 if context=='ordinary' else 540)
        summary=summarize(rows,scenario['configurations']);pairs=comparisons(rows)
        for r in summary:r['context']=context
        for r in pairs:r['context']=context
        process.write_csv(out/context/'individual_runs.csv',rows)
        process.write_csv(out/context/'summary.csv',summary)
        plot_rows=[]
        for item in summary:
            method=('Wilson score' if item['metric'] in ('pdr','fallback_triggered') else
                    'Bootstrap percentile' if item['metric'] in ('traffic_light_wait_s','ev_delay_vs_freeflow_s') else 'Student-t')
            plot_rows.append({**item,'unit':({**process.METRICS,**EXTRA})[item['metric']][1],'ci_method':method})
        process.write_csv(out/context/'graph_plot_data.csv',plot_rows)
        process.write_csv(out/context/'paired_comparisons.csv',pairs)
        cohort_summaries=[];cohort_pairs=[]
        for condition in ('normal','controlled_stall'):
            cohort=[r for r in rows if r['scenario_condition']==condition]
            stats=summarize(cohort,scenario['configurations']);paired=comparisons(cohort)
            for r in stats:r.update(context=context,scenario_condition=condition)
            for r in paired:r.update(context=context,scenario_condition=condition)
            cohort_summaries+=stats;cohort_pairs+=paired
        process.write_csv(out/context/'summary_cohorts.csv',cohort_summaries)
        process.write_csv(out/context/'paired_cohorts.csv',cohort_pairs)
        draw(summary,context,out/context/'graphs')
        allrows+=rows;allaudit+=audit;allpairs+=pairs;allsummaries+=summary
    process.write_csv(out/'individual_runs.csv',allrows);process.write_csv(out/'paired_comparisons.csv',allpairs)
    (out/'audit.json').write_text(json.dumps(dict(passed=True,runs=len(allrows),graphs=len(list(out.glob('*/graphs/*.png'))),evidence=allaudit,
                    scope='Completeness, raw precision, input hashes, signal and stop metric reconciliation; no effect-size gate.'),indent=2)+'\n')
    lines=['# Matched signal-policy results','','This study compares Fog and Cloud route planning with local Mist route planning and a Fog fallback. SUMO moves the vehicles and controls safe driving. OMNeT++ and Veins carry the emergency message through roadside units and vehicles. After the EV receives the message, the selected framework plans a route and requests safe signal priority. Dynamic Mist reviews received road information as the EV travels. A 500 ms watchdog requests Fog when initial Mist work is unfinished. The 900 ms worker stalls are controlled injected faults, not naturally observed failures.','','Low, medium and high demand use 72, 144 and 200 scheduled background trips. Every configuration shares the same trips and EV speed cap for each matched seed. All 30 reported seeds are retained. Ordinary traffic and the existing physical obstruction are separate experiments.','','Preserved original-policy comparisons and fair advance-policy controls. Negative changes favor proposed for latency, response, stops and delay; positive changes favor proposed for green share and speed. Difference intervals are proposed minus baseline. Time metrics use available delivered pairs.','','## Supervisor requirements A–D, matched advance policy','','FogCloudAStarAdvance uses exactly the same 250 m / 20 s request policy as proposed. The two-step policy ablations are retained in paired_comparisons.csv.','','| Context | Density | Requirement / metric | Baseline | Proposed | Change % | Paired difference 95% CI | Pairs |','| --- | --- | --- | ---: | ---: | ---: | --- | ---: |']
    requirements={'route_decision_ms':'A: decision ms','ev_response_s':'B: response s',
                  'traffic_light_wait_s':'D: signal waiting s','ev_full_stops':'C: full stops',
                  'ev_green_approach_fraction':'C: green approach share','background_time_loss_s':'C: background time loss s'}
    for r in allpairs:
        if r['comparison']!='matched_policy' or r['metric'] not in requirements:continue
        change=f"{r['percent_change']:.2f}" if r['percent_change'] is not None else 'undefined (baseline zero)'
        lines.append(f"| {r['context']} | {r['density']} | {requirements[r['metric']]} | {r['mean_B']:.3f} | {r['mean_A']:.3f} | {change} | [{r['ci95_lower']:.3f}, {r['ci95_upper']:.3f}] | {r['n_pairs']} |")
    lines += ['', '## Separate the signal policy and framework effects', '',
              'The original comparison changes both the framework and signal request timing. The matched comparison holds request timing equal. Fog advance versus Fog reactive isolates the signal policy within Fog routing; Mist advance versus Mist reactive does the same within static Mist. Framework differences also include initial computation and controlled fallback, so matched results are not claimed as routing alone. All other measured contrasts are in paired_comparisons.csv.', '',
              '| Context | Density | Comparison | Baseline response s | Comparison response s | Change % | Paired difference 95% CI s | Pairs |',
              '| --- | --- | --- | ---: | ---: | ---: | --- | ---: |']
    comparison_names={'original_policy':'Proposed versus Fog reactive',
                      'matched_policy':'Proposed versus Fog advance',
                      'fog_signal_policy':'Fog advance versus Fog reactive',
                      'static_mist_signal_policy':'Mist advance versus Mist reactive',
                      'matched_static_routing':'Proposed versus Mist advance'}
    for r in allpairs:
        if r['metric']!='ev_response_s':continue
        change=f"{r['percent_change']:.2f}" if r['percent_change'] is not None else 'undefined'
        lines.append(f"| {r['context']} | {r['density']} | {comparison_names[r['comparison']]} | {r['mean_B']:.3f} | {r['mean_A']:.3f} | {change} | [{r['ci95_lower']:.3f}, {r['ci95_upper']:.3f}] | {r['n_pairs']} |")
    primary=('pdr','nrl','throughput_bps','e2e_delay_ms','route_decision_ms','ev_response_s','traffic_light_wait_s')
    lines += ['', '## Seven primary metrics', '',
              'Cells show the measured mean and sample count. Their 95% intervals are in summary.csv and every graph. PDR and EM throughput describe the shared alert service, which acts before routing. One delivered 256 byte EM contributes 2048 / 900 = 2.27556 bit/s; equal throughput among delivered runs is expected under this definition. No-preemption is displayed only on the signal waiting graph.', '']
    summary_index={(r['context'],r['density'],r['configuration'],r['metric']):r for r in allsummaries}
    for context in ('ordinary','obstruction'):
        for density in ('low','medium','high'):
            lines += [f'### {context} {density}', '',
                      '| Configuration | PDR | NRL | EM throughput bit/s | EM E2E ms | Decision ms | Response s | Signal wait s |',
                      '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
            for config in REPORTED:
                if config=='NoPreemptionBaseline':continue
                cells=[config]
                for metric in primary:
                    item=summary_index.get((context,density,config,metric))
                    cells.append(f"{item['mean']:.3f} (n={item['n']})" if item else 'not observed')
                lines.append('| '+' | '.join(cells)+' |')
            lines.append('')
    lines+=['','## Interpretation and limits','','A: only an interval below zero supports faster decisions. B: compare the measured size with the requested substantial margin; ordinary physical limits remain. C: full stops, green passage and background time loss are distinct operational measures, but none is guaranteed to improve. D: zero waiting is retained when observed; no artificial stop is inserted. Whole-route slow time detects crawling hidden by the 20 m / 0.1 m/s waiting definition. Green classification is sampled within 500 ms and cannot prove the exact continuous crossing instant. Controlled 900 ms stalls remain injected faults. Ordinary and obstruction results are not pooled.','','Full new graphs and CSVs are in results/policy_validation/. Earlier main results and the previous Word submission are retained as historical results, not overwritten or presented as the new policy experiment.']
    selection=scenario['selection']
    lines += ['', '## Held-out tuning outcome', '',
              f"The fixed rule selected {selection['candidate']}. Only seeds 101–110 were used. Each candidate has 60 scheduled density/context/seed cells; response means use the same delivered cells. No reported seed was used for selection. The selected settings and model-source/binary hashes were frozen before reported runs.", '',
              '| Candidate | Scheduled | Arrivals | Mean response s | Mean applied route changes |',
              '| --- | ---: | ---: | ---: | ---: |']
    for score in selection['scores']:
        lines.append(f"| {score['candidate']} | {score['scheduled']} | {score['arrivals']} | {score['mean_response_s']:.3f} | {score['mean_route_changes']:.3f} |")
    if selection['candidate']=='MistTuningReference':
        lines += ['', 'The tested tuning alternatives did not improve held-out response. The reference was retained; this experiment does not claim a new routing improvement from those alternatives.']
    lines += ['', '## Signal waiting and whole-route motion', '',
              'Means below use delivered runs. Near-signal slow time uses speed below 1 m/s within the same 20 m signal zone. The scheduled-start stop count localizes stop onsets on A0A1 within 0.2 m of the shared 30 m stop. Other stops are not automatically attributed to signals. All durations retain the 500 ms SUMO state resolution.', '',
              '| Context | Density | Configuration | Arrivals | Zero signal waits | Signal wait s | Whole-route below 1 m/s s | Near-signal below 1 m/s s | Full stops | Stops at scheduled start | Green on approach share |',
              '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for context in ('ordinary','obstruction'):
        for density in ('low','medium','high'):
            for config in ('FogCloudAStarAdvance','MistDynamicFogFallback'):
                group=[r for r in allrows if r['context']==context and r['density']==density and r['configuration']==config and r['ev_response_s'] is not None]
                mean=lambda field:statistics.mean(r[field] for r in group)
                lines.append(f"| {context} | {density} | {config} | {len(group)} | {sum(r['traffic_light_wait_s']==0 for r in group)} | {mean('traffic_light_wait_s'):.3f} | {mean('ev_below_1_s'):.3f} | {mean('ev_near_signal_below_1_s'):.3f} | {mean('ev_full_stops'):.3f} | {mean('ev_full_stops_at_scheduled_start'):.3f} | {mean('ev_green_approach_fraction'):.3f} |")
    incident_rows=[r for r in allrows if r['context']=='obstruction']
    lines += ['', '## Physical obstruction realization', '',
              f"FCD records at least one physically stopped incident vehicle during 90–250 s in {sum(r['incident_maximum_stopped']>0 for r in incident_rows)}/{len(incident_rows)} assigned obstruction runs. No seed is dropped for weaker realized exposure. Per-run insertion and maximum queue counts are exported.", '',
              '| Configuration | Density | Runs | Any stopped blocker | All three stopped together |', '| --- | --- | ---: | ---: | ---: |']
    for c in REPORTED:
        if c=='NoPreemptionBaseline':continue
        for density in ('low','medium','high'):
            group=[r for r in incident_rows if r['configuration']==c and r['density']==density]
            lines.append(f"| {c} | {density} | {len(group)} | {sum(r['incident_maximum_stopped']>0 for r in group)} | {sum(r['incident_maximum_stopped']==3 for r in group)} |")
    lines += ['', '## Measured requirement verdicts', '',
              'The previously requested 20% margin is shown as a reference for B, not a data-acceptance gate. C requires at least two supported improvements among full stops, green share and background time loss. D distinguishes lower waiting from the requested nonzero waiting.', '',
              '| Context | Density | A: decision | B: at least 20% response reduction | C: two distinct supported metric wins | D: lower and positive signal waiting |',
              '| --- | --- | --- | --- | --- | --- |']
    for context in ('ordinary','obstruction'):
        for density in ('low','medium','high'):
            group={r['metric']:r for r in allpairs if r['context']==context and r['density']==density and r['comparison']=='matched_policy'}
            a,b,d=group['route_decision_ms'],group['ev_response_s'],group['traffic_light_wait_s']
            wins=[m for m in ('ev_full_stops','ev_green_approach_fraction','background_time_loss_s')
                  if (group[m]['ci95_lower']>0 if m=='ev_green_approach_fraction' else group[m]['ci95_upper']<0)]
            av='Met' if a['ci95_upper']<0 else 'Not established'
            bv='Met' if b['percent_change'] is not None and b['percent_change']<=-20 and b['ci95_upper']<0 else 'Not met'
            cv=('Met' if len(wins)>=2 else 'Not met')+f' ({len(wins)}/3)'
            dv='Met' if d['mean_A']>0 and d['ci95_upper']<0 else ('Zero retained; nonzero request not met' if d['mean_A']==0 else 'Improvement not established')
            lines.append(f'| {context} | {density} | {av} | {bv} | {cv} | {dv} |')
    lines += ['', '## All new comparison graphs', '',
              'Each figure uses the same raw-to-summary pipeline. No-preemption appears only for traffic-light waiting. Original and matched policy labels are visible on the axes.', '']
    metric_order={metric:index for index,metric in enumerate((*primary,*[m for m in {**process.METRICS,**EXTRA} if m not in primary]))}
    for graph in sorted(out.glob('*/graphs/*.png'),key=lambda p:(p.parent.parent.name!='ordinary',metric_order.get(p.stem.rsplit('-',1)[0],999),('low','medium','high').index(p.stem.rsplit('-',1)[1]))):
        relative=graph.relative_to(ROOT).as_posix()
        lines += [f'### {graph.parent.parent.name}: {graph.stem}', '', f'![{graph.stem}](../{relative})', '']
    (ROOT/'docs/POLICY_VALIDATION.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'artifacts/policy_validation').mkdir(parents=True,exist_ok=True)
    (ROOT/'artifacts/policy_validation/workspaces.json').write_text(json.dumps(dict(ordinary=str(ordinary),obstruction=str(obstruction)),indent=2)+'\n')
    for name in ('METHODOLOGY.md','VERIFICATION.md','PROGRESS.md','CLIENT_BASELINE_COMPARISON.md','CLIENT_20_PERCENT_FEASIBILITY.md'):
        path=ROOT/'docs'/name;original=path.read_text(encoding='utf-8')
        banner='> Retained original-policy experiment. See [POLICY_VALIDATION.md](POLICY_VALIDATION.md) for the new matched-policy results and unmet requirements.\n\n'
        original=original.removeprefix(banner)
        marker='\n## Matched-policy extension (2026-10-10)\n'
        original=original.split(marker)[0]
        note=(marker+'\nThe new isolated experiment contains 630 ordinary and 540 obstruction runs, plus 180 held-out candidate runs on seeds 101–110. '
              'Previous tables in this file describe the retained original-policy experiment. New matched-policy estimates and explicit unmet requirements are in [POLICY_VALIDATION.md](POLICY_VALIDATION.md). '
              'The fixed design is in [POLICY_EXPERIMENT_PLAN.md](POLICY_EXPERIMENT_PLAN.md); the prior timing and zero-wait diagnosis is in [DIAGNOSIS.md](DIAGNOSIS.md). '
              'The selected settings are frozen in results/policy_validation/selection.json. No artificial waiting or outcome gate is used.\n')
        path.write_text(banner+original+note,encoding='utf-8')
    methodology=ROOT/'docs/METHODOLOGY.md'
    with methodology.open('a',encoding='utf-8') as handle:
        handle.write('\nNew metric definitions: full stops are below-0.1 m/s episodes after reaching 1 m/s, with recovery to 1 m/s required between stops. '
                     'Whole-route slow time integrates below-1 m/s samples from navigation release, excluding the initial hold and including the shared scheduled 30 m stop. '
                     'Green crossing share counts the prior approach link lamp in the phase observed at first entry sample, divided by observed signal entries; the exact crossing is only resolved to 500 ms. '
                     'Green approach share instead records the lamp on first entry within 20 m of the next TLS on each external edge visit; a red arrival followed by a green crossing stays a red arrival. '
                     'Crossing on green can be common to every configuration because all respect red-light safety; it does not establish an unstopped green arrival. '
                     'Background time loss uses SUMO tripinfo at 900 s, including unfinished observed trips, restricted to common background IDs within each seed/context across preempting configurations. '
                     'Observed, matched and unfinished background counts are exported to disclose censoring. '
                     'Mean EV speed is distance divided by travel time and is secondary, not counted as independent evidence for C. '
                     'New continuous metric intervals use the existing Student-t implementation; zero-inflated signal waiting retains bootstrap intervals. '
                     'Matched difference intervals are paired Student-t, exploratory and unadjusted for multiple testing. Normal and controlled-stall cohort summaries and pairs are exported separately.\n')
    readme=ROOT/'README.md'
    text=readme.read_text(encoding='utf-8')
    text=text.replace('Earlier results below remain historical until the new full matrix is processed.',
                      'The new complete matched-policy results and all new graphs are in [POLICY_VALIDATION.md](docs/POLICY_VALIDATION.md). Earlier results below remain historical.')
    readme.write_text(text,encoding='utf-8')
    feasibility=ROOT/'docs/CLIENT_20_PERCENT_FEASIBILITY.md'
    from client_response_target import optimistic_route_distance
    bound=optimistic_route_distance(ROOT/'simulations/grid/grid.net.xml','A0A1','D2D3')/13.9
    extra=['','### Updated bound against the matched advance-policy baseline','','| Context | Density | Matched baseline s | Optimistic bound s | Maximum theoretically possible reduction % | 20% target below bound |','| --- | --- | ---: | ---: | ---: | --- |']
    for r in allpairs:
        if r['comparison']=='matched_policy' and r['metric']=='ev_response_s':
            extra.append(f"| {r['context']} | {r['density']} | {r['mean_B']:.3f} | {bound:.3f} | {100*(r['mean_B']-bound)/r['mean_B']:.2f} | {'Yes' if .8*r['mean_B']<bound else 'No'} |")
    extra+=['','This bound remains optimistic and excludes the common scheduled start stop, junctions, acceleration and communication. It is not an achievable performance prediction.']
    with feasibility.open('a',encoding='utf-8') as handle:handle.write('\n'.join(extra)+'\n')
    print(f'Processed and audited {len(allrows)} reported runs without outcome gating.')


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('phase',choices=('tune','report'))
    p.add_argument('--ordinary',type=Path,required=True);p.add_argument('--obstruction',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'results/policy_validation')
    a=p.parse_args();(tune if a.phase=='tune' else report)(a.ordinary,a.obstruction,a.output)


if __name__=='__main__':main()
