import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.repository_fleet_intake import (
    IntakeError, build_plan, execute_intake, validate_scope,
)


def meta(full_name, *, private=False, size=1024):
    return {
        "full_name": full_name, "private": private, "archived": False,
        "default_branch": "main", "pushed_at": "2026-11-01T00:00:00Z",
        "size": size, "clone_url": f"https://github.com/{full_name}.git",
        "license": {"spdx_id": "MIT"},
    }


class RepositoryFleetIntakeTests(unittest.TestCase):
    def test_scope_rejects_duplicates_and_path_traversal(self):
        with self.assertRaises(IntakeError):
            validate_scope("fisallllll280-code", ["VAIXLNS", "VAIXLNS"], 20)
        with self.assertRaises(IntakeError):
            validate_scope("fisallllll280-code", ["../outside"], 20)

    def test_plan_is_read_only_and_deterministic(self):
        reader = lambda name: meta(name)
        first = build_plan("fisallllll280-code", ["VAIXLNS"], metadata_reader=reader)
        second = build_plan("fisallllll280-code", ["VAIXLNS"], metadata_reader=reader)
        self.assertEqual(first, second)
        self.assertEqual(first["mode"], "PLAN_ONLY")
        self.assertFalse(first["safety"]["remote_write"])
        self.assertEqual(first["items"][0]["status"], "READY")

    def test_private_repository_is_never_admitted(self):
        plan = build_plan(
            "fisallllll280-code", ["private-repo"],
            metadata_reader=lambda name: meta(name, private=True),
        )
        self.assertEqual(plan["items"][0]["status"], "SKIPPED_PRIVATE")

    def test_identity_mismatch_is_blocked(self):
        plan = build_plan(
            "fisallllll280-code", ["VAIXLNS"],
            metadata_reader=lambda name: meta("other-owner/VAIXLNS"),
        )
        self.assertEqual(plan["items"][0]["status"], "BLOCKED")

    def test_size_budget_blocks_entire_ready_batch(self):
        plan = build_plan(
            "fisallllll280-code", ["one", "two"],
            max_total_size_mb=1,
            metadata_reader=lambda name: meta(name, size=2048),
        )
        self.assertTrue(all(x["status"] == "BLOCKED_SIZE_BUDGET" for x in plan["items"]))

    def test_execution_requires_explicit_network_gate(self):
        plan = build_plan("fisallllll280-code", ["VAIXLNS"], metadata_reader=lambda n: meta(n))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(IntakeError, "NETWORK_GATE_CLOSED"):
                execute_intake(plan, Path(tmp) / "fleet", network_enabled=False)

    def test_existing_mirror_is_never_modified(self):
        plan = build_plan("fisallllll280-code", ["VAIXLNS"], metadata_reader=lambda n: meta(n))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fleet"
            root.mkdir()
            target = root / "fisallllll280-code--VAIXLNS.git"
            target.mkdir()
            marker = target / "preserve.txt"
            marker.write_text("keep", encoding="utf-8")
            calls = []
            def runner(args, timeout=0):
                calls.append(args)
                return subprocess.CompletedProcess(args, 0, "abc\n", "")
            receipt = execute_intake(plan, root, network_enabled=True, git_runner=runner)
            self.assertEqual(receipt["results"][0]["intake_status"], "EXISTS_NOT_MODIFIED")
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            self.assertEqual(calls, [])

    def test_mirror_clone_and_verification(self):
        plan = build_plan("fisallllll280-code", ["VAIXLNS"], metadata_reader=lambda n: meta(n))
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            def runner(args, timeout=0):
                calls.append(args)
                if args[:3] == ["git", "clone", "--mirror"]:
                    Path(args[-1]).mkdir()
                    return subprocess.CompletedProcess(args, 0, "", "")
                if args[-1] == "HEAD":
                    return subprocess.CompletedProcess(args, 0, "a" * 40 + "\n", "")
                return subprocess.CompletedProcess(args, 0, "true\n", "")
            receipt = execute_intake(plan, Path(tmp) / "fleet", network_enabled=True, git_runner=runner)
            self.assertEqual(receipt["results"][0]["intake_status"], "MIRRORED")
            self.assertEqual(receipt["results"][0]["observed_head_sha"], "a" * 40)
            self.assertFalse(receipt["safety"]["source_code_execution"])
            self.assertEqual(len(calls), 3)

    def test_failed_partial_clone_is_preserved(self):
        plan = build_plan("fisallllll280-code", ["VAIXLNS"], metadata_reader=lambda n: meta(n))
        with tempfile.TemporaryDirectory() as tmp:
            def runner(args, timeout=0):
                if args[:3] == ["git", "clone", "--mirror"]:
                    Path(args[-1]).mkdir()
                    return subprocess.CompletedProcess(args, 1, "", "network interrupted")
                raise AssertionError("verification must not run after failed clone")
            receipt = execute_intake(plan, Path(tmp) / "fleet", network_enabled=True, git_runner=runner)
            self.assertEqual(receipt["results"][0]["intake_status"], "CLONE_FAILED_PARTIAL_PRESERVED")
            self.assertTrue(Path(receipt["results"][0]["local_path"]).is_dir())


if __name__ == "__main__":
    unittest.main()
