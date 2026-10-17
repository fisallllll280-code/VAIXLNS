#!/usr/bin/env python3
"""Validate research JSON records without third-party dependencies.

This validator checks structural and epistemic invariants. It does not validate
scientific truth, verify remote sources, or replace JSON Schema validation.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STATUSES = {
    "PROPOSAL", "SPECIFIED", "IMPLEMENTED", "VERIFIED", "PARTIAL",
    "MISSING", "CONFLICT", "RECOVERED", "BLOCKED", "REJECTED",
}
ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._:-]{2,127}$")
REQUIRED = {"record_id", "title", "domain", "status", "question", "sources", "method", "created_at"}


def validate_record(record: object, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{path}: root must be a JSON object"]
    missing = sorted(REQUIRED - record.keys())
    if missing:
        errors.append(f"{path}: missing required keys: {', '.join(missing)}")
        return errors
    record_id = record.get("record_id")
    if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
        errors.append(f"{path}: invalid record_id")
    if record.get("status") not in STATUSES:
        errors.append(f"{path}: unsupported status")
    if not isinstance(record.get("domain"), list) or not record["domain"]:
        errors.append(f"{path}: domain must be a non-empty list")
    if not isinstance(record.get("sources"), list):
        errors.append(f"{path}: sources must be a list")
    else:
        for i, source in enumerate(record["sources"]):
            if not isinstance(source, dict) or not source.get("source_id") or not source.get("locator"):
                errors.append(f"{path}: source[{i}] requires source_id and locator")
    if not isinstance(record.get("method"), dict) or not record["method"].get("description"):
        errors.append(f"{path}: method.description is required")
    if record.get("status") == "VERIFIED":
        refs = record.get("evidence_refs")
        results = record.get("results")
        review = record.get("review")
        if not isinstance(refs, list) or not refs or not all(isinstance(x, str) and x.strip() for x in refs):
            errors.append(f"{path}: VERIFIED requires non-empty evidence_refs")
        if not isinstance(results, list) or not results:
            errors.append(f"{path}: VERIFIED requires recorded results")
        if not isinstance(review, dict) or review.get("decision") != "ACCEPT" or not review.get("reviewer"):
            errors.append(f"{path}: VERIFIED requires independent accepted review metadata")
    return errors


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv] or [Path("research/records")]
    files: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".json":
            files.append(root)
        elif root.is_dir():
            files.extend(sorted(root.rglob("*.json")))
        else:
            print(f"ERROR: path not found: {root}", file=sys.stderr)
            return 2
    errors: list[str] = []
    seen: dict[str, Path] = {}
    for path in files:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: cannot read valid JSON: {exc}")
            continue
        errors.extend(validate_record(record, path))
        if isinstance(record, dict) and isinstance(record.get("record_id"), str):
            key = record["record_id"]
            if key in seen:
                errors.append(f"{path}: duplicate record_id {key!r}; first seen in {seen[key]}")
            else:
                seen[key] = path
    if errors:
        print("\n".join(f"ERROR: {e}" for e in errors))
        return 1
    print(f"PASS: {len(files)} research record(s) structurally valid; no scientific truth claim implied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
