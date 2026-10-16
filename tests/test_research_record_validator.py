import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_research_records.py"
SPEC = importlib.util.spec_from_file_location("validate_research_records", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ResearchRecordValidatorTests(unittest.TestCase):
    def setUp(self):
        self.valid = {
            "record_id": "RESEARCH.TEST.001",
            "title": "A reproducible test record",
            "domain": ["computer_science"],
            "status": "PROPOSAL",
            "question": "Does the proposed method improve the baseline?",
            "sources": [],
            "method": {"description": "Compare against a pinned baseline."},
            "created_at": "2026-10-16",
        }

    def test_minimal_proposal_is_structurally_valid(self):
        self.assertEqual([], MODULE.validate_record(self.valid, Path("record.json")))

    def test_verified_without_evidence_is_rejected(self):
        record = dict(self.valid, status="VERIFIED")
        errors = MODULE.validate_record(record, Path("record.json"))
        self.assertTrue(any("evidence_refs" in e for e in errors))
        self.assertTrue(any("results" in e for e in errors))
        self.assertTrue(any("review" in e for e in errors))

    def test_source_without_locator_is_rejected(self):
        record = dict(self.valid, sources=[{"source_id": "SRC-1"}])
        errors = MODULE.validate_record(record, Path("record.json"))
        self.assertTrue(any("source[0]" in e for e in errors))

    def test_non_object_root_is_rejected(self):
        self.assertTrue(MODULE.validate_record([], Path("record.json")))

    def test_duplicate_ids_are_rejected_by_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.json").write_text(json.dumps(self.valid), encoding="utf-8")
            (root / "b.json").write_text(json.dumps(self.valid), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertIn("duplicate record_id", completed.stdout)


if __name__ == "__main__":
    unittest.main()
