import json
import unittest
from pathlib import Path

from scripts.validate_global_engineering_discovery_fabric import MANIFEST, SCHEMA, validate


class GlobalEngineeringDiscoveryFabricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_manifest_and_schema_pass_structural_checks(self):
        self.assertEqual(validate(self.data, self.schema), [])

    def test_eight_capabilities_exist_without_verified_claims(self):
        ids = [item["id"] for item in self.data["capabilities"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertCountEqual(ids, [f"GEDF-{i:03d}" for i in range(1, 9)])
        self.assertNotIn("VERIFIED", [item["state"] for item in self.data["capabilities"]])

    def test_canonical_authority_is_unchanged(self):
        authority = self.data["authority"]
        self.assertEqual(authority["canonical_source"], "project.genome::v1.0.0")
        self.assertEqual(authority["authority_anchor"], "Ω0_GENESIS_CORE")
        self.assertEqual(authority["master_index"], "Ω.000")
        self.assertEqual(authority["canonical_mutation"], "NOT_AUTHORIZED")
        self.assertEqual(authority["state_promotion"], "DISABLED")

    def test_cannot_claim_runtime_evidence_from_specification_only(self):
        data = json.loads(json.dumps(self.data))
        data["evidence_state"] = "REPRODUCIBLE_EVIDENCE"
        self.assertTrue(any("runtime evidence" in error for error in validate(data, self.schema)))

    def test_partnership_claim_is_rejected(self):
        data = json.loads(json.dumps(self.data))
        data["candidate_interoperability_sources"][0]["relationship_state"] = "OFFICIAL_PARTNER"
        self.assertTrue(any("unverified partnership" in error for error in validate(data, self.schema)))

    def test_bad_official_reference_is_rejected(self):
        data = json.loads(json.dumps(self.data))
        data["candidate_interoperability_sources"][0]["official_reference"] = "javascript:alert(1)"
        self.assertTrue(any("HTTPS URLs" in error for error in validate(data, self.schema)))

    def test_score_weights_must_sum_to_declared_rubric(self):
        data = json.loads(json.dumps(self.data))
        data["innovation_scoring"]["dimensions"][0]["weight"] = 99
        self.assertTrue(any("weights" in error for error in validate(data, self.schema)))

    def test_missing_acceptance_criteria_is_rejected(self):
        data = json.loads(json.dumps(self.data))
        data["capabilities"][0]["acceptance"] = []
        self.assertTrue(any("acceptance must be a non-empty list" in error for error in validate(data, self.schema)))

    def test_cannot_reparent_system_under_new_root(self):
        data = json.loads(json.dumps(self.data))
        data["system"]["parent"] = "GLOBAL"
        self.assertTrue(any("child subsystem" in error for error in validate(data, self.schema)))


if __name__ == "__main__":
    unittest.main()
