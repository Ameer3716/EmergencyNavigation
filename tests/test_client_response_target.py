"""Verify the optimistic bound includes the whole shortest legal route."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('target_audit', Path(__file__).resolve().parents[1] / 'analysis/client_response_target.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ResponseTargetBound(unittest.TestCase):
    def test_shortest_legal_route_includes_start_and_destination(self):
        network = '<net>'
        for name, length in [('A', 10), ('B', 90), ('C', 2), ('D', 10), ('unconnected', 1)]:
            network += f'<edge id="{name}"><lane length="{length}" /></edge>'
        for source, target in [('A', 'B'), ('B', 'D'), ('A', 'C'), ('C', 'D')]:
            network += f'<connection from="{source}" to="{target}" />'
        network += '</net>'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'network.xml'
            path.write_text(network)
            self.assertEqual(module.optimistic_route_distance(path, 'A', 'D'), 22)
            with self.assertRaises(ValueError):
                module.optimistic_route_distance(path, 'A', 'unconnected')
