#!/usr/bin/env python3
"""Audit the four-system registry and emit a digest-bound, read-only evidence report.

This tool validates declared identities and all six interface edges locally. It
never probes networks, executes workloads, changes canonical files, or upgrades
a declared edge to LIVE_VERIFIED. Runtime proof must be supplied and reviewed
by a separate authorized process.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "registry/federation/four-system-interface-registry.v1.json"
EXPECTED_SYSTEMS = {"VAIXLNS", "VLNS", "VX", "NEXNET"}
EXPECTED_EDGES = {
    frozenset(("VAIXLNS", "VLNS")),
    frozenset(("VAIXLNS", "VX")),
    frozenset(("VAIXLNS", "NEXNET")),
    frozenset(("VLNS", "VX")),
    frozenset(("VLNS", "NEXNET")),
    frozenset(("VX", "NEXNET")),
}
EDGE_STATUSES = {
    "LIVE_VERIFIED", "SPECIFIED_NOT_CONNECTED", "IDENTITY_UNVERIFIED",
    "CONTRACT_PENDING", "TEST_PENDING", "BLOCKED", "CONFLICT",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
            text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def validate_registry(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_id") != "VAIXLNS.FOUR_SYSTEM_INTERFACE_REGISTRY":
        errors.append("schema_id is missing or unexpected")
    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if data.get("canonical_source") != "project.genome::v1.0.0":
        errors.append("canonical_source must remain project.genome::v1.0.0")
    if data.get("master_index") != "Ω.000":
        errors.append("master_index must remain Ω.000")
    invariants = data.get("invariants")
    required_invariants = (
        "system_identity_is_not_repository_identity",
        "no_endpoint_inference_from_repository_presence",
        "no_automatic_canonical_promotion",
        "preserve_original_artifacts_and_lineage",
        "unresolved_identity_mapping_blocks_live_activation",
        "production_writes_require_separate_authorized_gate",
    )
    if not isinstance(invariants, dict):
        errors.append("invariants must be an object")
    else:
        for key in required_invariants:
            if invariants.get(key) is not True:
                errors.append(f"invariants.{key} must be true")

    systems = data.get("systems")
    if not isinstance(systems, list):
        errors.append("systems must be a list")
        systems = []
    system_ids = [item.get("system_id") for item in systems if isinstance(item, dict)]
    if set(system_ids) != EXPECTED_SYSTEMS or len(system_ids) != len(EXPECTED_SYSTEMS):
        errors.append("systems must contain VAIXLNS, VLNS, VX, NEXNET exactly once")
    for item in systems:
        if not isinstance(item, dict):
            errors.append("each system entry must be an object")
            continue
        sid = item.get("system_id", "<missing>")
        if not item.get("role"):
            errors.append(f"{sid}: role is required")
        if item.get("identity_status") not in {"SOURCE_OBSERVED", "IDENTITY_UNVERIFIED", "CONFLICT"}:
            errors.append(f"{sid}: identity_status is invalid")
        runtime = item.get("runtime")
        if not isinstance(runtime, dict):
            errors.append(f"{sid}: runtime must be an object")
        elif runtime.get("status") == "LIVE_VERIFIED":
            errors.append(f"{sid}: registry declaration alone cannot assert LIVE_VERIFIED")
        elif runtime.get("status") not in {"SOURCE_OBSERVED", "SPECIFIED_NOT_CONNECTED", "IDENTITY_UNVERIFIED", "CONTRACT_PENDING", "TEST_PENDING", "BLOCKED", "CONFLICT"}:
            errors.append(f"{sid}: runtime status is invalid")
        if isinstance(runtime, dict) and runtime.get("endpoint") and not runtime.get("endpoint_source"):
            errors.append(f"{sid}: endpoint requires an explicit endpoint_source")

    edges = data.get("interface_edges")
    if not isinstance(edges, list):
        errors.append("interface_edges must be a list")
        edges = []
    pairs: list[frozenset[str]] = []
    edge_ids: list[str] = []
    for edge in edges:
        if not isinstance(edge, dict):
            errors.append("each interface edge must be an object")
            continue
        eid = edge.get("edge_id", "<missing>")
        edge_ids.append(eid)
        source, target = edge.get("source"), edge.get("target")
        if source not in EXPECTED_SYSTEMS or target not in EXPECTED_SYSTEMS or source == target:
            errors.append(f"{eid}: source/target must be distinct known systems")
        else:
            pairs.append(frozenset((source, target)))
        if edge.get("status") not in EDGE_STATUSES:
            errors.append(f"{eid}: status is invalid")
        if edge.get("transport") == "NOT_CONFIGURED" and edge.get("status") == "LIVE_VERIFIED":
            errors.append(f"{eid}: unconfigured transport cannot be LIVE_VERIFIED")
        if not edge.get("required_evidence"):
            errors.append(f"{eid}: required_evidence must not be empty")
    if len(edge_ids) != len(set(edge_ids)):
        errors.append("edge_id values must be unique")
    if set(pairs) != EXPECTED_EDGES or len(pairs) != len(EXPECTED_EDGES):
        errors.append("interface_edges must cover all six unique system pairs exactly once")
    gate = data.get("live_activation_gate")
    if not isinstance(gate, dict) or not gate.get("required_for_each_edge") or not gate.get("forbidden_until_gate_passes"):
        errors.append("live_activation_gate must define requirements and forbidden actions")
    return errors


def build_report(data: dict[str, Any], registry_sha256: str, revision: str | None = None,
                 generated_at: str | None = None) -> dict[str, Any]:
    errors = validate_registry(data)
    systems = data.get("systems", []) if isinstance(data.get("systems"), list) else []
    edges = data.get("interface_edges", []) if isinstance(data.get("interface_edges"), list) else []
    identity_blockers = [
        {"code": "SYSTEM_IDENTITY_UNRESOLVED", "system_id": item.get("system_id")}
        for item in systems if isinstance(item, dict) and item.get("identity_status") != "SOURCE_OBSERVED"
    ]
    edge_results = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source, target = edge.get("source"), edge.get("target")
        unresolved = {
            item.get("system_id") for item in systems
            if isinstance(item, dict) and item.get("identity_status") != "SOURCE_OBSERVED"
        }
        status = edge.get("status", "BLOCKED")
        if source in unresolved or target in unresolved:
            status = "IDENTITY_UNVERIFIED"
        elif edge.get("transport") == "NOT_CONFIGURED" and status == "LIVE_VERIFIED":
            status = "BLOCKED"
        elif status == "LIVE_VERIFIED":
            # Static registry content is never sufficient to attest runtime behavior.
            status = "TEST_PENDING"
        edge_results.append({
            "edge_id": edge.get("edge_id"),
            "source": source,
            "target": target,
            "transport": edge.get("transport"),
            "declared_status": edge.get("status"),
            "audit_status": status,
            "live_verified": False,
            "required_evidence": edge.get("required_evidence", []),
        })
    valid = not errors
    report: dict[str, Any] = {
        "schema": "VAIXLNS.OmegaArenaAuditReceipt.v1",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "source": {
            "repository_revision": revision,
            "registry_path": str(DEFAULT_REGISTRY.relative_to(ROOT)) if DEFAULT_REGISTRY.is_relative_to(ROOT) else DEFAULT_REGISTRY.name,
            "registry_sha256": registry_sha256,
        },
        "mode": "OFFLINE_READ_ONLY",
        "assessment": {
            "status": "PENDING_VERIFICATION" if valid else "BLOCKED",
            "registry_validation": "PASS" if valid else "FAIL",
            "systems_total": len(systems),
            "edges_total": len(edges),
            "live_verified_edges": 0,
            "identity_blockers": len(identity_blockers),
            "canonical_write_performed": False,
            "network_probe_performed": False,
            "workload_executed": False,
            "production_activation_authorized": False,
        },
        "systems": [
            {"system_id": item.get("system_id"), "identity_status": item.get("identity_status"),
             "runtime_status": (item.get("runtime") or {}).get("status")}
            for item in systems if isinstance(item, dict)
        ],
        "edges": edge_results,
        "blockers": identity_blockers + [{"code": "REGISTRY_INVALID", "detail": error} for error in errors],
        "non_claims": [
            "Repository or manifest presence does not prove a live service.",
            "This offline audit does not contact endpoints or execute workloads.",
            "No edge is LIVE_VERIFIED without authorized behavior tests and independently reviewed, revision-bound evidence.",
            "No canonical data was changed and no production activation was attempted.",
        ],
    }
    report["report_sha256"] = digest_bytes(canonical_json(report))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="local registry JSON")
    parser.add_argument("--output", type=Path, help="optional path for the JSON report")
    args = parser.parse_args()
    try:
        raw = args.registry.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": "OMEGA_ARENA_INPUT_BLOCKED", "detail": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print(json.dumps({"error": "OMEGA_ARENA_INPUT_BLOCKED", "detail": "registry root must be an object"}), file=sys.stderr)
        return 2
    report = build_report(data, digest_bytes(raw), revision=git_revision(args.registry.resolve().parent))
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["assessment"]["registry_validation"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
