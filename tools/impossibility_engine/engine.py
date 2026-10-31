"""Deterministic impossibility triage and feasibility-planning prototype.

This module does not prove physical impossibility or autonomously execute plans.
It identifies explicit contradictions and produces evidence-oriented next steps.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable
import hashlib
import json


ENGINE_VERSION = "0.1.0"
VALID_EVIDENCE_STATES = {"OBSERVED", "INFERRED", "HYPOTHESIS", "UNKNOWN", "CONTRADICTED"}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    statement: str
    evidence_needed: str


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _range_conflicts(constraints: Iterable[dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    for item in constraints:
        if not isinstance(item, dict) or item.get("kind") != "range":
            continue
        variable = item.get("variable")
        low = item.get("min")
        high = item.get("max")
        if not isinstance(variable, str) or not variable.strip():
            continue
        if isinstance(low, (int, float)) and isinstance(high, (int, float)) and low > high:
            findings.append(Finding(
                code="RANGE_CONTRADICTION",
                severity="BLOCKING",
                statement=f"Declared lower bound for '{variable}' ({low}) exceeds upper bound ({high}).",
                evidence_needed="Confirm units, bounds, and whether either constraint may be relaxed."
            ))
    return findings


def assess(problem: dict[str, Any]) -> dict[str, Any]:
    """Return a conservative, deterministic feasibility assessment for a problem record."""
    if not isinstance(problem, dict):
        raise TypeError("problem must be a JSON object")

    title = str(problem.get("title") or "Untitled engineering challenge").strip()
    goal = str(problem.get("goal") or "").strip()
    constraints = problem.get("constraints") or []
    resources = problem.get("resources") or []
    evidence = problem.get("evidence") or []

    if not isinstance(constraints, list) or not all(isinstance(x, dict) for x in constraints):
        raise ValueError("constraints must be a list of objects")
    if not isinstance(resources, list) or not all(isinstance(x, str) for x in resources):
        raise ValueError("resources must be a list of strings")
    if not isinstance(evidence, list) or not all(isinstance(x, dict) for x in evidence):
        raise ValueError("evidence must be a list of objects")

    findings = _range_conflicts(constraints)
    unknown_evidence = [
        item for item in evidence
        if item.get("state", "UNKNOWN") not in VALID_EVIDENCE_STATES
    ]
    if unknown_evidence:
        raise ValueError("each evidence item state must be one of: " + ", ".join(sorted(VALID_EVIDENCE_STATES)))

    missing = []
    if not goal:
        missing.append("A precise, observable success condition.")
    if not constraints:
        missing.append("Explicit constraints, including units and non-negotiable limits.")
    if not evidence:
        missing.append("Evidence for key assumptions and any claimed impossibility.")

    if findings:
        status = "CONTRADICTION_DETECTED"
        summary = "At least one declared constraint set is internally inconsistent; resolve it before planning execution."
    elif missing:
        status = "INSUFFICIENT_SPECIFICATION"
        summary = "The goal cannot be responsibly assessed yet; gather the missing specification and evidence."
    else:
        status = "ENGINEERING_CHALLENGE"
        summary = "No supported proof of impossibility was found by this deterministic triage. Feasibility remains unproven."

    plan = [
        {"step": 1, "action": "Define measurable success criteria", "output": "Acceptance contract", "gate": "Every criterion is observable and testable."},
        {"step": 2, "action": "Separate facts, assumptions, and unknowns", "output": "Evidence ledger", "gate": "Each important claim has a state and provenance."},
        {"step": 3, "action": "Map constraints to candidate mechanisms", "output": "Constraint-to-mechanism matrix", "gate": "Every hard constraint is addressed or explicitly unresolved."},
        {"step": 4, "action": "Generate at least two materially different routes", "output": "Alternative designs with trade-offs", "gate": "Compare cost, risk, time, and reversibility."},
        {"step": 5, "action": "Run the cheapest falsifying experiment first", "output": "Reproducible experiment record", "gate": "Record inputs, environment, result, and artifact hash."},
        {"step": 6, "action": "Update the feasibility classification", "output": "Versioned decision record", "gate": "Never label VERIFIED without reproducible evidence."},
    ]

    alternatives = [
        {"route": "RELAX_CONSTRAINT", "when": "A conflicting or overly strict constraint is negotiable.", "tradeoff": "May change the original objective."},
        {"route": "SUBSTITUTE_MECHANISM", "when": "The goal is valid but the proposed mechanism is blocked.", "tradeoff": "Requires validating functional equivalence."},
        {"route": "DECOMPOSE_GOAL", "when": "The whole target exceeds current resources or capabilities.", "tradeoff": "May deliver value in staged increments."},
        {"route": "BOUND_THE_CLAIM", "when": "Evidence supports only a narrower operating range.", "tradeoff": "The result must state its limits."},
    ]

    result = {
        "engine": "OMEGA-IMPOSSIBILITY-ENGINE",
        "version": ENGINE_VERSION,
        "state": "SPECIFIED",
        "title": title,
        "goal": goal,
        "classification": status,
        "summary": summary,
        "findings": [asdict(x) for x in findings],
        "missing_information": missing,
        "known_resources": resources,
        "evidence_ledger": evidence,
        "candidate_routes": alternatives,
        "execution_plan": plan,
        "safety_boundary": {
            "no_external_calls": True,
            "no_code_execution": True,
            "no_claim_of_physical_impossibility_without_domain_proof": True,
            "no_AUTOMATIC_VERIFIED_promotion": True,
            "human_approval_required_for_side_effects": True,
        },
        "limits": [
            "This is deterministic triage, not a general theorem prover or scientific oracle.",
            "Absence of a detected contradiction does not establish feasibility.",
            "Physical or mathematical impossibility requires domain-specific formal proof or validated evidence.",
        ],
    }
    result["assessment_sha256"] = _stable_hash(result)
    return result
