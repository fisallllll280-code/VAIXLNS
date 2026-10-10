import unittest

from tools.sovereign_console.scale_engine import ScaleEngine


class ScaleEngineTests(unittest.TestCase):
    def setUp(self):
        self.facts = {
            "agent_count": 13,
            "system_count": 4,
            "connection_count": 4,
            "verified_connections": 0,
            "authenticated_connections": 0,
            "genome_available": True,
            "index_available": True,
            "runtime_configured": False,
            "provider_configured": False,
            "allowlisted_commands": True,
            "durable_learning_store": False,
            "evidence_refs": ["project.genome", "registry/omega/omega-000-master-index.json"],
        }

    def test_all_scenario_detects_federation_and_runtime_obstacles(self):
        result = ScaleEngine().simulate("all", self.facts)
        ids = {item.finding_id for item in result.findings}
        self.assertIn("SCALE-GROWTH-003", ids)
        self.assertIn("SCALE-FED-002", ids)
        self.assertIn("SCALE-AGENT-001", ids)
        self.assertIn("SCALE-AGENT-002", ids)
        self.assertEqual(result.outcome, "BLOCKED")
        self.assertEqual(result.epistemic_state, "SPECIFIED")

    def test_simulation_hash_is_deterministic_for_same_facts(self):
        engine = ScaleEngine()
        first = engine.simulate("federation", self.facts)
        second = engine.simulate("federation", self.facts)
        self.assertEqual(first.trace_hash, second.trace_hash)
        self.assertEqual(first.findings, second.findings)

    def test_authenticated_verified_links_remove_authentication_obstacle(self):
        facts = dict(self.facts)
        facts.update(connection_count=1, verified_connections=1, authenticated_connections=1)
        result = ScaleEngine().simulate("federation", facts)
        ids = {item.finding_id for item in result.findings}
        self.assertNotIn("SCALE-FED-002", ids)
        self.assertNotIn("SCALE-FED-003", ids)

    def test_unknown_scenario_fails_closed(self):
        with self.assertRaises(ValueError):
            ScaleEngine().simulate("invent-anything", self.facts)

    def test_missing_canonical_sources_are_blockers(self):
        facts = dict(self.facts, genome_available=False, index_available=False)
        result = ScaleEngine().simulate("knowledge", facts)
        ids = {item.finding_id for item in result.findings}
        self.assertIn("SCALE-KNOW-001", ids)
        self.assertIn("SCALE-KNOW-002", ids)


if __name__ == "__main__":
    unittest.main()
