"""Verify fair controls, held-out selection and independent mobility evidence."""
import json
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
sys.path.insert(0,str(ROOT/'scripts'))
from policy_validation import effective_parameters, comparisons, EXTRA, first_approach_states
from run_policy_validation import TUNING, settings_lines
from raw_data import events, scalars


class TestPolicyDesign(unittest.TestCase):
    def test_matched_policy_comparison_is_distinct(self):
        rows=[]
        for seed in (1,2,3):
            for c,v in (('FogCloudAStar',160),('FogCloudAStarAdvance',150),('MistDynamicFogFallback',149)):
                rows.append(dict(configuration=c,density='low',seed=seed,ev_response_s=v))
        paired=comparisons(rows)
        matched=[r for r in paired if r['comparison']=='matched_policy' and r['metric']=='ev_response_s'][0]
        original=[r for r in paired if r['comparison']=='original_policy' and r['metric']=='ev_response_s'][0]
        self.assertEqual(matched['mean_paired_diff'],-1)
        self.assertEqual(original['mean_paired_diff'],-11)
        self.assertEqual(matched['n_pairs'],3)
        self.assertEqual(matched['ci95_lower'],-1)

    def test_tuning_does_not_change_initial_computation_or_input(self):
        allowed={'dynamicUpdateInterval','minimumRouteImprovement','slowRouteImprovement','minimumRerouteGap'}
        for settings in TUNING.values():self.assertEqual({p for p,_ in settings_lines(settings)},allowed)

    def test_red_arrival_is_not_relabelled_green_after_waiting(self):
        rows=[dict(edge=e,nextTls=light,time=str(t),tlsDistance=str(distance),linkState=state)
              for e,light,t,distance,state in [('A','J1',1,25,'r'),('A','J1',1.5,19,'r'),
               ('A','J1',1.6,19,'r'),('A','J1',4,2,'G'),(':J1','J2',4.5,200,'r'),
               ('B','J2',6,18,'G'),('B','J2',6.1,18,'G')]]
        arrivals=first_approach_states(rows,0)
        self.assertEqual([r['state'] for r in arrivals],['r','G'])
        self.assertEqual(len(arrivals),2)
        self.assertEqual(first_approach_states(rows,None),[])


class TestPolicyEvidence(unittest.TestCase):
    def test_reported_matrix_and_selection(self):
        output=ROOT/'results/policy_validation'
        if not (output/'audit.json').exists():self.skipTest('New reported experiment is still running')
        audit=json.loads((output/'audit.json').read_text())
        self.assertTrue(audit['passed']);self.assertEqual(audit['runs'],1170)
        selection=json.loads((output/'selection.json').read_text())
        self.assertEqual(selection['training_seeds'],list(range(101,111)))
        self.assertEqual(selection['reported_seeds_used_for_selection'],[])
        for context,expected in (('ordinary',630),('obstruction',540)):
            rows=events(output/context/'individual_runs.csv');self.assertEqual(len(rows),expected)
            for c in {r['configuration'] for r in rows}:
                for d in ('low','medium','high'):
                    self.assertEqual({int(r['seed']) for r in rows if r['configuration']==c and r['density']==d},set(range(1,31)))
            summary=events(output/context/'summary.csv')
            self.assertTrue(all(r['metric']=='traffic_light_wait_s' for r in summary if r['configuration']=='NoPreemptionBaseline'))
            plotted=events(output/context/'graph_plot_data.csv')
            self.assertEqual(len(plotted),len(summary))
            for source,plot in zip(summary,plotted):
                for field in ('mean','ci95_lower','ci95_upper','n'):self.assertEqual(source[field],plot[field])
            expected_graphs={f"{r['metric']}-{r['density']}.png" for r in summary}
            self.assertEqual({p.name for p in (output/context/'graphs').glob('*.png')},expected_graphs)

    def test_slow_time_and_crossing_evidence(self):
        mapping=ROOT/'artifacts/policy_validation/workspaces.json'
        if not mapping.exists():self.skipTest('New reported experiment is still running')
        workspaces=json.loads(mapping.read_text())
        for context,path in workspaces.items():
            root=Path(path)
            self.assertTrue(root.is_dir(),f'Missing retained raw workspace: {root}')
            sources=list((root/'results/raw').glob('*.sca'))
            self.assertEqual(len(sources),630 if context=='ordinary' else 540)
            for scalar in sources:
                values=scalars(scalar)
                if not values['evResponseTime']:continue
                release=values['evNavigationReleaseTime'][0]
                rows=events(root/f'artifacts/logs/batch/mobility-{scalar.stem}.csv')
                slow=sum(.1 for r in rows if r['speed'] and float(r['time'])+1e-9>=release and float(r['speed'])<1)
                self.assertAlmostEqual(values['evTimeBelow1Mps'][0],slow,places=6)
                moving=False;in_stop=False;stops=0
                for row in rows:
                    if not row['speed'] or float(row['time'])+1e-9<release:continue
                    speed=float(row['speed'])
                    if speed>=1:moving=True;in_stop=False
                    elif speed<.1 and moving and not in_stop:stops+=1;in_stop=True
                self.assertEqual(values['evFullStops'][0],stops)
                entries=[r for r in rows if r['junctionEvent']=='junction_entry']
                self.assertEqual(values['evSignalCrossings'][0],len(entries))
                self.assertEqual(values['evSignalsPassedOnGreen'][0],sum(r['crossingLinkState'] in ('G','g') for r in entries))
                parameters=effective_parameters(scalar)
                self.assertEqual(parameters['releaseSpeed'],{'13.9mps'})


if __name__=='__main__':unittest.main()
