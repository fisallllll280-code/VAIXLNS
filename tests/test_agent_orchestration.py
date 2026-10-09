from datetime import datetime, timedelta, timezone
import unittest

from vcre.agent_orchestration import (
    AuthorityGrant,
    EvidenceReceipt,
    OrchestrationError,
    TaskEnvelope,
    TaskRecord,
    TaskState,
    Verdict,
    authorize_dispatch,
    canonical_fingerprint,
    decide_admission,
    quarantine_result,
    validate_and_record_evidence,
    verify_independently,
)


NOW = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


def envelope(**overrides):
    values = dict(
        task_id="task-001",
        run_id="run-001",
        candidate_id="candidate-001",
        candidate_fingerprint=canonical_fingerprint({"candidate": 1}),
        source_revision="abcdef0123456",
        role="IMPLEMENTER",
        principal_id="agent-builder",
        capability_contract=("repo.read", "sandbox.test"),
        input_artifact_refs=("artifact://source",),
        required_output_contract="contract://test-report",
        proof_obligations=("PO-001",),
        max_wall_time_ms=30_000,
        max_tokens=12_000,
        max_tool_calls=20,
        permitted_tools=("repo.read", "sandbox.test"),
        authority_grant_ref="grant-001",
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        idempotency_key="idempotency-key-0001",
        resource_ref="candidate://candidate-001",
    )
    values.update(overrides)
    return TaskEnvelope(**values)


def grant(**overrides):
    values = dict(
        grant_id="grant-001",
        principal_id="agent-builder",
        capabilities=frozenset({"repo.read", "sandbox.test"}),
        resource_scope=frozenset({"candidate://candidate-001"}),
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        revoked=False,
    )
    values.update(overrides)
    return AuthorityGrant(**values)


def dispatched_record():
    record = TaskRecord(envelope())
    authorize_dispatch(
        record,
        registered_principal_id="agent-builder",
        registered_capabilities=("repo.read", "sandbox.test"),
        grant=grant(),
        now=NOW,
    )
    return record


def receipt(task=None, **overrides):
    task = task or envelope()
    values = dict(
        artifact_ref="artifact://evidence/1",
        sha256="a" * 64,
        task_id=task.task_id,
        principal_id=task.principal_id,
        candidate_fingerprint=task.candidate_fingerprint,
        source_revision=task.source_revision,
        produced_at=NOW,
        result_contract_valid=True,
        measurements={"tests_passed": 12},
    )
    values.update(overrides)
    return EvidenceReceipt(**values)


class AgentOrchestrationTests(unittest.TestCase):
    def test_fingerprint_is_key_order_independent(self):
        self.assertEqual(canonical_fingerprint({"a": 1, "b": 2}),
                         canonical_fingerprint({"b": 2, "a": 1}))

    def test_expired_grant_is_denied(self):
        record = TaskRecord(envelope())
        with self.assertRaisesRegex(OrchestrationError, "authority grant"):
            authorize_dispatch(
                record,
                registered_principal_id="agent-builder",
                registered_capabilities=("repo.read", "sandbox.test"),
                grant=grant(expires_at=NOW - timedelta(seconds=1)),
                now=NOW,
            )
        self.assertEqual(record.state, TaskState.REJECTED)

    def test_identity_mismatch_is_denied(self):
        record = TaskRecord(envelope())
        with self.assertRaisesRegex(OrchestrationError, "identity mismatch"):
            authorize_dispatch(
                record,
                registered_principal_id="other-agent",
                registered_capabilities=("repo.read", "sandbox.test"),
                grant=grant(),
                now=NOW,
            )
        self.assertEqual(record.state, TaskState.REJECTED)

    def test_missing_capability_is_denied(self):
        record = TaskRecord(envelope())
        with self.assertRaisesRegex(OrchestrationError, "lacks required capability"):
            authorize_dispatch(
                record,
                registered_principal_id="agent-builder",
                registered_capabilities=("repo.read",),
                grant=grant(),
                now=NOW,
            )

    def test_result_is_quarantined_before_evidence(self):
        record = dispatched_record()
        with self.assertRaisesRegex(OrchestrationError, "quarantined"):
            validate_and_record_evidence(record, receipt=receipt(), now=NOW)
        digest = quarantine_result(record, result={"success": True, "payload": "untrusted"})
        self.assertTrue(digest.startswith("sha256:"))
        validate_and_record_evidence(record, receipt(record.envelope), now=NOW)
        self.assertEqual(record.state, TaskState.EVIDENCE_RECORDED)

    def test_stale_candidate_evidence_is_rejected(self):
        record = dispatched_record()
        quarantine_result(record, result={"report": "done"})
        stale = receipt(record.envelope, candidate_fingerprint=canonical_fingerprint({"candidate": 2}))
        with self.assertRaisesRegex(OrchestrationError, "fingerprint drift"):
            validate_and_record_evidence(record, receipt=stale, now=NOW)

    def test_producer_cannot_verify_own_task(self):
        record = dispatched_record()
        quarantine_result(record, result={"report": "done"})
        validate_and_record_evidence(record, receipt=receipt(record.envelope), now=NOW)
        with self.assertRaisesRegex(OrchestrationError, "separation-of-duties"):
            verify_independently(record, verifier_principal_id="agent-builder",
                                 independent_check_passed=True)
        self.assertEqual(record.state, TaskState.REJECTED)

    def test_independent_verifier_and_explicit_admission_close_task(self):
        record = dispatched_record()
        quarantine_result(record, result={"report": "done"})
        validate_and_record_evidence(record, receipt=receipt(record.envelope), now=NOW)
        self.assertEqual(
            verify_independently(record, verifier_principal_id="agent-verifier",
                                 independent_check_passed=True),
            Verdict.PASS,
        )
        decide_admission(record, authority_decision=Verdict.PASS,
                         decision_ref="decision://authority/42")
        self.assertEqual(record.state, TaskState.CLOSED)

    def test_failed_independent_check_holds_task(self):
        record = dispatched_record()
        quarantine_result(record, result={"report": "done"})
        validate_and_record_evidence(record, receipt=receipt(record.envelope), now=NOW)
        self.assertEqual(
            verify_independently(record, verifier_principal_id="agent-verifier",
                                 independent_check_passed=False),
            Verdict.HOLD,
        )
        self.assertEqual(record.state, TaskState.HOLD)

    def test_naive_timestamp_is_rejected(self):
        record = TaskRecord(envelope(issued_at=datetime(2026, 10, 10, 11, 0),
                                     expires_at=datetime(2026, 10, 10, 13, 0)))
        with self.assertRaisesRegex(OrchestrationError, "timezone"):
            authorize_dispatch(
                record,
                registered_principal_id="agent-builder",
                registered_capabilities=("repo.read", "sandbox.test"),
                grant=grant(),
                now=NOW,
            )

    def test_illegal_transition_is_rejected(self):
        record = TaskRecord(envelope())
        with self.assertRaisesRegex(OrchestrationError, "illegal task transition"):
            record.transition(TaskState.CLOSED, "skip all gates")


if __name__ == "__main__":
    unittest.main()
