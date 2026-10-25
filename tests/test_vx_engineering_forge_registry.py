"""Offline contract tests; no runtime or external model calls."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_vx_engineering_forge_registry import validate, REGISTRY

class TestForgeRegistry(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    def test_registry(self):
        self.assertEqual(validate(self.data), [])
    def test_missing_id(self):
        self.data["domains"][0].pop("id")
        self.assertTrue(validate(self.data))
    def test_blank_name(self):
        self.data["domains"][0]["name"] = " "
        self.assertTrue(validate(self.data))
    def test_duplicate_id(self):
        self.data["domains"][1]["id"] = self.data["domains"][0]["id"]
        self.assertTrue(validate(self.data))
    def test_activation_denied(self):
        self.data["activation"] = "ACTIVE"
        self.assertTrue(validate(self.data))
    def test_paid_operation_denied(self):
        self.data["policies"]["external_spend_sar"] = 1
        self.assertTrue(validate(self.data))

if __name__ == "__main__":
    unittest.main()
