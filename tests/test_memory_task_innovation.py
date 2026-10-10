import json
import tempfile
import unittest
from pathlib import Path

from vaixlns_engineering.memory_task_innovation import (
    MemoryLedger, plan_tasks, propose_innovations, transition_task,
)


class MemoryLedgerTests(unittest.TestCase):
    def test_append_retrieve_and_verify_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = MemoryLedger(Path(temp) / "memory.jsonl")
            row = ledger.append(kind="decision", content="Preserve original VAIXLNS index",
                                source_ref="docs/constitution.md", tags=["canonical", "index"])
            self.assertTrue(ledger.verify()["valid"])
            found = ledger.retrieve("VAIXLNS original index", limit=5)
            self.assertEqual(found[0]["record_id"], row["record_id"])
            self.assertEqual(found[0]["retrieval_method"], "deterministic_lexical_overlap")

    def test_tampering_is_detected_and_append_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "memory.jsonl"
            ledger = MemoryLedger(path)
            ledger.append(kind="idea", content="Evidence-first innovation", source_ref="proposal.md")
            row = json.loads(path.read_text(encoding="utf-8"))
            row["content"] = "tampered content"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            self.assertFalse(ledger.verify()["valid"])
            with self.assertRaises(ValueError):
                ledger.append(kind="idea", content="another idea", source_ref="proposal.md")

    def test_invalid_memory_kind_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                MemoryLedger(Path(temp) / "memory.jsonl").append(
                    kind="execute_shell", content="x", source_ref="x"
                )


class TaskPlanningTests(unittest.TestCase):
    def test_deterministic_topological_order_and_blocking(self):
        tasks = [
            {"task_id": "C", "goal": "integrate", "depends_on": ["A", "B"]},
            {"task_id": "B", "goal": "test"},
            {"task_id": "A", "goal": "specify"},
        ]
        result = plan_tasks(tasks)
        self.assertEqual(result["order"], ["A", "B", "C"])
        states = {task["task_id"]: task["state"] for task in result["tasks"]}
        self.assertEqual(states, {"A": "READY", "B": "READY", "C": "BLOCKED"})

    def test_missing_dependency_and_cycle_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing dependency"):
            plan_tasks([{"task_id": "A", "goal": "x", "depends_on": ["Z"]}])
        with self.assertRaisesRegex(ValueError, "cycle"):
            plan_tasks([
                {"task_id": "A", "goal": "x", "depends_on": ["B"]},
                {"task_id": "B", "goal": "y", "depends_on": ["A"]},
            ])

    def test_done_requires_evidence_with_source_and_digest(self):
        task = {"task_id": "T1", "goal": "validate", "state": "RUNNING",
                "required_evidence": ["test_report"]}
        with self.assertRaisesRegex(ValueError, "missing evidence"):
            transition_task(task, "DONE", [])
        evidence = [{"type": "test_report", "source_ref": "ci/run/1", "digest": "sha256:abc"}]
        updated = transition_task(task, "DONE", evidence)
        self.assertEqual(updated["state"], "DONE")
        self.assertEqual(updated["completion_evidence"], evidence)

    def test_illegal_transition_rejected(self):
        with self.assertRaisesRegex(ValueError, "illegal task transition"):
            transition_task({"state": "PROPOSED"}, "DONE", [])


class InnovationTests(unittest.TestCase):
    def test_innovations_are_hypotheses_not_verified_claims(self):
        result = propose_innovations("recover interrupted engineering work", [
            {"record_id": "MEM-1"}
        ], ["preserve canonical index"])
        self.assertEqual(len(result), 4)
        self.assertTrue(all(item["state"] == "PROPOSAL" for item in result))
        self.assertTrue(all(item["promotion_authorized"] is False for item in result))
        self.assertTrue(all(item["derived_from_memory_ids"] == ["MEM-1"] for item in result))


if __name__ == "__main__":
    unittest.main()
