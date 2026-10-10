import hashlib
import sqlite3
from pathlib import Path

import pytest

from vaixlns_cognitive_runtime import (
    Claim,
    Evidence,
    MemoryStore,
    build_task_plan,
    evaluate_claim,
    requires_human_approval,
)


def test_plain_language_build_request_routes_to_builder_and_verifier():
    plan = build_task_plan("ابن لوحة تعرض حالة المستودع وتختبر الملفات")
    roles = [step.role for step in plan.steps]
    assert plan.intent_class == "build"
    assert "vx.systems_architect" in roles
    assert "vx.builder_executor" in roles
    assert "vx.verification_mind" in roles
    assert plan.status == "PLANNED"


def test_repair_request_routes_to_xv_repair_engineer():
    plan = build_task_plan("أصلح الاختبارات الفاشلة ثم تحقق من الإصلاح")
    assert plan.intent_class == "repair"
    assert "xv.repair_engineer" in [step.role for step in plan.steps]


def test_research_request_includes_research_mind():
    plan = build_task_plan("Study and explain the source code with evidence")
    assert plan.intent_class == "research"
    assert "vx.research_mind" in [step.role for step in plan.steps]


def test_external_and_canonical_requests_require_approval():
    assert requires_human_approval("deploy to production")[0]
    assert requires_human_approval("عدّل project.genome")[0]
    plan = build_task_plan("انشر التطبيق للعامة")
    assert plan.requires_approval is True
    assert any(step.approval_required for step in plan.steps)


def test_empty_request_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        build_task_plan("   ")


def test_verified_claim_without_evidence_is_downgraded():
    assessment = evaluate_claim(Claim("c1", "Claim", "VERIFIED"))
    assert assessment.effective_state == "UNVERIFIED"
    assert assessment.admissible_as_verified is False


def test_verified_claim_needs_hash_method_and_independent_review():
    evidence = Evidence(
        evidence_id="e1",
        source_uri="https://example.invalid/source",
        content_sha256=hashlib.sha256(b"source snapshot").hexdigest(),
        retrieved_at="2026-10-10T00:00:00Z",
    )
    incomplete = Claim("c1", "Claim", "VERIFIED", evidence_ids=("e1",), verification_method="unit tests")
    assert evaluate_claim(incomplete, [evidence]).effective_state == "UNVERIFIED"
    complete = Claim(
        "c1", "Claim", "VERIFIED", evidence_ids=("e1",),
        verification_method="reproducible test suite", independent_review=True
    )
    assert evaluate_claim(complete, [evidence]).admissible_as_verified is True


def test_conflict_is_not_silently_promoted():
    assessment = evaluate_claim(Claim("c1", "Conflicting claim", "CONFLICT"))
    assert assessment.effective_state == "CONFLICT"


def test_memory_append_search_and_chain_validation(tmp_path: Path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    event = store.append("task", {"goal": "inspect repository", "state": "PLANNED"})
    assert event["seq"] == 1
    assert len(store.search("repository")) == 1
    assert store.verify_chain()["valid"] is True
    store.append("test", {"result": "pass"})
    assert store.verify_chain()["events_checked"] == 2


def test_memory_events_reject_update_and_delete(tmp_path: Path):
    db_path = tmp_path / "memory.sqlite3"
    store = MemoryStore(db_path)
    store.append("task", {"goal": "test immutability"})
    with sqlite3.connect(db_path) as db:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute("UPDATE memory_events SET event_type='edited' WHERE seq=1")
        db.rollback()
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute("DELETE FROM memory_events WHERE seq=1")
        db.rollback()
    assert store.verify_chain()["valid"] is True


def test_memory_integrity_detects_tampering():
    # A direct SQL rewrite simulates database corruption or tampering.
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        db_path = Path(directory) / "memory.sqlite3"
        store = MemoryStore(db_path)
        store.append("task", {"goal": "original"})
        with sqlite3.connect(db_path) as db:
            db.execute("DROP TRIGGER memory_events_no_update")
            db.execute("UPDATE memory_events SET payload_json='{"goal":"tampered"}' WHERE seq=1")
            db.commit()
        result = store.verify_chain()
        assert result["valid"] is False
        assert result["reason"] == "event_hash_mismatch"


def test_identical_requests_have_same_step_structure():
    one = build_task_plan("research this repository")
    two = build_task_plan("research this repository")
    assert [step.role for step in one.steps] == [step.role for step in two.steps]
    assert [step.objective for step in one.steps] == [step.objective for step in two.steps]
