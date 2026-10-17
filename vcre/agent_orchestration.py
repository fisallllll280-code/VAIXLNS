"""Governed specialist-agent orchestration primitives for VAIXLNS.

This module validates task dispatch and evidence admission metadata. It does not
launch remote agents or confer authority; callers must provide authenticated
principals and grants from the real runtime.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Sequence


class OrchestrationError(ValueError):
    """Raised when a task violates the orchestration contract."""


class TaskState(str, Enum):
    PROPOSED = "PROPOSED"
    CONTRACT_VALIDATED = "CONTRACT_VALIDATED"
    IDENTITY_BOUND = "IDENTITY_BOUND"
    CAPABILITY_CHECKED = "CAPABILITY_CHECKED"
    AUTHORITY_GRANTED = "AUTHORITY_GRANTED"
    DISPATCHED = "DISPATCHED"
    RESULT_QUARANTINED = "RESULT_QUARANTINED"
    OUTPUT_VALIDATED = "OUTPUT_VALIDATED"
    EVIDENCE_RECORDED = "EVIDENCE_RECORDED"
    INDEPENDENTLY_CHECKED = "INDEPENDENTLY_CHECKED"
    ADMISSION_DECIDED = "ADMISSION_DECIDED"
    CLOSED = "CLOSED"
    HOLD = "HOLD"
    REJECTED = "REJECTED"


class Verdict(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    REJECT = "REJECT"


@dataclass(frozen=True)
class AuthorityGrant:
    grant_id: str
    principal_id: str
    capabilities: frozenset[str]
    resource_scope: frozenset[str]
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False

    def allows(self, principal_id: str, required: Sequence[str], resource: str,
               now: datetime) -> bool:
        now = _aware_utc(now)
        return (
            not self.revoked
            and self.principal_id == principal_id
            and self.issued_at <= now < self.expires_at
            and set(required).issubset(self.capabilities)
            and resource in self.resource_scope
        )


@dataclass(frozen=True)
class TaskEnvelope:
    task_id: str
    run_id: str
    candidate_id: str
    candidate_fingerprint: str
    source_revision: str
    role: str
    principal_id: str
    capability_contract: tuple[str, ...]
    input_artifact_refs: tuple[str, ...]
    required_output_contract: str
    proof_obligations: tuple[str, ...]
    max_wall_time_ms: int
    max_tokens: int
    max_tool_calls: int
    permitted_tools: tuple[str, ...]
    authority_grant_ref: str
    issued_at: datetime
    expires_at: datetime
    idempotency_key: str
    resource_ref: str
    failure_policy: str = "FAIL_CLOSED"

    def validate(self, now: datetime) -> None:
        required_text = {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "candidate_id": self.candidate_id,
            "source_revision": self.source_revision,
            "role": self.role,
            "principal_id": self.principal_id,
            "required_output_contract": self.required_output_contract,
            "authority_grant_ref": self.authority_grant_ref,
            "idempotency_key": self.idempotency_key,
            "resource_ref": self.resource_ref,
        }
        if any(not isinstance(value, str) or not value.strip()
               for value in required_text.values()):
            raise OrchestrationError("required text fields must be non-empty")
        if not self.candidate_fingerprint.startswith("sha256:") or len(self.candidate_fingerprint) != 71:
            raise OrchestrationError("candidate_fingerprint must be sha256:<64 hex chars>")
        try:
            int(self.candidate_fingerprint[7:], 16)
        except ValueError as exc:
            raise OrchestrationError("candidate_fingerprint must be hexadecimal") from exc
        if not self.capability_contract or any(not item.strip() for item in self.capability_contract):
            raise OrchestrationError("capability_contract must contain non-empty capabilities")
        if len(set(self.capability_contract)) != len(self.capability_contract):
            raise OrchestrationError("capability_contract must not contain duplicates")
        if min(self.max_wall_time_ms, self.max_tokens, self.max_tool_calls) <= 0:
            raise OrchestrationError("all execution budgets must be positive")
        if self.failure_policy != "FAIL_CLOSED":
            raise OrchestrationError("only FAIL_CLOSED is supported")
        now = _aware_utc(now)
        issued, expires = _aware_utc(self.issued_at), _aware_utc(self.expires_at)
        if expires <= issued:
            raise OrchestrationError("task expiry must follow issue time")
        if not issued <= now < expires:
            raise OrchestrationError("task envelope is not currently valid")


@dataclass(frozen=True)
class EvidenceReceipt:
    artifact_ref: str
    sha256: str
    task_id: str
    principal_id: str
    candidate_fingerprint: str
    source_revision: str
    produced_at: datetime
    result_contract_valid: bool
    measurements: Mapping[str, Any] = field(default_factory=dict)

    def validate_for(self, task: TaskEnvelope, now: datetime) -> None:
        if not self.artifact_ref.strip():
            raise OrchestrationError("evidence artifact_ref is required")
        if len(self.sha256) != 64:
            raise OrchestrationError("evidence sha256 must contain 64 hex chars")
        try:
            int(self.sha256, 16)
        except ValueError as exc:
            raise OrchestrationError("evidence sha256 must be hexadecimal") from exc
        if self.task_id != task.task_id or self.principal_id != task.principal_id:
            raise OrchestrationError("evidence producer/task identity mismatch")
        if self.candidate_fingerprint != task.candidate_fingerprint:
            raise OrchestrationError("stale evidence: candidate fingerprint drift")
        if self.source_revision != task.source_revision:
            raise OrchestrationError("stale evidence: source revision drift")
        if _aware_utc(self.produced_at) > _aware_utc(now):
            raise OrchestrationError("evidence timestamp is in the future")
        if not self.result_contract_valid:
            raise OrchestrationError("evidence output contract was not validated")


@dataclass
class TaskRecord:
    envelope: TaskEnvelope
    state: TaskState = TaskState.PROPOSED
    events: list[tuple[TaskState, str]] = field(default_factory=list)
    evidence: EvidenceReceipt | None = None
    verifier_principal_id: str | None = None
    verdict: Verdict | None = None

    def transition(self, target: TaskState, reason: str) -> None:
        allowed = {
            TaskState.PROPOSED: {TaskState.CONTRACT_VALIDATED, TaskState.HOLD, TaskState.REJECTED},
            TaskState.CONTRACT_VALIDATED: {TaskState.IDENTITY_BOUND, TaskState.HOLD, TaskState.REJECTED},
            TaskState.IDENTITY_BOUND: {TaskState.CAPABILITY_CHECKED, TaskState.HOLD, TaskState.REJECTED},
            TaskState.CAPABILITY_CHECKED: {TaskState.AUTHORITY_GRANTED, TaskState.HOLD, TaskState.REJECTED},
            TaskState.AUTHORITY_GRANTED: {TaskState.DISPATCHED, TaskState.HOLD, TaskState.REJECTED},
            TaskState.DISPATCHED: {TaskState.RESULT_QUARANTINED, TaskState.HOLD, TaskState.REJECTED},
            TaskState.RESULT_QUARANTINED: {TaskState.OUTPUT_VALIDATED, TaskState.HOLD, TaskState.REJECTED},
            TaskState.OUTPUT_VALIDATED: {TaskState.EVIDENCE_RECORDED, TaskState.HOLD, TaskState.REJECTED},
            TaskState.EVIDENCE_RECORDED: {TaskState.INDEPENDENTLY_CHECKED, TaskState.HOLD, TaskState.REJECTED},
            TaskState.INDEPENDENTLY_CHECKED: {TaskState.ADMISSION_DECIDED, TaskState.HOLD, TaskState.REJECTED},
            TaskState.ADMISSION_DECIDED: {TaskState.CLOSED},
            TaskState.CLOSED: set(), TaskState.HOLD: set(), TaskState.REJECTED: set(),
        }
        if target not in allowed[self.state]:
            raise OrchestrationError(f"illegal task transition: {self.state.value} -> {target.value}")
        self.state = target
        self.events.append((target, reason))


def canonical_fingerprint(value: Any) -> str:
    """Fingerprint JSON-compatible data independent of dictionary key order."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def authorize_dispatch(record: TaskRecord, *, registered_principal_id: str,
                       registered_capabilities: Sequence[str], grant: AuthorityGrant,
                       now: datetime) -> None:
    """Validate envelope, bind identity, check capability and authority, then dispatch."""
    task = record.envelope
    try:
        task.validate(now)
        record.transition(TaskState.CONTRACT_VALIDATED, "envelope schema and time window valid")
        if registered_principal_id != task.principal_id:
            raise OrchestrationError("registered principal identity mismatch")
        record.transition(TaskState.IDENTITY_BOUND, "registered principal bound")
        if not set(task.capability_contract).issubset(set(registered_capabilities)):
            raise OrchestrationError("principal lacks required capability")
        record.transition(TaskState.CAPABILITY_CHECKED, "capability contract satisfied")
        if grant.grant_id != task.authority_grant_ref or not grant.allows(
            task.principal_id, task.capability_contract, task.resource_ref, now
        ):
            raise OrchestrationError("authority grant missing, expired, revoked, or out of scope")
        record.transition(TaskState.AUTHORITY_GRANTED, "scoped authority grant accepted")
        record.transition(TaskState.DISPATCHED, "dispatch authorized; execution delegated to runtime")
    except OrchestrationError as exc:
        if record.state not in (TaskState.HOLD, TaskState.REJECTED, TaskState.CLOSED):
            record.transition(TaskState.REJECTED, str(exc))
        raise


