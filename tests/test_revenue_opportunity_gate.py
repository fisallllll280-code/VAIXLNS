import unittest
from scripts.revenue_opportunity_gate import validate

GOOD = """# Revenue Opportunity Register
Status: INITIAL_DESK_RESEARCH — NOT QUALIFIED; NO CUSTOMER NEED OR PURCHASE INTENT VERIFIED
| Candidate | Public evidence | Testable commercial hypothesis | Qualification question | Public source |
|---|---|---|---|---|
| Example Co | Public software services | May need a scoped QA review | Is QA a current pain? | https://example.com/ |
## Guardrails
Do not contact anyone or publish outreach without human approval.
No spending, money movement, external contact, or public posting without explicit authorization.
Preserve project.genome, Ω.000, and all historical artifacts.
No customer need or purchase intent verified.
"""

class RevenueOpportunityGateTests(unittest.TestCase):
    def test_valid_register_passes_without_claiming_demand(self):
        result = validate(GOOD, "fixture.md")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["candidate_count"], 1)
        self.assertIn("not proof of customer demand", result["limitations"][0].lower())

    def test_missing_source_fails(self):
        result = validate(GOOD.replace("https://example.com/", "missing"), "fixture.md")
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("HTTPS source URL" in error for error in result["errors"]))

    def test_qualified_status_fails_closed(self):
        result = validate(GOOD.replace("Status: INITIAL_DESK_RESEARCH — NOT QUALIFIED", "Status: QUALIFIED"), "fixture.md")
        self.assertEqual(result["status"], "FAIL")

if __name__ == "__main__":
    unittest.main()
