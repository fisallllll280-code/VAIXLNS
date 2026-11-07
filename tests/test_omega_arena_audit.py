import copy
import json
import unittest

from scripts.omega_arena_audit import (
    DEFAULT_REGISTRY,
    build_report,
    digest_bytes,
    validate_registry,
)


class OmegaArenaAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = DEFAULT_REGISTRY.read_bytes()
        cls.registry = json.loads(cls.raw.decode("utf-8"))

    def test_current_registry_validates_but_does_not_claim_live_integration(self):
        report = build_report(self.registry, digest_bytes(self.raw), revision="test-revision", generated_at="2026-01-01T00:00:00Z")
        self.assertEqual(report["assessment"]["registry_validation"], "PASS")
        self.assertEqual(report["assessment"]["status"], "PENDING_VERIFICATION")
        self.assertEqual(report["assessment"]["systems_total"], 4)
        self.assertEqual(report["assessment"]["edges_total"], 6)
        self.assertEqual(report["assessment"]["live_verified_edges"], 0)
        self.assertFalse(report["assessment"]["network_probe_performed"])
        self.assertFalse(report["assessment"]["canonical_write_performed"])

    def test_all_six_pairs_are_covered(self):
        report = build_report(self.registry, digest_bytes(self.raw), generated_at="fixed")
        pairs = {frozenset((edge["source"], edge["target"])) for edge in report["edges"]}
        self.assertEqual(len(pairs), 6)
        self.assertTrue(all(edge["live_verified"] is False for edge in report["edges"]))

    def test_unresolved_identity_blocks_incident_edges(self):
        report = build_report(self.registry, digest_bytes(self.raw), generated_at="fixed")
        unresolved = {
            item["system_id"] for item in report["systems"]
            if item["identity_status"] != "SOURCE_OBSERVED"
        }
        for edge in report["edges"]:
            if edge["source"] in unresolved or edge["target"] in unresolved:
                self.assertEqual(edge["audit_status"], "IDENTITY_UNVERIFIED")

    def test_manifest_cannot_self_attest_live_on_unconfigured_transport(self):
        data = copy.deepcopy(self.registry)
        data["interface_edges"][0]["status"] = "LIVE_VERIFIED"
        self.assertTrue(any("unconfigured transport cannot be LIVE_VERIFIED" in error for error in validate_registry(data)))
        report = build_report(data, "0" * 64, generated_at="fixed")
        self.assertEqual(report["assessment"]["status"], "BLOCKED")
        self.assertEqual(report["assessment"]["live_verified_edges"], 0)

    def test_missing_edge_fails_closed(self):
        data = copy.deepcopy(self.registry)
        data["interface_edges"].pop()
        errors = validate_registry(data)
        self.assertTrue(any("all six unique system pairs" in error for error in errors))
        report = build_report(data, "0" * 64, generated_at="fixed")
        self.assertEqual(report["assessment"]["registry_validation"], "FAIL")
        self.assertEqual(report["assessment"]["status"], "BLOCKED")

    def test_digest_is_stable_for_identical_inputs(self):
        first = build_report(self.registry, digest_bytes(self.raw), revision="abc", generated_at="fixed")
        second = build_report(copy.deepcopy(self.registry), digest_bytes(self.raw), revision="abc", generated_at="fixed")
        self.assertEqual(first, second)
        self.assertEqual(first["report_sha256"], second["report_sha256"])


if __name__ == "__main__":
    unittest.main()
