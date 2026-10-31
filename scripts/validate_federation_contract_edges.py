#!/usr/bin/env python3
"""Validate typed inter-system contracts and prevent unsafe federation activation.

This offline validator checks declared boundaries only. It does not make network
connections or establish that any adapter, endpoint, or runtime is running.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "registry/federation/federation_contract_edges.v1.json"
SYSTEMS_MANIFEST = ROOT / "registry/federation/four_system_unification.v1.json"

ALLOWED_KINDS = {
    "knowledge_observation",
    "discovery_proposal",
    "execution_request",
    "execution_evidence",
}
ALLOWED_STATUSES = {
    "BLOCKED_IDENTITY",
    "SPECIFIED_NOT_CONNECTED",
    "ADMISSION_REQUIRED",
    "ACTIVE_VERIFIED",
}
REQUIRED_EDGES = {
    ("VLNS", "VAIXLNS", "knowledge_observation"),
    ("NEXNET", "VAIXLNS", "discovery_proposal"),
    ("VAIXLNS", "VX", "execution_request"),
    ("VX", "VAIXLNS", "execution_evidence"),
}
UNVERIFIED = "UNVERIFIED"


def validate(data: dict[str, Any], systems_data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if data.get("contract_id") != "VAIXLNS.FEDERATION.CONTRACT_EDGES.V1":
        errors.append("contract_id must identify the v1 federation contract")
    authority = data.get("authority", {})
    if authority.get("canonical_source") != "project.genome":
        errors.append("canonical_source must remain project.genome")
    if authority.get("master_index") != "Ω.000":
        errors.append("master_index must remain Ω.000")
    if authority.get("federation_owner") != "VAIXLNS":
        errors.append("VAIXLNS must remain federation authority")
    if authority.get("execution_owner") != "VX":
        errors.append("VX must remain the execution owner")

    rules = data.get("boundary_rules", {})
    expected_rules = {
        "direct_cross_repository_imports_allowed": False,
        "cross_system_calls_require_declared_adapter": True,
        "identity_mismatch_behavior": "BLOCK",
        "unknown_contract_behavior": "BLOCK",
        "incomplete_evidence_behavior": "HOLD",
        "execution_requires_explicit_authority_grant": True,
        "runtime_claim_requires_current_observation": True,
        "proposal_can_mutate_canonical_state": False,
        "failure_mode": "FAIL_CLOSED",
    }
    for key, expected in expected_rules.items():
        if rules.get(key) != expected:
            errors.append(f"boundary_rules.{key} must be {expected!r}")

    systems = systems_data.get("systems", [])
    if not isinstance(systems, list):
        return errors + ["systems manifest must contain a systems list"]
    system_map = {
        item.get("system_id"): item
        for item in systems
        if isinstance(item, dict) and isinstance(item.get("system_id"), str)
    }
    if set(system_map) != {"VAIXLNS", "VLNS", "VX", "NEXNET"}:
        errors.append("referenced systems must be the four distinct system identities")

    edges = data.get("edges")
    if not isinstance(edges, list):
        return errors + ["edges must be a list"]
    edge_ids = [e.get("edge_id") for e in edges if isinstance(e, dict)]
    if len(edge_ids) != len(edges) or len(edge_ids) != len(set(edge_ids)):
        errors.append("every edge must be an object with a unique edge_id")

    observed_edges: set[tuple[str, str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            errors.append("every edge must be an object")
            continue
        eid = edge.get("edge_id", "<missing>")
        source = edge.get("from_system")
        target = edge.get("to_system")
        kind = edge.get("kind")
        status = edge.get("status")
        enabled = edge.get("enabled")

        if source not in system_map or target not in system_map:
            errors.append(f"{eid}: both endpoints must reference declared system IDs")
            continue
        if source == target:
            errors.append(f"{eid}: self-edges are not allowed")
        if kind not in ALLOWED_KINDS:
            errors.append(f"{eid}: unsupported edge kind")
        else:
            observed_edges.add((source, target, kind))
        if status not in ALLOWED_STATUSES:
            errors.append(f"{eid}: unsupported status")
        if not isinstance(enabled, bool):
            errors.append(f"{eid}: enabled must be boolean")
        if not edge.get("adapter"):
            errors.append(f"{eid}: adapter is required; direct coupling is prohibited")
        if not edge.get("contract_ref"):
            errors.append(f"{eid}: contract_ref is required")
        if edge.get("failure_mode") != "FAIL_CLOSED":
            errors.append(f"{eid}: failure_mode must be FAIL_CLOSED")
        if not isinstance(edge.get("allowed_effects"), list) or not edge.get("allowed_effects"):
            errors.append(f"{eid}: allowed_effects must be a non-empty list")
        if not isinstance(edge.get("forbidden_effects"), list) or not edge.get("forbidden_effects"):
            errors.append(f"{eid}: forbidden_effects must be a non-empty list")
        if not isinstance(edge.get("required_evidence"), list) or not edge.get("required_evidence"):
            errors.append(f"{eid}: required_evidence must be a non-empty list")

        endpoint_states = {
            system_map.get(source, {}).get("identity_state"),
            system_map.get(target, {}).get("identity_state"),
        }
        has_unverified_identity = UNVERIFIED in endpoint_states
        if enabled is True and has_unverified_identity:
            errors.append(f"{eid}: cannot enable an edge with an unresolved system identity")
        if status == "BLOCKED_IDENTITY":
            if enabled is not False:
                errors.append(f"{eid}: BLOCKED_IDENTITY edges must be disabled")
            if not has_unverified_identity:
                errors.append(f"{eid}: BLOCKED_IDENTITY requires an unresolved endpoint identity")
        if status == "SPECIFIED_NOT_CONNECTED" and enabled is not False:
            errors.append(f"{eid}: SPECIFIED_NOT_CONNECTED edges must remain disabled")
        if status == "ACTIVE_VERIFIED":
            receipt = edge.get("activation_evidence")
            if enabled is not True:
                errors.append(f"{eid}: ACTIVE_VERIFIED requires enabled=true")
            if not isinstance(receipt, dict) or not all(
                receipt.get(k) for k in ("source_revision", "evidence_uri", "digest", "observed_at")
            ):
                errors.append(f"{eid}: ACTIVE_VERIFIED requires revision-bound activation evidence")
        elif edge.get("activation_evidence") not in (None, {}):
            errors.append(f"{eid}: activation evidence cannot promote a non-active edge implicitly")

        if kind == "execution_request":
            forbidden = set(edge.get("forbidden_effects", []))
            if source != "VAIXLNS" or target != "VX":
                errors.append(f"{eid}: execution requests must flow VAIXLNS -> VX")
            if edge.get("requires_authority_grant") is not True:
                errors.append(f"{eid}: execution requests require an explicit authority grant")
            if not {"unscoped_execution", "self_authorization"}.issubset(forbidden):
                errors.append(f"{eid}: execution requests must forbid unscoped execution and self-authorization")
        if kind in {"knowledge_observation", "discovery_proposal"}:
            forbidden = set(edge.get("forbidden_effects", []))
            if target != "VAIXLNS":
                errors.append(f"{eid}: observations/proposals must enter through VAIXLNS")
            if not {"canonical_write", "production_execution", "authority_grant"}.issubset(forbidden):
                errors.append(f"{eid}: observations/proposals cannot carry canonical or execution authority")
        if kind == "execution_evidence":
            forbidden = set(edge.get("forbidden_effects", []))
            if source != "VX" or target != "VAIXLNS":
                errors.append(f"{eid}: execution evidence must flow VX -> VAIXLNS")
            if not {"canonical_write", "authority_grant"}.issubset(forbidden):
                errors.append(f"{eid}: execution evidence cannot itself authorize canonical changes")

    missing_edges = REQUIRED_EDGES - observed_edges
    if missing_edges:
        errors.append("missing required typed edges: " + ", ".join(
            f"{a}->{b}:{kind}" for a, b, kind in sorted(missing_edges)
        ))
    if data.get("status") not in {"PROPOSAL", "SPECIFIED", "PARTIAL"}:
        errors.append("contract status must remain non-verified until independent validation")
    return errors


def main() -> int:
    try:
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        systems_data = json.loads(SYSTEMS_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot load federation contract: {exc}", file=sys.stderr)
        return 2
    errors = validate(data, systems_data)
    if errors:
        print("FAIL: federation contract edges")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: typed federation contract invariants")
    print("LIMIT: adapters are specified, not connected; no runtime or deployment claim is made")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
