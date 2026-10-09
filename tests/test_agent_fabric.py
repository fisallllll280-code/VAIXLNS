import json
import tempfile
import unittest
from pathlib import Path

from agents.agent_fabric import AgentRegistry, AgentRegistryError, DEFAULT_HANDOFF_CHAIN


class AgentFabricTests(unittest.TestCase):
    def test_default_registry_reads_thirteen_canonical_definitions(self):
        registry = AgentRegistry()
        agents = registry.all()
        self.assertEqual(len(agents), 13)
        self.assertEqual(agents[0].agent_id, "AG-001")
        self.assertEqual(registry.get("ag-013").authority_scope, "governance")

    def test_default_handoff_chain_references_registered_agents(self):
        registry = AgentRegistry()
        known = {agent.agent_id for agent in registry.all()}
        self.assertEqual(len(DEFAULT_HANDOFF_CHAIN), len(set(DEFAULT_HANDOFF_CHAIN)))
        self.assertTrue(set(DEFAULT_HANDOFF_CHAIN).issubset(known))

    def test_capability_filter_is_metadata_only_and_scope_aware(self):
        registry = AgentRegistry()
        matches = registry.capable_of(["proof", "tests"], authority_scopes=["verification"])
        self.assertEqual([agent.agent_id for agent in matches], ["AG-010"])

    def test_duplicate_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "agents.json"
            path.write_text(json.dumps({"agents": [
                {"agent_id": "AG-1", "canonical_name": "One"},
                {"agent_id": "AG-1", "canonical_name": "Duplicate"},
            ]}), encoding="utf-8")
            with self.assertRaises(AgentRegistryError):
                AgentRegistry(path)


if __name__ == "__main__":
    unittest.main()
