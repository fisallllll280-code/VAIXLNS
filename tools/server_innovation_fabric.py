"""Evidence-gated server innovation candidate assessment for VAIXLNS.

This module evaluates explicit candidate records only. It does not discover or
probe endpoints, execute remote code, grant runtime authority, or admit a server.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Iterable
from urllib.parse import urlsplit


class NoveltyReviewStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    INSUFFICIENT_COVERAGE = "INSUFFICIENT_COVERAGE"
    CONTRADICTED_BY_PRIOR_ART = "CONTRADICTED_BY_PRIOR_ART"
    COMPLETE = "COMPLETE"


class GateStatus(str, Enum):
    NOT_RUN = "NOT_RUN"
    PASS = "PASS"
    FAIL = "FAIL"


class ServerAssessmentDecision(str, Enum):
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"
    ELIGIBLE_FOR_GOVERNANCE = "ELIGIBLE_FOR_GOVERNANCE"
    NOT_NOVEL_FOR_CURRENT_SCOPE = "NOT_NOVEL_FOR_CURRENT_SCOPE"


@dataclass(frozen=True)
class ServerInnovationCandidate:
    """Provenance-first description of a server/tool capability candidate."""

    server_id: str
    display_name: str
    server_class: str
    source_uri: str
    source_revision: str
    owner: str
    capability_claims: tuple[str, ...]
    known_capabilities: tuple[str, ...]
    capability_gap_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    prior_art_refs: tuple[str, ...]
    novelty_review_status: NoveltyReviewStatus = NoveltyReviewStatus.NOT_STARTED
    identity_status: GateStatus = GateStatus.NOT_RUN
    contract_status: GateStatus = GateStatus.NOT_RUN
    sandbox_test_status: GateStatus = GateStatus.NOT_RUN
    recovery_replay_status: GateStatus = GateStatus.NOT_RUN
    security_review_status: GateStatus = GateStatus.NOT_RUN
    independent_verification_status: GateStatus = GateStatus.NOT_RUN
    # Kept for audit completeness; it can never authorize itself.
    requested_runtime_admission: bool = False


@dataclass(frozen=True)
class ServerInnovationAssessment:
    server_id: str
    candidate_digest: str
    decision: ServerAssessmentDecision
    novelty_status: NoveltyReviewStatus
    capability_delta: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    blockers: tuple[str, ...]
    required_next_steps: tuple[str, ...]
    runtime_authorized: bool = False
    canonical_admission_authorized: bool = False
    assessment_version: str = "VAIXLNS-SERVER-INNOVATION-1.0.0"

    def to_record(self) -> dict[str, Any]:
        """Return a JSON-safe record with enum values flattened explicitly."""
        return {
            "server_id": self.server_id,
            "candidate_digest": self.candidate_digest,
            "decision": self.decision.value,
            "novelty_status": self.novelty_status.value,
            "capability_delta": list(self.capability_delta),
            "missing_requirements": list(self.missing_requirements),
            "blockers": list(self.blockers),
            "required_next_steps": list(self.required_next_steps),
            "runtime_authorized": False,
            "canonical_admission_authorized": False,
            "assessment_version": self.assessment_version,
        }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest_candidate(candidate: ServerInnovationCandidate) -> str:
    payload = asdict(candidate)
    for key, value in tuple(payload.items()):
        if isinstance(value, Enum):
            payload[key] = value.value
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _is_safe_source_uri(uri: str) -> bool:
    """Accept source identifiers/HTTPS URLs without dereferencing them."""
    if not isinstance(uri, str) or not uri.strip():
        return False
    if uri.startswith(("repo:", "artifact:", "archive:", "registry:")):
        return len(uri.split(":", 1)[1].strip()) > 0
    parsed = urlsplit(uri)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def assess_server_candidate(candidate: ServerInnovationCandidate) -> ServerInnovationAssessment:
    """Assess novelty/capability evidence without granting admission authority.

    Decision policy is intentionally fail-closed. ELIGIBLE_FOR_GOVERNANCE means
    only that a separate authority may review a complete evidence package.
    It never means the server is trusted, connected, deployed, or admitted.
    """
    if not candidate.server_id.strip() or not candidate.display_name.strip() or not candidate.server_class.strip():
        raise ValueError("server_id, display_name and server_class are required")
    if len(set(candidate.capability_claims)) != len(candidate.capability_claims):
        raise ValueError("capability_claims must not contain duplicates")
    if len(set(candidate.capability_gap_ids)) != len(candidate.capability_gap_ids):
        raise ValueError("capability_gap_ids must not contain duplicates")

    missing: list[str] = []
    blockers: list[str] = []
    next_steps: list[str] = []
    capability_delta = tuple(sorted(set(candidate.capability_claims) - set(candidate.known_capabilities)))

    # Credentials and live endpoint probing are deliberately outside this evaluator.
    if not _is_safe_source_uri(candidate.source_uri):
        blockers.append("SOURCE_REFERENCE_INVALID_OR_UNSAFE")
    if not candidate.source_revision.strip():
        missing.append("PINNED_SOURCE_REVISION")
    if not candidate.owner.strip():
        missing.append("ACCOUNTABLE_OWNER")
    if not candidate.capability_claims:
        missing.append("DECLARED_CAPABILITY_CLAIMS")
    if not candidate.capability_gap_ids:
        missing.append("EXPLICIT_CAPABILITY_GAP_IDS")
    if not candidate.evidence_refs:
        missing.append("TRACEABLE_EVIDENCE_REFERENCES")

    if candidate.identity_status == GateStatus.FAIL:
        blockers.append("IDENTITY_VERIFICATION_FAILED")
    elif candidate.identity_status != GateStatus.PASS:
        missing.append("IDENTITY_VERIFICATION")

    if candidate.contract_status == GateStatus.FAIL:
        blockers.append("CONTRACT_VALIDATION_FAILED")
    elif candidate.contract_status != GateStatus.PASS:
        missing.append("SERVER_CONTRACT_VALIDATION")

    for field_name, status in (
        ("SANDBOX_TESTS", candidate.sandbox_test_status),
        ("RECOVERY_AND_REPLAY_TESTS", candidate.recovery_replay_status),
        ("SECURITY_REVIEW", candidate.security_review_status),
        ("INDEPENDENT_VERIFICATION", candidate.independent_verification_status),
    ):
        if status == GateStatus.FAIL:
            blockers.append(f"{field_name}_FAILED")
        elif status != GateStatus.PASS:
            missing.append(field_name)

    if not capability_delta:
        blockers.append("NO_UNMET_CAPABILITY_DELTA_IDENTIFIED")
    if not set(candidate.capability_gap_ids).intersection(candidate.capability_claims):
        missing.append("CAPABILITY_GAP_TO_CLAIM_MAPPING")

    if candidate.novelty_review_status == NoveltyReviewStatus.CONTRADICTED_BY_PRIOR_ART:
        blockers.append("PRIOR_ART_CONTRADICTS_NOVELTY_CLAIM")
    elif candidate.novelty_review_status != NoveltyReviewStatus.COMPLETE:
        missing.append("COMPLETED_PRIOR_ART_REVIEW")
    if candidate.novelty_review_status == NoveltyReviewStatus.COMPLETE and not candidate.prior_art_refs:
        missing.append("PRIOR_ART_COVERAGE_REFERENCES")

    # A request field cannot alter this gate: candidates never self-authorize.
    if blockers:
        if set(blockers) == {"NO_UNMET_CAPABILITY_DELTA_IDENTIFIED"}:
            decision = ServerAssessmentDecision.NOT_NOVEL_FOR_CURRENT_SCOPE
            next_steps.extend([
                "PRESERVE_CANDIDATE_AND_EVIDENCE",
                "LINK_TO_EXISTING_CAPABILITY_OWNER",
                "DO_NOT_CREATE_A_NEW_CANONICAL_INNOVATION",
            ])
        else:
            decision = (
                ServerAssessmentDecision.QUARANTINED
                if any("IDENTITY" in item or "SOURCE_REFERENCE" in item for item in blockers)
                else ServerAssessmentDecision.REJECTED
            )
            next_steps.extend(["PRESERVE_CANDIDATE_AND_EVIDENCE", "REVIEW_BLOCKERS_BEFORE_RETRY"])
    elif missing:
        decision = ServerAssessmentDecision.RESEARCH_REQUIRED
        next_steps.extend(sorted(set(missing)))
    else:
        decision = ServerAssessmentDecision.ELIGIBLE_FOR_GOVERNANCE
        next_steps.extend([
            "SUBMIT_TO_INDEPENDENT_GOVERNANCE_REVIEW",
            "REVALIDATE_IDENTITY_AND_PROOF_FRESHNESS_AT_ADMISSION",
            "KEEP_RUNTIME_AND_CANONICAL_ADMISSION_CLOSED_UNTIL_AUTHORIZED",
        ])

    return ServerInnovationAssessment(
        server_id=candidate.server_id,
        candidate_digest=_digest_candidate(candidate),
        decision=decision,
        novelty_status=candidate.novelty_review_status,
        capability_delta=capability_delta,
        missing_requirements=tuple(sorted(set(missing))),
        blockers=tuple(sorted(set(blockers))),
        required_next_steps=tuple(next_steps),
        runtime_authorized=False,
        canonical_admission_authorized=False,
    )


def assess_many(candidates: Iterable[ServerInnovationCandidate]) -> tuple[ServerInnovationAssessment, ...]:
    """Return deterministic assessments sorted by stable server identifier."""
    materialized = list(candidates)
    ids = [candidate.server_id for candidate in materialized]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate server_id values must be unique within one assessment batch")
    results = [assess_server_candidate(candidate) for candidate in materialized]
    return tuple(sorted(results, key=lambda item: item.server_id))
