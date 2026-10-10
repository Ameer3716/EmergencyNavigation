"""Check incident provenance, complete matched results and reported recovery savings."""
import hashlib
import json
import statistics
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from congestion_validation import collect, recovery
from raw_data import events


class TestCongestionValidation(unittest.TestCase):
    def test_incident_evidence_and_summaries(self):
        rows, proof = collect(ROOT / 'artifacts/congestion_validation')
        self.assertEqual(len(rows), 360)
        report = json.loads((ROOT / 'results/congestion_validation/validation_report.json').read_text())
        self.assertTrue(report['passed'])
        self.assertEqual(report['incident_evidence'], proof)
        summary = events(ROOT / 'results/congestion_validation/summary.csv')
        for item in summary:
            values = [r[item['metric']] for r in rows if r['configuration'] == item['configuration']
                      and r['density'] == item['density'] and r[item['metric']] is not None]
            self.assertEqual(len(values), int(item['n']))
            self.assertAlmostEqual(statistics.mean(values), float(item['mean']))
        graphs = list((ROOT / 'results/congestion_validation/graphs').glob('*.png'))
        self.assertEqual(len(graphs), 12)
        with zipfile.ZipFile(ROOT / 'docs/Emergency_Vehicle_Navigation_Final_Submission.docx') as doc:
            embedded = {hashlib.sha256(doc.read(n)).digest() for n in doc.namelist() if n.startswith('word/media/')}
        self.assertTrue({hashlib.sha256(p.read_bytes()).digest() for p in graphs} <= embedded)

    def test_matched_recovery(self):
        rows = recovery()
        expected = sum(r['configuration'] == 'MistDynamicFogFallback' and r['fallback_triggered'] == '1'
                       for r in events(ROOT / 'results/processed/individual_runs-batch.csv'))
        self.assertEqual(len(rows), expected)
        for r in events(ROOT / 'results/congestion_validation/fault_recovery_summary.csv'):
            group = [x['recovery_saved_ms'] for x in rows if x['density'] == r['density']]
            self.assertEqual(len(group), int(r['n']))
            self.assertAlmostEqual(statistics.mean(group), float(r['mean']))


if __name__ == '__main__':
    unittest.main()
