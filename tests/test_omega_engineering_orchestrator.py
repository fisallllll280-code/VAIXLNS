"""Tests for the evidence-linking engineering orchestrator."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.omega_engineering_orchestrator import build_report, digest_json


def write_artifact(root: Path, name: str, payload: dict, hash_key: str):
    payload[hash_key] = digest_json(payload)
    (root / name).write_text(json.dumps(payload), encoding="utf-8")


class OmegaEngineeringOrchestratorTests(unittest.TestCase):
    def make_inputs(self, root: Path):
        write_artifact(root, "innovation-network.json", {
            "schema": "vaixlns.innovation-network.v1",
            "summary": {"innovation_count": 1, "task_count": 11},
        }, "network_sha256")
        write_artifact(root, "omega-research-results.json", {
            "schema": "vaixlns.omega-research-fabric.v1",
            "index": {"file_count": 2}, "query": "test evidence",
        }, "result_sha256")
        write_artifact(root, "engineering-execution-plan.json", {
            "schema": "vaixlns.engineering-agent-fabric.v1",
            "repository_revision": "abc123", "summary": {"runtime_verified": False},
        }, "plan_sha256")
        (root / "test-suite.log").write_text("Ran 5 tests in 0.100s\n\nOK\n", encoding="utf-8")

    def test_linked_valid_artifacts_produce_review_state_not_auto_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_inputs(root)
            report = build_report(root)
            self.assertEqual(report["state"], "READY_FOR_ENGINEERING_REVIEW_NOT_AUTO_RELEASED")
            self.assertEqual(report["test_evidence"]["state"], "PASS")
            self.assertFalse(report["release_policy"]["auto_merge"])
            self.assertFalse(report["external_systems"]["connectivity_verified"])
            self.assertTrue(any(link["from"] == "omega-research-results.json" for link in report["links"]))

    def test_integrity_failure_blocks_review_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_inputs(root)
            plan = json.loads((root / "engineering-execution-plan.json").read_text())
            plan["summary"]["runtime_verified"] = True
            (root / "engineering-execution-plan.json").write_text(json.dumps(plan), encoding="utf-8")
            report = build_report(root)
            self.assertEqual(report["state"], "BLOCKED_INTEGRITY_OR_SCHEMA_FAILURE")
            self.assertIn("engineering-execution-plan.json", report["blockers"]["integrity_failures"])

    def test_missing_required_index_blocks_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "test-suite.log").write_text("Ran 1 test in 0.001s\n\nOK\n", encoding="utf-8")
            self.assertEqual(build_report(root)["state"], "BLOCKED_MISSING_OR_INCOMPLETE_EVIDENCE")

    def test_failure_requires_failure_localization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_inputs(root)
            (root / "test-suite.log").write_text("Ran 5 tests in 0.100s\n\nFAILED (failures=1)\n", encoding="utf-8")
            report = build_report(root)
            self.assertEqual(report["state"], "BLOCKED_TEST_FAILURE_DIAGNOSTIC_REQUIRED")
            self.assertEqual(report["failure_diagnostic_state"], "DIAGNOSTIC_MISSING_OR_INVALID")

    def test_report_hash_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_inputs(root)
            self.assertEqual(build_report(root), build_report(root))


if __name__ == "__main__":
    unittest.main()
