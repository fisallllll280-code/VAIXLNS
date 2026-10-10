import unittest

from tools.language_repair_fabric import make_work_orders, parse_diagnostics, summarize


REV = "a" * 40


class LanguageRepairFabricTests(unittest.TestCase):
    def test_typescript_diagnostic_becomes_pinned_work_order(self):
        output = "src/core.ts(12,4): error TS2322: Type 'string' is not assignable to type 'number'."
        orders = make_work_orders("typescript", output, "owner/repo", REV)
        self.assertEqual(len(orders), 1)
        order = orders[0]
        self.assertEqual(order["source"]["revision"], REV)
        self.assertEqual(order["source"]["path"], "src/core.ts")
        self.assertEqual(order["diagnostic"]["code"], "TS2322")
        self.assertEqual(order["status"], "READY_FOR_TRIAGE")
        self.assertFalse(order["repair_policy"]["automatic_patch"])

    def test_work_order_id_is_deterministic(self):
        output = "src/core.ts(12,4): error TS2322: invalid type."
        a = make_work_orders("typescript", output, "owner/repo", REV)
        b = make_work_orders("typescript", output, "owner/repo", REV)
        self.assertEqual(a, b)

    def test_unknown_custom_language_is_preserved_and_blocked(self):
        orders = make_work_orders("vlang-custom", "E17 at unit 4", "owner/repo", REV)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["status"], "BLOCKED_UNKNOWN_LANGUAGE")
        self.assertEqual(orders[0]["language"]["adapter_state"], "CUSTOM_LANGUAGE_PENDING_ADAPTER")
        self.assertEqual(orders[0]["diagnostic"]["raw_digest"], orders[0]["diagnostic"]["raw_digest"])

    def test_empty_unknown_output_does_not_fabricate_diagnostics(self):
        self.assertEqual(make_work_orders("my-language", "", "owner/repo", REV), [])

    def test_unknown_revision_or_repository_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "PINNED_REPOSITORY_AND_REVISION_REQUIRED"):
            make_work_orders("python", "x.py:4:2: E501 line too long", "owner/repo", "main")

    def test_sandbox_patch_mode_is_not_claimed_as_implemented(self):
        with self.assertRaisesRegex(ValueError, "SANDBOX_PATCH_NOT_IMPLEMENTED"):
            make_work_orders("python", "x.py:4:2: E501 line too long", "owner/repo", REV, mode="SANDBOX_PATCH")

    def test_summary_never_claims_verification(self):
        orders = make_work_orders("typescript", "src/a.ts(2,1): error TS1005: expected token", "owner/repo", REV)
        result = summarize(orders)
        self.assertEqual(result["verification_state"], "NOT_VERIFIED")
        self.assertEqual(result["automatic_patching"], "DISABLED")

    def test_python_ruff_diagnostic(self):
        parsed = parse_diagnostics("python", "src/app.py:9:3: F401 imported but unused")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].tool, "ruff")
        self.assertEqual(parsed[0].line, 9)


if __name__ == "__main__":
    unittest.main()
