import copy
import unittest

from scripts.sovereign_meta_kernel import SCHEMA_VERSION, evaluate_transition, sha256_json


def valid_package():
    return {
        "schema_version": SCHEMA_VERSION,
        "before": {
            "entity_id": "VAIXLNS.NODE.001",
            "constitution_hash": "a" * 64,
            "lineage_id": "VAIXLNS.GENESIS.0001",
        },
        "change": {
            "change_id": "CHANGE.0001",
            "changed_fields": ["runtime.timeout"],
            "requested_actions": ["run-tests"],
            "simulation": {"passed": True, "evidence_ref": "proof:simulation:001"},
            "tests": {"passed": True, "evidence_ref": "proof:tests:001"},
            "rollback_plan_ref": "rollback:001",
        },
        "authority": {
            "status": "APPROVED",
            "approver_id": "governance-board",
            "signature_verified": True,
        },
        "evidence": [
            {"source": "ci://run/123", "sha256": "b" * 64, "verified": True}
        ],
        "policy": {
            "immutable_fields": ["entity_id", "lineage_id", "constitution_hash"],
            "authorized_approvers": ["governance-board"],
            "minimum_evidence_count": 1,
            "require_simulation": True,
            "require_tests": True,
        },
    }


class SovereignMetaKernelTests(unittest.TestCase):
    def test_valid_change_is_only_eligible_not_executed(self):
        result = evaluate_transition(valid_package())
        self.assertEqual(result["decision"], "ELIGIBLE_FOR_SEPARATE_APPROVAL")
        self.assertIn("ELIGIBILITY_IS_NOT_EXECUTION", result["warnings"][0])

    def test_constitutional_identity_change_is_blocked(self):
        package = valid_package()
        package["change"]["changed_fields"].append("constitution_hash")
        self.assertIn(
            "CONSTITUTIONAL_INVARIANT_CHANGE_BLOCKED",
            evaluate_transition(package)["errors"],
        )

    def test_unapproved_authority_is_rejected(self):
        package = valid_package()
        package["authority"]["status"] = "PENDING"
        self.assertIn("AUTHORITY_NOT_APPROVED", evaluate_transition(package)["errors"])

    def test_unauthorized_approver_is_rejected(self):
        package = valid_package()
        package["authority"]["approver_id"] = "unlisted-agent"
        self.assertIn("APPROVER_NOT_AUTHORIZED", evaluate_transition(package)["errors"])

    def test_unverified_signature_is_rejected(self):
        package = valid_package()
        package["authority"]["signature_verified"] = False
        self.assertIn("AUTHORITY_SIGNATURE_NOT_VERIFIED", evaluate_transition(package)["errors"])

    def test_missing_simulation_and_tests_are_rejected(self):
        package = valid_package()
        package["change"].pop("simulation")
        package["change"].pop("tests")
        result = evaluate_transition(package)
        self.assertIn("SIMULATION_PROOF_REQUIRED", result["errors"])
        self.assertIn("TEST_PROOF_REQUIRED", result["errors"])

    def test_privileged_actions_require_external_gate(self):
        package = valid_package()
        package["change"]["requested_actions"] = ["canonical-write", "production-deploy"]
        self.assertIn("PRIVILEGED_ACTION_REQUIRES_EXTERNAL_GATE", evaluate_transition(package)["errors"])

    def test_evidence_must_be_verifiable(self):
        package = valid_package()
        package["evidence"][0]["sha256"] = "not-a-digest"
        self.assertIn("EVIDENCE_0_SHA256_INVALID", evaluate_transition(package)["errors"])

    def test_input_digest_changes_when_input_changes(self):
        package = valid_package()
        first = evaluate_transition(package)["input_sha256"]
        package["change"]["change_id"] = "CHANGE.0002"
        second = evaluate_transition(package)["input_sha256"]
        self.assertNotEqual(first, second)

    def test_decision_is_deterministic(self):
        package = valid_package()
        self.assertEqual(evaluate_transition(package), evaluate_transition(copy.deepcopy(package)))

    def test_canonical_json_digest_is_stable_across_key_order(self):
        self.assertEqual(sha256_json({"a": 1, "b": 2}), sha256_json({"b": 2, "a": 1}))


if __name__ == "__main__":
    unittest.main()
