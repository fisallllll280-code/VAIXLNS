"""Evidence-first append-only engineering memory ledger.

Uses only the Python standard library. The JSONL file is a durable,
tamper-evident local ledger, not a protected or distributed storage system.
Protect it with permissions and backups.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

GENESIS_HASH = "0" * 64
EPISTEMIC_STATES = {"PROPOSAL", "SPECIFIED", "IMPLEMENTED", "VERIFIED", "PARTIAL", "MISSING", "CONFLICT", "RECOVERED"}
LIFECYCLE_STATES = {"DRAFT", "ACTIVE", "EVOLVING", "QUARANTINED", "ARCHIVED"}
MEMORY_TYPES = {"DISCOVERY", "DESIGN", "DECISION", "IMPLEMENTATION", "TEST", "FAILURE", "BENCHMARK", "CONSTRAINT", "PATTERN", "LESSON"}
VERIFICATION_RESULTS = {"NOT_RUN", "PASS", "FAIL", "PARTIAL"}


class MemoryValidationError(ValueError):
    """Raised when a memory record violates the evidence/promotion contract."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_text(mapping: dict[str, Any], key: str) -> None:
    if not isinstance(mapping.get(key), str) or not mapping[key].strip():
        raise MemoryValidationError(f"{key} must be a non-empty string")


def validate_record(record: dict[str, Any]) -> None:
    """Validate required fields and fail-closed promotion rules."""
    if not isinstance(record, dict):
        raise MemoryValidationError("record must be an object")
    for key in ("record_id", "schema_version", "subject", "summary", "recorded_at"):
        _require_text(record, key)
    if record.get("schema_version") != "1.0.0":
        raise MemoryValidationError("unsupported schema_version")
    if record.get("memory_type") not in MEMORY_TYPES:
        raise MemoryValidationError("invalid memory_type")
    if record.get("epistemic_state") not in EPISTEMIC_STATES:
        raise MemoryValidationError("invalid epistemic_state")
    if record.get("lifecycle_state") not in LIFECYCLE_STATES:
        raise MemoryValidationError("invalid lifecycle_state")

    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        raise MemoryValidationError("provenance must be an object")
    for key in ("repository", "revision", "path", "content_sha256"):
        _require_text(provenance, key)
    digest = provenance["content_sha256"]
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise MemoryValidationError("provenance.content_sha256 must be a lowercase SHA-256 digest")

    evidence = record.get("evidence")
    if not isinstance(evidence, list):
        raise MemoryValidationError("evidence must be an array")
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise MemoryValidationError(f"evidence[{index}] must be an object")
        for key in ("kind", "ref", "digest"):
            _require_text(item, key)
        digest = item["digest"]
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise MemoryValidationError(f"evidence[{index}].digest must be a lowercase SHA-256 digest")

    verification = record.get("verification")
    if not isinstance(verification, dict):
        raise MemoryValidationError("verification must be an object")
    _require_text(verification, "method")
    if verification.get("result") not in VERIFICATION_RESULTS:
        raise MemoryValidationError("invalid verification.result")

    lineage = record.get("lineage", {})
    if not isinstance(lineage, dict):
        raise MemoryValidationError("lineage must be an object")
    for key in ("derived_from", "supersedes", "related"):
        value = lineage.get(key, [])
        if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
            raise MemoryValidationError(f"lineage.{key} must be an array of non-empty strings")

    if record["epistemic_state"] == "VERIFIED":
        if verification["result"] != "PASS":
            raise MemoryValidationError("VERIFIED requires verification.result=PASS")
        _require_text(verification, "reproduction_command")
        if not evidence:
            raise MemoryValidationError("VERIFIED requires at least one evidence item")
    if record.get("promotion_authority") == "self":
        raise MemoryValidationError("self-promotion is forbidden")


def _unsigned_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "record_hash"}


def verify_ledger(path: str | Path) -> dict[str, Any]:
    """Verify JSONL syntax, record hashes, and the previous-hash chain."""
    ledger_path = Path(path)
    if not ledger_path.exists():
        return {"valid": True, "records": 0, "head_hash": GENESIS_HASH}
    previous_hash = GENESIS_HASH
    count = 0
    seen_ids: set[str] = set()
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise MemoryValidationError(f"invalid JSON on line {line_number}") from exc
            validate_record(record)
            if record.get("previous_record_hash") != previous_hash:
                raise MemoryValidationError(f"broken previous-record link on line {line_number}")
            if record.get("record_id") in seen_ids:
                raise MemoryValidationError(f"duplicate record_id on line {line_number}")
            expected_hash = sha256_json(_unsigned_record(record))
            if record.get("record_hash") != expected_hash:
                raise MemoryValidationError(f"record hash mismatch on line {line_number}")
            previous_hash = expected_hash
            seen_ids.add(record["record_id"])
            count += 1
    return {"valid": True, "records": count, "head_hash": previous_hash}


def append_record(path: str | Path, record: dict[str, Any]) -> dict[str, Any]:
    """Append a validated record and fsync it; historical entries are never edited."""
    validate_record(record)
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    state = verify_ledger(ledger_path)
    existing_ids: set[str] = set()
    if ledger_path.exists():
        with ledger_path.open("r", encoding="utf-8") as handle:
            existing_ids = {json.loads(line)["record_id"] for line in handle if line.strip()}
    if record["record_id"] in existing_ids:
        raise MemoryValidationError("record_id already exists; append a new versioned record")

    entry = dict(record)
    entry["previous_record_hash"] = state["head_hash"]
    entry["record_hash"] = sha256_json(entry)
    payload = canonical_json(entry) + "\n"
    descriptor = os.open(ledger_path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    verify_ledger(ledger_path)
    return entry


def search_records(path: str | Path, query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Deterministic lexical baseline; semantic retrieval remains an adapter."""
    if limit < 1:
        raise ValueError("limit must be >= 1")
    needle = query.casefold().strip()
    if not needle:
        raise ValueError("query must be non-empty")
    ledger_path = Path(path)
    if not ledger_path.exists():
        return []
    matches = []
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            searchable = " ".join(str(record.get(k, "")) for k in ("subject", "summary", "memory_type")).casefold()
            if needle in searchable:
                matches.append(record)
    return list(reversed(matches[-limit:]))
