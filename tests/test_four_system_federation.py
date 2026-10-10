import json
import unittest
from pathlib import Path

from scripts.validate_four_system_federation import MANIFEST, validate


class FourSystemFederationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_current_manifest_passes(self):
        self.assertEqual(validate(self.data), [])

    def test_all_four_system_identities_are_distinct_records(self):
        ids = [item["system_id"] for item in self.data["systems"]]
        self.assertCountEqual(ids, ["VAIXLNS", "VLNS", "VX", "NEXNET"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_canonical_genome_and_omega_index_are_fixed(self):
        authority = self.data["authority"]
        self.assertEqual(authority["canonical_source"], "project.genome")
        self.assertEqual(authority["master_index"], "Ω.000")

    def test_unresolved_repository_names_cannot_be_silently_promoted(self):
        for sid in ("VLNS", "NEXNET"):
            record = next(x for x in self.data["systems"] if x["system_id"] == sid)
            self.assertEqual(record["identity_state"], "UNVERIFIED")
            self.assertIn("↔", record["unresolved_mapping"])

    def test_destructive_merge_is_blocked(self):
        data = json.loads(json.dumps(self.data))
        data["policy"]["allow_destructive_merge"] = True
        self.assertTrue(any("allow_destructive_merge" in e for e in validate(data)))

    def test_missing_original_preservation_is_rejected(self):
        data = json.loads(json.dumps(self.data))
        data["policy"]["preserve_original_ideas"] = False
        self.assertTrue(any("preserve_original_ideas" in e for e in validate(data)))

    def test_verified_cannot_be_used_as_implementation_state(self):
        data = json.loads(json.dumps(self.data))
        data["systems"][0]["implementation_state"] = "VERIFIED"
        self.assertTrue(any("implementation_state" in e for e in validate(data)))

    def test_unresolved_identity_requires_explicit_mapping(self):
        data = json.loads(json.dumps(self.data))
        record = next(x for x in data["systems"] if x["system_id"] == "VLNS")
        record.pop("unresolved_mapping")
        self.assertTrue(any("unresolved identity" in e for e in validate(data)))


if __name__ == "__main__":
    unittest.main()
