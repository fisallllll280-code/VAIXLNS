import json
import tempfile
import unittest
from pathlib import Path
from scripts.arcx_reconstruct import reconstruct, sha256

class ArcxReconstructionTests(unittest.TestCase):
    def test_manifest_hashes_and_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            (root / "module.py").write_text("VALUE = 7\n", encoding="utf-8")
            result = reconstruct(root)
            record = result["model"]["files"][0]
            self.assertEqual(record["sha256"], sha256(b"VALUE = 7\n"))
            self.assertEqual(result["eir"]["sources"][0]["path"], "module.py")
            self.assertFalse(result["eir"]["promotion_allowed"])
            self.assertEqual(result["receipt"]["authority_decision"], "PENDING")

    def test_timestamp_is_not_part_of_normalized_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.md").write_text("hello", encoding="utf-8")
            first = reconstruct(root)
            second = reconstruct(root)
            self.assertEqual(first["receipt"]["normalized_model_sha256"], second["receipt"]["normalized_model_sha256"])

    def test_large_file_is_reported_as_gap(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "large.bin").write_bytes(b"x" * (5 * 1024 * 1024 + 1))
            result = reconstruct(root)
            self.assertEqual(result["receipt"]["reconstruction_state"], "PARTIAL")
            self.assertIn("large.bin", result["model"]["skipped_large_files"])

    def test_expected_revision_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "SOURCE_REVISION"):
                reconstruct(temp, "a" * 40)

    def test_outputs_are_json_compatible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.py").write_text("x=1\n", encoding="utf-8")
            result = reconstruct(root)
            self.assertEqual(json.loads(json.dumps(result["eir"]))["schema_version"], "arcx-eir-v1")

if __name__ == "__main__":
    unittest.main()
