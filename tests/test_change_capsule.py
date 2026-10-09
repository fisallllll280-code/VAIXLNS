import unittest

from scripts.validate_change_capsule import CapsuleError, validate_capsule


def valid_capsule():
    return {
        "capsule_version": "1.0.0",
        "capsule_id": "omega-capsule-test-001",
        "task": {
            "task_id": "task-001",
            "summary": "Add a guarded test fixture",
            "acceptance_criteria": ["Validator accepts the fixture"],
        },
        "repository": {
            "repository": "fisallllll280-code/VAIXLNS",
            "base_revision": "a" * 40,
        },
        "change": {
            "allowed_paths": ["tests/fixtures/example.json"],
            "changed_paths": ["tests/fixtures/example.json"],
            "diff_sha256": "b" * 64,
        },
        "verification": {
            "environment": "python-3.x / ubuntu-latest",
            "checks": [{"name": "unit-tests", "result": "PASS", "command": "python -m unittest"}],
            "evidence_refs": ["artifact://capsule-test/evidence.json"],
        },
        "admission": {"state": "ADMITTED", "reason": "All declared checks passed"},
    }


class ChangeCapsuleTests(unittest.TestCase):
    def test_accepts_valid_admitted_capsule(self):
        self.assertTrue(validate_capsule(valid_capsule()))

    def test_rejects_missing_lineage_revision(self):
        capsule = valid_capsule()
        capsule["repository"]["base_revision"] = "main"
        with self.assertRaisesRegex(CapsuleError, "base_revision"):
            validate_capsule(capsule)

    def test_rejects_change_outside_allowed_scope(self):
        capsule = valid_capsule()
        capsule["change"]["changed_paths"].append("project.genome")
        with self.assertRaisesRegex(CapsuleError, "outside authorized scope"):
            validate_capsule(capsule)

    def test_rejects_backslash_path_separators(self):
        capsule = valid_capsule()
        capsule["change"]["changed_paths"] = ["tests\\\\..\\\\project.genome"]
        capsule["change"]["allowed_paths"] = ["tests\\\\..\\\\project.genome"]
        with self.assertRaisesRegex(CapsuleError, "invalid path"):
            validate_capsule(capsule)

    def test_rejects_parent_path_traversal(self):
        capsule = valid_capsule()
        capsule["change"]["changed_paths"] = ["../project.genome"]
        capsule["change"]["allowed_paths"] = ["../project.genome"]
        with self.assertRaisesRegex(CapsuleError, "parent traversal"):
            validate_capsule(capsule)

    def test_rejects_admission_when_check_failed(self):
        capsule = valid_capsule()
        capsule["verification"]["checks"][0]["result"] = "FAIL"
        with self.assertRaisesRegex(CapsuleError, "not PASS"):
            validate_capsule(capsule)

    def test_rejects_admission_without_evidence(self):
        capsule = valid_capsule()
        capsule["verification"]["evidence_refs"] = []
        with self.assertRaisesRegex(CapsuleError, "evidence reference"):
            validate_capsule(capsule)

    def test_allows_blocked_capsule_with_failure(self):
        capsule = valid_capsule()
        capsule["verification"]["checks"][0]["result"] = "FAIL"
        capsule["admission"] = {"state": "BLOCKED", "reason": "Regression test failed"}
        self.assertIn("admission state: BLOCKED", validate_capsule(capsule))

    def test_rejects_duplicate_changed_paths(self):
        capsule = valid_capsule()
        capsule["change"]["changed_paths"].append(capsule["change"]["changed_paths"][0])
        with self.assertRaisesRegex(CapsuleError, "duplicate paths"):
            validate_capsule(capsule)


if __name__ == "__main__":
    unittest.main()
