import unittest
from scripts.vx_forge_local_agents import execute_local

AGENTS=[{"id":"research-local","role":"research"},{"id":"review-local","role":"independent_verification"},{"id":"finance-local","role":"finance_analysis"}]
MISSION={"mission_id":"SMOKE","goal":"Review bounded indexing","roles":["research","independent_verification"]}
class LocalAgentTests(unittest.TestCase):
    def test_default_hold(self):
        self.assertEqual(execute_local(MISSION,AGENTS)["status"],"HOLD")
    def test_local_activation(self):
        r=execute_local(MISSION,AGENTS,approved=True)
        self.assertEqual(r["status"],"LOCAL_COMPLETED")
        self.assertEqual(len(r["results"]),2)
        self.assertFalse(r["verified"])
        self.assertEqual(r["provider_calls"],0)
    def test_repeatable(self):
        self.assertEqual(execute_local(MISSION,AGENTS,approved=True)["receipt_digest"],execute_local(MISSION,AGENTS,approved=True)["receipt_digest"])
    def test_finance_never_transacts(self):
        m={"mission_id":"FIN","goal":"Assess risk","roles":["finance_analysis"]}
        r=execute_local(m,AGENTS,approved=True)
        self.assertEqual(r["financial_actions"],0)
    def test_no_trading(self):
        m=dict(MISSION,action="trade")
        with self.assertRaises(ValueError):
            execute_local(m,AGENTS,approved=True)
if __name__=="__main__":
    unittest.main()
