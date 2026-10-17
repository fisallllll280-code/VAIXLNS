#!/usr/bin/env python3
"""Validate the four-system interface registry without probing or activating endpoints."""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "registry/federation/four-system-interface-registry.v1.json"
ALLOWED_STATUS = {"SOURCE_OBSERVED", "SPECIFIED_NOT_CONNECTED", "IDENTITY_UNVERIFIED", "CONTRACT_PENDING", "TEST_PENDING", "LIVE_VERIFIED", "BLOCKED", "CONFLICT"}
EXPECTED_SYSTEMS = {"VAIXLNS", "VLNS", "VX", "NEXNET"}

def validate(document: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["ROOT_MUST_BE_OBJECT"]
    if document.get("schema_id") != "VAIXLNS.FOUR_SYSTEM_INTERFACE_REGISTRY":
        errors.append("SCHEMA_ID_MISMATCH")
    if document.get("canonical_source") != "project.genome::v1.0.0" or document.get("master_index") != "Ω.000":
        errors.append("CANONICAL_REFERENCE_MISMATCH")
    systems = document.get("systems")
    if not isinstance(systems, list):
        return errors + ["SYSTEMS_MUST_BE_LIST"]
    ids = [item.get("system_id") for item in systems if isinstance(item, dict)]
    if set(ids) != EXPECTED_SYSTEMS or len(ids) != len(EXPECTED_SYSTEMS):
        errors.append("SYSTEM_ID_SET_MISMATCH_OR_DUPLICATE")
    for system in systems:
        if not isinstance(system, dict):
            errors.append("SYSTEM_ENTRY_MUST_BE_OBJECT")
            continue
        sid = system.get("system_id", "<unknown>")
        if system.get("identity_status") not in ALLOWED_STATUS:
            errors.append(f"{sid}:INVALID_IDENTITY_STATUS")
        runtime = system.get("runtime")
        if not isinstance(runtime, dict):
            errors.append(f"{sid}:RUNTIME_DECLARATION_MISSING")
            continue
        if runtime.get("status") == "LIVE_VERIFIED":
            proof = runtime.get("proof_required")
            if not isinstance(proof, list) or not proof:
                errors.append(f"{sid}:LIVE_STATUS_WITHOUT_PROOF_REQUIREMENTS")
        if runtime.get("endpoint") is not None and not isinstance(runtime.get("endpoint"), str):
            errors.append(f"{sid}:ENDPOINT_MUST_BE_STRING_OR_NULL")
        for surface in system.get("repository_surfaces", []):
            if not isinstance(surface, dict) or not surface.get("repository"):
                errors.append(f"{sid}:INVALID_REPOSITORY_SURFACE")
            elif surface.get("status") not in ALLOWED_STATUS:
                errors.append(f"{sid}:INVALID_REPOSITORY_STATUS")
    edges = document.get("interface_edges")
    if not isinstance(edges, list):
        return errors + ["INTERFACE_EDGES_MUST_BE_LIST"]
    edge_ids = [edge.get("edge_id") for edge in edges if isinstance(edge, dict)]
    if len(edge_ids) != len(set(edge_ids)):
        errors.append("DUPLICATE_EDGE_ID")
    for edge in edges:
        if not isinstance(edge, dict):
            errors.append("EDGE_ENTRY_MUST_BE_OBJECT")
            continue
        if edge.get("source") not in EXPECTED_SYSTEMS or edge.get("target") not in EXPECTED_SYSTEMS:
            errors.append(f"{edge.get('edge_id', '<unknown>')}:UNKNOWN_ENDPOINT_SYSTEM")
        if edge.get("source") == edge.get("target"):
            errors.append(f"{edge.get('edge_id', '<unknown>')}:SELF_EDGE_FORBIDDEN")
        if edge.get("status") not in ALLOWED_STATUS:
            errors.append(f"{edge.get('edge_id', '<unknown>')}:INVALID_EDGE_STATUS")
        if edge.get("transport") == "NOT_CONFIGURED" and edge.get("status") == "LIVE_VERIFIED":
            errors.append(f"{edge.get('edge_id', '<unknown>')}:LIVE_WITHOUT_CONFIGURED_TRANSPORT")
        if not isinstance(edge.get("required_evidence"), list) or not edge.get("required_evidence"):
            errors.append(f"{edge.get('edge_id', '<unknown>')}:EVIDENCE_REQUIREMENTS_MISSING")
    invariants = document.get("invariants", {})
    for key in ("system_identity_is_not_repository_identity", "no_endpoint_inference_from_repository_presence", "no_automatic_canonical_promotion", "preserve_original_artifacts_and_lineage", "unresolved_identity_mapping_blocks_live_activation", "production_writes_require_separate_authorized_gate"):
        if invariants.get(key) is not True:
            errors.append(f"INVARIANT_NOT_ENFORCED:{key}")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    try:
        raw = args.registry.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"state": "FAIL", "error": f"REGISTRY_READ_FAILED:{exc}"}, ensure_ascii=False), file=sys.stderr)
        return 2
    errors = validate(document)
    report = {
        "schema": "VAIXLNS.FourSystemInterfaceAudit.v1",
        "state": "PASS" if not errors else "FAIL",
        "registry_path": str(args.registry),
        "registry_sha256": hashlib.sha256(raw).hexdigest(),
        "system_count": len(document.get("systems", [])) if isinstance(document, dict) and isinstance(document.get("systems"), list) else 0,
        "interface_edge_count": len(document.get("interface_edges", [])) if isinstance(document, dict) and isinstance(document.get("interface_edges"), list) else 0,
        "live_verified_edges": [edge.get("edge_id") for edge in document.get("interface_edges", []) if edge.get("status") == "LIVE_VERIFIED"] if isinstance(document, dict) else [],
        "configured_transports": [edge.get("edge_id") for edge in document.get("interface_edges", []) if edge.get("transport") != "NOT_CONFIGURED"] if isinstance(document, dict) else [],
        "errors": errors,
        "scope": "STATIC_CONTRACT_AUDIT_ONLY_NO_NETWORK_PROBES_NO_RUNTIME_CLAIMS"
    }
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
