import unittest

from experiments.windows_boot_recovery.diagnostics import (
    DiagnosticContractError,
    RemediationRequest,
    authorize_remediation,
    rank_hypotheses,
)


class WindowsBootRecoveryFabricTests(unittest.TestCase):
    def test_triage_is_deterministic_and_hash_linked(self):
        symptoms = ("boot_loop", "update_failed", "system_file_integrity_warning")
        self.assertEqual(rank_hypotheses(symptoms), rank_hypotheses(symptoms))
        result = rank_hypotheses(symptoms)
        self.assertEqual(result["mode"], "READ_ONLY_TRIAGE")
        self.assertTrue(result["no_automatic_repair"])
        self.assertEqual(len(result["evidence_hash"]), 64)
        self.assertGreaterEqual(result["candidates"][0]["relative_weight"], result["candidates"][-1]["relative_weight"])

    def test_symptom_order_does_not_change_result(self):
        a = rank_hypotheses(("boot_loop", "update_failed"))
        b = rank_hypotheses(("update_failed", "boot_loop"))
        self.assertEqual(a, b)

    def test_unknown_symptom_fails_closed(self):
        with self.assertRaisesRegex(DiagnosticContractError, "UNKNOWN_SYMPTOM"):
            rank_hypotheses(("magic_repair",))

    def test_empty_symptom_set_is_rejected(self):
        with self.assertRaisesRegex(DiagnosticContractError, "AT_LEAST_ONE_SYMPTOM"):
            rank_hypotheses(())

    def test_duplicate_symptoms_are_rejected(self):
        with self.assertRaisesRegex(DiagnosticContractError, "DUPLICATE_SYMPTOM"):
            rank_hypotheses(("boot_loop", "boot_loop"))

    def test_read_only_action_never_executes(self):
        result = authorize_remediation(RemediationRequest("collect-logs", "read_only"))
        self.assertEqual(result["decision"], "PROPOSED_READ_ONLY")
        self.assertFalse(result["execution_performed"])

    def test_reversible_change_requires_approval(self):
        result = authorize_remediation(RemediationRequest("repair-startup", "reversible_system_change"))
        self.assertEqual(result["decision"], "AWAITING_APPROVAL")
        self.assertFalse(result["execution_performed"])

    def test_approval_receipt_does_not_execute_prototype_action(self):
        result = authorize_remediation(RemediationRequest(
            "repair-startup", "reversible_system_change", True, "approval:example"
        ))
        self.assertEqual(result["decision"], "APPROVAL_RECEIPT_PRESENT_REVIEW_REQUIRED")
        self.assertFalse(result["execution_performed"])

    def test_destructive_security_and_canonical_actions_are_blocked(self):
        for effect in ("destructive_change", "security_bypass", "canonical_write"):
            with self.subTest(effect=effect):
                result = authorize_remediation(RemediationRequest("dangerous-action", effect))
                self.assertEqual(result["decision"], "BLOCKED")
                self.assertFalse(result["execution_performed"])


if __name__ == "__main__":
    unittest.main()
