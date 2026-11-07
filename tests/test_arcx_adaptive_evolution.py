import unittest
from scripts.arcx_adaptive_evolution import plan_evolution

class BoundedAdaptiveEvolutionTests(unittest.TestCase):
    def setUp(self):
        self.boundary = "a" * 64
        self.system = {"system_id": "VX", "boundary_sha256": self.boundary, "allowed_capabilities": ["local-cache", "index-optimization"]}
        self.evidence = [{"source_revision": "b" * 40, "sha256": "c" * 64, "independent_validation": True}]

    def proposal(self, **overrides):
        item = {
            "proposal_id": "proposal-1", "system_id": "VX", "boundary_sha256": self.boundary,
            "capability_id": "local-cache", "change_class": "LOCAL_CACHE",
            "benefit_score": 0.8, "risk_score": 0.2, "evidence": self.evidence,
        }
        item.update(overrides)
        return item

    def test_valid_local_change_is_review_only(self):
        plan = plan_evolution(self.system, [self.proposal()])
        self.assertEqual(plan["state"], "READY_FOR_REVIEW")
        self.assertEqual(plan["proposals"][0]["state"], "PENDING_HUMAN_REVIEW")
        self.assertFalse(plan["proposals"][0]["authority_granted"])
        self.assertFalse(plan["changes_applied"])
        self.assertFalse(plan["execution_performed"])

    def test_capability_outside_boundary_is_blocked(self):
        plan = plan_evolution(self.system, [self.proposal(capability_id="production-admin")])
        self.assertEqual(plan["proposals"][0]["state"], "BLOCKED")
        self.assertIn("CAPABILITY_OUTSIDE_SYSTEM_BOUNDARY", plan["proposals"][0]["blockers"])

    def test_boundary_change_is_blocked(self):
        plan = plan_evolution(self.system, [self.proposal(boundary_sha256="d" * 64)])
        self.assertIn("BOUNDARY_DIGEST_MISMATCH", plan["proposals"][0]["blockers"])

    def test_cross_system_write_is_never_local_evolution(self):
        plan = plan_evolution(self.system, [self.proposal(change_class="CROSS_SYSTEM_WRITE")])
        self.assertIn("CHANGE_CLASS_REQUIRES_SEPARATE_GOVERNED_WORKFLOW", plan["proposals"][0]["blockers"])

    def test_missing_independent_validation_stays_pending(self):
        evidence = [{"source_revision": "b" * 40, "sha256": "c" * 64, "independent_validation": False}]
        plan = plan_evolution(self.system, [self.proposal(evidence=evidence)])
        self.assertEqual(plan["proposals"][0]["state"], "PENDING_EVIDENCE")

    def test_invalid_evidence_digest_blocks(self):
        evidence = [{"source_revision": "b" * 40, "sha256": "bad", "independent_validation": True}]
        plan = plan_evolution(self.system, [self.proposal(evidence=evidence)])
        self.assertEqual(plan["proposals"][0]["state"], "BLOCKED")
        self.assertIn("INVALID_EVIDENCE_DIGEST", plan["proposals"][0]["blockers"])

    def test_nonpositive_net_value_is_rejected(self):
        plan = plan_evolution(self.system, [self.proposal(benefit_score=0.2, risk_score=0.3)])
        self.assertEqual(plan["proposals"][0]["state"], "REJECTED_LOW_NET_VALUE")

    def test_plan_digest_is_deterministic(self):
        a = plan_evolution(self.system, [self.proposal()])
        b = plan_evolution(self.system, [self.proposal()])
        self.assertEqual(a["plan_sha256"], b["plan_sha256"])

    def test_scores_reject_nan_and_boolean(self):
        for score in (float("nan"), True, -0.1, 1.1):
            plan = plan_evolution(self.system, [self.proposal(benefit_score=score)])
            self.assertEqual(plan["proposals"][0]["state"], "BLOCKED")

    def test_malformed_change_class_fails_closed(self):
        plan = plan_evolution(self.system, [self.proposal(change_class=["LOCAL_CACHE"])])
        self.assertEqual(plan["proposals"][0]["state"], "BLOCKED")
        self.assertIn("UNKNOWN_OR_NONLOCAL_CHANGE_CLASS", plan["proposals"][0]["blockers"])

if __name__ == "__main__":
    unittest.main()
