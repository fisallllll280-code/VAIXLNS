from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agents.agent_fabric import AgentRegistry, DEFAULT_HANDOFF_CHAIN


class AgentRegistryTests(unittest.TestCase):
    def test_loads_canonical_registry_and_default_chain(self):
        registry = AgentRegistry()
        agents = registry.all()
        self.assertEqual(len(agents), 13)
        self.assertEqual(tuple(agent.agent_id for agent in agents), DEFAULT_HANDOFF_CHAIN)
        self.assertEqual(registry.get("AG-001").canonical_name, "Index Archaeologist")
        self.assertEqual(registry.get("AG-013").authority_scope, "governance")

    def test_registry_records_are_immutable(self):
        agent = AgentRegistry().get("AG-001")
        with self.assertRaises((AttributeError, TypeError)):
            agent.agent_id = "AG-999"

    def test_unknown_agent_raises_key_error(self):
        with self.assertRaises(KeyError):
            AgentRegistry().get("AG-999")

    def test_duplicate_agent_ids_fail_closed(self):
        source = json.loads(AgentRegistry().path.read_text(encoding="utf-8"))
        source["agents"].append(dict(source["agents"][0]))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate_id"):
                AgentRegistry(path)

    def test_malformed_registry_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            path.write_text('{"agents": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "empty"):
                AgentRegistry(path)


if __name__ == "__main__":
    unittest.main()
