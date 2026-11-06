"""Deterministic policy gate for proposed sovereign system transitions.

This module evaluates a declared change package. It does not execute changes,
authenticate identities, enforce OS isolation, or replace external authorization.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA_VERSION = "vaixl-meta-kernel/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_AUTONOMOUS_ACTIONS = {
    "canonical-write",
    "production-deploy",
    "self-promote",
    "financial-transfer",
    "credential-issue",
}


def canonical_json(value: Any) -> bytes:
    """Serialize JSON deterministically for stable digest calculation."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def evaluate_transition(package: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic decision record; never apply the requested change."""
    errors: list[str] = []
    warnings: list[str] = []

    if package.get("schema_version") != SCHEMA_VERSION:
        errors.append("SCHEMA_VERSION_UNSUPPORTED")

    before = package.get("before")
    change = package.get("change")
    authority = package.get("authority")
    evidence = package.get("evidence")
    policy = package.get("policy")

    if not isinstance(before, dict):
        errors.append("BEFORE_STATE_REQUIRED")
        before = {}
    if not isinstance(change, dict):
        errors.append("CHANGE_REQUIRED")
        change = {}
    if not isinstance(authority, dict):
        errors.append("AUTHORITY_RECORD_REQUIRED")
        authority = {}
    if not isinstance(evidence, list):
        errors.append("EVIDENCE_LIST_REQUIRED")
        evidence = []
    if not isinstance(policy, dict):
        errors.append("POLICY_REQUIRED")
        policy = {}

    required_identity = ("entity_id", "constitution_hash", "lineage_id")
    for key in required_identity:
        if not isinstance(before.get(key), str) or not before.get(key):
            errors.append(f"BEFORE_{key.upper()}_REQUIRED")

    constitution_hash = before.get("constitution_hash", "")
    if constitution_hash and not HEX64.fullmatch(constitution_hash):
        errors.append("CONSTITUTION_HASH_INVALID")

    changed_fields = change.get("changed_fields", [])
    if not isinstance(changed_fields, list) or not all(
        isinstance(item, str) for item in changed_fields
    ):
        errors.append("CHANGED_FIELDS_INVALID")
        changed_fields = []

    immutable_fields = set(policy.get("immutable_fields", [
        "entity_id", "lineage_id", "constitution_hash"
    ]))
    if immutable_fields.intersection(changed_fields):
        errors.append("CONSTITUTIONAL_INVARIANT_CHANGE_BLOCKED")

    requested_actions = change.get("requested_actions", [])
    if not isinstance(requested_actions, list) or not all(
        isinstance(item, str) for item in requested_actions
    ):
        errors.append("REQUESTED_ACTIONS_INVALID")
        requested_actions = []

    forbidden = set(requested_actions).intersection(FORBIDDEN_AUTONOMOUS_ACTIONS)
    if forbidden:
        errors.append("PRIVILEGED_ACTION_REQUIRES_EXTERNAL_GATE")

    allowed_approvers = policy.get("authorized_approvers", [])
    approver = authority.get("approver_id")
    if not isinstance(allowed_approvers, list) or not all(
        isinstance(item, str) for item in allowed_approvers
    ):
        errors.append("AUTHORIZED_APPROVERS_POLICY_INVALID")
        allowed_approvers = []
    if authority.get("status") != "APPROVED":
        errors.append("AUTHORITY_NOT_APPROVED")
    elif not approver or approver not in allowed_approvers:
        errors.append("APPROVER_NOT_AUTHORIZED")

    if authority.get("signature_verified") is not True:
        errors.append("AUTHORITY_SIGNATURE_NOT_VERIFIED")

    if len(evidence) < int(policy.get("minimum_evidence_count", 1)):
        errors.append("INSUFFICIENT_EVIDENCE")

    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(f"EVIDENCE_{index}_INVALID")
            continue
        if not isinstance(item.get("source"), str) or not item["source"]:
            errors.append(f"EVIDENCE_{index}_SOURCE_REQUIRED")
        if not isinstance(item.get("sha256"), str) or not HEX64.fullmatch(item["sha256"]):
            errors.append(f"EVIDENCE_{index}_SHA256_INVALID")
        if item.get("verified") is not True:
            errors.append(f"EVIDENCE_{index}_NOT_VERIFIED")

    simulation = change.get("simulation")
    if policy.get("require_simulation", True) and not (
        isinstance(simulation, dict) and simulation.get("passed") is True
        and simulation.get("evidence_ref")
    ):
        errors.append("SIMULATION_PROOF_REQUIRED")

    test_result = change.get("tests")
    if policy.get("require_tests", True) and not (
        isinstance(test_result, dict) and test_result.get("passed") is True
        and test_result.get("evidence_ref")
    ):
        errors.append("TEST_PROOF_REQUIRED")

    if change.get("rollback_plan_ref") is None:
        errors.append("ROLLBACK_PLAN_REQUIRED")

    errors = sorted(set(errors))
    decision = "REJECTED" if errors else "ELIGIBLE_FOR_SEPARATE_APPROVAL"
    if not errors:
        warnings.append(
            "ELIGIBILITY_IS_NOT_EXECUTION; external enforcement and final approval remain required"
        )

    decision_body = {
        "schema_version": SCHEMA_VERSION,
        "decision": decision,
        "errors": errors,
        "warnings": warnings,
        "input_sha256": sha256_json(package),
        "entity_id": before.get("entity_id"),
        "change_id": change.get("change_id"),
    }
    decision_body["decision_sha256"] = sha256_json(decision_body)
    return decision_body
