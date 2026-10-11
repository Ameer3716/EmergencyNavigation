"""Isolated matched signal-policy and held-out tuning experiments."""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import run_batch as batch
from run_congestion_validation import prepare

TUNING = {
    'MistTuningReference': dict(review_s=5, improvement=.10, slow_improvement=.05, gap_s=30),
    'MistTuningFast': dict(review_s=2, improvement=.05, slow_improvement=.05, gap_s=10),
    'MistTuningBalanced': dict(review_s=3, improvement=.08, slow_improvement=.05, gap_s=20),
}
REPORTED = batch.POLICY_CONFIGS


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--context', choices=('ordinary','obstruction'),required=True)
    parser.add_argument('--phase', choices=('tuning','report'),required=True)
    parser.add_argument('--selection', type=Path)
    parser.add_argument('--jobs',type=int,default=6)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    destination=args.workspace.resolve()
    # An entire workspace has one writer. Independent suites may run together,
    # while a second launcher waits and reuses only a complete identical matrix.
    import fcntl
    lock=(destination.parent/f'.{destination.name}.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX)
    seeds=list(range(101,111)) if args.phase=='tuning' else list(range(1,31))
    configs=tuple(TUNING) if args.phase=='tuning' else tuple(c for c in REPORTED if args.context=='ordinary' or c!='NoPreemptionBaseline')
    if destination.exists() and not args.resume:
        prior=json.loads((destination/'scenario.json').read_text())
        assert prior['phase']==args.phase and prior['context']==args.context
        assert prior['executed_seeds']==seeds and prior['configurations']==list(configs)
        expected=[destination/f'results/raw/{c}-{d}-seed{s}.{ext}' for c in configs
                  for d in ('low','medium','high') for s in seeds for ext in ('sca','vec','vci')]
        if all(p.exists() and p.stat().st_size for p in expected):
            print(f'Reuse complete identical matrix: {destination}',flush=True)
            return
        raise SystemExit('Workspace incomplete; explicitly resume after diagnosing the prior writer')
    if not args.resume:prepare(batch.ROOT,destination,with_incident=args.context=='obstruction')
    scenario=json.loads((destination/'scenario.json').read_text())
    selected=None
    if args.phase=='report':
        if not args.selection:parser.error('Reported runs require frozen held-out selection')
        selected=json.loads(args.selection.read_text())
        assert selected['training_seeds']==list(range(101,111))
        assert selected['reported_seeds_used_for_selection']==[]
    scenario.update(phase=args.phase,context=args.context,executed_seeds=seeds,configurations=configs,execution_jobs=args.jobs,
                    expected_runs=3*len(seeds)*len(configs),tuning_candidates=TUNING,
                    selection=selected,acceptance='Completeness, inputs and model validity only; never effect size.',
                    metrics='500 ms SUMO states, 100 ms accumulator; route release excludes initial hold from slow metrics.')
    (destination/'scenario.json').write_text(json.dumps(scenario,indent=2)+'\n')
    ini=destination/'simulations/grid/omnetpp.ini'
    if not args.resume:
        with ini.open('a') as handle:
            for config,settings in TUNING.items():
                handle.write(f'\n[Config {config}]\nextends = MistDynamicFogFallback\n')
                for param,value in settings_lines(settings):handle.write(f'*.node[*].appl.{param} = {value}\n')
    original_ini=batch.one_omnet_config
    def configured(directory,config,density,seed,logs,limit):
        original_ini(directory,config,density,seed,logs,limit)
        if config=='MistDynamicFogFallback' and selected:
            with (directory/'omnetpp.ini').open('a') as handle:
                for param,value in settings_lines(selected['settings']):handle.write(f'*.node[*].appl.{param} = {value}\n')
    original_sumo=batch.one_sumo_config
    def evidence(directory,route_name,seed,summary_path=None):
        original_sumo(directory,route_name,seed,summary_path)
        if summary_path:
            path=directory/'grid.sumocfg';tree=ET.parse(path);output=tree.getroot().find('output')
            ET.SubElement(output,'tripinfo-output',value=str(summary_path).replace('sumo-summary-','tripinfo-'))
            ET.SubElement(output,'tripinfo-output.write-unfinished',value='true')
            if args.context=='obstruction':
                ET.SubElement(output,'fcd-output',value=str(summary_path).replace('sumo-summary-','incident-fcd-'))
                ET.SubElement(output,'device.fcd.probability',value='0')
            tree.write(path,encoding='utf-8',xml_declaration=True)
    batch.one_omnet_config=configured;batch.one_sumo_config=evidence
    batch.ROOT=destination;batch.GRID=destination/'simulations/grid';batch.CONFIGS=configs
    sys.argv=[sys.argv[0],'--seeds',*map(str,seeds),'--configs',*configs,'--jobs',str(args.jobs),
              '--artifact-root',str(destination),'--sim-time-limit','900','--resume-incomplete']
    batch.main()


def settings_lines(s):
    return [('dynamicUpdateInterval',f"{s['review_s']}s"),('minimumRouteImprovement',str(s['improvement'])),
            ('slowRouteImprovement',str(s['slow_improvement'])),('minimumRerouteGap',f"{s['gap_s']}s")]


if __name__=='__main__':main()
