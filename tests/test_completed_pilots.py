import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from export_completed_pilots import completed_stems
from raw_data import events

class CompletedPilotExport(unittest.TestCase):
    def test_partial_termination_is_never_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'results/raw';raw.mkdir(parents=True)
            logs=root/'artifacts/logs/batch';logs.mkdir(parents=True)
            for stem in ('complete','partial','missing_vector'):
                for extension in ('sca','vci','vec.gz'):
                    if stem=='missing_vector' and extension=='vec.gz':continue
                    (raw/f'{stem}.{extension}').write_bytes(b'evidence')
                (logs/f'{stem}-stdout.txt').write_text('Simulation time limit reached -- at t='+('100' if stem=='partial' else '900')+'s\nEnd.\n')
            self.assertEqual(completed_stems(root),{'complete'})

    def test_published_rows_have_only_completed_seed_keys(self):
        out=ROOT/'results/next_validation/completed_pilots'
        if not (out/'audit.json').exists():self.skipTest('Export in progress')
        audit=json.loads((out/'audit.json').read_text())
        rows=events(out/'individual_runs.csv')
        self.assertTrue(audit['passed']);self.assertEqual(len(rows),109)
        self.assertFalse(audit['reported_batch_started'])
        for window,expected in ((360,60),(120,49)):
            selected=[r for r in rows if int(r['pilot_window_s'])==window]
            self.assertEqual(len(selected),expected)
            actual=completed_stems(Path(r'\\wsl.localhost\opp_env\home\opp_env')/f'next_pilot_{window}_20261011')
            self.assertEqual({f"{r['configuration']}-{r['density']}-seed{r['seed']}" for r in selected},actual)

if __name__=='__main__':unittest.main()
