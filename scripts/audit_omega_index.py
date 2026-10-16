#!/usr/bin/env python3
"""Read-only structural audit for the canonical Omega master index.

This tool never writes to project.genome or Ω.000. It emits a separate report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(index_path: Path, repository_root: Path) -> dict[str, Any]:
    raw = index_path.read_bytes()
    document = json.loads(raw)
    records = document.get("records")
    if not isinstance(records, list):
        raise ValueError("index.records must be a JSON array")

    ids = [record.get("id") for record in records if isinstance(record, dict) and record.get("id")]
    id_counts = Counter(ids)
    duplicate_ids = sorted(identifier for identifier, count in id_counts.items() if count > 1)
    all_ids = set(ids)
    missing_required = []
    unknown_parents = []
    evidence_refs: list[tuple[str, str]] = []
    type_counts: Counter[str] = Counter()
    lifecycle_counts: Counter[str] = Counter()
    epistemic_counts: Counter[str] = Counter()

    for position, record in enumerate(records):
        if not isinstance(record, dict):
            missing_required.append({"record_position": position, "field": "record_object"})
            continue
        identifier = record.get("id")
        for field in ("id", "type", "lifecycle_state", "epistemic_state"):
            if not record.get(field):
                missing_required.append({"record_position": position, "id": identifier, "field": field})
        type_counts[str(record.get("type", "MISSING"))] += 1
        lifecycle_counts[str(record.get("lifecycle_state", "MISSING"))] += 1
        epistemic_counts[str(record.get("epistemic_state", "MISSING"))] += 1
        parent = record.get("parent")
        if parent and parent not in all_ids:
            unknown_parents.append({"id": identifier, "parent": parent})
        refs = record.get("evidence_refs", [])
        if not isinstance(refs, list):
            missing_required.append({"record_position": position, "id": identifier, "field": "evidence_refs_array"})
            continue
        for ref in refs:
            if isinstance(ref, str) and ref.strip():
                evidence_refs.append((str(identifier or f"record:{position}"), ref))
            else:
                missing_required.append({"record_position": position, "id": identifier, "field": "evidence_ref_string"})

    missing_evidence = []
    unsafe_refs = []
    seen_refs: set[str] = set()
    duplicate_evidence_refs = []
    for source_id, ref in evidence_refs:
        if ref in seen_refs:
            duplicate_evidence_refs.append(ref)
        seen_refs.add(ref)
        candidate = Path(ref)
        if candidate.is_absolute() or ".." in candidate.parts:
            unsafe_refs.append({"id": source_id, "ref": ref})
            continue
        if not (repository_root / candidate).is_file():
            missing_evidence.append({"id": source_id, "ref": ref})

    return {
        "audit_schema": "vx.omega-index-audit.v1",
        "audit_mode": "READ_ONLY_DERIVED_REPORT",
        "index_id": document.get("index_id"),
        "declared_status": document.get("status"),
        "index_path": str(index_path),
        "index_sha256": hashlib.sha256(raw).hexdigest(),
        "record_count": len(records),
        "unique_id_count": len(all_ids),
        "duplicate_ids": duplicate_ids,
        "missing_required_fields": missing_required,
        "unknown_parent_refs": unknown_parents,
        "evidence_ref_count": len(evidence_refs),
        "unique_evidence_ref_count": len(seen_refs),
        "duplicate_evidence_refs": sorted(set(duplicate_evidence_refs)),
        "missing_evidence_files": missing_evidence,
        "unsafe_evidence_refs": unsafe_refs,
        "record_type_counts": dict(sorted(type_counts.items())),
        "lifecycle_state_counts": dict(sorted(lifecycle_counts.items())),
        "epistemic_state_counts": dict(sorted(epistemic_counts.items())),
        "recovery_note": (
            "This audit covers records currently present in this index only. "
            "It does not prove atomic recovery of any external archive or missing historical records."
        ),
        "integrity_gate": "FAIL" if duplicate_ids or missing_required or unsafe_refs else "PASS",
        "evidence_completeness": "INCOMPLETE" if missing_evidence or unknown_parents else "NO_MISSING_REFERENCES_DETECTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default="registry/omega/omega-000-master-index.json")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default="-", help="Report path, or '-' for stdout")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    index_path = (root / args.index).resolve()
    if not index_path.is_file():
        parser.error(f"index file not found: {index_path}")
    report = audit(index_path, root)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out == "-":
        print(encoded, end="")
    else:
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded, encoding="utf-8")
    return 1 if report["integrity_gate"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
