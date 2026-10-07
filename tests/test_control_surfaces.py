import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
FOUR_DIRECTIONS = ["semantic", "structural", "operational", "evolutionary"]


class ControlSurfaceTests(unittest.TestCase):
    def test_agent_registry_is_complete(self):
        data = json.loads((ROOT / "registry/agents/VAIXLNS_AGENT_REGISTRY_V1.json").read_text())
        self.assertEqual(data["status"], "IMPLEMENTED")
        ids = [agent["agent_id"] for agent in data["agents"]]
        self.assertEqual(len(ids), 13)
        self.assertEqual(ids, [f"AG-{i:03d}" for i in range(1, 14)])
        self.assertEqual(data["handoff_chain"], [
            "AG-001", "AG-002", "AG-003", "AG-004", "AG-005", "AG-006",
            "AG-007", "AG-008", "AG-009", "AG-010", "AG-013", "AG-011", "AG-012",
        ])

    def test_json_schemas_and_templates_parse(self):
        paths = [
            "schemas/vaixl-agent-genome-v1.schema.json",
            "schemas/vaixl-agent-handoff-v1.schema.json",
            "schemas/vaixl-agent-wallet-authorization-v1.schema.json",
            "schemas/vaixl-agent-event-v1.schema.json",
            "schemas/vaixl-pattern-v1.schema.json",
            "schemas/vaixl-private-language-vault-binding.schema.json",
            "templates/agents/agent-record-v1.json",
            "templates/agents/agent-task-v1.json",
            "templates/pattern/pattern-language-v1.json",
            "templates/evidence/agent-evidence-v1.json",
        ]
        for path in paths:
            with self.subTest(path=path):
                json.loads((ROOT / path).read_text())

    def test_pattern_template_locks_four_directions(self):
        pattern = json.loads((ROOT / "templates/pattern/pattern-language-v1.json").read_text())
        self.assertEqual(pattern["directions"], FOUR_DIRECTIONS)

    def test_secret_placeholder_is_not_real_secret(self):
        task = json.loads((ROOT / "templates/agents/agent-task-v1.json").read_text())
        self.assertEqual(task["pattern_context"]["language"]["binding_fingerprint"],
                         "REPLACE_WITH_64_HEX_FINGERPRINT")


if __name__ == "__main__":
    unittest.main()
