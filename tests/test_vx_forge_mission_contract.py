import unittest
from scripts.vx_forge_mission_contract import plan_mission

AGENTS = [{"id":"r","role":"research"},{"id":"v","role":"independent_verification"},{"id":"f","role":"finance_analysis"}]
class MissionTests(unittest.TestCase):
    def test_research_plan(self):
        r=plan_mission({"mission_id":"M1","goal":"test"}, AGENTS)
        self.assertEqual(r["status"],"PLANNED")
        self.assertEqual(r["external_effects"],"DISABLED")
    def test_finance_read_only(self):
        r=plan_mission({"mission_id":"M2","goal":"risk","roles":["finance_analysis","independent_verification"]}, AGENTS)
        self.assertEqual(r["finance_mode"],"ANALYSIS_ONLY")
    def test_no_trades(self):
        with self.assertRaises(ValueError):
            plan_mission({"mission_id":"M3","goal":"buy","action":"trade"}, AGENTS)
    def test_no_spending(self):
        with self.assertRaises(ValueError):
            plan_mission({"mission_id":"M4","goal":"buy","budget_sar":1}, AGENTS)
    def test_missing_role(self):
        with self.assertRaises(ValueError):
            plan_mission({"mission_id":"M5","goal":"simulate","roles":["physics"]}, AGENTS)
    def test_duplicate_agent(self):
        with self.assertRaises(ValueError):
            plan_mission({"mission_id":"M6","goal":"test"}, AGENTS+AGENTS[:1])
if __name__=="__main__":
    unittest.main()
