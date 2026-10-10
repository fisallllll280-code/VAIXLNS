import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_innovation_operation_index import build, outputs, rid, state

class TestInnovationOperationIndex(unittest.TestCase):
    def test_index_contains_cross_source_innovations(self):
        records = build(ROOT)
        names = {record["name"] for record in records}
        self.assertGreater(len(records), 60)
        self.assertIn("Ω-Pattern Foundry / Private Pattern Intelligence Boundary", names)
        self.assertIn("ARC-X Ω — Epistemic Reality Compiler / Repository Reconstruction", names)
        self.assertTrue(any("Research-to-Engineering Decision Fabric" in name for name in names))

    def test_every_record_has_description_and_operating_mechanism(self):
        for record in build(ROOT):
            self.assertTrue(record["description"].strip(), record["name"])
            self.assertTrue(record["operating_mechanism"], record["name"])
            self.assertIn(record["profile_quality"], {"SOURCE_BACKED","CURATED_DESIGN_DRAFT","RULE_DERIVED_DRAFT"})
            self.assertFalse(record["canonical_promotion_allowed"], record["name"])

    def test_state_parser_does_not_promote_substrings(self):
        self.assertEqual(state("IMPLEMENTEDIFIED"), "SOURCE-ASSERTED")
        self.assertEqual(state("IMPLEMENTED / PARTIAL"), "PARTIAL")
        self.assertEqual(state("UNKNOWN"), "UNKNOWN")
        self.assertEqual(state("PROPOSED"), "PROPOSAL")

    def test_stable_ids(self):
        self.assertEqual(rid("Identity Fabric","Identity"), rid("Identity Fabric","Identity"))
        self.assertNotEqual(rid("Identity Fabric","Identity"), rid("Contract Fabric","Contracts"))

    def test_profile_enrichment_never_adds_a_synthetic_proposal_state(self):
        records = {record["name"]: record for record in build(ROOT)}
        redf = records["Ω Research-to-Engineering Decision Fabric (REDF)"]
        self.assertEqual(redf["status"], "IMPLEMENTED")
        self.assertNotIn("PROPOSAL", redf["source_statuses"])
        generator = records["VAIXLNS Innovation Operation Index Generator"]
        self.assertEqual(generator["status"], "SPECIFIED")
        self.assertNotIn("PROPOSAL", generator["source_statuses"])
        self.assertFalse(generator["canonical_promotion_allowed"])

    def test_measurement_states_do_not_overwrite_readiness_state(self):
        records = {record["name"]: record for record in build(ROOT)}
        identity = records["Identity Fabric"]
        self.assertEqual(identity["status"], "CANONICAL")
        self.assertNotIn("CONFLICT", identity["source_statuses"])
        self.assertTrue(any(
            obs["axis"] == "measurement" and obs["state"] == "PROPOSAL"
            for obs in identity["status_observations"]
        ))

    def test_generated_outputs_are_current(self):
        for path, expected in outputs(ROOT).items():
            self.assertTrue(path.is_file(), str(path))
            self.assertEqual(path.read_text(encoding="utf-8"), expected, str(path))

    def test_validator_passes(self):
        result = subprocess.run([sys.executable,"tools/validate_innovation_operation_index.py"],
            cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__ == "__main__":
    unittest.main()
