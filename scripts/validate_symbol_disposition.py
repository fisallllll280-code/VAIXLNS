#!/usr/bin/env python3
"""Fail-closed, read-only validator for VAIXLNS disposition and symbol indexes.

This script never moves, rewrites, renames, deletes, or promotes a source.
Run from any directory: python scripts/validate_symbol_disposition.py --root .
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

DISPOSITION = "registry/indexes/disposition-quarantine.v1.json"
SYMBOLS = "registry/indexes/symbol-semantic-index.v1.json"
PROTECTED = (
    "project.genome",
    "registry/omega/omega-000-master-index.json",
    "archive/",
    "docs/recovery/",
    "docs/indexes/",
    "registry/",
    "schemas/",
)
ALLOWED_STATES = {"REVIEW", "QUARANTINE_CANDIDATE", "RETIRED_APPROVED"}
TARGET_TYPES = {"registry_identity", "external_repository", "repository_file", "index", "model", "tool", "defect", "workflow", "design", "innovation", "agent", "service", "dependency", "other"}
SHA_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def git_blob_sha(data: bytes) -> str:
    """Git blob SHA-1 (not a SHA-256 digest)."""
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def is_protected(locator: str) -> bool:
    return any(locator == item or (item.endswith("/") and locator.startswith(item))
               for item in PROTECTED)


def load_json(root: Path, relative: str) -> dict:
    path = root / relative
    if not path.is_file():
        raise ValueError("REQUIRED_INDEX_MISSING:" + relative)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("INVALID_INDEX_OBJECT:" + relative)
    return payload


def validate(root: Path) -> dict:
    """Return a deterministic audit; do not mutate checkout or canonical indexes."""
    root = Path(root).resolve()
    disposition = load_json(root, DISPOSITION)
    symbols = load_json(root, SYMBOLS)
    errors = []
    records = disposition.get("records", [])
    entries = symbols.get("entries", [])
    if not isinstance(records, list) or not isinstance(entries, list):
        raise ValueError("RECORD_LIST_REQUIRED")
    if disposition.get("authority") != "VAIXLNS" or symbols.get("authority") != "VAIXLNS":
        errors.append("AUTHORITY_MISMATCH")
    if disposition.get("index_id") != "VAIXLNS.DISPOSITION_QUARANTINE":
        errors.append("DISPOSITION_ID_MISMATCH")
    if symbols.get("index_id") != "VAIXLNS.SYMBOL_SEMANTIC":
        errors.append("SYMBOL_ID_MISMATCH")

    seen_ids = set()
    excluded = []
    for record in records:
        if not isinstance(record, dict):
            errors.append("DISPOSITION_RECORD_NOT_OBJECT")
            continue
        rid = record.get("id", "")
        if not rid or rid in seen_ids:
            errors.append("INVALID_OR_DUPLICATE_DISPOSITION_ID:" + str(rid))
        seen_ids.add(rid)
        state = record.get("state")
        if state not in ALLOWED_STATES:
            errors.append("INVALID_DISPOSITION_STATE:" + str(rid))
        if record.get("source_deleted") is not False:
            errors.append("NO_SOURCE_DELETION_ALLOWED:" + str(rid))
        target = record.get("target_locator", "")
        if not isinstance(target, str) or not target:
            errors.append("TARGET_REQUIRED:" + str(rid))
            target = ""
        if record.get("target_type") not in TARGET_TYPES:
            errors.append("UNKNOWN_TARGET_TYPE:" + str(rid))
        if not isinstance(record.get("evidence"), list) or not record["evidence"]:
            errors.append("EVIDENCE_REQUIRED:" + str(rid))
            evidence_rows = []
        else:
            evidence_rows = record["evidence"]
        for evidence in evidence_rows:
            if not isinstance(evidence, dict):
                errors.append("EVIDENCE_RECORD_NOT_OBJECT:" + str(rid))
                continue
            relative = evidence.get("path", "")
            sha = evidence.get("blob_sha", "")
            if (not isinstance(relative, str) or relative.startswith("/") or
                ".." in Path(relative).parts or not SHA_RE.fullmatch(str(sha))):
                errors.append("INVALID_EVIDENCE_REFERENCE:" + str(rid))
                continue
            file_path = (root / relative).resolve()
            if not file_path.is_relative_to(root) or not file_path.is_file():
                errors.append("EVIDENCE_NOT_OBSERVED:" + str(rid) + ":" + relative)
                continue
            if git_blob_sha(file_path.read_bytes()) != sha:
                errors.append("EVIDENCE_BLOB_MISMATCH:" + str(rid) + ":" + relative)

        if record.get("active_projection_excluded") is True:
            approval = record.get("reviewed_decision")
            snapshot = record.get("rollback_snapshot")
            complete = (
                state == "RETIRED_APPROVED"
                and record.get("dependency_audit") == "PASS"
                and record.get("unique_knowledge_recovered") is True
                and isinstance(approval, dict)
                and all(approval.get(k) for k in ("reviewer", "approval_ref", "date"))
                and isinstance(snapshot, dict)
                and bool(snapshot.get("source_ref"))
                and isinstance(snapshot.get("sha256"), str)
                and bool(SHA256_RE.fullmatch(snapshot["sha256"]))
                and bool(record.get("evidence"))
            )
            if not complete:
                errors.append("EXCLUSION_WITHOUT_PROOF_GATES:" + str(rid))
            elif record.get("target_type") == "repository_file" and is_protected(target):
                errors.append("PROTECTED_SOURCE_CANNOT_BE_EXCLUDED:" + str(rid))
            else:
                excluded.append(rid)
        elif record.get("active_projection_excluded") is not False:
            errors.append("EXCLUSION_BOOLEAN_REQUIRED:" + str(rid))

    symbol_ids = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("SYMBOL_RECORD_NOT_OBJECT")
            continue
        sid = entry.get("id", "")
        if not sid or sid in symbol_ids:
            errors.append("INVALID_OR_DUPLICATE_SYMBOL_ID:" + str(sid))
        symbol_ids.add(sid)
        if not all(isinstance(entry.get(k), str) and entry[k].strip()
                   for k in ("unicode", "role", "ar", "en")):
            errors.append("SYMBOL_FIELDS_MISSING:" + str(sid))
        if entry.get("state") not in {"PROPOSED", "SPECIFIED"}:
            errors.append("SYMBOL_IS_NOT_RUNTIME_PROOF:" + str(sid))
        if entry.get("action_authority") not in {"NONE", "VX_ASSURANCE_GATE_ONLY"}:
            errors.append("UNSAFE_SYMBOL_AUTHORITY:" + str(sid))
        if entry.get("role") == "evidence.verified":
            if entry.get("requires_evidence") is not True or entry.get("action_authority") != "VX_ASSURANCE_GATE_ONLY":
                errors.append("UNSAFE_VERIFIED_SYMBOL:" + str(sid))

    return {
        "audit_status": "PASS" if not errors else "BLOCKED",
        "index_status": "NOT_RUNTIME_VERIFIED",
        "disposition_candidates": len(records),
        "symbols_proposed": len(entries),
        "active_projection_excluded": excluded,
        "source_deletions_performed": 0,
        "errors": sorted(errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path, help="Optional JSON report path; no source writes")
    args = parser.parse_args()
    try:
        result = validate(args.root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"audit_status": "BLOCKED", "errors": [str(exc)],
                  "source_deletions_performed": 0}
    content = json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    print(content, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(content, encoding="utf-8")
    return 0 if result["audit_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
