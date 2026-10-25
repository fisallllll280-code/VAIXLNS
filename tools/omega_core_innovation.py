"""Ω-Core reference engine: capability gaps, noninflating evidence, scoped governance.
Pure Python standard library. Draft implementation; production signing and persistence external.
"""
from dataclasses import dataclass, field
from typing import FrozenSet, Tuple

@dataclass(frozen=True)
class Capability:
    identifier: str
    required: FrozenSet[str]
    available: FrozenSet[str]
    verified: FrozenSet[str]
    evidence_refs: Tuple[str, ...] = ()

    def __post_init__(self):
        if not self.identifier or not self.verified <= self.available:
            raise ValueError("Invalid capability identity or verified subset")

    def gaps(self):
        return {
            "unavailable": sorted(self.required - self.available),
            "unverified": sorted((self.required & self.available) - self.verified),
        }

@dataclass(frozen=True)
class Evidence:
    identifier: str
    root: str
    content_digest: str
    claim: str
    valid: bool
    independent_test: bool = False
    dependencies: Tuple[str, ...] = ()

def fuse(claim: str, evidence: Tuple[Evidence, ...]):
    """Conservative support: group by common provenance root; duplicated report never adds roots."""
    if len({e.identifier for e in evidence}) != len(evidence):
        raise ValueError("Duplicate evidence identifier")
    known = {e.identifier: e for e in evidence}
    roots = set()
    rejected = []
    for item in evidence:
        if item.claim != claim or not item.valid or not item.root or not item.content_digest:
            rejected.append(item.identifier)
            continue
        if any(dep not in known for dep in item.dependencies):
            rejected.append(item.identifier)
            continue
        # A derived document may not claim independent support through a different root.
        if any(known[dep].root != item.root for dep in item.dependencies):
            rejected.append(item.identifier)
            continue
        if item.independent_test:
            roots.add((item.root, item.content_digest))
    # Multiple independent tests from the same source root count as one support unit.
    unique_roots = sorted({root for root, _ in roots})
    return {"claim": claim, "independent_roots": unique_roots,
            "support_count": len(unique_roots), "rejected": sorted(rejected)}

@dataclass(frozen=True)
class PermitRequest:
    capability_id: str
    environment: str
    policy_digest: str
    requested_action: str
    tests_passed: bool
    evidence_claim: str

def govern(request: PermitRequest, assurance: dict, *, policy_approved: bool,
           minimum_independent_roots: int = 1):
    if not request.capability_id or not request.environment or not request.policy_digest:
        return {"decision": "HOLD", "reason": "MISSING_SCOPE"}
    if request.requested_action not in ("EXPERIMENT", "PRODUCTION"):
        return {"decision": "REJECT", "reason": "UNKNOWN_ACTION"}
    if not policy_approved:
        return {"decision": "HOLD", "reason": "POLICY_NOT_APPROVED"}
    if request.requested_action == "EXPERIMENT":
        if request.environment != "isolated":
            return {"decision": "REJECT", "reason": "EXPERIMENT_NOT_ISOLATED"}
        return {"decision": "APPROVE_EXPERIMENT", "reason": "ISOLATED_ONLY"}
    if not request.tests_passed:
        return {"decision": "HOLD", "reason": "TESTS_NOT_PASSED"}
    if assurance.get("claim") != request.evidence_claim:
        return {"decision": "HOLD", "reason": "CLAIM_MISMATCH"}
    if assurance.get("support_count", 0) < minimum_independent_roots:
        return {"decision": "HOLD", "reason": "INSUFFICIENT_INDEPENDENT_EVIDENCE"}
    return {"decision": "ELIGIBLE_FOR_SIGNED_PERMIT", "reason": "EXTERNAL_SIGNATURE_REQUIRED"}