def quarantine_result(record: TaskRecord, *, result: Mapping[str, Any]) -> str:
    """Quarantine any worker result before trusting or interpreting its claims."""
    if record.state != TaskState.DISPATCHED:
        raise OrchestrationError("only dispatched tasks may return results")
    digest = canonical_fingerprint(result)
    record.transition(TaskState.RESULT_QUARANTINED, f"untrusted result quarantined; digest={digest}")
    return digest


def validate_and_record_evidence(record: TaskRecord, *, receipt: EvidenceReceipt,
                                 now: datetime) -> None:
    if record.state != TaskState.RESULT_QUARANTINED:
        raise OrchestrationError("result must be quarantined before evidence validation")
    receipt.validate_for(record.envelope, now)
    record.transition(TaskState.OUTPUT_VALIDATED, "output and provenance contract validated")
    record.evidence = receipt
    record.transition(TaskState.EVIDENCE_RECORDED, "immutable evidence receipt attached")


def verify_independently(record: TaskRecord, *, verifier_principal_id: str,
                         independent_check_passed: bool) -> Verdict:
    if record.state != TaskState.EVIDENCE_RECORDED or record.evidence is None:
        raise OrchestrationError("evidence must be recorded before independent verification")
    if verifier_principal_id == record.envelope.principal_id:
        record.transition(TaskState.REJECTED, "producer cannot independently verify own consequential task")
        raise OrchestrationError("producer/verifier separation-of-duties violation")
    record.verifier_principal_id = verifier_principal_id
    if not independent_check_passed:
        record.verdict = Verdict.HOLD
        record.transition(TaskState.HOLD, "independent verification did not pass")
        return Verdict.HOLD
    record.verdict = Verdict.PASS
    record.transition(TaskState.INDEPENDENTLY_CHECKED, "distinct verifier accepted evidence")
    return Verdict.PASS


def decide_admission(record: TaskRecord, *, authority_decision: Verdict,
                     decision_ref: str) -> None:
    if record.state != TaskState.INDEPENDENTLY_CHECKED:
        raise OrchestrationError("independent verification required before admission decision")
    if not decision_ref.strip():
        raise OrchestrationError("admission decision must reference an auditable decision")
    if authority_decision == Verdict.HOLD:
        record.transition(TaskState.HOLD, f"authority decision HOLD: {decision_ref}")
        return
    if authority_decision == Verdict.REJECT:
        record.transition(TaskState.REJECTED, f"authority decision REJECT: {decision_ref}")
        return
    record.transition(TaskState.ADMISSION_DECIDED, f"explicit authority decision PASS: {decision_ref}")
    record.transition(TaskState.CLOSED, "task lifecycle closed")


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise OrchestrationError("timestamps must include a timezone")
    return value.astimezone(timezone.utc)
