import unittest

from agents.agent_fabric import (
    AgentFabric,
    AgentPolicy,
    AgentRegistry,
    HandoffEnvelope,
    CORE_AGENT_SPECS,
)
from agents.agent_wallet import AgentEconomicWallet
from verification.agent_verifier import AgentVerifier


class AgentFabricTests(unittest.TestCase):
    def setUp(self):
        self.fabric = AgentFabric(signing_key=b"ci-agent-key")

    def _task(self, **overrides):
        task = {
            "task_id": "TASK-1",
            "capability": "architecture-analysis",
            "authority_scope": "read.registry",
            "tool": "registry.read",
            "pattern_context": {
                "language": {
                    "language_id": "L1",
                    "binding_fingerprint": "f" * 64,
                },
                "replay": {"seed": "deterministic"},
            },
            "estimated_cost": "10.00",
            "actual_cost": "7.50",
            "asset": "USD",
            "handoff_target": "AG-005",
            "expected_output": "evidence_bundle",
        }
        task.update(overrides)
        return task

    def test_registry_contains_all_core_specialized_agents(self):
        registry = AgentRegistry()
        self.assertEqual(len(registry.all()), 13)
        self.assertEqual({x.agent_id for x in registry.all()}, {x.agent_id for x in CORE_AGENT_SPECS})

    def test_policy_rejects_unowned_authority_and_tools(self):
        spec = AgentRegistry().get("AG-008")
        self.assertEqual(
            AgentPolicy.authorize(
                spec,
                capability="architecture-search",
                authority_scope="runtime.execute",
                tool="vx.execute",
            )["state"],
            "REJECT",
        )

    def test_handoff_signature_is_deterministic(self):
        envelope = HandoffEnvelope(
            task_id="T",
            source_agent="AG-004",
            target_agent="AG-005",
            reason="research",
            required_capabilities=("research",),
            input_artifact_ids=(),
            evidence_refs=(),
            constraints=(),
            expected_output="evidence",
            authority_scope=("read.external",),
            expiry="task-scope",
        )
        sig = envelope.signature(b"k")
        self.assertEqual(len(sig), 64)
        self.assertTrue(envelope.verify(b"k", sig))
        self.assertFalse(envelope.verify(b"wrong", sig))

    def test_dispatch_integrates_agent_mind_pattern_wallet_handoff_and_proof(self):
        wallet = AgentEconomicWallet(
            balances={"USD": "100.00"},
            allowed_agents=("AG-004",),
        )
        result = self.fabric.dispatch(self._task(), wallet=wallet)
        self.assertEqual(result["state"], "SIMULATED")
        self.assertEqual(result["verification_state"], "VERIFIED")
        self.assertEqual(result["final_disposition"], "HOLD")
        self.assertEqual(len(result["routes"]), 4)
        self.assertEqual(result["wallet_settlement"]["actual_amount"], "7.50000000")
        self.assertEqual(result["wallet_settlement"]["refund"], "2.50000000")
        self.assertEqual(wallet.state()["balances"]["USD"], "92.50000000")
        self.assertEqual(result["mind_exchange"]["source_agent"], "AG-004")
        self.assertEqual(result["mind_exchange"]["target_agent"], "AG-005")
        self.assertEqual(len(result["mind_exchange"]["state_hash"]), 64)
        proof = AgentVerifier.verify(
            routes=result["routes"],
            handoff=result["handoff"],
            signature=result["handoff_signature"],
            signing_key=b"ci-agent-key",
            events=result["events"],
            wallet_settlement=result["wallet_settlement"],
            mind_exchange=result["mind_exchange"],
        )
        self.assertEqual(proof["state"], "PASS")

    def test_missing_pattern_binding_holds_without_wallet_charge(self):
        wallet = AgentEconomicWallet(balances={"USD": "100.00"}, allowed_agents=("AG-004",))
        result = self.fabric.dispatch(
            self._task(pattern_context={"language": {"language_id": "L1"}}),
            wallet=wallet,
        )
        self.assertEqual(result["state"], "HOLD")
        self.assertNotIn("wallet_settlement", result)
        self.assertEqual(wallet.state()["balances"]["USD"], "100.00000000")

    def test_malformed_pattern_context_fails_closed(self):
        result = self.fabric.dispatch(self._task(pattern_context=["not", "a", "mapping"]))
        self.assertEqual(result["state"], "HOLD")
        self.assertEqual(result["reason"], "pattern_context_not_mapping")

    def test_wallet_authorization_failure_holds_without_side_effect(self):
        wallet = AgentEconomicWallet(balances={"USD": "1.00"}, allowed_agents=("AG-004",))
        result = self.fabric.dispatch(self._task(), wallet=wallet)
        self.assertEqual(result["state"], "HOLD")
        self.assertIn("wallet_authorization_blocked:", result["reason"])
        self.assertEqual(wallet.state()["balances"]["USD"], "1.00000000")

    def test_unauthorized_handoff_target_is_rejected(self):
        result = self.fabric.dispatch(self._task(handoff_target="AG-013"))
        self.assertEqual(result["state"], "REJECT")
        self.assertEqual(result["reason"], "handoff_target_not_authorized")


if __name__ == "__main__":
    unittest.main()
