"""Offline catalog and safety tests; no external providers."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from vx_forge_model_catalog import build_catalog, shortlist, benchmark

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"provider":"p","model":"m","version":"v1","capabilities":["mathematics"]}]
    def test_index_and_shortlist(self):
        catalog = build_catalog(self.rows)
        self.assertEqual(len(shortlist(catalog, "mathematics")), 1)
        self.assertEqual(catalog["status"], "UNCONNECTED")
    def test_duplicate_identity(self):
        with self.assertRaises(ValueError):
            build_catalog(self.rows * 2)
    def test_missing_identity(self):
        row = copy.deepcopy(self.rows[0])
        row["model"] = " "
        with self.assertRaises(ValueError):
            build_catalog([row])
    def test_unsupported_capability(self):
        with self.assertRaises(ValueError):
            shortlist(build_catalog(self.rows), "unsafe")
    def test_tampered_catalog(self):
        catalog = build_catalog(self.rows)
        catalog["entries"][0]["model"] = "tampered"
        with self.assertRaises(ValueError):
            shortlist(catalog, "mathematics")
    def test_bounded_fanout(self):
        with self.assertRaises(ValueError):
            shortlist(build_catalog(self.rows), "mathematics", max_candidates=10000)
    def test_synthetic_benchmark(self):
        result = benchmark(100)
        self.assertEqual(result["records"], 100)
        self.assertEqual(result["provider_calls"], 0)

if __name__ == "__main__":
    unittest.main()
