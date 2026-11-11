"""Evidence-gated task routing and verified feedback for VX.

No network calls, credential handling or base-model weight updates occur here.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import FrozenSet, Iterable

@dataclass(frozen=True)
class Candidate:
    provider: str
    model_id: str
    capabilities: FrozenSet[str]
    state: str = "NOT_CONFIGURED"
    sovereignty: str = "external"
    unit_cost: float = 0.0

@dataclass(frozen=True)
class Task:
    task_id: str
    required: FrozenSet[str]
    allowed_providers: FrozenSet[str] = frozenset()
    require_sovereign: bool = False
    max_unit_cost: float = 0.0

@dataclass(frozen=True)
class Receipt:
    task_id: str
    provider: str
    model_id: str
    score: float
    evidence_id: str
    verified: bool

def rank(task: Task, candidates: Iterable[Candidate], receipts: Iterable[Receipt] = ()) -> list[dict]:
    """Stable explainable ranking. No dispatch occurs; only ACTIVE candidates can be eligible."""
    verified: dict[tuple[str, str], list[float]] = {}
    for r in receipts:
        if r.verified and r.evidence_id.strip() and 0 <= r.score <= 1:
            verified.setdefault((r.provider, r.model_id), []).append(r.score)
    output = []
    for c in candidates:
        reasons = []
        if c.state != "ACTIVE":
            reasons.append("not_active")
        if not task.required.issubset(c.capabilities):
            reasons.append("capability_mismatch")
        if task.allowed_providers and c.provider not in task.allowed_providers:
            reasons.append("provider_not_allowed")
        if task.require_sovereign and c.sovereignty != "sovereign":
            reasons.append("sovereignty_mismatch")
        if c.unit_cost < 0 or c.unit_cost > task.max_unit_cost:
            reasons.append("budget_exceeded")
        scores = verified.get((c.provider, c.model_id), [])
        quality = (1.5 + sum(scores)) / (3 + len(scores))
        output.append({"provider": c.provider, "model_id": c.model_id,
                       "eligible": not reasons, "reasons": reasons,
                       "verified_samples": len(scores), "estimated_quality": round(quality, 6)})
    return sorted(output, key=lambda x: (not x["eligible"], -x["estimated_quality"], x["provider"], x["model_id"]))

def select(task: Task, candidates: Iterable[Candidate], receipts: Iterable[Receipt] = ()) -> dict:
    eligible = [r for r in rank(task, candidates, receipts) if r["eligible"]]
    if not eligible:
        return {"status": "BLOCKED", "candidate": None, "reason": "no_eligible_verified_active_model"}
    return {"status": "PROPOSED", "candidate": eligible[0], "reason": "eligible_model_ranked_from_verified_feedback"}
