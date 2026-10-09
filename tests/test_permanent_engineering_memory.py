import tempfile
import unittest
from pathlib import Path

from scripts.permanent_engineering_memory import MemoryValidationError, append_record, verify_ledger, search_records


def sample_record(record_id="mem-001", state="IMPLEMENTED"):
    return {
        "schema_version": "1.0.0",
        "record_id": record_id,
        "memory_type": "DESIGN",
        "subject": "Permanent engineering memory",
        "summary": "Evidence-bound memory preserves provenance and lineage.",
        "epistemic_state": state,
        "lifecycle_state": "ACTIVE",
        "provenance": {
            "repository": "owner/repo",
            "revision": "abc123",
            "path": "docs/memory.md",
            "content_sha256": "a" * 64
        },
        "evidence": [{"kind": "test", "ref": "tests/test_memory.py", "digest": "b" * 64}],
        "verification": {"method": "unit test", "result": "PASS", "reproduction_command": "python -m unittest"},
        "lineage": {"derived_from": [], "supersedes": [], "related": []},
        "recorded_at": "2026-10-09T00:00:00Z"
    }


class PermanentEngineeringMemoryTests(unittest.TestCase):
    def test_append_and_verify_hash_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "memory.jsonl"
            first = append_record(path, sample_record())
            second = append_record(path, sample_record("mem-002"))
            self.assertEqual(second["previous_record_hash"], first["record_hash"])
            report = verify_ledger(path)
            self.assertTrue(report["valid"])
            self.assertEqual(report["records"], 2)

    def test_duplicate_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "memory.jsonl"
            append_record(path, sample_record())
            with self.assertRaises(MemoryValidationError):
                append_record(path, sample_record())

    def test_verified_requires_pass_command_and_evidence(self):
        record = sample_record(state="VERIFIED")
        record["verification"]["result"] = "NOT_RUN"
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(MemoryValidationError):
                append_record(Path(temp) / "memory.jsonl", record)

    def test_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "memory.jsonl"
            append_record(path, sample_record())
            raw = path.read_text(encoding="utf-8").replace("Evidence-bound", "Tampered")
            path.write_text(raw, encoding="utf-8")
            with self.assertRaises(MemoryValidationError):
                verify_ledger(path)

    def test_search_returns_matching_record(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "memory.jsonl"
            append_record(path, sample_record())
            found = search_records(path, "provenance")
            self.assertEqual([item["record_id"] for item in found], ["mem-001"])


if __name__ == "__main__":
    unittest.main()
