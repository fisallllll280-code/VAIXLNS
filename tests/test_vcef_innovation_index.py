import copy
import json
import unittest
from pathlib import Path
from scripts.validate_vcef_innovation_index import validate

ROOT = Path(__file__).resolve().parents[1]

class VCEFIndexTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "registry/computer-engineering/VCEF_INNOVATION_INDEX_V1.json").read_text(encoding="utf-8"))

    def test_manifest_passes(self):
        self.assertEqual(validate(self.data), [])

    def test_duplicate_innovation_fails(self):
        self.data["innovations"].append(copy.deepcopy(self.data["innovations"][0]))
        self.assertTrue(validate(self.data))

    def test_unproven_source_fails(self):
        self.data["innovations"][0]["sources"] = []
        self.assertTrue(validate(self.data))

    def test_canonical_promotion_fails(self):
        self.data["status"] = "VERIFIED"
        self.assertTrue(validate(self.data))

    def test_hardware_fabrication_authorization_fails(self):
        self.data["policy"]["no_automatic_hardware_fabrication"] = False
        self.assertTrue(validate(self.data))

if __name__ == "__main__":
    unittest.main()
