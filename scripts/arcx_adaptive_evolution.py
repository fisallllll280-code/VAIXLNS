"""ARC-X bounded adaptive-evolution planner. Pure, deterministic, and non-executing."""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REVISION = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_LOCAL_CLASSES = {"LOCAL_REFACTOR", "LOCAL_OPTIMIZATION", "LOCAL_CACHE", "LOCAL_INDEX"}
_FORBIDDEN_CLASSES = {
    "CANON_CHANGE", "AUTHORITY_CHANGE", "CROSS_SYSTEM_WRITE",
    "EXTERNAL_SIDE_EFFECT", "PRODUCTION_MUTATION",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _score(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and 0 <= value <= 1


def _evidence_state(evidence: Any) -> tuple[str, list[str]]:
    if not isinstance(evidence, list) or not evidence:
        return "PENDING_EVIDENCE", ["EVIDENCE_RECORD_REQUIRED"]
    blockers: list[str] = []
    has_independent = False
    for item in evidence:
        if not isinstance(item, dict):
            blockers.append("INVALID_EVIDENCE_RECORD")
            continue
        revision = item.get("source_revision")
        sha = item.get("sha256")
        if not isinstance(revision, str) or not _REVISION.fullmatch(revision):
            blockers.append("INVALID_EVIDENCE_SOURCE_REVISION")
        if not isinstance(sha, str) or not _SHA256.fullmatch(sha):
            blockers.append("INVALID_EVIDENCE_DIGEST")
        if item.get("independent_validation") is True and not blockers:
            has_independent = True
    if blockers:
        return "BLOCKED", sorted(set(blockers))
    if not has_independent:
        return "PENDING_EVIDENCE", ["INDEPENDENT_VALIDATION_REQUIRED"]
    return "EVIDENCE_PRESENT", []


def plan_evolution(system: dict[str, Any], proposals: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate local proposals without applying changes or granting authority."""
    errors: list[str] = []
    system_id = system.get("system_id") if isinstance(system, dict) else None
    boundary = system.get("boundary_sha256") if isinstance(system, dict) else None
    capabilities = system.get("allowed_capabilities") if isinstance(system, dict) else None
    if not isinstance(system_id, str) or not system_id.strip():
        errors.append("INVALID_SYSTEM_ID")
    if not isinstance(boundary, str) or not _SHA256.fullmatch(boundary):
        errors.append("INVALID_BOUNDARY_DIGEST")
    if not isinstance(capabilities, list) or any(not isinstance(x, str) or not x.strip() for x in capabilities):
        errors.append("INVALID_ALLOWED_CAPABILITIES")
        capabilities = []
    if not isinstance(proposals, list):
        proposals = []
        errors.append("INVALID_PROPOSAL_LIST")

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for proposal in proposals:
        blockers: list[str] = []
        if not isinstance(proposal, dict):
            results.append({"proposal_id": None, "state": "BLOCKED", "blockers": ["INVALID_PROPOSAL_RECORD"], "applied": False})
            continue
        pid = proposal.get("proposal_id")
        if not isinstance(pid, str) or not pid.strip():
            blockers.append("INVALID_PROPOSAL_ID")
            pid = None
        elif pid in seen:
            blockers.append("DUPLICATE_PROPOSAL_ID")
        else:
            seen.add(pid)

        if proposal.get("system_id") != system_id:
            blockers.append("SYSTEM_ID_MISMATCH")
        if proposal.get("boundary_sha256") != boundary:
            blockers.append("BOUNDARY_DIGEST_MISMATCH")
        capability = proposal.get("capability_id")
        if not isinstance(capability, str) or capability not in capabilities:
            blockers.append("CAPABILITY_OUTSIDE_SYSTEM_BOUNDARY")

        change_class = proposal.get("change_class")
        if not isinstance(change_class, str):
            blockers.append("UNKNOWN_OR_NONLOCAL_CHANGE_CLASS")
        elif change_class in _FORBIDDEN_CLASSES:
            blockers.append("CHANGE_CLASS_REQUIRES_SEPARATE_GOVERNED_WORKFLOW")
        elif change_class not in _ALLOWED_LOCAL_CLASSES:
            blockers.append("UNKNOWN_OR_NONLOCAL_CHANGE_CLASS")

        benefit = proposal.get("benefit_score")
        risk = proposal.get("risk_score")
        if not _score(benefit) or not _score(risk):
            blockers.append("BENEFIT_AND_RISK_MUST_BE_FINITE_SCORES_IN_RANGE")
            net = None
        else:
            net = round(float(benefit) - float(risk), 8)

        evidence_state, evidence_blockers = _evidence_state(proposal.get("evidence"))
        if evidence_state == "BLOCKED":
            blockers.extend(evidence_blockers)

        if blockers:
            state = "BLOCKED"
        elif evidence_state != "EVIDENCE_PRESENT":
            state = "PENDING_EVIDENCE"
        elif net is not None and net <= 0:
            state = "REJECTED_LOW_NET_VALUE"
        else:
            state = "PENDING_HUMAN_REVIEW"

        results.append({
            "proposal_id": pid,
            "system_id": proposal.get("system_id"),
            "capability_id": capability,
            "change_class": change_class,
            "state": state,
            "benefit_score": benefit if _score(benefit) else None,
            "risk_score": risk if _score(risk) else None,
            "net_score": net,
            "evidence_state": evidence_state,
            "blockers": sorted(set(blockers)),
            "authority_granted": False,
            "applied": False,
        })

    results.sort(key=lambda x: (str(x.get("proposal_id")), str(x.get("capability_id"))))
    if errors or any(x["state"] == "BLOCKED" for x in results):
        state = "BLOCKED"
    elif any(x["state"] == "PENDING_HUMAN_REVIEW" for x in results):
        state = "READY_FOR_REVIEW"
    elif any(x["state"] == "PENDING_EVIDENCE" for x in results):
        state = "PENDING_EVIDENCE"
    else:
        state = "NO_APPROVED_CHANGE"

    plan: dict[str, Any] = {
        "schema_version": "arcx-bounded-evolution-plan-v1",
        "system_id": system_id,
        "boundary_sha256": boundary,
        "state": state,
        "proposals": results,
        "errors": sorted(set(errors)),
        "authority_decision": "PENDING",
        "execution_performed": False,
        "canonical_write_performed": False,
        "changes_applied": False,
    }
    plan["plan_sha256"] = digest(plan)
    return plan
