import unittest

from agents.agent_fabric import AgentDefinition, AgentRegistry, DEFAULT_HANDOFF_CHAIN


class AgentFabricTests(unittest.TestCase):
    def test_default_registry_has_thirteen_connected_roles(self):
        registry = AgentRegistry()
        agents = registry.all()
        self.assertEqual(len(agents), 13)
        self.assertEqual(tuple(agent.agent_id for agent in agents), DEFAULT_HANDOFF_CHAIN)
        self.assertEqual(registry.validate_handoff_chain(), ())

    def test_every_agent_has_bounded_authority(self):
        registry = AgentRegistry()
        for agent in registry.all():
            self.assertFalse(agent.may_execute, agent.agent_id)
            self.assertFalse(agent.may_promote, agent.agent_id)
            self.assertTrue(agent.authority_scope, agent.agent_id)

    def test_duplicate_agent_identity_is_rejected(self):
        agent = AgentDefinition(
            "AG-X", "TEST", "Test agent", ("test",), ("input",), ("output",)
        )
        with self.assertRaisesRegex(ValueError, "DUPLICATE_AGENT_ID"):
            AgentRegistry((agent, agent))

    def test_incompatible_handoff_is_rejected(self):
        a = AgentDefinition("AG-A", "A", "source", ("a",), ("input",), ("out-a",))
        b = AgentDefinition("AG-B", "B", "target", ("b",), ("out-b",), ("out-b2",))
        registry = AgentRegistry((a, b))
        self.assertIn("HANDOFF_CONTRACT_MISMATCH:AG-A->AG-B",
                      registry.validate_handoff_chain(("AG-A", "AG-B")))

    def test_unknown_agent_is_not_silently_resolved(self):
        with self.assertRaisesRegex(KeyError, "UNKNOWN_AGENT_ID"):
            AgentRegistry().get("AG-NOT-REGISTERED")

    def test_self_promotion_role_is_rejected_at_definition_time(self):
        with self.assertRaisesRegex(ValueError, "AGENT_SELF_PROMOTION_IS_FORBIDDEN"):
            AgentDefinition(
                "AG-SELF", "UNSAFE", "unsafe", ("x",), ("input",), ("output",),
                may_promote=True,
            )


if __name__ == "__main__":
    unittest.main()
