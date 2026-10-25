import json
import unittest
from pathlib import Path
from scripts.validate_assembly_federation import validate

ROOT = Path(__file__).resolve().parents[1]

class AssemblyFederationTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "registry/assemblies/assembly-federation.v1.json").read_text(encoding="utf-8"))

    def test_current_manifest(self):
        errors, summary = validate(self.data)
        self.assertEqual(errors, [])
        self.assertEqual(summary["groups"], 8)

    def test_unsafe_auto_publish_rejected(self):
        self.data["policy"]["auto_publish"] = True
        self.assertTrue(validate(self.data)[0])

    def test_identity_conflict_cannot_bypass_hold(self):
        self.data["groups"][1]["state"] = "INVENTORIED"
        self.assertTrue(validate(self.data)[0])

    def test_archive_claim_cannot_be_promoted(self):
        self.data["omega_infinity"]["verification_state"] = "VERIFIED"
        self.assertTrue(validate(self.data)[0])

    def test_duplicate_repository_rejected(self):
        self.data["groups"][2]["repositories"].append("fisallllll280-code/VAIXLNS")
        self.assertTrue(validate(self.data)[0])

if __name__ == "__main__":
    unittest.main()
