import unittest
from datetime import datetime, timedelta, timezone

from scripts.omega_readiness_bridge import DEFAULT_HARD_GATES, evaluate_readiness

NOW = datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc)
STAMP = "2026-10-28T09:00:00Z"
HASH = "a" * 64


def packet():
    return {
        "capability_id": "synthetic.compute.hybrid",
        "observed_at": STAMP,
        "max_age_seconds": 300,
        "checks": {gate: "PASS" for gate in DEFAULT_HARD_GATES},
        "dependencies": [
            {"id": "vx-node-sim-01", "status": "PASS", "observed_at": STAMP}
        ],
        "evidence": [
            {"ref": "fixture://synthetic/run-001", "sha256": HASH,
             "verified": True, "observed_at": STAMP}
        ],
    }


class OmegaReadinessBridgeTests(unittest.TestCase):
    def test_complete_fresh_packet_is_ready_but_not_execution(self):
        result = evaluate_readiness(packet(), now=NOW)
        self.assertEqual(result["status"], "READY")
        self.assertFalse(result["execution_performed"])
        self.assertFalse(result["external_calls_performed"])
        self.assertTrue(result["human_approval_required"])
        self.assertEqual(len(result["report_sha256"]), 64)

    def test_missing_hard_gate_fails_closed(self):
        data = packet()
        del data["checks"]["integrity"]
        result = evaluate_readiness(data, now=NOW)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("HARD_GATE_UNKNOWN:integrity", result["blockers"])

    def test_failed_dependency_fails_closed(self):
        data = packet()
        data["dependencies"][0]["status"] = "FAIL"
        result = evaluate_readiness(data, now=NOW)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("DEPENDENCY_FAIL:vx-node-sim-01", result["blockers"])

    def test_stale_observation_is_not_ready(self):
        data = packet()
        data["observed_at"] = (NOW - timedelta(seconds=301)).isoformat()
        result = evaluate_readiness(data, now=NOW)
        self.assertEqual(result["observation_status"], "STALE")
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("OBSERVATION_STALE", result["blockers"])

    def test_unverified_or_bad_hash_evidence_is_rejected(self):
        data = packet()
        data["evidence"][0]["sha256"] = "not-a-hash"
        data["evidence"][0]["verified"] = False
        result = evaluate_readiness(data, now=NOW)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("NO_VALID_EVIDENCE", result["blockers"])

    def test_future_observation_is_rejected(self):
        data = packet()
        data["observed_at"] = (NOW + timedelta(minutes=2)).isoformat()
        result = evaluate_readiness(data, now=NOW)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("OBSERVATION_FROM_FUTURE", result["blockers"])

    def test_degraded_soft_check_is_reported_as_degraded(self):
        data = packet()
        data["checks"]["optional_diagnostics"] = "DEGRADED"
        result = evaluate_readiness(data, now=NOW)
        self.assertEqual(result["status"], "DEGRADED")

    def test_malformed_status_types_do_not_crash(self):
        data = packet()
        data["checks"]["availability"] = []
        data["dependencies"][0]["status"] = {}
        result = evaluate_readiness(data, now=NOW)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("INVALID_STATUS:availability", result["blockers"])
        self.assertIn("DEPENDENCY_UNKNOWN:vx-node-sim-01", result["blockers"])

    def test_unknown_optional_check_is_not_reported_ready(self):
        data = packet()
        data["checks"]["optional_diagnostics"] = "UNKNOWN"
        result = evaluate_readiness(data, now=NOW)
        self.assertEqual(result["status"], "DEGRADED")

    def test_invalid_input_never_passes(self):
        result = evaluate_readiness(None, now=NOW)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("INVALID_INPUT_SHAPE", result["blockers"])


if __name__ == "__main__":
    unittest.main()
