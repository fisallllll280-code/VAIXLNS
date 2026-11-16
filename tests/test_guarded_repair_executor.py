import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.guarded_repair_executor import RepairError, prepare_repair

REV = "a" * 40


def make_plan(path: str, original: bytes, **overrides):
    change = {
        "path": path,
        "operation": "replace_text",
        "expected_sha256": hashlib.sha256(original).hexdigest(),
        "old_text": "broken_value",
        "new_text": "correct_value",
        "expected_occurrences": 1,
    }
    change.update(overrides.pop("change", {}))
    plan = {
        "schema_version": "1.0.0",
        "repair_id": "FIX-TEST-001",
        "repository": "owner/repo",
        "base_revision": REV,
        "change": change,
    }
    plan.update(overrides)
    return plan


class GuardedRepairExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        self.target = self.root / "src" / "module.py"
        self.original = b"value = 'broken_value'\n"
        self.target.write_bytes(self.original)

    def tearDown(self):
        self.temp.cleanup()

    def test_dry_run_does_not_modify_file(self):
        receipt = prepare_repair(make_plan("src/module.py", self.original), self.root, REV)
        self.assertEqual(receipt["status"], "PATCH_CANDIDATE_READY")
        self.assertFalse(receipt["applied"])
        self.assertEqual(receipt["verification_state"], "NOT_VERIFIED")
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_explicit_apply_replaces_expected_text(self):
        receipt = prepare_repair(make_plan("src/module.py", self.original), self.root, REV, apply=True)
        self.assertEqual(self.target.read_bytes(), b"value = 'correct_value'\n")
        self.assertEqual(receipt["status"], "PATCH_APPLIED_NOT_VERIFIED")
        self.assertTrue(receipt["applied"])
        self.assertEqual(receipt["postimage_sha256_observed"], hashlib.sha256(self.target.read_bytes()).hexdigest())

    def test_stale_revision_fails_closed(self):
        with self.assertRaisesRegex(RepairError, "current checkout"):
            prepare_repair(make_plan("src/module.py", self.original), self.root, "b" * 40)

    def test_preimage_hash_mismatch_fails_closed(self):
        plan = make_plan("src/module.py", self.original)
        plan["change"]["expected_sha256"] = "0" * 64
        with self.assertRaisesRegex(RepairError, "does not match"):
            prepare_repair(plan, self.root, REV, apply=True)
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_non_unique_anchor_fails_closed(self):
        original = b"broken_value + broken_value\n"
        self.target.write_bytes(original)
        with self.assertRaisesRegex(RepairError, "occurrence count"):
            prepare_repair(make_plan("src/module.py", original), self.root, REV, apply=True)
        self.assertEqual(self.target.read_bytes(), original)

    def test_canonical_genome_is_protected(self):
        genome = self.root / "project.genome"
        genome.write_text("broken_value", encoding="utf-8")
        original = genome.read_bytes()
        with self.assertRaisesRegex(RepairError, "read-only"):
            prepare_repair(make_plan("project.genome", original), self.root, REV, apply=True)
        self.assertEqual(genome.read_bytes(), original)

    def test_master_index_is_protected(self):
        index = self.root / "registry" / "omega" / "omega-000-master-index.json"
        index.parent.mkdir(parents=True)
        index.write_text('{"value":"broken_value"}', encoding="utf-8")
        original = index.read_bytes()
        with self.assertRaisesRegex(RepairError, "read-only"):
            prepare_repair(make_plan("registry/omega/omega-000-master-index.json", original), self.root, REV, apply=True)
        self.assertEqual(index.read_bytes(), original)

    def test_path_traversal_is_blocked(self):
        outside = self.root.parent / "outside.txt"
        outside.write_text("broken_value", encoding="utf-8")
        with self.assertRaisesRegex(RepairError, "traversal"):
            prepare_repair(make_plan("../outside.txt", outside.read_bytes()), self.root, REV)

    def test_unknown_operation_is_blocked(self):
        plan = make_plan("src/module.py", self.original, change={"operation": "run_shell"})
        with self.assertRaisesRegex(RepairError, "only replace_text"):
            prepare_repair(plan, self.root, REV)

    def test_multiple_file_changes_are_not_accepted(self):
        plan = make_plan("src/module.py", self.original)
        plan["change"] = [plan["change"], plan["change"]]
        with self.assertRaisesRegex(RepairError, "change must be an object"):
            prepare_repair(plan, self.root, REV)


if __name__ == "__main__":
    unittest.main()
