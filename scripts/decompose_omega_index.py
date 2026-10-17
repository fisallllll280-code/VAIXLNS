#!/usr/bin/env python3
"""Deterministically decompose Ω.000 into derived nodes, edges, and risk findings.

Read-only: source index is never rewritten. No network access is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DEFAULT_INDEX = Path("registry/omega/omega-000-master-index.json")


def decompose(index_path: Path, repository_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    raw = index_path.read_bytes()
    source = json.loads(raw)
    records = source.get("records")
    if not isinstance(records, list):
        raise ValueError("Ω.000 must contain a records array")

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    ids: list[str] = []
    evidence_paths: set[str] = set()
    field_counts: Counter[str] = Counter()
    by_type: Counter[str] = Counter()
    by_lifecycle: Counter[str] = Counter()
    by_epistemic: Counter[str] = Counter()
    by_owner: Counter[str] = Counter()
    id_counts: Counter[str] = Counter()

    for position, record in enumerate(records):
        if not isinstance(record, dict):
            findings.append({"severity": "HIGH", "code": "RECORD_NOT_OBJECT", "position": position})
            continue
        identifier = str(record.get("id") or f"UNNAMED:{position}")
        ids.append(identifier)
        id_counts[identifier] += 1
        field_counts.update(record.keys())
        record_type = str(record.get("type") or "MISSING")
        lifecycle = str(record.get("lifecycle_state") or "MISSING")
        epistemic = str(record.get("epistemic_state") or "MISSING")
        owner = str(record.get("canonical_owner") or "MISSING")
        by_type[record_type] += 1
        by_lifecycle[lifecycle] += 1
        by_epistemic[epistemic] += 1
        by_owner[owner] += 1

        required = ("id", "type", "role", "lifecycle_state", "epistemic_state", "canonical_owner", "evidence_refs")
        missing = [field for field in required if not record.get(field)]
        if missing:
            findings.append({"severity": "HIGH", "code": "REQUIRED_FIELDS_MISSING", "id": identifier, "fields": missing})
        if epistemic == "IMPLEMENTED" and lifecycle in ("PROPOSED", "DRAFT"):
            findings.append({"severity": "HIGH", "code": "STATE_MISMATCH", "id": identifier, "lifecycle_state": lifecycle, "epistemic_state": epistemic})
        if epistemic == "PARTIAL":
            findings.append({"severity": "MEDIUM", "code": "PARTIAL_IMPLEMENTATION", "id": identifier})
        if lifecycle == "PROPOSED":
            findings.append({"severity": "LOW", "code": "PROPOSED_NOT_ACTIVE", "id": identifier})

        node = {
            "id": identifier,
            "position": position,
            "type": record_type,
            "role": record.get("role"),
            "lifecycle_state": lifecycle,
            "epistemic_state": epistemic,
            "canonical_owner": owner,
            "evidence_ref_count": len(record.get("evidence_refs", [])) if isinstance(record.get("evidence_refs"), list) else 0,
            "missing_required_fields": missing,
        }
        nodes.append(node)

        parent = record.get("parent")
        if parent:
            edges.append({"from": identifier, "to": str(parent), "kind": "PARENT"})
        for ref in record.get("evidence_refs", []) if isinstance(record.get("evidence_refs"), list) else []:
            if not isinstance(ref, str) or not ref.strip():
                findings.append({"severity": "MEDIUM", "code": "INVALID_EVIDENCE_REF", "id": identifier, "value": repr(ref)})
                continue
            if ref in evidence_paths:
                edges.append({"from": identifier, "to": ref, "kind": "EVIDENCE", "duplicate_path_across_index": True})
            else:
                edges.append({"from": identifier, "to": ref, "kind": "EVIDENCE", "duplicate_path_across_index": False})
            evidence_paths.add(ref)
            if ref.startswith("https://"):
                edges.append({"from": identifier, "to": ref, "kind": "EXTERNAL_EVIDENCE"})
            else:
                candidate = Path(ref)
                if candidate.is_absolute() or ".." in candidate.parts:
                    findings.append({"severity": "HIGH", "code": "UNSAFE_EVIDENCE_PATH", "id": identifier, "path": ref})
                elif not (repository_root / candidate).is_file():
                    findings.append({"severity": "MEDIUM", "code": "EVIDENCE_FILE_NOT_FOUND_IN_CHECKOUT", "id": identifier, "path": ref})

    duplicates = sorted(identifier for identifier, count in id_counts.items() if count > 1)
    for identifier in duplicates:
        findings.append({"severity": "HIGH", "code": "DUPLICATE_ID", "id": identifier, "count": id_counts[identifier]})

    nodes_by_owner = {key: value for key, value in sorted(by_owner.items())}
    findings.sort(key=lambda item: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(item.get("severity", "LOW"), 3), item.get("code", ""), item.get("id", "")))
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    return {
        "schema_version": "vx.omega-decomposition.v1",
        "mode": "READ_ONLY_DERIVED_ANALYSIS",
        "source": {
            "path": str(index_path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "index_id": source.get("index_id"),
            "declared_status": source.get("status"),
            "golden_source": source.get("golden_source"),
            "authority_anchor": source.get("authority_anchor"),
            "bytes": len(raw),
        },
        "summary": {
            "record_count": len(nodes),
            "unique_id_count": len(set(ids)),
            "duplicate_id_count": len(duplicates),
            "edge_count": len(edges),
            "unique_evidence_path_count": len(evidence_paths),
            "evidence_reference_count": sum(1 for edge in edges if edge["kind"] == "EVIDENCE"),
            "record_type_counts": dict(sorted(by_type.items())),
            "lifecycle_counts": dict(sorted(by_lifecycle.items())),
            "epistemic_counts": dict(sorted(by_epistemic.items())),
            "owner_counts": nodes_by_owner,
            "field_presence_counts": dict(sorted(field_counts.items())),
            "finding_counts_by_severity": dict(sorted(Counter(x["severity"] for x in findings).items())),
            "elapsed_ms": elapsed_ms,
        },
        "nodes": nodes,
        "edges": edges,
        "findings": findings,
        "scope_warning": (
            "This decomposes only the records present in this Ω.000 file. "
            "It does not prove restoration of the historical 0001–2750 corpus or any external archive."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default=str(DEFAULT_INDEX))
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default="-")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    index_path = (root / args.index).resolve()
    if not index_path.is_file():
        parser.error(f"index file not found: {index_path}")
    report = decompose(index_path, root)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out == "-":
        print(output, end="")
    else:
        destination = Path(args.out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(output, encoding="utf-8")
    return 1 if report["summary"]["duplicate_id_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
