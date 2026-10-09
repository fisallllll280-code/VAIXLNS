import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_innovation_operation_index import build, outputs, rid

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

    def test_stable_ids(self):
        self.assertEqual(rid("Identity Fabric","Identity"), rid("Identity Fabric","Identity"))
        self.assertNotEqual(rid("Identity Fabric","Identity"), rid("Contract Fabric","Contracts"))

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
