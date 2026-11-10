"""Tests for the first executable ARC-X Ω runtime slice."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.arc_x_runtime import reconstruct, verify_artifacts, inspect_artifacts


class ArcXRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.output = self.root / ".arcx"
        self._git("init", "-q")
        self._git("config", "user.email", "arcx-tests@example.invalid")
        self._git("config", "user.name", "ARC-X Tests")
        (self.root / "README.md").write_text("test repository\n", encoding="utf-8")
        genome = {"system": {"id": "TEST-SYSTEM", "canonical_repository": "example/fixture"},
                  "genesis": {"authority_anchor": "TEST-ANCHOR"},
                  "master_index": {"id": "Ω.000"},
                  "canonical_source": {"status": "CANONICAL"}}
        (self.root / "project.genome").write_text(json.dumps(genome, ensure_ascii=False), encoding="utf-8")
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "demo.py").write_text("print('ok')\n", encoding="utf-8")
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_demo.py").write_text("assert 1 + 1 == 2\n", encoding="utf-8")
        (self.root / ".env").write_text("SECRET=never-index-this\n", encoding="utf-8")
        self._git("add", "README.md", "project.genome", "scripts/demo.py", "tests/test_demo.py")
        self._git("commit", "-qm", "fixture")

    def _git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args],
                                capture_output=True, text=True, check=False)
        if result.returncode:
            self.fail(f"git {' '.join(args)} failed: {result.stderr}")

    def test_reconstruct_verify_and_deterministic_eir(self):
        result = reconstruct(self.root, self.output)
        self.assertEqual(result["result"], "RECONSTRUCTION_CREATED")
        self.assertEqual(result["verification_state"], "PARTIAL")
        self.assertEqual(result["authority_decision"], "PENDING")
        report = verify_artifacts(self.root, self.output)
        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["semantic_correctness"], "NOT_CLAIMED")
        self.assertTrue(all(v == "PASS" for v in report["checks"].values()))
        before = (self.output / "eir.json").read_bytes()
        reconstruct(self.root, self.output)
        self.assertEqual(before, (self.output / "eir.json").read_bytes())

    def test_source_mutation_fails_integrity_verification(self):
        reconstruct(self.root, self.output)
        (self.root / "README.md").write_text("mutated after fingerprint\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "SOURCE_CONTENT_HASH_MISMATCH|SOURCE_MANIFEST_MISMATCH"):
            verify_artifacts(self.root, self.output)

    def test_revision_pin_mismatch_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "REVISION_PIN_MISMATCH"):
            reconstruct(self.root, self.output, "0" * 40)

    def test_authority_is_never_self_granted(self):
        reconstruct(self.root, self.output)
        eir = json.loads((self.output / "eir.json").read_text(encoding="utf-8"))
        record = json.loads((self.output / "reconstruction.record.json").read_text(encoding="utf-8"))
        self.assertFalse(eir["governance"]["self_authority"])
        self.assertFalse(eir["governance"]["canonical_write_permitted"])
        self.assertEqual(eir["governance"]["authority_decision"], "PENDING")
        self.assertFalse(record["self_authority"])
        self.assertEqual(record["verification_state"], "PARTIAL")
        self.assertEqual(record["proof_status"], "PENDING")

    def test_secret_files_and_generated_artifacts_are_excluded(self):
        reconstruct(self.root, self.output)
        receipt = json.loads((self.output / "source.receipt.json").read_text(encoding="utf-8"))
        paths = {item["path"] for item in receipt["materials"]}
        self.assertNotIn(".env", paths)
        self.assertNotIn(".arcx/eir.json", paths)
        self.assertGreaterEqual(receipt["excluded_file_counts"]["secret_material"], 1)

    def test_inspect_does_not_promote_state(self):
        reconstruct(self.root, self.output)
        result = inspect_artifacts(self.output)
        self.assertEqual(result["verification_state"], "PARTIAL")
        self.assertEqual(result["authority_decision"], "PENDING")
        self.assertIsNone(result["execution_evidence"])


if __name__ == "__main__":
    unittest.main()
