import gzip
import importlib.util
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'analysis'))
from run_next_validation import incident_draw, incident_special, network_data, shortest_route
from next_validation import bootstrap, fcd_metrics, paired, summarize, archive_vectors, verify_vectors, fog_review_metrics, frozen_source
from raw_data import events

class NextDesign(unittest.TestCase):
    @unittest.skipUnless(sys.platform=='win32','Windows UNC mapping')
    def test_binary_lookup_uses_frozen_source_not_linux_workspace_symlink(self):
        root=Path(r'\\wsl.localhost\opp_env\home\opp_env\next_pilot_360_20261011')
        expected=Path(r'\\wsl.localhost\opp_env\home\opp_env\next_source_20261011')
        self.assertEqual(frozen_source(root,dict(source_project='/home/opp_env/next_source_20261011')),expected)

    def test_dynamic_fog_keeps_unanswered_requests_and_remote_latency(self):
        route=[dict(action='applied',reason='cloud',location='cloud'),
            dict(action='review_requested',reason='fog_network',location='fog'),
            dict(action='discarded',reason='unanswered_fog_review',location='fog'),
            dict(action='review_requested',reason='fog_network',location='fog'),
            dict(action='evaluated',reason='fog_periodic',location='fog'),
            dict(action='applied',reason='low_speed',location='fog')]
        value=dict(fogRequests=[1,1,1],dynamicFogUnansweredReviews=[1],dynamicFogReplyLatency=[.327])
        self.assertEqual(fog_review_metrics(value,route),dict(fog_requests=3,fog_completed_reviews=1,
            fog_unanswered_reviews=1,route_changes=1,route_reviews=2))
        with self.assertRaises(AssertionError):fog_review_metrics({**value,'dynamicFogReplyLatency':[.01]},route)
        with self.assertRaises(AssertionError):fog_review_metrics(value,route+[dict(action='computed',reason='local',location='mist')])

    def test_incidents_are_deterministic_legal_and_varied(self):
        network=ROOT/'simulations/grid/grid.net.xml'
        _,turns=network_data(network)
        draws=[incident_draw(network,s) for s in range(1,31)]
        self.assertEqual(draws,[incident_draw(network,s) for s in range(1,31)])
        self.assertGreater(len({d['edge'] for d in draws}),1)
        self.assertGreater(len({d['start_s'] for d in draws}),10)
        self.assertEqual({d['vehicles'] for d in draws},{1,2,3})
        for draw in draws:
            self.assertIn(draw['edge'],shortest_route(network)[1:-1])
            self.assertIn(draw['continuation'],turns[draw['edge']])
            self.assertTrue(60<=draw['start_s']<=150)
            with tempfile.TemporaryDirectory() as folder:
                out=Path(folder)/'special.xml'
                incident_special(ROOT/'simulations/grid/special.rou.xml',out,draw)
                vehicles=ET.parse(out).getroot().findall('vehicle')
                self.assertEqual(len(vehicles),2+draw['vehicles'])
                departures=[float(v.get('depart')) for v in vehicles]
                self.assertEqual(departures,sorted(departures))

    def test_bootstrap_retains_zero_and_signed_differences(self):
        self.assertEqual(bootstrap([0]*30),(0.,0.))
        self.assertEqual(bootstrap([-2]*30),(-2.,-2.))
        self.assertEqual(bootstrap([1,4,-3]),bootstrap([1,4,-3]))

    def test_missing_arrival_retained_but_not_given_fake_response(self):
        rows=[]
        for seed in (1,2,3):
            for config in ('FogCloudAStarAdvance','MistDynamicFogFallback','NoPreemptionBaseline'):
                rows.append(dict(seed=seed,density='heavy600',configuration=config,
                    ev_response_s=None if seed==3 else 100 if config=='MistDynamicFogFallback' else 120,
                    pdr=0 if seed==3 else 1,traffic_light_wait_s=1 if config=='MistDynamicFogFallback' else 3))
        stats=summarize(rows)
        self.assertTrue(all(r['metric']=='traffic_light_wait_s' for r in stats if r['configuration']=='NoPreemptionBaseline'))
        delivery=next(r for r in stats if r['configuration']=='MistDynamicFogFallback' and r['metric']=='pdr')
        self.assertEqual(delivery['n'],3)
        comparison=next(p for p in paired(rows,'MistDynamicFogFallback','FogCloudAStarAdvance','test') if p['metric']=='ev_response_s')
        self.assertEqual(comparison['n_pairs'],2)
        self.assertEqual(comparison['paired_difference'],-20)

    def test_vector_archival_preserves_all_evidence_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'results/raw';raw.mkdir(parents=True)
            run=root/'simulations/batch/high-seed1/MistDynamicFogFallback/results';run.mkdir(parents=True)
            logs=root/'artifacts/logs/batch';logs.mkdir(parents=True)
            stem='MistDynamicFogFallback-high-seed1'
            original=b'Vector values with full precision: 0.123456789012345\n'*100
            (raw/f'{stem}.vci').write_bytes(b'index')
            (raw/f'{stem}.vec').write_bytes(original)
            (run/'Batch-#0.vec').write_bytes(original)
            (logs/f'manifest-{stem}.json').write_text('{}')
            archive_vectors(root)
            verify_vectors(root)
            with gzip.open(raw/f'{stem}.vec.gz','rb') as handle:self.assertEqual(handle.read(),original)
            self.assertFalse((run/'Batch-#0.vec').exists())

    def test_fcd_queues_exclude_ev_and_parked_accident(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fcd.xml.gz'
            with gzip.open(path,'wt') as handle:
                handle.write('<fcd-export><timestep time="100">'
                    '<vehicle id="normal0" lane="C1C2_0" speed="0"/>'
                    '<vehicle id="normal1" lane="C1C2_0" speed="0.5"/>'
                    '<vehicle id="ambulance" lane="C1C2_0" speed="0"/>'
                    '<vehicle id="accident" lane="C1C2_0" speed="0"/>'
                    '<vehicle id="incidentQueue0" lane="C1C2_0" speed="0"/>'
                    '</timestep></fcd-export>')
            result=fcd_metrics(path,['C1C2'],dict(edge='C1C2',start_s=90,stop_until_s=250))
            self.assertEqual(result['fcd_max_queue'],2)
            self.assertEqual(result['background_below_1_vehicle_s'],1)
            self.assertEqual(result['incident_max_stopped'],1)

class NextEvidence(unittest.TestCase):
    def test_final_evidence(self):
        path=ROOT/'results/next_validation/audit.json'
        if not path.exists():self.skipTest('Next experiment is in progress')
        value=json.loads(path.read_text())
        self.assertTrue(value['passed'])
        for matrix in value['matrices']:
            self.assertEqual(matrix['seeds'],list(range(1,31)))
            self.assertEqual(matrix['actual_runs'],matrix['expected_runs'])
        self.assertTrue(value['regression']['passed'])
        for folder in (ROOT/'results/next_validation').iterdir():
            if not folder.is_dir() or not (folder/'summary.csv').exists() or folder.name.startswith('pilot_'):continue
            summary=events(folder/'summary.csv')
            plotted=events(folder/'graph_plot_data.csv')
            self.assertEqual(summary,plotted)
            self.assertTrue(all(r['metric']=='traffic_light_wait_s' for r in summary if r['configuration']=='NoPreemptionBaseline'))
            self.assertEqual({p.name for p in (folder/'graphs').glob('*.png')},{f"{r['metric']}-{r['density']}.png" for r in summary})

if __name__=='__main__':unittest.main()
