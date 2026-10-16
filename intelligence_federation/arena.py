"""Deterministic Ω-Arena orchestration, scoring, attribution, and 7-day gating.

This module intentionally depends only on standard-library primitives and the
existing VAIXLNS federation boundary. Provider execution is injected through
an adapter; the Arena owns orchestration, scoring, replay gating, and lineage
semantics but never canonicalizes itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Iterable, Mapping, Sequence


DEFAULT_WEIGHTS: Mapping[str, float] = {
    "correctness": 0.20,
    "reproducibility": 0.15,
    "security": 0.10,
    "completeness": 0.10,
    "contradiction_resistance": 0.10,
    "evidence_quality": 0.15,
    "robustness": 0.10,
    "innovation": 0.10,
}


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class ArenaManifest:
    arena_id: str
    task_id: str
    protocol_version: str
    task_corpus_hash: str
    environment_hash: str
    participants: tuple[str, ...]
    phases: tuple[str, ...]
    authority: str = "VX"
    evidence_required: bool = True
    replay_required: bool = True
    revalidation_days: int = 7

    def freeze_hash(self) -> str:
        return sha256({
            "arena_id": self.arena_id,
            "task_id": self.task_id,
            "protocol_version": self.protocol_version,
            "task_corpus_hash": self.task_corpus_hash,
            "environment_hash": self.environment_hash,
            "participants": self.participants,
            "phases": self.phases,
            "authority": self.authority,
            "evidence_required": self.evidence_required,
            "replay_required": self.replay_required,
            "revalidation_days": self.revalidation_days,
        })


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    originator: str
    contributors: tuple[str, ...] = ()
    derived_from: tuple[str, ...] = ()
    capability_ids: tuple[str, ...] = ()
    output_digest: str = ""


@dataclass(frozen=True)
class MatchResult:
    candidate_id: str
    first_success_at: str
    metrics: Mapping[str, float]
    evidence_refs: tuple[str, ...]
    replay_passed: bool
    hard_failures: tuple[str, ...] = ()
    innovation_fingerprint: str = ""
    first_observation_event: str = ""
    first_success_event: str = ""

    def normalized_metrics(self) -> dict[str, float]:
        return {
            key: max(0.0, min(100.0, float(self.metrics.get(key, 0.0))))
            for key in DEFAULT_WEIGHTS
        }


@dataclass(frozen=True)
class RankedCandidate:
    candidate_id: str
    score: float
    eligible: bool
    reason: str
    rank: int | None = None


@dataclass(frozen=True)
class TournamentResult:
    status: str
    champion_candidate_id: str | None
    ranking: tuple[RankedCandidate, ...]
    winner_locked_at: str | None = None


class ArenaInvariantError(ValueError):
    """Raised when an Arena invariant is violated."""


class OmegaArena:
    def __init__(
        self,
        manifest: ArenaManifest,
        *,
        weights: Mapping[str, float] | None = None,
    ) -> None:
        chosen = dict(weights or DEFAULT_WEIGHTS)
        if set(chosen) != set(DEFAULT_WEIGHTS):
            raise ArenaInvariantError("Scoring metrics must match the Arena contract.")
        if any(value < 0 for value in chosen.values()):
            raise ArenaInvariantError("Scoring weights cannot be negative.")
        if abs(sum(chosen.values()) - 1.0) > 1e-9:
            raise ArenaInvariantError("Scoring weights must sum to 1.0.")
        self.manifest = manifest
        self.weights = chosen
        self.frozen_hash = manifest.freeze_hash()

    def score(self, result: MatchResult) -> float:
        metrics = result.normalized_metrics()
        return round(
            sum(metrics[name] * self.weights[name] for name in self.weights), 6
        )

    def rank(
        self,
        candidates: Sequence[tuple[Candidate, MatchResult]],
        *,
        now: str,
    ) -> TournamentResult:
        current = parse_time(now)
        ranked: list[RankedCandidate] = []

        for candidate, result in candidates:
            failures = list(result.hard_failures)
            if self.manifest.evidence_required and not result.evidence_refs:
                failures.append("EVIDENCE_REQUIRED")
            if self.manifest.replay_required and not result.replay_passed:
                failures.append("REPLAY_REQUIRED")

            score = self.score(result)
            eligible = not failures
            reason = "ELIGIBLE" if eligible else "|".join(sorted(set(failures)))
            ranked.append(
                RankedCandidate(
                    candidate_id=candidate.candidate_id,
                    score=score,
                    eligible=eligible,
                    reason=reason,
                )
            )

        ranked.sort(key=lambda item: (-int(item.eligible), -item.score, item.candidate_id))
        ranked = [
            replace(item, rank=index)
            for index, item in enumerate(ranked, start=1)
        ]

        eligible = [item for item in ranked if item.eligible]
        if not eligible:
            return TournamentResult(
                status="NO_ELIGIBLE_CANDIDATE",
                champion_candidate_id=None,
                ranking=tuple(ranked),
            )

        champion = eligible[0]
        candidate_map = {candidate.candidate_id: result for candidate, result in candidates}
        winner_result = candidate_map[champion.candidate_id]
        revalidation_at = parse_time(winner_result.first_success_at) + timedelta(
            days=self.manifest.revalidation_days
        )

        if current < revalidation_at:
            return TournamentResult(
                status="PROVISIONAL",
                champion_candidate_id=None,
                ranking=tuple(ranked),
            )

        locked_at = current.isoformat().replace("+00:00", "Z")
        return TournamentResult(
            status="TOURNAMENT_CHAMPION",
            champion_candidate_id=champion.candidate_id,
            ranking=tuple(ranked),
            winner_locked_at=locked_at,
        )


def build_invention_record(candidate: Candidate, result: MatchResult) -> dict:
    """Build a lineage reference that points to existing Evidence/Provenance records."""
    if not result.first_observation_event:
        raise ArenaInvariantError("Attribution requires first_observation_event.")
    if not result.innovation_fingerprint:
        raise ArenaInvariantError("Attribution requires innovation_fingerprint.")

    return {
        "invention_id": f"INV-{sha256(result.innovation_fingerprint)[:16]}",
        "invention_fingerprint": result.innovation_fingerprint,
        "first_observation_event": result.first_observation_event,
        "first_appearance": result.first_success_at,
        "originator": {"type": "provider_or_team", "id": candidate.originator},
        "first_success_event": result.first_success_event or None,
        "contributions": [
            {
                "contributor_type": "provider_or_team",
                "contributor_id": contributor,
                "contribution_type": "derived_or_improved",
                "derived_from": list(candidate.derived_from),
            }
            for contributor in candidate.contributors
        ],
        "derived_from": list(candidate.derived_from),
        "novelty_evidence": list(result.evidence_refs),
        "execution_evidence": list(result.evidence_refs),
        "verification_evidence": list(result.evidence_refs),
        "replay_evidence": list(result.evidence_refs) if result.replay_passed else [],
        "success_count": 1,
        "revalidation_window": None,
        "champion_window": None,
        "status": "CANDIDATE",
        "supersedes": None,
        "superseded_by": None,
    }


def validate_attribution(record: Mapping[str, object]) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    originator = record.get("originator")
    if not isinstance(originator, Mapping) or not originator.get("id"):
        errors.append("ORIGINATOR_REQUIRED")
    if not record.get("first_observation_event"):
        errors.append("FIRST_OBSERVATION_REQUIRED")
    if not record.get("invention_fingerprint"):
        errors.append("INVENTION_FINGERPRINT_REQUIRED")
    return (not errors, tuple(errors))
