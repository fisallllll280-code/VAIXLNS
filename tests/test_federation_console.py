import json
import tempfile
import unittest
from pathlib import Path

from tools.sovereign_console.engine import CommandEngine


class FederationDashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write_json("registry/federation/vlns-capability-index.v1.json", {
            "catalog_id": "test",
            "status": "PROPOSED",
            "systems": [
                {"system_id": "VAIXLNS", "role": "Control plane", "identity_status": "CANONICAL", "epistemic_state": "IMPLEMENTED", "repository_surfaces": ["owner/canon"]},
                {"system_id": "VLNS", "role": "Discovery", "identity_status": "UNVERIFIED", "epistemic_state": "SPECIFIED", "repository_surfaces": ["owner/NAXLNS (candidate)"], "declared_capabilities": ["repository discovery"]},
                {"system_id": "VX", "role": "Execution", "identity_status": "CANONICAL", "epistemic_state": "PARTIAL", "repository_surfaces": ["owner/VX"]},
                {"system_id": "NEXNET", "role": "Research", "identity_status": "UNVERIFIED", "epistemic_state": "UNVERIFIED", "repository_surfaces": ["owner/NEXENT (candidate)"]}
            ],
            "connections": [
                {"connection_id": "E1", "source_system": "VLNS", "target_system": "VAIXLNS", "contract_state": "DOCUMENTED", "live_state": "UNVERIFIED", "authenticated": False}
            ],
            "capability_catalog": [
                {"capability_id": "CAP-1", "name": "Architecture candidates", "status": "SPECIFIED", "implementation_state": "UNVERIFIED", "description": "architecture synthesis"}
            ],
            "properties": [
                {"property_id": "PROP-1", "category": "IDENTITY", "name": "Repository mapping", "value": "VLNS ↔ NAXLNS is unverified", "state": "UNVERIFIED", "source_refs": ["docs/identity.md"]}
            ],
            "gaps": [
                {"gap_id": "GAP-1", "severity": "BLOCKER", "topic": "Identity", "issue": "VLNS mapping unresolved", "required_evidence": "identity evidence", "next_action": "resolve mapping"}
            ]
        })
        self.write_json("registry/vlns_connection_status.v1.json", {
            "status": "UNREACHABLE_FROM_CURRENT_EXECUTION_ENVIRONMENT",
            "authenticated_connection": False,
            "last_probe": "2026-10-06"
        })
        self.engine = CommandEngine(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def write_json(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def test_federation_status_shows_four_systems_without_claiming_live_links(self):
        result = self.engine.execute("federation status")
        self.assertTrue(result["ok"], result["lines"])
        self.assertEqual(result["data"]["system_count"], 4)
        self.assertEqual(result["data"]["verified_live_links"], 0)
        self.assertFalse(result["data"]["external_probe_performed"])
        self.assertIn("UNVERIFIED", "\n".join(result["lines"]))

    def test_vlns_inspection_preserves_candidate_identity(self):
        result = self.engine.execute("federation inspect VLNS")
        self.assertTrue(result["ok"], result["lines"])
        self.assertEqual(result["data"]["identity_status"], "UNVERIFIED")
        self.assertIn("NAXLNS", " ".join(result["data"]["repository_surfaces"]))

    def test_capability_search_finds_architecture_capability(self):
        result = self.engine.execute("federation capabilities architecture")
        self.assertTrue(result["ok"], result["lines"])
        self.assertEqual([row["capability_id"] for row in result["data"]["capabilities"]], ["CAP-1"])

    def test_attribute_search_finds_identity_property(self):
        result = self.engine.execute("federation attributes identity")
        self.assertTrue(result["ok"], result["lines"])
        self.assertEqual([row["property_id"] for row in result["data"]["properties"]], ["PROP-1"])

    def test_gap_board_exposes_blocker(self):
        result = self.engine.execute("federation gaps")
        self.assertTrue(result["ok"], result["lines"])
        self.assertEqual(result["data"]["gaps"][0]["severity"], "BLOCKER")

    def test_missing_federation_catalog_fails_closed(self):
        empty = CommandEngine(self.root / "empty")
        result = empty.execute("federation status")
        self.assertFalse(result["ok"])
        self.assertIn("missing", result["summary"].lower())


if __name__ == "__main__":
    unittest.main()
