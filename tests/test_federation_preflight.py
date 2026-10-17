import copy
import json
import unittest

from scripts.federation_preflight import EDGES_MANIFEST, SYSTEMS_MANIFEST, build_report


class FederationPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.systems = json.loads(SYSTEMS_MANIFEST.read_text(encoding="utf-8"))
        cls.edges = json.loads(EDGES_MANIFEST.read_text(encoding="utf-8"))

    def test_preflight_is_structurally_valid_but_not_operational(self):
        report = build_report(self.systems, self.edges)
        self.assertEqual(report["assessment"]["manifest_validation"], "PASS")
        self.assertEqual(report["assessment"]["admission_status"], "BLOCKED")
        self.assertFalse(report["assessment"]["connectivity_verified"])
        self.assertFalse(report["assessment"]["runtime_observed"])

    def test_no_side_effect_or_authority_is_claimed(self):
        report = build_report(self.systems, self.edges)
        self.assertFalse(report["assessment"]["canonical_write_performed"])
        self.assertFalse(report["assessment"]["authority_granted"])
        self.assertFalse(report["assessment"]["execution_performed"])

    def test_current_unresolved_identities_are_visible_as_blockers(self):
        report = build_report(self.systems, self.edges)
        mappings = {
            item.get("mapping") for item in report["blockers"]
            if item.get("code") == "SYSTEM_IDENTITY_UNRESOLVED"
        }
        self.assertEqual(mappings, {"VLNS ↔ NAXLNS", "NEXNET ↔ NEXENT"})

    def test_all_current_edges_remain_disabled(self):
        report = build_report(self.systems, self.edges)
        self.assertEqual(report["summary"]["edges_total"], 4)
        self.assertEqual(report["summary"]["active_verified_edges"], 0)
        self.assertEqual(report["summary"]["disabled_or_unconnected_edges"], 4)

    def test_report_digest_is_deterministic(self):
        first = build_report(self.systems, self.edges)
        second = build_report(copy.deepcopy(self.systems), copy.deepcopy(self.edges))
        self.assertEqual(first["report_sha256"], second["report_sha256"])
        self.assertEqual(first, second)

    def test_invalid_contract_is_reported_as_invalid(self):
        edges = copy.deepcopy(self.edges)
        edges["edges"][0]["failure_mode"] = "ALLOW"
        report = build_report(self.systems, edges)
        self.assertEqual(report["assessment"]["manifest_validation"], "FAIL")
        self.assertEqual(report["assessment"]["admission_status"], "INVALID")
        self.assertTrue(any(x.get("code") == "EDGE_CONTRACT_INVALID" for x in report["blockers"]))


if __name__ == "__main__":
    unittest.main()
