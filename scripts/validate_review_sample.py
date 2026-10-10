#!/usr/bin/env python3
"""Validate an isolated real simulation sample before the matched experiment."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from process_results import one_run, events, write_csv

CONFIGS = ('FogCloudAStar','MistAStar','MistDynamicAStar','MistDynamicFogFallback','NoPreemptionBaseline')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifact-root', type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    import process_results
    process_results.ROOT = root
    result, checks = [], []
    for density in ('low','medium','high'):
        for seed in (1,4):
            for cfg in CONFIGS:
                stem = f'{cfg}-{density}-seed{seed}'
                scalar = root / 'results/raw' / (stem+'.sca')
                if not scalar.exists():
                    raise SystemExit(f'Sample not complete: {stem}')
                row = one_run(cfg, scalar, density, seed, root / 'artifacts/logs/batch' / ('emergency-'+stem+'.csv'))
                result.append(row)
                content = scalar.read_text(encoding='utf-8')
                checks.append(all(x in content for x in ('config *.node[*].appl.telemetryValidationDelay 0ms','config *.node[*].appl.watchdogThreshold 500ms','config *.metrics.pollInterval 100ms')))
                checks.append(row['delivered_messages'] == 0 or row['arrival_confirmed'] == 1)
    lookup = {(r['configuration'],r['density'],r['seed']):r for r in result}
    evidence = {}
    for density in ('low','medium','high'):
        normal = lookup['MistDynamicFogFallback',density,1]
        stall = lookup['MistDynamicFogFallback',density,4]
        no_backup = lookup['MistDynamicAStar',density,4]
        checks += [normal['fallback_triggered'] == 0, stall['fallback_triggered'] == 1,
                   stall['route_decision_ms'] < no_backup['route_decision_ms']]
        fb = events(root / 'artifacts/logs/batch' / f'fallback-MistDynamicFogFallback-{density}-seed4.csv')
        checks.append(fb[0]['fallbackReason'] == 'controlled_stall_timeout')
        priority = [lookup['FogCloudAStar',density,s]['traffic_light_wait_s'] for s in (1,4)]
        control = [lookup['NoPreemptionBaseline',density,s]['traffic_light_wait_s'] for s in (1,4)]
        checks.append(sum(priority) < sum(control))
        checks.append(all(lookup['MistDynamicAStar',density,s]['route_reviews'] > 0 for s in (1,4)))
        evidence[density] = {'priority_wait_s':priority,'control_wait_s':control,
                             'normal_mist_decision_ms': normal['route_decision_ms'],
                             'stall_mist_decision_ms':no_backup['route_decision_ms'],
                             'stall_fog_decision_ms':stall['route_decision_ms'],
                             'peak_background': [lookup['MistAStar',density,s]['peak_active_background'] for s in (1,4)]}
    response = [lookup['MistAStar',d,1]['ev_response_s'] for d in ('low','medium','high')]
    checks.append(max(response)-min(response) > .1)
    checks.append(any(r['configuration'] != 'NoPreemptionBaseline' and r['traffic_light_wait_s'] > 0 for r in result))
    output = {'passed':all(checks), 'checks_passed':sum(checks), 'checks_total':len(checks),
              'runs':len(result),'seed1_mist_response_s':response,'evidence':evidence}
    write_csv(root / 'results/processed/individual_runs-sample.csv', result)
    (ROOT / 'artifacts/sample_validation.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output,indent=2))
    if not output['passed']:
        raise SystemExit('Sample validation failed; inspect the measured evidence')


if __name__ == '__main__':
    main()
