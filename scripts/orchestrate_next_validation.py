"""Resume the predeclared experiment, freeze pilot scope, then audit results."""
import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
sys.path.insert(0,str(ROOT/'scripts'))
import next_validation as analysis
import run_batch as batch

NATIVE=Path(r'\\wsl.localhost\opp_env\home\opp_env')
SOURCE='/home/opp_env/next_source_20261011'
OUTPUT=ROOT/'results/next_validation'
ARTIFACTS=ROOT/'artifacts/next_validation'
ARTIFACTS.mkdir(parents=True,exist_ok=True)
STATUS=ARTIFACTS/'status.json'

def status(phase,**kwargs):
    value=dict(phase=phase,checked_at=datetime.now().astimezone().isoformat(),**kwargs)
    temporary=STATUS.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(STATUS)
    print(phase,kwargs,flush=True)

def run(command,log):
    with (ARTIFACTS/log).open('a') as handle:
        result=subprocess.run(command,cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(f'Command failed; see {ARTIFACTS/log}')

def completed(root,expected):
    return (root/'execution.json').exists() and len(list((root/'results/raw').glob('*.vci')))==expected

def launch(folder,context,phase,seeds,densities,configs,window=360,jobs=24):
    root=NATIVE/folder
    expected=len(seeds)*len(densities)*len(configs)
    if completed(root,expected):return root
    command=['wsl','-d','opp_env','--','bash',SOURCE+'/scripts/run_batch_env.sh','--next-validation',
        '--workspace','/home/opp_env/'+folder,'--context',context,'--phase',phase,
        '--seeds',*map(str,seeds),'--densities',*densities,'--configs',*configs,'--demand-end',str(window),'--jobs',str(jobs)]
    if root.exists():command.append('--resume')
    run(command,folder+'.log')
    assert completed(root,expected)
    return root

def amend(text):
    path=ROOT/'docs/NEXT_PLAN.md'
    with path.open('a',encoding='utf-8') as handle:
        handle.write('\n## Measured scheduling amendment '+datetime.now().astimezone().isoformat()+'\n\n'+text+'\n')
    shutil.copy2(path,NATIVE/'next_source_20261011/docs/NEXT_PLAN.md')

def main():
    import msvcrt
    with (ARTIFACTS/'orchestrator.lock').open('a+') as lock:
        lock.seek(0);lock.write('0');lock.flush();lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        started_file=ARTIFACTS/'started.json'
        if not started_file.exists():started_file.write_text(json.dumps(dict(started_at=time.time(),deadline_hours=24),indent=2)+'\n')
        started=json.loads(started_file.read_text())['started_at']
        reg=analysis.regression(NATIVE/'next_regression_20261011',NATIVE/'policy_tuning_ordinary_20261010')
        (ARTIFACTS/'regression.json').write_text(json.dumps(reg,indent=2)+'\n')
        decision_file=ARTIFACTS/'decision.json'
        if not decision_file.exists():
            scores=[]
            for window in (360,120,60):
                folder=f'next_pilot_{window}_20261011'
                root=NATIVE/folder
                # The initial pilot may already be running in the interactive session.
                if window==360 and root.exists() and not (root/'execution.json').exists():
                    while not completed(root,60):
                        status('demand_pilot',window_s=window,completed=len(list((root/'results/raw').glob('*.vci'))),expected=60)
                        time.sleep(30)
                else:
                    status('demand_pilot',window_s=window,expected=60)
                    root=launch(folder,'dense','pilot',list(range(101,111)),['heavy400','heavy600'],
                        [analysis.BASELINE,analysis.PROPOSED,analysis.DYNAMIC],window,20)
                analysis.archive_vectors(root)
                status('processing_pilot',window_s=window)
                analysis.pilot(root,OUTPUT/f'pilot_{window}')
                score=json.loads((OUTPUT/f'pilot_{window}/pilot_audit.json').read_text())
                scores.append(score)
                if score['congestion_qualified']:break
                elapsed=(time.time()-started)/3600
                if elapsed>6:
                    amend(f'Pilot elapsed {elapsed:.2f} h. Further demand escalation omitted to preserve runtime; congestion qualification remains unmet.')
                    break
            latest=scores[-1]
            # Use measured total pilot wall time at only 20 active simulations,
            # with a reserve; do not assume ideal scaling to 96 workers.
            heavy_hours=latest['execution']['wall_seconds']/3600/60*480
            other_hours=(240+180)/5.2/60
            elapsed=(time.time()-started)/3600
            estimate=elapsed+1.25*(heavy_hours+other_hours)+2
            densities=['heavy400','heavy600'];ablation=['low','medium','high'];reductions=[]
            if estimate>24:
                densities=['heavy600'];reductions.append('400-trip reported cell omitted; every retained cell keeps all 30 seeds')
                estimate-=1.25*heavy_hours/2
            if estimate>24:
                ablation=['high'];reductions.append('Historical ablation reduced to high density in both contexts; all 30 seeds retained')
                estimate-=1.25*120/5.2/60
            decision=dict(window_s=latest['departure_end_s'],congestion_qualified=latest['congestion_qualified'],
                pilot_windows=[s['departure_end_s'] for s in scores],pilot_response_rise_s=latest['paired_response_rise_s'],
                reported_densities=densities,ablation_densities=ablation,estimated_total_hours=estimate,
                pilot_elapsed_hours=elapsed,reductions=reductions,optional_cost_adopted=False,
                pilot_timing=[dict(window_s=s['departure_end_s'],wall_seconds=s['execution']['wall_seconds'],
                    timed_runs=s['execution'].get('timed_runs',0),
                    measured_active_process_seconds=s['execution'].get('active_process_seconds'),
                    active_process_seconds_upper_bound=s['execution']['wall_seconds']*20) for s in scores],
                source_binary_sha256=__import__('hashlib').sha256((NATIVE/'next_source_20261011/src/out/clang-release/libsrc.so').read_bytes()).hexdigest())
            amend('Frozen before reported runs: '+json.dumps(decision,sort_keys=True)+'. No reported seed used for selection; no outcome acceptance gate.')
            decision_file.write_text(json.dumps(decision,indent=2)+'\n')
        decision=json.loads(decision_file.read_text())
        if decision['estimated_total_hours']>24:
            status('runtime_budget_exceeded',decision=decision,reason='Even reduced cells exceed 24 h; no reported matrix launched')
            return
        definitions=[('dense','next_report_dense_20261011',decision['reported_densities'],list(batch.NEXT_CONFIGS),decision['window_s'],36),
            ('random_incident','next_report_random_20261011',['high'],list(batch.NEXT_CONFIGS),360,24),
            ('ordinary_ablation','next_report_ordinary_ablation_20261011',decision['ablation_densities'],[analysis.DYNAMIC],360,12),
            ('fixed_ablation','next_report_fixed_ablation_20261011',decision['ablation_densities'],[analysis.DYNAMIC],360,12)]
        expected=sum(len(d)*len(c)*30 for _,_,d,c,_,_ in definitions)
        status('reported_matrices',expected_new_runs=expected,decision=decision)
        def report_matrix(spec):
            context,folder,densities,configs,window,jobs=spec
            return context,str(launch(folder,context,'report',list(range(1,31)),densities,configs,window,jobs))
        with ThreadPoolExecutor(max_workers=4) as pool:
            workspaces=dict(pool.map(report_matrix,definitions))
        manifest=dict(native_root=str(NATIVE),workspaces=workspaces,decision=decision,regression=reg,
                      started_at=started,reported_finished_at=time.time())
        (ARTIFACTS/'workspaces.json').write_text(json.dumps(manifest,indent=2)+'\n')
        status('processing_reported_results',expected_new_runs=expected)
        run([sys.executable,'analysis/next_validation.py','report','--manifest',str(ARTIFACTS/'workspaces.json'),
             '--output',str(OUTPUT)],'processing.log')
        status('running_tests')
        run([sys.executable,'-m','unittest','discover','-s','tests','-v'],'all_tests.log')
        run(['wsl','-d','opp_env','--','bash','/mnt/d/Codex/EmergencyNavigation/scripts/test_routing.sh'],'routing_tests.log')
        run([sys.executable,'scripts/audit_batch.py'],'historical_audit.log')
        status('awaiting_word_verification',reported_runs=expected,simulation_and_analysis_hours=(time.time()-started)/3600,
               report='docs/NEXT_RESULTS.md',summary='docs/SUPERVISOR_SUMMARY.md',
               reason='Word authoring/rendering requires approved document runtime and visual review')

if __name__=='__main__':
    try:main()
    except Exception as error:
        status('needs_diagnosis',error=str(error))
        raise
