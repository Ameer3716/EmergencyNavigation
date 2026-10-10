"""Check direct baseline pairs and retain zero-valued and missing observations."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
from process_results import paired_comparisons


class TestClientBaselineComparison(unittest.TestCase):
    def test_matched_baseline_and_missing_values(self):
        rows = [dict(configuration=c, density='low', seed=s, traffic_light_wait_s=v)
                for c, s, v in [('FogCloudAStar', 1, 0), ('MistDynamicFogFallback', 1, 0),
                                ('FogCloudAStar', 2, 4), ('MistDynamicFogFallback', 2, 2),
                                ('FogCloudAStar', 3, None), ('MistDynamicFogFallback', 3, 1)]]
        result = paired_comparisons(rows, [('MistDynamicFogFallback', 'FogCloudAStar', ['traffic_light_wait_s'])])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['n_pairs'], 2)
        self.assertEqual(result[0]['N_scheduled'], 3)
        self.assertEqual(result[0]['mean_A'], 1)
        self.assertEqual(result[0]['mean_B'], 2)
        self.assertEqual(result[0]['mean_paired_diff'], -1)


if __name__ == '__main__':
    unittest.main()
