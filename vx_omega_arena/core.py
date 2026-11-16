"""Deterministic, offline-first Ω-Arena runtime primitives.

No network calls, provider invocation, repository mutation, or promotion side effects.
All scores are candidate-local and never establish a permanent winner.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping

GENESIS = "0" * 64
METRICS = (
    "correctness", "reproducibility", "security", "completeness",
    "contradiction_resistance", "evidence_quality", "robustness", "innovation",
)
DEFAULT_WEIGHTS = {
    "correctness": 0.25,
    "reproducibility": 0.15,
    "security": 0.15,
    "completeness": 0.15,
    "contradiction_resistance": 0.10,
    "evidence_quality": 0.10,
    "robustness": 0.07,
    "innovation": 0.03,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    adapter_version: str
    status: str = "UNCONFIGURED"
    endpoint_source: str | None = None

    def eligible_for_live_invocation(self) -> bool:
        # This runtime deliberately does not invoke providers.
        return False


@dataclass(frozen=True)
class CandidateResult:
    candidate_id: str
    task_id: str
    provider_id: str
    metrics: Mapping[str, float]
    evidence_refs: tuple[str, ...]
    execution_mode: str = "SYNTHETIC"

    def validate(self) -> None:
        if not self.candidate_id or not self.task_id or not self.provider_id:
            raise ValueError("candidate_id, task_id and provider_id are required")
        if self.execution_mode not in {"SYNTHETIC", "OFFLINE_REPLAY", "AUTHORIZED_LIVE"}:
            raise ValueError("unsupported execution_mode")
        if set(self.metrics) != set(METRICS):
            raise ValueError("metrics must contain exactly the declared metric set")
        for key, value in self.metrics.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{key} must be numeric")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{key} must be within [0, 1]")
        if not self.evidence_refs:
            raise ValueError("at least one evidence reference is required")


@dataclass(frozen=True)
class EvidenceEvent:
    sequence: int
    event_type: str
    payload: Mapping[str, Any]
    previous_hash: str
    event_hash: str


class EvidenceLedger:
    """Append-only in-memory hash chain suitable for deterministic local runs."""

    def __init__(self) -> None:
        self._events: list[EvidenceEvent] = []

    @property
    def events(self) -> tuple[EvidenceEvent, ...]:
        return tuple(self._events)

    def append(self, event_type: str, payload: Mapping[str, Any]) -> EvidenceEvent:
        if not event_type:
            raise ValueError("event_type is required")
        sequence = len(self._events) + 1
        previous = self._events[-1].event_hash if self._events else GENESIS
        body = {"sequence": sequence, "event_type": event_type,
                "payload": dict(payload), "previous_hash": previous}
        event = EvidenceEvent(**body, event_hash=sha256(canonical_bytes(body)))
        self._events.append(event)
        return event

    @staticmethod
    def verify(events: Iterable[EvidenceEvent]) -> bool:
        previous = GENESIS
        expected_sequence = 1
        for event in events:
            body = {"sequence": event.sequence, "event_type": event.event_type,
                    "payload": dict(event.payload), "previous_hash": event.previous_hash}
            if event.sequence != expected_sequence or event.previous_hash != previous:
                return False
            if sha256(canonical_bytes(body)) != event.event_hash:
                return False
            previous = event.event_hash
            expected_sequence += 1
        return True

    @staticmethod
    def replay(events: Iterable[EvidenceEvent]) -> dict[str, Any]:
        snapshot = tuple(events)
        if not EvidenceLedger.verify(snapshot):
            raise ValueError("evidence chain verification failed")
        return {"event_count": len(snapshot),
                "head_hash": snapshot[-1].event_hash if snapshot else GENESIS,
                "replay_status": "PASS"}


def score_candidate(result: CandidateResult,
                    weights: Mapping[str, float] = DEFAULT_WEIGHTS) -> float:
    result.validate()
    if set(weights) != set(METRICS):
        raise ValueError("weights must contain exactly the declared metric set")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0
           for v in weights.values()):
        raise ValueError("weights must be non-negative numbers")
    total = sum(float(v) for v in weights.values())
    if total <= 0:
        raise ValueError("weight total must be positive")
    return round(sum(float(result.metrics[k]) * float(weights[k]) for k in METRICS)
                   / total, 8)


def promotion_gate(*, evidence_valid: bool, replay_valid: bool,
                   independent_review: bool, explicit_user_approval: bool,
                   canonical_scope: bool = False) -> dict[str, Any]:
    checks = {
        "evidence_valid": evidence_valid,
        "replay_valid": replay_valid,
        "independent_review": independent_review,
        "explicit_user_approval": explicit_user_approval,
        "canonical_scope_clear": not canonical_scope,
    }
    passed = all(checks.values())
    return {
        "status": "ELIGIBLE_FOR_SEPARATE_AUTHORIZATION" if passed else "BLOCKED",
        "checks": checks,
        "promotion_performed": False,
        "merge_performed": False,
        "deployment_performed": False,
    }


def candidate_receipt(result: CandidateResult, score: float) -> dict[str, Any]:
    body = {"candidate": asdict(result), "score": score,
            "score_scope": "FROZEN_TASK_ONLY",
            "permanent_winner": False}
    return {**body, "receipt_sha256": sha256(canonical_bytes(body))}
