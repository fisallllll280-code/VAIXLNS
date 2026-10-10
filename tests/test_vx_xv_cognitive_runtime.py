import hashlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

# Repository-wide unittest runners may not install this alpha package or set PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vaixlns_cognitive_runtime import (
    Claim,
    Evidence,
    MemoryStore,
    build_task_plan,
    evaluate_claim,
    requires_human_approval,
)


class CognitiveRuntimeTests(unittest.TestCase):
    def test_plain_language_build_request_routes_to_builder_and_verifier(self):
        plan = build_task_plan("ابن لوحة تعرض حالة المستودع وتختبر الملفات")
        roles = [step.role for step in plan.steps]
        self.assertEqual(plan.intent_class, "build")
        self.assertIn("vx.systems_architect", roles)
        self.assertIn("vx.builder_executor", roles)
        self.assertIn("vx.verification_mind", roles)
        self.assertEqual(plan.status, "PLANNED")

    def test_repair_request_routes_to_xv_repair_engineer(self):
        plan = build_task_plan("أصلح الاختبارات الفاشلة ثم تحقق من الإصلاح")
        self.assertEqual(plan.intent_class, "repair")
        self.assertIn("xv.repair_engineer", [step.role for step in plan.steps])

    def test_research_request_includes_research_mind(self):
        plan = build_task_plan("Study and explain the source code with evidence")
        self.assertEqual(plan.intent_class, "research")
        self.assertIn("vx.research_mind", [step.role for step in plan.steps])

    def test_external_and_canonical_requests_require_approval(self):
        self.assertTrue(requires_human_approval("deploy to production")[0])
        self.assertTrue(requires_human_approval("عدّل project.genome")[0])
        plan = build_task_plan("انشر التطبيق للعامة")
        self.assertTrue(plan.requires_approval)
        self.assertGreater(len(plan.approval_reasons), 0)
        self.assertEqual(plan.status, "PLANNED")

    def test_empty_request_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            build_task_plan("   ")

    def test_verified_claim_without_evidence_is_downgraded(self):
        assessment = evaluate_claim(Claim("c1", "Claim", "VERIFIED"), evidence=())
        self.assertEqual(assessment.effective_state, "UNVERIFIED")
        self.assertFalse(assessment.admissible_as_verified)

    def test_verified_claim_needs_hash_method_and_independent_review(self):
        evidence = Evidence(
            evidence_id="e1",
            source_uri="https://example.invalid/source",
            content_sha256=hashlib.sha256(b"source snapshot").hexdigest(),
            retrieved_at="2026-10-10T00:00:00Z",
        )
        incomplete = Claim(
            "c1", "Claim", "VERIFIED",
            evidence_ids=("e1",), verification_method="unit tests"
        )
        self.assertEqual(evaluate_claim(incomplete, [evidence]).effective_state, "UNVERIFIED")
        complete = Claim(
            "c1", "Claim", "VERIFIED",
            evidence_ids=("e1",),
            verification_method="reproducible test suite",
            independent_review=True,
        )
        self.assertTrue(evaluate_claim(complete, [evidence]).admissible_as_verified)

    def test_conflict_is_not_silently_promoted(self):
        assessment = evaluate_claim(Claim("c1", "Conflicting claim", "CONFLICT"))
        self.assertEqual(assessment.effective_state, "CONFLICT")

    def test_memory_append_search_and_chain_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = MemoryStore(Path(directory) / "memory.sqlite3")
            event = store.append("task", {"goal": "inspect repository", "state": "PLANNED"})
            self.assertEqual(event["seq"], 1)
            self.assertEqual(len(store.search("repository")), 1)
            self.assertTrue(store.verify_chain()["valid"])
            store.append("test", {"result": "pass"})
            self.assertEqual(store.verify_chain()["events_checked"], 2)

    def test_memory_events_reject_update_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "memory.sqlite3"
            store = MemoryStore(db_path)
            store.append("task", {"goal": "test immutability"})
            with sqlite3.connect(db_path) as db:
                with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only"):
                    db.execute("UPDATE memory_events SET event_type='edited' WHERE seq=1")
                db.rollback()
                with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only"):
                    db.execute("DELETE FROM memory_events WHERE seq=1")
                db.rollback()
            self.assertTrue(store.verify_chain()["valid"])

    def test_memory_integrity_detects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "memory.sqlite3"
            store = MemoryStore(db_path)
            store.append("task", {"goal": "original"})
            with sqlite3.connect(db_path) as db:
                db.execute("DROP TRIGGER memory_events_no_update")
                db.execute(
                    "UPDATE memory_events SET payload_json=? WHERE seq=1",
                    ('{"goal":"tampered"}',),
                )
                db.commit()
            result = store.verify_chain()
            self.assertFalse(result["valid"])
            self.assertEqual(result["reason"], "event_hash_mismatch")

    def test_identical_requests_have_same_step_structure(self):
        one = build_task_plan("research this repository")
        two = build_task_plan("research this repository")
        self.assertEqual([step.role for step in one.steps], [step.role for step in two.steps])
        self.assertEqual([step.objective for step in one.steps], [step.objective for step in two.steps])


if __name__ == "__main__":
    unittest.main()
