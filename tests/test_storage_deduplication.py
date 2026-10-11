import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('storage_dedup', Path(__file__).resolve().parents[1]/'scripts/deduplicate_policy_storage.py')
storage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(storage)

class StorageTests(unittest.TestCase):
    def make_case(self, root):
        raw = root/'results/raw'
        run = root/'simulations/batch/low-seed1/MistAStar/results'
        raw.mkdir(parents=True)
        run.mkdir(parents=True)
        for ext in ('sca', 'vec', 'vci'):
            (raw/f'MistAStar-low-seed1.{ext}').write_bytes(b'original evidence\n')
            (run/f'Batch-#0.{ext}').write_bytes(b'original evidence\n')
        return raw, run

    def test_identical_copies_share_storage_and_keep_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw, run = self.make_case(root)
            self.assertEqual(storage.deduplicate(root), (3, 54))
            for ext in ('sca', 'vec', 'vci'):
                a, b = raw/f'MistAStar-low-seed1.{ext}', run/f'Batch-#0.{ext}'
                self.assertTrue(os.path.samefile(a, b))
                self.assertEqual(a.read_bytes(), b'original evidence\n')
            self.assertEqual(storage.deduplicate(root), (0, 0))

    def test_different_evidence_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw, run = self.make_case(root)
            (run/'Batch-#0.vec').write_bytes(b'different evidence')
            storage.deduplicate(root)
            self.assertEqual((run/'Batch-#0.vec').read_bytes(), b'different evidence')
            self.assertFalse(os.path.samefile(raw/'MistAStar-low-seed1.vec', run/'Batch-#0.vec'))

    def test_incomplete_run_is_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw, run = self.make_case(root)
            (raw/'MistAStar-low-seed1.vci').write_bytes(b'')
            self.assertEqual(storage.deduplicate(root), (0, 0))
            self.assertFalse(os.path.samefile(raw/'MistAStar-low-seed1.vec', run/'Batch-#0.vec'))
