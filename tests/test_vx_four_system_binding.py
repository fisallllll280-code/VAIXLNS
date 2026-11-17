import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINDING_PATH = ROOT / "deploy" / "federation" / "vx-four-system-binding.v1.json"


class VXFourSystemBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def test_all_four_systems_are_declared(self):
        systems = {item["system_id"]: item for item in self.binding["systems"]}
        self.assertEqual(set(systems), {"VAIXLNS", "VLNS", "VX", "NEXNET"})
        self.assertEqual(systems["VX"]["repository"], "fisallllll280-code/VX-runtime")

    def test_canonical_sources_are_referenced_not_replaced(self):
        self.assertEqual(self.binding["canonical_sources"]["genome"], "project.genome")
        self.assertEqual(
            self.binding["canonical_sources"]["master_index"],
            "registry/omega/omega-000-master-index.json",
        )
        self.assertFalse(self.binding["policy"]["modify_project_genome"])
        self.assertFalse(self.binding["policy"]["modify_master_index"])

    def test_unknown_identity_mappings_are_not_claimed_as_verified(self):
        states = {item["system_id"]: item["binding_status"] for item in self.binding["systems"]}
        self.assertEqual(states["VLNS"], "IDENTITY_MAPPING_UNVERIFIED")
        self.assertEqual(states["NEXNET"], "IDENTITY_MAPPING_UNVERIFIED")
        self.assertIn("RUNTIME_CONNECTIVITY_UNVERIFIED", states["VX"])

    def test_live_status_and_credentials_are_not_fabricated(self):
        for key in ("service_urls", "credentials", "runtime_status", "health_status", "test_results"):
            self.assertIn(key, self.binding["unavailable_values_must_remain_unset"])
        self.assertEqual(self.binding["status"], "SPECIFIED")
        self.assertIn("Do not label the federation CONNECTED or VERIFIED", self.binding["admission_rule"])

    def test_execution_requires_authorization_and_evidence(self):
        self.assertFalse(self.binding["policy"]["execute_without_authorization"])
        required = set(self.binding["required_runtime_evidence"])
        self.assertTrue({
            "authenticated_health_check",
            "contract_conformance_test",
            "authorized_end_to_end_execution",
            "event_and_evidence_hash",
            "replay_or_reproducibility_check",
        }.issubset(required))


if __name__ == "__main__":
    unittest.main()
