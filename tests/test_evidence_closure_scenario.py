import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from evidence_closure_scenario import Scenario, simulate

class EvidenceClosureScenarioTests(unittest.TestCase):
    def test_ideal(self):
        x=simulate(Scenario())
        self.assertEqual((x["working_weeks"],x["projected_linked"],x["estimated_cost_sar"]), (4,177,113620))
    def test_rework(self):
        x=simulate(Scenario(first_pass_acceptance=.85))
        self.assertEqual((x["accepted_weekly"],x["working_weeks"],x["estimated_cost_sar"]),(34,5,138575))
    def test_missing_sources(self):
        x=simulate(Scenario(first_pass_acceptance=.85,source_availability=.9))
        self.assertEqual((x["blocked_sources"],x["projected_linked"]),(15,162))
        self.assertLess(x["projected_coverage_pct"],100)
    def test_rework_and_outage(self):
        x=simulate(Scenario(first_pass_acceptance=.6,paid_interruption_weeks=1))
        self.assertEqual((x["elapsed_weeks"],x["estimated_cost_sar"]),(8,213440))
    def test_accelerated(self):
        x=simulate(Scenario(attempts_weekly=48,first_pass_acceptance=.85,weekly_sar=25860))
        self.assertEqual((x["accepted_weekly"],x["working_weeks"],x["estimated_cost_sar"]),(40,4,132756))
    def test_invalid(self):
        with self.assertRaises(ValueError):simulate(Scenario(source_availability=1.1))

if __name__ == "__main__":
    unittest.main()
