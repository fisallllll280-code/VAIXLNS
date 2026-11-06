import hashlib
import unittest

from scripts.omega_reality_forge import evaluate


def artifact(kind, payload, state="TESTED"):
    return {"kind": kind, "payload": payload, "sha256": hashlib.sha256(payload.encode()).hexdigest(), "state": state}


def plan():
    return {
        "schema": "vaixl.omega.reality-forge.plan.v1",
        "tasks": [
            {"task_id": "T-01", "owner_agent": "engineering", "depends_on": [], "required_evidence": ["test-log"]},
            {"task_id": "T-02", "owner_agent": "integration", "depends_on": ["T-01"], "required_evidence": ["restore-receipt"]},
        ],
    }


class RealityForgeTests(unittest.TestCase):
    def test_missing_evidence_fails_closed(self):
        result = evaluate(plan(), {"evidence": {}})
        self.assertEqual(result["task_states"]["T-01"], "PENDING_VERIFICATION")
        self.assertEqual(result["task_states"]["T-02"], "BLOCKED_DEPENDENCY")
        self.assertFalse(result["execution_performed"])

    def test_valid_evidence_unlocks_review_not_execution(self):
        evidence = {"evidence": {
            "T-01": {"artifacts": [artifact("test-log", "tests passed")]},
            "T-02": {"artifacts": [artifact("restore-receipt", "restore matched")]},
        }}
        result = evaluate(plan(), evidence)
        self.assertEqual(result["task_states"]["T-01"], "READY_FOR_REVIEW")
        self.assertEqual(result["task_states"]["T-02"], "READY_FOR_REVIEW")
        self.assertEqual(result["status"], "PENDING_HUMAN_REVIEW")
        self.assertFalse(result["promotion_performed"])

    def test_tampered_payload_is_rejected(self):
        item = artifact("test-log", "original")
        item["payload"] = "tampered"
        result = evaluate(plan(), {"evidence": {"T-01": {"artifacts": [item]}}})
        self.assertEqual(result["task_states"]["T-01"], "PENDING_VERIFICATION")

    def test_unknown_dependency_rejected(self):
        bad = {"schema": "vaixl.omega.reality-forge.plan.v1", "tasks": [
            {"task_id": "A", "owner_agent": "x", "depends_on": ["MISSING"], "required_evidence": ["proof"]}
        ]}
        with self.assertRaises(ValueError):
            evaluate(bad, {"evidence": {}})

    def test_event_chain_is_deterministic(self):
        evidence = {"evidence": {}}
        self.assertEqual(evaluate(plan(), evidence)["event_chain_head_sha256"],
                         evaluate(plan(), evidence)["event_chain_head_sha256"])


if __name__ == "__main__":
    unittest.main()
