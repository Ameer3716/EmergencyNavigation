"""Check supplemental conclusions against preserved raw evidence."""
import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
sys.path.insert(0, str(ROOT / 'scripts'))
from supplemental_validation import route_rows, route_summary, signal_rows
from raw_data import events


class TestSupplementalValidation(unittest.TestCase):
    def test_preserved_main_batch_and_route_counts(self):
        manifest = events(ROOT / 'artifacts/raw_evidence_manifest.csv')
        scalars = [r for r in manifest if r['raw_file'].endswith('.sca')]
        self.assertEqual(len(scalars), 450)
        for r in scalars:
            self.assertEqual(hashlib.sha256((ROOT / 'results/raw' / r['raw_file']).read_bytes()).hexdigest(), r['sha256'])
        measured = route_summary(route_rows(ROOT))
        saved = events(ROOT / 'results/supplemental/route_transaction_summary.csv')
        self.assertEqual(len(saved), len(measured))
        for actual, expected in zip(saved, measured):
            for k in ('n', 'requests_sent', 'replies_accepted'):
                self.assertEqual(int(actual[k]), expected[k])
            if expected['mean'] is None:
                self.assertEqual(actual['mean'], '')
            else:
                self.assertAlmostEqual(float(actual['mean']), expected['mean'])
        self.assertNotIn('NoPreemptionBaseline', {r['configuration'] for r in saved})

    def test_red_signal_evidence_and_graph_gallery(self):
        rows, timing = signal_rows(ROOT / 'artifacts/signal_validation')
        self.assertEqual(len(rows), 18)
        self.assertTrue(timing['passed'])
        saved = events(ROOT / 'results/supplemental/red_signal_runs.csv')
        for a, b in zip(rows, saved):
            self.assertAlmostEqual(a['traffic_light_wait_s'], float(b['traffic_light_wait_s']))
        graphs = list((ROOT / 'results/supplemental/graphs').glob('*.png'))
        self.assertEqual(len(graphs), 12)
        with zipfile.ZipFile(ROOT / 'docs/Emergency_Vehicle_Navigation_Final_Submission.docx') as doc:
            media = {hashlib.sha256(doc.read(n)).digest() for n in doc.namelist() if n.startswith('word/media/')}
        self.assertTrue({hashlib.sha256(p.read_bytes()).digest() for p in graphs} <= media)
        report = json.loads((ROOT / 'results/supplemental/validation_report.json').read_text())
        self.assertFalse(report['headline_definitions_changed'])


if __name__ == '__main__':
    unittest.main()
