"""Validate current measured deliverables without hardcoding historical outcomes."""
import hashlib
import math
import statistics
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
sys.path.insert(0, str(ROOT / 'scripts'))
from raw_data import events
from validate_timing_evidence import audit
from process_results import CONFIGS, ALL_CONFIGS, METRICS
from scipy.stats import t


def read(name):
    return events(ROOT / 'results/processed' / name)


class TestThesisDeliverable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs = read('individual_runs-batch.csv')
        cls.lookup = {(r['configuration'], r['density'], r['seed']): r for r in cls.runs}

    def test_matrix(self):
        expected = {(c, d, str(s)) for c in ALL_CONFIGS for d in ('low', 'medium', 'high') for s in range(1, 31)}
        self.assertEqual(len(self.runs), 450)
        self.assertEqual(set(self.lookup), expected)

    def test_timing_and_precision(self):
        result = audit(ROOT)
        self.assertEqual(result['runs'], 450)
        self.assertTrue(result['passed'], result['failures'][:10])
        self.assertGreater(result['green_transitions'], 0)
        self.assertGreater(result['fog_timing_balances'], 0)

    def test_dynamic_reroutes_and_reviews(self):
        for config in CONFIGS[2:]:
            total = 0
            for r in self.runs:
                if r['configuration'] != config:
                    continue
                rows = events(ROOT / f"artifacts/logs/batch/routing-{config}-{r['density']}-seed{r['seed']}.csv")
                changes = [e for e in rows if e['action'] == 'applied' and e['reason'] in ('cost_improvement', 'low_speed')]
                self.assertEqual(int(r['route_changes']), len(changes))
                self.assertEqual(int(r['route_reviews']), sum(e['action'] == 'evaluated' for e in rows))
                for e in changes:
                    self.assertLess(float(e['estimatedCost']), float(e['currentRemainingCost']))
                total += len(changes)
            self.assertGreater(total, 0)

    def test_fallback_assignment_and_balance(self):
        rows = read('fallback_validation.csv')
        self.assertEqual(len(rows), 90)
        for density in ('low', 'medium', 'high'):
            group = [r for r in rows if r['density'] == density]
            self.assertEqual(sum(r['scenario_condition'] == 'controlled_stall' for r in group), 8)
            self.assertTrue(6 <= sum(int(r['fallback_triggered']) for r in group) <= 10)
        for r in rows:
            if r['fallback_triggered'] == '1':
                self.assertEqual(r['failure_reason'], 'controlled_stall_timeout')
                self.assertAlmostEqual(float(r['wait_before_fog_s']), .5)
                self.assertAlmostEqual(float(r['final_decision_latency_s']),
                                       float(r['wait_before_fog_s']) + float(r['fog_computation_s']) + float(r['communication_delay_s']))

    def test_paired_statistics(self):
        for r in read('paired_comparisons.csv'):
            a = [v for v in self.runs if v['configuration'] == r['config_A'] and v['density'] == r['density']]
            diff = [float(v[r['metric']]) - float(self.lookup[r['config_B'], r['density'], v['seed']][r['metric']])
                    for v in a if v[r['metric']] and self.lookup[r['config_B'], r['density'], v['seed']][r['metric']]]
            self.assertEqual(int(r['n_pairs']), len(diff))
            mean, sd = statistics.mean(diff), statistics.stdev(diff)
            self.assertAlmostEqual(float(r['mean_paired_diff']), mean)
            if sd > 1e-9:
                margin = t.ppf(.975, len(diff)-1) * sd / math.sqrt(len(diff))
                self.assertAlmostEqual(float(r['ci95_lower']), mean-margin)
                self.assertAlmostEqual(float(r['ci95_upper']), mean+margin)

    def test_graphs_and_report(self):
        graph_names = {f'{m}-{d}.png' for m in METRICS for d in ('low', 'medium', 'high')}
        graph_names |= {f'{m}-{c}-{d}.png' for m in ('route_decision_ms', 'ev_response_s')
                        for c in ('normal', 'controlled_stall') for d in ('low', 'medium', 'high')}
        graph_names |= {f'paired_{m}-{d}.png' for m in ('route_decision_ms', 'ev_response_s') for d in ('low', 'medium', 'high')}
        graphs = list((ROOT/'results/graphs').glob('*.png'))
        self.assertEqual({p.name for p in graphs}, graph_names)
        with zipfile.ZipFile(ROOT/'docs/Emergency_Vehicle_Navigation_Final_Submission.docx') as z:
            embedded = {hashlib.sha256(z.read(n)).digest() for n in z.namelist() if n.startswith('word/media/')}
        self.assertTrue({hashlib.sha256(p.read_bytes()).digest() for p in graphs} <= embedded)

    def test_waiting_only_baseline(self):
        for r in read('summary-batch.csv') + read('graph_plot_data.csv') + read('summary-cohorts.csv'):
            if r['configuration'] == 'NoPreemptionBaseline':
                self.assertEqual(r['metric'], 'traffic_light_wait_s')
        summary = {(r['configuration'], r['density'], r['metric']): float(r['mean']) for r in read('summary-batch.csv')}
        for d in ('low', 'medium', 'high'):
            for c in CONFIGS:
                self.assertGreater(summary[c, d, 'traffic_light_wait_s'], 0)
                self.assertLess(summary[c, d, 'traffic_light_wait_s'], summary['NoPreemptionBaseline', d, 'traffic_light_wait_s'])


if __name__ == '__main__':
    unittest.main()
