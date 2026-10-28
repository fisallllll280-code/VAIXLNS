import unittest
from tools.gov_sand_case_triage import Scenario, assess

class TriageTests(unittest.TestCase):
    def test_no_consent_blocks(self):
        self.assertEqual(assess(Scenario(10000, 3000, 2000))["status"], "BLOCKED_NO_CONSENT")
    def test_budget_deficit(self):
        r = assess(Scenario(5000, 3500, 2000, True))
        self.assertEqual(r["financial_band"], "BUDGET_DEFICIT")
        self.assertEqual(r["monthly_balance_sar"], -500)
    def test_payment_pressure(self):
        self.assertEqual(assess(Scenario(10000, 2000, 5000, True))["financial_band"], "PAYMENT_PRESSURE")
    def test_external_action_always_blocked(self):
        r = assess(Scenario(15000, 2000, 2000, True))
        self.assertFalse(r["external_action_allowed"])
        self.assertIsNone(r["government_entitlement_decision"])
        self.assertTrue(r["human_review_required"])
    def test_bad_numbers(self):
        for bad in (-1, float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                assess(Scenario(bad, 100, 100, True))

if __name__ == "__main__":
    unittest.main()
