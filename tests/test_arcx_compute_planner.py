import unittest
from scripts.arcx_compute_planner import plan_compute
class ComputePlannerTests(unittest.TestCase):
 def setUp(self):
  self.workload={"workload_type":"benchmark","cpu":4,"memory_gib":16,"duration_minutes":30,"estimated_cost":2.5,"region":"region-a","image_digest":"sha256:"+"a"*64}
  self.policy={"allowed_regions":["region-a"],"approved_image_digests":[self.workload["image_digest"]],"max_cost":5,"max_concurrency":2,"ttl_enforced":True,"public_ingress_allowed":False}
 def test_valid_request_is_plan_only(self):
  p=plan_compute(self.workload,self.policy); self.assertEqual(p["state"],"PLAN_ONLY"); self.assertFalse(p["execution_performed"]); self.assertFalse(p["approved"])
 def test_over_budget_blocked(self):
  p=plan_compute(dict(self.workload,estimated_cost=6),self.policy); self.assertIn("BUDGET_LIMIT_EXCEEDED",p["blockers"])
 def test_unapproved_region_blocked(self):
  self.assertIn("REGION_NOT_ALLOWED",plan_compute(dict(self.workload,region="unknown"),self.policy)["blockers"])
 def test_unapproved_image_blocked(self):
  self.assertIn("IMAGE_NOT_APPROVED",plan_compute(dict(self.workload,image_digest="bad"),self.policy)["blockers"])
 def test_public_ingress_blocked(self):
  self.assertIn("PUBLIC_INGRESS_MUST_BE_DISABLED",plan_compute(self.workload,dict(self.policy,public_ingress_allowed=True))["blockers"])
 def test_missing_ttl_blocked(self):
  self.assertIn("TTL_ENFORCEMENT_REQUIRED",plan_compute(self.workload,dict(self.policy,ttl_enforced=False))["blockers"])
if __name__=="__main__": unittest.main()
