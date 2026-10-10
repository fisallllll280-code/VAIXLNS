import unittest
from scripts.arcx_model_router import plan_route
class ModelRouterTests(unittest.TestCase):
 def setUp(self):
  self.request={"task_class":"summarization","required_capabilities":["text"],"data_class":"public","tenant_id":"tenant-a"}
  self.policy={"allowed_providers":["provider-a"],"allowed_models":["model-x"],"allowed_data_classes":["public"],"allowed_task_classes":["summarization"]}
  self.entry={"provider_id":"provider-a","model_id":"model-x","revision":"v1","state":"ACTIVE","metadata_state":"VERIFIED","capabilities":["text"],"data_policy_allows":True,"tenant_isolation_verified":True,"contract_sha256":"a"*64}
 def test_eligible_candidate_only(self):
  p=plan_route(self.request,[self.entry],self.policy); self.assertEqual(p["state"],"ROUTE_CANDIDATES_READY"); self.assertFalse(p["provider_called"])
 def test_unverified_provider_never_routed(self):
  e=dict(self.entry,metadata_state="PENDING_VERIFICATION"); self.assertEqual(plan_route(self.request,[e],self.policy)["state"],"NO_ELIGIBLE_MODEL")
 def test_data_policy_blocks_before_routing(self):
  p=plan_route(dict(self.request,data_class="restricted"),[self.entry],self.policy); self.assertEqual(p["state"],"BLOCKED"); self.assertIn("DATA_CLASS_NOT_ALLOWED",p["blockers"])
 def test_unapproved_provider_excluded(self):
  e=dict(self.entry,provider_id="provider-b"); self.assertEqual(plan_route(self.request,[e],self.policy)["state"],"NO_ELIGIBLE_MODEL")
 def test_tenant_isolation_required(self):
  e=dict(self.entry,tenant_isolation_verified=False); self.assertEqual(plan_route(self.request,[e],self.policy)["state"],"NO_ELIGIBLE_MODEL")
 def test_deterministic_plan(self):
  self.assertEqual(plan_route(self.request,[self.entry],self.policy)["plan_sha256"],plan_route(self.request,[self.entry],self.policy)["plan_sha256"])
if __name__=="__main__": unittest.main()
