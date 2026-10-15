#!/usr/bin/env python3
"""Read-only R-Ω Forge preflight scaffold for evidence-gated engineering.

No network calls, model calls, production writes, or canonical mutations occur.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_SYSTEMS = {"VAIXLNS", "VLNS", "VX", "NEXNET"}
EXPECTED_EDGES = {
    frozenset(("VAIXLNS", "VLNS")),
    frozenset(("VAIXLNS", "VX")),
    frozenset(("VAIXLNS", "NEXNET")),
    frozenset(("VLNS", "VX")),
    frozenset(("VLNS", "NEXNET")),
    frozenset(("VX", "NEXNET")),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_registry(doc: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["REGISTRY_ROOT_NOT_OBJECT"]
    if doc.get("canonical_source") != "project.genome::v1.0.0" or doc.get("master_index") != "Ω.000":
        errors.append("CANONICAL_AUTHORITY_REFERENCE_MISMATCH")
    systems = doc.get("systems")
    if not isinstance(systems, list):
        return errors + ["SYSTEMS_NOT_LIST"]
    ids = [s.get("system_id") for s in systems if isinstance(s, dict)]
    if set(ids) != EXPECTED_SYSTEMS or len(ids) != len(EXPECTED_SYSTEMS):
        errors.append("SYSTEM_SET_MISMATCH_OR_DUPLICATE")
    edges = doc.get("interface_edges")
    if not isinstance(edges, list):
        return errors + ["EDGES_NOT_LIST"]
    observed: set[frozenset[str]] = set()
    edge_ids: set[str] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            errors.append("EDGE_NOT_OBJECT")
            continue
        edge_id = edge.get("edge_id")
        if not isinstance(edge_id, str) or not edge_id:
            errors.append("EDGE_ID_MISSING")
        elif edge_id in edge_ids:
            errors.append("DUPLICATE_EDGE_ID:" + edge_id)
        edge_ids.add(edge_id)
        source, target = edge.get("source"), edge.get("target")
        if source not in EXPECTED_SYSTEMS or target not in EXPECTED_SYSTEMS or source == target:
            errors.append("INVALID_EDGE_ENDPOINTS:" + str(edge_id))
            continue
        observed.add(frozenset((source, target)))
        if edge.get("transport") == "NOT_CONFIGURED" and edge.get("status") == "LIVE_VERIFIED":
            errors.append("FALSE_LIVE_CLAIM:" + str(edge_id))
        if not isinstance(edge.get("required_evidence"), list) or not edge["required_evidence"]:
            errors.append("EVIDENCE_REQUIREMENTS_MISSING:" + str(edge_id))
    if observed != EXPECTED_EDGES or len(edges) != 6:
        errors.append("SIX_EDGE_TOPOLOGY_MISMATCH")
    return errors


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_report(registry_path: Path, index_dir: Path | None) -> dict[str, Any]:
    raw = registry_path.read_bytes()
    registry = json.loads(raw.decode("utf-8"))
    errors = validate_registry(registry)
    edge_rows = []
    for edge in registry.get("interface_edges", []) if isinstance(registry, dict) else []:
        if isinstance(edge, dict):
            edge_rows.append({
                "edge_id": edge.get("edge_id"),
                "source": edge.get("source"),
                "target": edge.get("target"),
                "status": edge.get("status", "PENDING_VERIFICATION"),
                "transport": edge.get("transport", "UNKNOWN"),
                "evidence_requirements": edge.get("required_evidence", []),
                "live_claim_allowed": edge.get("status") == "LIVE_VERIFIED" and edge.get("transport") != "NOT_CONFIGURED",
            })
    coverage: dict[str, Any] = {"status": "NOT_PROVIDED", "artifact_hashes": {}, "summary": None}
    if index_dir is not None:
        coverage["status"] = "MISSING_OR_INCOMPLETE"
        names = (
            "zero-loss-index.v1.json",
            "zero-loss-source-index.v1.json",
            "zero-loss-atomic-records.v1.jsonl",
            "zero-loss-coverage.v1.json",
            "zero-loss-cross-reference.v1.json",
            "index-recovery-receipt.v1.json",
        )
        missing = [name for name in names if not (index_dir / name).is_file()]
        coverage["missing_artifacts"] = missing
        if not missing:
            coverage["artifact_hashes"] = {name: sha256_file(index_dir / name) for name in names}
            receipt = load_json(index_dir / "index-recovery-receipt.v1.json")
            coverage["receipt_status"] = receipt.get("status")
            summary = load_json(index_dir / "zero-loss-coverage.v1.json")
            coverage["summary"] = {
                "source_count": summary.get("source_count"),
                "atomic_records_created": summary.get("atomic_records_created"),
                "opaque_source_count": len(summary.get("opaque_sources", [])),
                "legacy_id_coverage": summary.get("legacy_id_coverage", {}),
            }
            coverage["status"] = "ARTIFACTS_PRESENT_REQUIRES_RECEIPT_REVIEW"
    return {
        "schema": "VAIXLNS.ROmegaForgePreflight.v1",
        "engine": "R-Ω Forge",
        "implementation_status": "PARTIAL",
        "execution_mode": "READ_ONLY_OFFLINE_PREFLIGHT",
        "authority": {"canonical_source": "project.genome::v1.0.0", "master_index": "Ω.000"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "registry": {"path": str(registry_path), "sha256": hashlib.sha256(raw).hexdigest()},
        "systems_expected": sorted(EXPECTED_SYSTEMS),
        "system_count_observed": len(registry.get("systems", [])) if isinstance(registry, dict) and isinstance(registry.get("systems"), list) else 0,
        "interface_edges": edge_rows,
        "edge_status_counts": {
            status: sum(1 for row in edge_rows if row["status"] == status)
            for status in sorted({row["status"] for row in edge_rows})
        },
        "index_recovery": coverage,
        "validation_errors": errors,
        "overall_status": "BLOCKED" if errors else "PENDING_VERIFICATION",
        "non_claims": [
            "No model provider was called.",
            "No external research was performed by this local scaffold.",
            "No network endpoint was probed.",
            "No live integration is asserted.",
            "No canonical source was modified.",
            "Artifact presence is not proof of historical completeness.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("registry/federation/four-system-interface-registry.v1.json"))
    parser.add_argument("--index-dir", type=Path, default=None, help="optional existing recovery output directory")
    parser.add_argument("--output", type=Path, default=None, help="write JSON report to this path; stdout otherwise")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.registry, args.index_dir)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema": "VAIXLNS.ROmegaForgePreflight.v1", "overall_status": "BLOCKED", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 1 if report["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
