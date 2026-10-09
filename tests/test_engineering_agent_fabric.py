"""Safety and determinism tests for the engineering-agent fabric."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.engineering_agent_fabric import AGENTS, RECIPES, build_plan, execute_approved, sha256_value


class EngineeringAgentFabricTests(unittest.TestCase):
    def make_project(self, root: Path):
        (root / "tests").mkdir()
        (root / "tests" / "test_example.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        (root / "src.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "README.md").write_text("Example project\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "tests@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test Runner"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "fixture"], check=True, capture_output=True)

    def test_plan_is_deterministic_and_hash_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            first = build_plan(root)
            second = build_plan(root)
            self.assertEqual(first, second)
            self.assertEqual(first["plan_sha256"], sha256_value({k: v for k, v in first.items() if k != "plan_sha256"}))

    def test_specialist_agents_are_planned_not_claimed_live(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            plan = build_plan(root)
            self.assertEqual(len(plan["agents"]), len(AGENTS))
            self.assertGreaterEqual(len(plan["agents"]), 10)
            self.assertEqual(plan["summary"]["agents_dispatched"], 0)
            self.assertTrue(all(agent["state"] == "PLANNED_NOT_DISPATCHED" for agent in plan["agents"]))

    def test_detected_commands_require_approval_and_are_not_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            plan = build_plan(root)
            self.assertTrue(all(candidate["approval_required"] for candidate in plan["execution_candidates"]))
            self.assertEqual(plan["summary"]["commands_executed"], 0)
            self.assertTrue(all(candidate["state"] in {"CANDIDATE_NOT_EXECUTED", "MANUAL_DISCOVERY_REQUIRED"} for candidate in plan["execution_candidates"]))

    def test_executor_rejects_revision_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            plan = build_plan(root)
            if not plan["repository_revision"]:
                self.skipTest("temporary directory is not a git repository")
            approval = root / "approval.json"
            approval.write_text(json.dumps({"repository_revision": "wrong", "authorized_by": "tester", "approval_ref": "TEST-1", "recipe_ids": ["python-unittest"]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly match"):
                execute_approved(root, plan, approval)

    def test_executor_rejects_unknown_or_non_allowlisted_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            plan = build_plan(root)
            approval = root / "approval.json"
            approval.write_text(json.dumps({"repository_revision": plan["repository_revision"], "authorized_by": "tester", "approval_ref": "TEST-2", "recipe_ids": ["rm-everything"]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "allowlisted"):
                execute_approved(root, plan, approval)


    def test_research_context_is_hash_checked_and_manifest_not_reindexed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(root)
            research = {
                "schema": "vaixlns.omega-research-fabric.v1",
                "index": {"inventory_sha256": "a" * 64},
                "query": "proof provenance",
                "local_results": [{"path": "docs/proof.md"}],
                "remote_discoveries": [],
                "provider_status": [],
                "server_status": [],
            }
            research["result_sha256"] = sha256_value(research)
            (root / "omega-research-results.json").write_text(json.dumps(research), encoding="utf-8")
            plan = build_plan(root)
            self.assertEqual(plan["research_context"]["state"], "PRESENT_HASH_VALID")
            self.assertEqual(plan["research_context"]["local_result_count"], 1)
            self.assertTrue(plan["research_context"]["remote_discoveries_remain_unverified"])
            self.assertNotIn("omega-research-results.json", {row["path"] for row in plan["artifacts"]})


if __name__ == "__main__":
    unittest.main()
