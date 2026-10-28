import unittest

from scripts.vx_reality_conflict_simulator import simulate


class VXRealityConflictSimulatorTests(unittest.TestCase):
    def test_conflicting_shared_invariant_blocks_promotion(self):
        report = simulate([], [
            {"system_id": "VLNS", "invariants": {"currency": "SAR"}},
            {"system_id": "NEXENT", "invariants": {"currency": "USD"}},
        ])
        self.assertEqual(report["status"], "CONFLICTS_FOUND")
        self.assertTrue(report["promotion_blocked"])
        self.assertEqual(report["findings"][0]["kind"], "CONTRACT_INVARIANT_CONFLICT")

    def test_dependency_version_conflict_is_reported(self):
        report = simulate([
            {"system_id": "A", "dependencies": {"libx": "1.0"}},
            {"system_id": "B", "dependencies": {"libx": "2.0"}},
        ])
        self.assertTrue(report["promotion_blocked"])
        self.assertIn("DEPENDENCY_VERSION_CONFLICT", [f["kind"] for f in report["findings"]])

    def test_duplicate_registry_ids_are_reported(self):
        report = simulate([], registry=[{"id": "VX-1"}, {"id": "VX-1"}])
        self.assertTrue(report["promotion_blocked"])
        self.assertEqual(report["findings"][0]["kind"], "DUPLICATE_ID")

    def test_clean_snapshot_does_not_claim_global_proof(self):
        report = simulate([{"system_id": "A", "dependencies": {"libx": "1.0"}}])
        self.assertFalse(report["promotion_blocked"])
        self.assertEqual(report["status"], "NO_CONFLICTS_DETECTED_IN_SUPPLIED_SNAPSHOT")
        self.assertTrue(report["limitations"])

    def test_report_hash_is_stable(self):
        sample = [{"system_id": "A", "dependencies": {"libx": "1.0"}}]
        self.assertEqual(simulate(sample)["report_sha256"], simulate(sample)["report_sha256"])


if __name__ == "__main__":
    unittest.main()
