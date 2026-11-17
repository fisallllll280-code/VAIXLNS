import unittest
from scripts.vx_autonomy_preflight import evaluate
SHA = "a" * 40
BASE = dict(action="SANDBOX_BUILD", repository="fisallllll280-code/VAIXLNS", branch="feat/safe", revision=SHA,
            paths=["docs/test.md"], external_cost_sar=0, sandbox_verified=True,
            tool_registered=True, actor_authorized=True)
class AutonomyTests(unittest.TestCase):
    def blocked(self, changes, reason):
        result = evaluate(dict(BASE, **changes))
        self.assertEqual(result["status"], "HOLD")
        self.assertIn(reason, result["reasons"])
    def test_safe_build(self): self.assertEqual(evaluate(BASE)["status"], "ELIGIBLE_FOR_ADAPTER_CHECK")
    def test_unknown_action(self): self.blocked({"action":"INVENT_ROOT"}, "UNKNOWN_ACTION")
    def test_cost(self): self.blocked({"external_cost_sar":1}, "NONZERO_OR_UNKNOWN_COST")
    def test_unknown_cost(self): self.blocked({"external_cost_sar":None}, "NONZERO_OR_UNKNOWN_COST")
    def test_bool_cost(self): self.blocked({"external_cost_sar":False}, "NONZERO_OR_UNKNOWN_COST")
    def test_main(self): self.blocked({"branch":"main"}, "ISOLATED_BRANCH_REQUIRED")
    def test_genome(self): self.blocked({"paths":["project.genome"]}, "PROTECTED_OR_UNSAFE_PATH")
    def test_omega(self): self.blocked({"paths":["registry/omega/omega-000-master-index.json"]}, "PROTECTED_OR_UNSAFE_PATH")
    def test_unregistered_tool(self): self.blocked({"tool_registered":False}, "UNREGISTERED_TOOL")
    def test_unauthorized_actor(self): self.blocked({"actor_authorized":False}, "ACTOR_NOT_AUTHORIZED")
    def test_sandbox(self): self.blocked({"sandbox_verified":False}, "SANDBOX_NOT_VERIFIED")
    def test_revision(self): self.blocked({"revision":"main"}, "PINNED_SHA_REQUIRED")
    def test_paid_action(self): self.blocked({"action":"PAID_API"}, "EXTERNAL_FINANCIAL_ACTION_BLOCKED")
    def test_release_without_approval(self): self.blocked({"action":"PUBLISH","target":"public"}, "RELEASE_APPROVAL_REQUIRED")
    def test_release_signed_bound(self):
        req = dict(BASE, action="PUBLISH", target="public", release_approval_id="r1")
        approved = dict(repository=BASE["repository"], revision=SHA, action="PUBLISH", target="public", status="APPROVED", verified_by_trusted_adapter=True)
        self.assertEqual(evaluate(req, approval_registry={"r1":approved})["status"], "ELIGIBLE_FOR_ADAPTER_CHECK")
        self.assertIn("RELEASE_APPROVAL_REQUIRED", evaluate(req, approval_registry={"r1":dict(approved, revision="b"*40)})["reasons"])
    def test_approved_release_still_blocks_cost(self):
        req = dict(BASE, action="PUBLISH", target="public", release_approval_id="r1", external_cost_sar=20)
        approved = dict(repository=BASE["repository"], revision=SHA, action="PUBLISH", target="public", status="APPROVED", verified_by_trusted_adapter=True)
        self.assertIn("NONZERO_OR_UNKNOWN_COST", evaluate(req, approval_registry={"r1":approved})["reasons"])
if __name__ == "__main__": unittest.main()
