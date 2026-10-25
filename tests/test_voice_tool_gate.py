import unittest
from tools.voice_tool_gate import VoiceToolRequest, ToolPolicy, evaluate, audit_projection

class VoiceGateTest(unittest.TestCase):
    def setUp(self):
        self.p=ToolPolicy(frozenset({"search_knowledge_base","create_support_ticket"}),True,"support")
    def req(self,tool="search_knowledge_base",**changes):
        args=dict(session_id="s",principal_id="p",tool=tool,request_id="r",environment="isolated",scope="support")
        args.update(changes)
        return VoiceToolRequest(**args)
    def test_search_eligible(self):
        self.assertEqual(evaluate(self.req(),self.p)["decision"],"ELIGIBLE_FOR_BACKEND_CHECK")
    def test_ticket_requires_confirmation(self):
        self.assertEqual(evaluate(self.req("create_support_ticket"),self.p)["reason"],"BOUND_CONFIRMATION_REQUIRED")
    def test_confirmation_bound_to_request(self):
        self.assertEqual(evaluate(self.req("create_support_ticket",confirmation_ref="signed-ref",confirmation_request_id="wrong"),self.p)["decision"],"HOLD")
    def test_ticket_only_eligible(self):
        self.assertEqual(evaluate(self.req("create_support_ticket",confirmation_ref="signed-ref",confirmation_request_id="r"),self.p)["decision"],"ELIGIBLE_FOR_BACKEND_CHECK")
    def test_unknown_tool(self):
        self.assertEqual(evaluate(self.req("transfer_money"),self.p)["decision"],"REJECT")
    def test_revoked(self):
        self.assertEqual(evaluate(self.req(),ToolPolicy(self.p.allowed,False,"support"))["decision"],"HOLD")
    def test_scope(self):
        self.assertEqual(evaluate(self.req(scope="finance"),self.p)["decision"],"HOLD")
    def test_missing_identity(self):
        self.assertEqual(evaluate(self.req(principal_id=""),self.p)["decision"],"HOLD")
    def test_audit_no_audio(self):
        self.assertNotIn("audio",audit_projection(self.req(),evaluate(self.req(),self.p)))

if __name__=="__main__":unittest.main()
