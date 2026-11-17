import json
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_genome import build_genome, stable_artifact_id


class KnowledgeGenomeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "guide.md").write_text("# Guide\n\n[Spec](../schemas/contract.schema.json)\n", encoding="utf-8")
        (self.root / "schemas").mkdir()
        (self.root / "schemas" / "contract.schema.json").write_text('{"type":"object"}\n', encoding="utf-8")
        (self.root / "src.py").write_text("print('hello')\n", encoding="utf-8")
        (self.root / "docs" / "missing.md").write_text("[Missing](not-present.md)\n[Escape](../../outside.txt)\n", encoding="utf-8")
        (self.root / ".env").write_text("NEVER_CAPTURE_THIS=secret\n", encoding="utf-8")
        (self.root / ".git").mkdir()
        (self.root / ".git" / "metadata").write_text("excluded\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_snapshot_is_deterministic(self):
        a = build_genome(self.root, "owner/sample", 100_000)
        b = build_genome(self.root, "owner/sample", 100_000)
        self.assertEqual(a, b)
        self.assertEqual(a["snapshot_fingerprint"], b["snapshot_fingerprint"])

    def test_stable_identity_is_path_based_not_content_based(self):
        before = stable_artifact_id("owner/sample", "src.py")
        (self.root / "src.py").write_text("print('changed')\n", encoding="utf-8")
        after = stable_artifact_id("owner/sample", "src.py")
        self.assertEqual(before, after)
        report = build_genome(self.root, "owner/sample", 100_000)
        self.assertEqual(report["epistemic_state"], "PARTIAL")

    def test_excluded_directories_are_counted(self):
        report = build_genome(self.root, "owner/sample", 100_000)
        self.assertEqual(report["coverage"]["excluded_directories_skipped"], 1)

    def test_secret_files_are_excluded(self):
        report = build_genome(self.root, "owner/sample", 100_000)
        paths = [item["source"]["path"] for item in report["artifacts"]]
        self.assertNotIn(".env", paths)
        self.assertEqual(report["coverage"]["sensitive_files_excluded"], 1)

    def test_local_markdown_reference_is_recorded(self):
        report = build_genome(self.root, "owner/sample", 100_000)
        self.assertTrue(any(item["relation"] == "REFERENCES" for item in report["relations"]))

    def test_unresolved_and_out_of_root_links_are_reported(self):
        report = build_genome(self.root, "owner/sample", 100_000)
        statuses = {item["status"] for item in report["unresolved_references"]}
        self.assertIn("UNRESOLVED_LOCAL_TARGET", statuses)
        self.assertIn("LINK_ESCAPES_REPOSITORY", statuses)

    def test_exact_byte_duplicates_are_linked_not_semantically_merged(self):
        (self.root / "copy.py").write_text((self.root / "src.py").read_text(encoding="utf-8"), encoding="utf-8")
        report = build_genome(self.root, "owner/sample", 100_000)
        duplicates = [item for item in report["relations"] if item["relation"] == "EXACT_BYTE_DUPLICATE_OF"]
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(report["epistemic_state"], "PARTIAL")

    def test_changed_file_is_detected_and_missing_file_is_preserved(self):
        initial = build_genome(self.root, "owner/sample", 100_000)
        baseline = self.root / "baseline.json"
        baseline.write_text(json.dumps(initial), encoding="utf-8")
        (self.root / "src.py").write_text("print('new')\n", encoding="utf-8")
        (self.root / "schemas" / "contract.schema.json").unlink()
        updated = build_genome(self.root, "owner/sample", 100_000, baseline)
        states = {item["source"]["path"]: item["change_state"] for item in updated["artifacts"]}
        self.assertEqual(states["src.py"], "CHANGED")
        self.assertEqual(len(updated["missing_from_current_snapshot"]), 1)
        missing = updated["missing_from_current_snapshot"][0]
        self.assertEqual(missing["status"], "MISSING_FROM_CURRENT_SNAPSHOT")
        self.assertIn("NO_DELETE", missing["action"])

    def test_baseline_file_is_excluded_from_comparison_scan(self):
        initial = build_genome(self.root, "owner/sample", 100_000)
        baseline = self.root / "baseline.json"
        baseline.write_text(json.dumps(initial), encoding="utf-8")
        updated = build_genome(self.root, "owner/sample", 100_000, baseline)
        self.assertNotIn("baseline.json", [item["source"]["path"] for item in updated["artifacts"]])

    def test_oversized_files_are_skipped_and_counted(self):
        (self.root / "large.bin").write_bytes(b"x" * 256)
        report = build_genome(self.root, "owner/sample", 100)
        self.assertEqual(report["coverage"]["oversize_files_skipped"], 1)
        self.assertNotIn("large.bin", [x["source"]["path"] for x in report["artifacts"]])

    def test_hashes_never_promote_artifact_to_verified(self):
        report = build_genome(self.root, "owner/sample", 100_000)
        self.assertNotEqual(report["epistemic_state"], "VERIFIED")
        self.assertTrue(all(item["semantic_status"] == "NOT_EXTRACTED" for item in report["artifacts"]))


if __name__ == "__main__":
    unittest.main()
