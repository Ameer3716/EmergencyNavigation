import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('storage_batch', Path(__file__).resolve().parents[1]/'scripts/run_batch.py')
batch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(batch)

class PublishingTests(unittest.TestCase):
    def test_rerun_cannot_change_previous_shared_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            run = root/'run'
            (run/'results').mkdir(parents=True)
            source = run/'results/Batch-#0.vec'
            source.write_bytes(b'prior measured values')
            raw = root/'canonical.vec'
            batch.publish_result(source, raw)
            self.assertTrue(os.path.samefile(source, raw))
            batch.detach_result_links(run)
            source.write_bytes(b'new measured values')
            self.assertEqual(raw.read_bytes(), b'prior measured values')
            batch.publish_result(source, raw)
            self.assertEqual(raw.read_bytes(), b'new measured values')
            self.assertTrue(os.path.samefile(source, raw))
