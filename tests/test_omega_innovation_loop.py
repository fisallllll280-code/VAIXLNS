import json
import tempfile
import unittest
from pathlib import Path
from scripts.omega_innovation_loop import analyze

class InnovationLoopTests(unittest.TestCase):
    def write_index(self, data):
        d = tempfile.TemporaryDirectory()
        p = Path(d.name) / "index.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return d, p

    def test_graph_and_simulation_are_deterministic(self):
        d, p = self.write_index({"index_id":"Ω.000","records":[{"id":"A"},{"id":"B","parent":"A"}]})
        try:
            a = analyze(p)
            self.assertEqual(a, analyze(p))
            self.assertEqual(a["simulation"]["direct_dependents"], ["B"])
            self.assertFalse(a["admission"]["eligible"])
        finally:
            d.cleanup()

    def test_unresolved_edges_are_not_hidden(self):
        d, p = self.write_index({"records":[{"id":"A","parent":"UNKNOWN"}]})
        try:
            self.assertEqual(len(analyze(p)["unresolved_edges"]), 1)
        finally:
            d.cleanup()

    def test_duplicate_ids_fail_closed(self):
        d, p = self.write_index({"records":[{"id":"A"},{"id":"A"}]})
        try:
            with self.assertRaises(ValueError):
                analyze(p)
        finally:
            d.cleanup()

if __name__ == "__main__":
    unittest.main()
