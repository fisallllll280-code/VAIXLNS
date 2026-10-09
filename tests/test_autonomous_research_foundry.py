import json
from pathlib import Path
import tempfile
import unittest

from scripts.autonomous_research_foundry import run_cycle


class AutonomousResearchFoundryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()
        (self.root / "registry").mkdir()
        (self.root / "docs" / "source.md").write_text(
            "Research is SPECIFIED; implementation remains PROPOSED. TODO: prior-art review.\n",
            encoding="utf-8",
        )
        self.queue_path = self.root / "registry" / "queue.json"
        self.queue_path.write_text(json.dumps({
            "schema": "VAIXLNS-AUTONOMOUS-FOUNDRY-QUEUE-1",
            "queue_id": "TEST.QUEUE",
            "limits": {"max_tasks_per_cycle": 2},
            "approved_public_repositories": [],
            "tasks": [
                {
                    "task_id": "TASK-01",
                    "priority": 10,
                    "problem": "Research handoffs lack measured evidence coverage",
                    "objective": "Propose an evidence-bound research handoff processor",
                    "constraints": ["read-only input", "no self-authorization"],
                    "capabilities": ["provenance", "coverage tracking"],
                    "public_repository_targets": [],
                    "local_source_paths": ["docs/source.md"],
                },
                {
                    "task_id": "TASK-02",
                    "priority": 5,
                    "problem": "Execution budgets are not consistently represented",
                    "objective": "Propose bounded processing with timeout and retry limits",
                    "constraints": ["bounded resources"],
                    "capabilities": ["budget tracking"],
                    "public_repository_targets": [],
                    "local_source_paths": ["docs/source.md"],
                },
                {
                    "task_id": "TASK-03",
                    "priority": 1,
                    "problem": "This task should be outside the configured cycle limit",
                    "objective": "Do not process this task when the configured limit is two",
                    "constraints": [],
                    "capabilities": ["test"],
                    "public_repository_targets": [],
                    "local_source_paths": [],
                },
            ],
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_cycle_creates_proposals_and_never_promotes_them(self):
        report = run_cycle(self.root, "registry/queue.json", public_sources=False)
        self.assertEqual(report["mode"], "LOCAL_ONLY")
        self.assertEqual(report["summary"]["task_count"], 2)
        self.assertEqual(report["summary"]["automatic_admissions"], 0)
        self.assertEqual(report["summary"]["verified_count"], 0)
        for item in report["tasks"]:
            self.assertEqual(item["candidate"]["status"], "PROPOSAL")
            self.assertEqual(item["candidate_state"], "READY_FOR_HUMAN_REVIEW")
            self.assertEqual(item["novelty_state"], "UNASSESSED")
            self.assertFalse(item["automatic_promotion"])
            self.assertEqual(item["admission_state"], "NOT_AUTHORIZED")

    def test_cycle_hash_is_stable_for_same_local_inputs(self):
        first = run_cycle(self.root, "registry/queue.json", public_sources=False)
        second = run_cycle(self.root, "registry/queue.json", public_sources=False)
        self.assertEqual(first["cycle_id"], second["cycle_id"])

    def test_local_source_is_hashed_and_signals_are_counted(self):
        report = run_cycle(self.root, "registry/queue.json", public_sources=False)
        source = report["source_coverage"]["local_manifest"]["docs/source.md"]
        self.assertEqual(source["state"], "READ")
        self.assertEqual(len(source["sha256"]), 64)
        self.assertGreaterEqual(source["signal_counts"].get("PROPOSED", 0), 1)
        self.assertFalse(source["content_executed"])

    def test_queue_path_cannot_escape_repository_root(self):
        with self.assertRaisesRegex(ValueError, "QUEUE_PATH_MUST_REMAIN_INSIDE_REPOSITORY"):
            run_cycle(self.root, "../outside.json")

    def test_source_path_traversal_is_marked_invalid(self):
        data = json.loads(self.queue_path.read_text(encoding="utf-8"))
        data["tasks"][0]["local_source_paths"] = ["../outside.md"]
        self.queue_path.write_text(json.dumps(data), encoding="utf-8")
        report = run_cycle(self.root, "registry/queue.json", public_sources=False)
        self.assertEqual(
            report["source_coverage"]["local_manifest"]["../outside.md"]["state"],
            "INVALID_PATH",
        )
        self.assertEqual(report["summary"]["automatic_admissions"], 0)

    def test_public_target_must_be_in_allow_list(self):
        data = json.loads(self.queue_path.read_text(encoding="utf-8"))
        data["tasks"][0]["public_repository_targets"] = ["unknown/remote"]
        self.queue_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PUBLIC_REPOSITORY_TARGET_NOT_ALLOWLISTED"):
            run_cycle(self.root, "registry/queue.json", public_sources=False)


if __name__ == "__main__":
    unittest.main()
