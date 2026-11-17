from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.capture_pinned_repo_snapshots import (
    REQUIRED_REPOSITORIES,
    SnapshotError,
    capture_from_mirror,
    validate_plan,
)


def run(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode:
        raise AssertionError(f"command failed: {command}\n{result.stderr}")
    return result.stdout.strip()


class PinnedSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source_bare = self.root / "origin.git"
        run(["git", "init", "--bare", str(self.source_bare)])
        self.work = self.root / "work"
        run(["git", "clone", str(self.source_bare), str(self.work)])
        run(["git", "-C", str(self.work), "checkout", "-b", "main"])
        run(["git", "-C", str(self.work), "config", "user.name", "Snapshot Test"])
        run(["git", "-C", str(self.work), "config", "user.email", "snapshot-test@example.invalid"])
        (self.work / "README.md").write_text("revision-pinned snapshot test\n", encoding="utf-8")
        (self.work / ".hidden-config").write_text("kept\n", encoding="utf-8")
        (self.work / "nested").mkdir()
        (self.work / "nested/file.txt").write_text("payload\n", encoding="utf-8")
        (self.work / "nested/link.txt").symlink_to("file.txt")
        run(["git", "-C", str(self.work), "add", "-A"])
        run(["git", "-C", str(self.work), "commit", "-m", "fixture"])
        run(["git", "-C", str(self.work), "push", "origin", "HEAD:main"])
        self.commit = run(["git", "-C", str(self.work), "rev-parse", "HEAD"])
        self.mirror = self.root / "mirror.git"
        run(["git", "clone", "--mirror", str(self.source_bare), str(self.mirror)])

    def tearDown(self):
        self.temp.cleanup()

    def test_plan_requires_four_allowlisted_repositories_and_full_sha(self):
        plan = {"schema": "VAIXLNS.PinnedSnapshotPlan.v1", "repositories": [
            {"repository": repo, "commit_sha": self.commit} for repo in REQUIRED_REPOSITORIES
        ]}
        normalized = validate_plan(plan)
        self.assertEqual([item["repository"] for item in normalized], list(REQUIRED_REPOSITORIES))
        with self.assertRaisesRegex(SnapshotError, "REQUIRED_REPOSITORIES_MISSING"):
            validate_plan({"schema": plan["schema"], "repositories": plan["repositories"][:3]})
        altered = json.loads(json.dumps(plan))
        altered["repositories"][0]["commit_sha"] = "main"
        with self.assertRaisesRegex(SnapshotError, "FULL_COMMIT_SHA_REQUIRED"):
            validate_plan(altered)
        sha256_style = json.loads(json.dumps(plan))
        sha256_style["repositories"][0]["commit_sha"] = "a" * 64
        with self.assertRaisesRegex(SnapshotError, "FULL_COMMIT_SHA_REQUIRED"):
            validate_plan(sha256_style)

    def test_snapshot_bundle_and_tree_restore_with_hidden_files_and_symlinks(self):
        out = self.root / "snapshots"
        receipt = capture_from_mirror(self.mirror, REQUIRED_REPOSITORIES[0], self.commit, out)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["source_tree_restore_test"], "PASS")
        self.assertEqual(receipt["git_bundle_restore_test"], "PASS")
        folder = next(out.iterdir())
        inventory = json.loads(next(folder.glob("*.file-inventory.json")).read_text(encoding="utf-8"))
        paths = {entry["path"] for entry in inventory["entries"]}
        self.assertIn(".hidden-config", paths)
        self.assertIn("nested/link.txt", paths)
        self.assertTrue(next(folder.glob("*.git.bundle")).is_file())
        self.assertTrue(next(folder.glob("*.source-tree.tar.gz")).is_file())

    def test_git_lfs_pointer_is_retained_but_blocks_complete_status(self):
        pointer = (
            "version https://git-lfs.github.com/spec/v1\n"
            "oid sha256:" + "a" * 64 + "\n"
            "size 2048\n"
        )
        (self.work / "large-model.bin").write_text(pointer, encoding="ascii")
        run(["git", "-C", str(self.work), "add", "large-model.bin"])
        run(["git", "-C", str(self.work), "commit", "-m", "lfs pointer fixture"])
        run(["git", "-C", str(self.work), "push", "origin", "HEAD:main"])
        new_sha = run(["git", "-C", str(self.work), "rev-parse", "HEAD"])
        run(["git", "--git-dir", str(self.mirror), "fetch", "origin", new_sha])
        out = self.root / "snapshots-lfs"
        receipt = capture_from_mirror(self.mirror, REQUIRED_REPOSITORIES[0], new_sha, out)
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertEqual(receipt["git_lfs_pointer_count"], 1)
        self.assertTrue(any(item["code"] == "GIT_LFS_PAYLOAD_NOT_CAPTURED" for item in receipt["blockers"]))

    def test_submodule_gitlink_is_explicit_blocker(self):
        gitlink_sha = self.commit
        run(["git", "-C", str(self.work), "update-index", "--add", "--cacheinfo", f"160000,{gitlink_sha},vendor/example"])
        run(["git", "-C", str(self.work), "commit", "-m", "submodule gitlink fixture"])
        run(["git", "-C", str(self.work), "push", "origin", "HEAD:main"])
        new_sha = run(["git", "-C", str(self.work), "rev-parse", "HEAD"])
        run(["git", "--git-dir", str(self.mirror), "fetch", "origin", new_sha])
        out = self.root / "snapshots-submodule"
        receipt = capture_from_mirror(self.mirror, REQUIRED_REPOSITORIES[0], new_sha, out)
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertEqual(receipt["submodule_count"], 1)
        self.assertEqual(receipt["blockers"][0]["code"], "SUBMODULE_CONTENT_NOT_CAPTURED")

    def test_snapshot_output_is_immutable_and_collision_fails(self):
        out = self.root / "snapshots-immutable"
        capture_from_mirror(self.mirror, REQUIRED_REPOSITORIES[0], self.commit, out)
        with self.assertRaises(FileExistsError):
            capture_from_mirror(self.mirror, REQUIRED_REPOSITORIES[0], self.commit, out)


if __name__ == "__main__":
    unittest.main()
