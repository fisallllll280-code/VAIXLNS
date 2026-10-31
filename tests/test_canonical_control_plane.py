import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.admission_gate import genome_digest


class TestCanonicalControlPlane(unittest.TestCase):
    def test_genome_integrity(self):
        genome = json.loads((ROOT / "project.genome").read_text(encoding="utf-8"))
        self.assertEqual(genome["integrity"]["canonical_hash"], genome_digest(genome))
        self.assertEqual(genome["canonical_source"]["authority"], "Ω0_GENESIS_CORE")

    def test_master_index(self):
        index = json.loads(
            (ROOT / "registry/omega/omega-000-master-index.json").read_text(encoding="utf-8")
        )
        self.assertEqual(index["index_id"], "Ω.000")
        self.assertEqual(index["golden_source"], "project.genome::v1.0.0")
        for record in index["records"]:
            self.assertIn(
                record["epistemic_state"],
                {
                    "PROPOSAL", "SPECIFIED", "IMPLEMENTED", "VERIFIED",
                    "PARTIAL", "MISSING", "CONFLICT", "RECOVERED",
                },
            )
            if record["epistemic_state"] == "VERIFIED":
                self.assertTrue(record["evidence_refs"])

    def test_admission_gate_passes(self):
        result = subprocess.run(
            [sys.executable, "scripts/admission_gate.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["admission"], "ADMITTED")
        self.assertEqual(payload["path_hygiene"], "PASS")


if __name__ == "__main__":
    unittest.main()
