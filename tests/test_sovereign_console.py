import json
import tempfile
import unittest
from pathlib import Path

from tools.sovereign_console.engine import CommandEngine, ZERO_HASH, canonical_digest


class SovereignConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        genome = {
            "schema_version": "1.0.0",
            "genesis": {"authority_anchor": "Ω0_GENESIS_CORE"},
            "canonical_source": {"type": "project.genome", "version": "1.0.0", "status": "CANONICAL"},
            "master_index": {"id": "Ω.000", "path": "registry/omega/omega-000-master-index.json"},
            "integrity": {"canonical_hash": ""},
        }
        genome["integrity"]["canonical_hash"] = canonical_digest(genome)
        self.write_json("project.genome", genome)
        self.write_json("registry/omega/omega-000-master-index.json", {
            "index_id": "Ω.000",
            "status": "CANONICAL",
            "name": "Test Master Index",
            "records": [
                {"id": "VX", "type": "SYSTEM", "role": "EXECUTION", "epistemic_state": "PARTIAL"}
            ],
        })
        self.write_json("registry/agent_registry.v1.json", {
            "status": "BASELINE_REGISTERED",
            "agents": [{
                "agent_id": "AG-001",
                "canonical_name": "Index Archaeologist",
                "family": "recovery",
                "capabilities": ["index", "archive"],
                "allowed_tools": ["fetch_file"],
                "authority_scope": "read-only",
                "primary_output": "atomic index records",
                "hard_rule": "source pin + hash + provenance",
            }],
        })
        self.write_text("registry/repository-orchestration/VAIXLNS_REPOSITORY_CONTRACT.md", "# test contract\n")
        self.write_text(".github/workflows/federation-integrity.yml", "name: test\n")
        self.write_text("scripts/federation_integrity_gate.py", "# test gate\n")
        self.engine = CommandEngine(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def write_text(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def write_json(self, relative, value):
        self.write_text(relative, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def test_genome_digest_passes_and_detects_tampering(self):
        self.assertTrue(self.engine.execute("genome verify")["ok"])
        genome = json.loads((self.root / "project.genome").read_text(encoding="utf-8"))
        genome["genesis"]["authority_anchor"] = "FORGED"
        self.write_json("project.genome", genome)
        result = self.engine.execute("genome verify")
        self.assertFalse(result["ok"])
        self.assertIn("mismatch", result["summary"].lower())

    def test_proof_gate_checks_canonical_surfaces(self):
        result = self.engine.execute("proof verify")
        self.assertTrue(result["ok"], result["lines"])
        self.assertEqual(result["data"]["failed"], 0)
        self.assertGreaterEqual(result["data"]["passed"], 9)

    def test_index_search_uses_registry_source_records(self):
        result = self.engine.execute("index search VX")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["data"]["matches"]), 1)
        self.assertEqual(result["data"]["matches"][0]["record"]["id"], "VX")

    def test_agent_inspection_returns_scope_and_hard_rule(self):
        result = self.engine.execute("agents inspect AG-001")
        self.assertTrue(result["ok"])
        self.assertIn("read-only", "\n".join(result["lines"]))
        self.assertIn("source pin", "\n".join(result["lines"]))

    def test_free_form_shell_command_is_not_executed(self):
        marker = self.root / "must-not-exist.txt"
        result = self.engine.execute(f"touch {marker}")
        self.assertFalse(result["ok"])
        self.assertFalse(marker.exists())
        self.assertIn("No shell command was executed", result["summary"])

    def test_simulation_is_reproducible_and_explicitly_non_operational(self):
        first = self.engine.execute("runtime simulate check canonical state")
        second = self.engine.execute("runtime simulate check canonical state")
        self.assertTrue(first["ok"])
        self.assertEqual(first["data"]["final_hash"], second["data"]["final_hash"])
        self.assertEqual(first["data"]["mode"], "SIMULATION_ONLY")
        self.assertEqual(first["data"]["epistemic_state"], "SPECIFIED")
        self.assertTrue(any("No project files were changed" in line for line in first["lines"]))

    def test_session_events_are_hash_linked(self):
        first = self.engine.execute("status")
        second = self.engine.execute("history")
        self.assertEqual(first["event"]["previous_hash"], ZERO_HASH)
        self.assertEqual(second["event"]["previous_hash"], first["event"]["event_hash"])
        self.assertEqual(len(first["event"]["event_hash"]), 64)

    def test_unknown_commands_fail_closed(self):
        result = self.engine.execute("sudo anything")
        self.assertFalse(result["ok"])
        self.assertIn("Unknown command", result["summary"])


if __name__ == "__main__":
    unittest.main()
