import unittest

from agents.agent_fabric import DEFAULT_HANDOFF_CHAIN, AgentRegistry
from agents.mind_federation import MindFederation, MindIdentity


class MindFederationTests(unittest.TestCase):
    def test_registry_agents_are_connected_by_default_chain(self):
        registry = AgentRegistry()
        federation = MindFederation.from_registry(
            tuple(agent.agent_id for agent in registry.all()),
            DEFAULT_HANDOFF_CHAIN,
        )
        self.assertEqual(federation.state()["mind_count"], 13)
        self.assertEqual(federation.state()["exchange_count"], 0)
        for source, target in zip(DEFAULT_HANDOFF_CHAIN, DEFAULT_HANDOFF_CHAIN[1:]):
            self.assertTrue(federation.connected(source, target))

    def test_semantic_state_exchange_is_recorded_and_hashed(self):
        federation = MindFederation()
        federation.register(MindIdentity("VM-1", "code", ("coding",)), agent_id="AG-A")
        federation.register(MindIdentity("VM-2", "research", ("research",)), agent_id="AG-B")
        federation.connect("AG-A", "AG-B")
        exchange = federation.exchange(
            source_agent="AG-A",
            target_agent="AG-B",
            semantic_state={
                "intent": "analyze",
                "requested_capability": "research",
                "assumptions": ["bounded"],
                "risk": "low",
                "evidence_refs": ["E1"],
                "requested_action": "review",
                "authority_scope": ["read.external"],
            },
            evidence_refs=("E1",),
            authority_scope=("read.external",),
        )
        self.assertEqual(len(exchange.state_hash), 64)
        self.assertEqual(federation.state()["exchange_count"], 1)

    def test_unlinked_exchange_is_denied(self):
        federation = MindFederation()
        federation.register(MindIdentity("VM-1", "code", ()), agent_id="AG-A")
        federation.register(MindIdentity("VM-2", "research", ()), agent_id="AG-B")
        with self.assertRaises(PermissionError):
            federation.exchange(
                source_agent="AG-A",
                target_agent="AG-B",
                semantic_state={
                    "intent": "x",
                    "requested_capability": "y",
                    "assumptions": [],
                    "risk": "low",
                    "evidence_refs": [],
                    "requested_action": "z",
                    "authority_scope": [],
                },
            )


if __name__ == "__main__":
    unittest.main()
