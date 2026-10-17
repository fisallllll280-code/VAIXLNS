#!/usr/bin/env python3
"""Produce a deterministic, read-only federation readiness report.

This command validates local declarations only. It never calls remote systems,
executes tasks, grants authority, changes canonical state, or probes endpoints.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_four_system_federation import validate as validate_system_manifest
from scripts.validate_federation_contract_edges import validate as validate_edge_contract


SYSTEMS_MANIFEST = ROOT / "registry/federation/four_system_unification.v1.json"
EDGES_MANIFEST = ROOT / "registry/federation/federation_contract_edges.v1.json"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def build_report(system_data: dict[str, Any], edge_data: dict[str, Any]) -> dict[str, Any]:
    system_errors = validate_system_manifest(system_data)
    edge_errors = validate_edge_contract(edge_data, system_data)
    systems = system_data.get("systems", []) if isinstance(system_data.get("systems"), list) else []
    edges = edge_data.get("edges", []) if isinstance(edge_data.get("edges"), list) else []

    identity_blockers = []
    for system in systems:
        if isinstance(system, dict) and system.get("identity_state") == "UNVERIFIED":
            identity_blockers.append({
                "code": "SYSTEM_IDENTITY_UNRESOLVED",
                "system_id": system.get("system_id"),
                "mapping": system.get("unresolved_mapping"),
            })

    edge_blockers = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        if edge.get("status") == "BLOCKED_IDENTITY":
            edge_blockers.append({
                "code": "EDGE_BLOCKED_BY_IDENTITY",
                "edge_id": edge.get("edge_id"),
                "from_system": edge.get("from_system"),
                "to_system": edge.get("to_system"),
            })
        elif edge.get("enabled") is not True:
            edge_blockers.append({
                "code": "EDGE_NOT_CONNECTED",
                "edge_id": edge.get("edge_id"),
                "status": edge.get("status"),
            })

    active_edges = [
        edge for edge in edges
        if isinstance(edge, dict)
        and edge.get("status") == "ACTIVE_VERIFIED"
        and edge.get("enabled") is True
    ]
    invalid = bool(system_errors or edge_errors)
    admission_status = (
        "INVALID" if invalid
        else "BLOCKED" if identity_blockers or any(
            isinstance(e, dict) and e.get("status") == "BLOCKED_IDENTITY" for e in edges
        )
        else "HOLD" if len(active_edges) != len(edges)
        else "READY_FOR_RUNTIME_OBSERVATION"
    )

    report: dict[str, Any] = {
        "schema_version": "vaixlns-federation-preflight-v1",
        "assessment": {
            "manifest_validation": "FAIL" if invalid else "PASS",
            "admission_status": admission_status,
            "connectivity_verified": False,
            "runtime_observed": False,
            "canonical_write_performed": False,
            "authority_granted": False,
            "execution_performed": False,
        },
        "source_digests": {
            "four_system_manifest_sha256": sha256_json(system_data),
            "contract_edges_manifest_sha256": sha256_json(edge_data),
        },
        "summary": {
            "systems_total": len(systems),
            "edges_total": len(edges),
            "active_verified_edges": len(active_edges),
            "identity_unverified_systems": len(identity_blockers),
            "identity_blocked_edges": sum(
                1 for e in edges if isinstance(e, dict) and e.get("status") == "BLOCKED_IDENTITY"
            ),
            "disabled_or_unconnected_edges": sum(
                1 for e in edges if isinstance(e, dict) and e.get("enabled") is not True
            ),
        },
        "systems": [
            {
                "system_id": item.get("system_id"),
                "identity_state": item.get("identity_state"),
                "implementation_state": item.get("implementation_state"),
                "repository_surfaces": item.get("repository_surfaces", []),
            }
            for item in systems if isinstance(item, dict)
        ],
        "edges": [
            {
                "edge_id": item.get("edge_id"),
                "from_system": item.get("from_system"),
                "to_system": item.get("to_system"),
                "kind": item.get("kind"),
                "status": item.get("status"),
                "enabled": item.get("enabled"),
                "adapter": item.get("adapter"),
                "contract_ref": item.get("contract_ref"),
            }
            for item in edges if isinstance(item, dict)
        ],
        "blockers": [
            *identity_blockers,
            *edge_blockers,
            *[{"code": "SYSTEM_MANIFEST_INVALID", "detail": e} for e in system_errors],
            *[{"code": "EDGE_CONTRACT_INVALID", "detail": e} for e in edge_errors],
        ],
        "limits": [
            "This preflight does not contact remote repositories or service endpoints.",
            "A structurally valid manifest does not prove an adapter is deployed or running.",
            "Identity, network connectivity, runtime health, and production readiness require separate evidence.",
        ],
    }
    report["report_sha256"] = sha256_json(report)
    return report


def main() -> int:
    try:
        system_data = json.loads(SYSTEMS_MANIFEST.read_text(encoding="utf-8"))
        edge_data = json.loads(EDGES_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": "PREFLIGHT_INPUT_UNAVAILABLE", "detail": str(exc)}))
        return 2
    report = build_report(system_data, edge_data)
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if report["assessment"]["manifest_validation"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
