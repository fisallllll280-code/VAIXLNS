import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.omega_git_diff_evidence import calculate_diff, verify_capsule


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()


class OmegaGitDiffEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "VAIXLNS Test")
        git(self.root, "config", "user.email", "test@vaixlns.invalid")
        (self.root / "existing.txt").write_text("before\n", encoding="utf-8")
        git(self.root, "add", "existing.txt")
        git(self.root, "commit", "-qm", "base")
        self.base = git(self.root, "rev-parse", "HEAD")
        (self.root / "existing.txt").write_text("after\n", encoding="utf-8")
        (self.root / "new.txt").write_text("new file\n", encoding="utf-8")
        git(self.root, "add", "existing.txt", "new.txt")
        git(self.root, "commit", "-qm", "candidate")
        self.candidate = git(self.root, "rev-parse", "HEAD")
        self.diff = calculate_diff(self.root, self.base, self.candidate)

    def tearDown(self):
        self.temp.cleanup()

    def capsule(self):
        return {
            "repository": {"repository": "example/fixture", "base_revision": self.base},
            "change": {
                "allowed_paths": ["existing.txt", "new.txt"],
                "changed_paths": self.diff["changed_paths"],
                "diff_sha256": self.diff["diff_sha256"],
            },
        }

    def test_hash_and_changed_paths_are_derived_from_git_objects(self):
        result = verify_capsule(self.root, self.capsule(), self.candidate)
        self.assertEqual(result["state"], "MATCH")
        self.assertTrue(result["digest_matches"])
        self.assertTrue(result["changed_paths_match"])
        self.assertEqual(result["actual_changed_paths"], ["existing.txt", "new.txt"])
        self.assertEqual(result["admission_decision"], "NOT_EVALUATED")

    def test_caller_supplied_wrong_digest_is_rejected(self):
        capsule = self.capsule()
        capsule["change"]["diff_sha256"] = "0" * 64
        result = verify_capsule(self.root, capsule, self.candidate)
        self.assertEqual(result["state"], "MISMATCH")
        self.assertFalse(result["digest_matches"])

    def test_changed_path_claim_must_match_git(self):
        capsule = self.capsule()
        capsule["change"]["changed_paths"] = ["existing.txt"]
        result = verify_capsule(self.root, capsule, self.candidate)
        self.assertEqual(result["state"], "MISMATCH")
        self.assertFalse(result["changed_paths_match"])

    def test_out_of_scope_path_fails_even_with_correct_digest(self):
        capsule = self.capsule()
        capsule["change"]["allowed_paths"] = ["existing.txt"]
        result = verify_capsule(self.root, capsule, self.candidate)
        self.assertEqual(result["state"], "MISMATCH")
        self.assertEqual(result["scope_violations"], ["new.txt"])

    def test_drive_qualified_scope_grant_is_rejected(self):
        capsule = self.capsule()
        capsule["change"]["allowed_paths"] = ["C:/Windows"]
        with self.assertRaisesRegex(ValueError, "drive-qualified"):
            verify_capsule(self.root, capsule, self.candidate)

    def test_candidate_revision_must_be_a_full_commit_sha(self):
        with self.assertRaisesRegex(ValueError, "full 40-character"):
            calculate_diff(self.root, self.base, "HEAD")

    def test_capsule_does_not_get_to_claim_admission(self):
        result = verify_capsule(self.root, self.capsule(), self.candidate)
        self.assertEqual(result["admission_decision"], "NOT_EVALUATED")
        self.assertIn("does not authenticate evidence references", result["note"])


if __name__ == "__main__":
    unittest.main()
