"""Bounded multi-agent / multi-model consultation over the existing VX federation.

This module builds a review plan; it never invokes paid APIs automatically.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from intelligence_federation.adaptive_router import Candidate, Task, Receipt, rank

ROLES = ("proposer", "challenger", "engineering_reviewer", "security_reviewer", "proof_reviewer")
ROLE_REQUIREMENTS = {
    "proposer": frozenset({"reasoning"}),
    "challenger": frozenset({"reasoning"}),
    "engineering_reviewer": frozenset({"coding"}),
    "security_reviewer": frozenset({"reasoning"}),
    "proof_reviewer": frozenset({"reasoning"}),
}

@dataclass(frozen=True)
class CouncilPolicy:
    max_models: int = 5
    max_unit_cost: float = 0.0
    min_distinct_providers: int = 2


def plan_council(mission_id: str, candidates: list[Candidate],
                 receipts: list[Receipt] | None = None,
                 policy: CouncilPolicy = CouncilPolicy()) -> dict[str, Any]:
    if not mission_id.strip() or not 1 <= policy.max_models <= 5 or policy.min_distinct_providers < 1:
        raise ValueError("INVALID_COUNCIL_POLICY")
    assigned: list[dict[str, str]] = []
    used = set()
    for role in ROLES[:policy.max_models]:
        task = Task(mission_id + ":" + role, ROLE_REQUIREMENTS[role],
                    max_unit_cost=policy.max_unit_cost)
        eligible = [r for r in rank(task, candidates, receipts or []) if r["eligible"]]
        eligible.sort(key=lambda r: (r["provider"] in used, -r["estimated_quality"], r["provider"]))
        if not eligible:
            return {"status": "BLOCKED", "reason": "NO_ELIGIBLE_MODEL_FOR_" + role.upper(),
                    "assignments": [], "api_called": False}
        choice = eligible[0]
        assigned.append({"role": role, "provider": choice["provider"], "model_id": choice["model_id"]})
        used.add(choice["provider"])
    if len(used) < policy.min_distinct_providers:
        return {"status": "BLOCKED", "reason": "INSUFFICIENT_INDEPENDENT_PROVIDERS",
                "assignments": [], "api_called": False}
    return {"status": "PROPOSED", "mission_id": mission_id,
            "assignments": assigned, "distinct_providers": len(used),
            "api_called": False, "commit_authorized": False,
            "next_gate": "REVALIDATE_REGISTRY_AUTH_SCOPE_AND_BUDGET_BEFORE_DISPATCH"}


def normalize_provider_registry(raw: dict[str, Any]) -> list[Candidate]:
    """Unverified provider metadata must never be admitted as ACTIVE."""
    result = []
    for p in raw.get("providers", []):
        if not p.get("provider") or not p.get("model_id"):
            continue
        result.append(Candidate(p["provider"], p["model_id"],
                                frozenset(p.get("verified_capabilities", [])),
                                state="NOT_CONFIGURED"))
    return result
