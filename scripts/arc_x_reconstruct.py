#!/usr/bin/env python3
"""Deterministic, evidence-preserving first slice of ARC-X reconstruction.

This tool inventories repository bytes; it does not execute discovered code,
grant authority, or promote claims to VERIFIED. Output artifacts contain paths,
sizes and digests rather than source contents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
SCHEMA_VERSION = "arc-x-eir-v1"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_revision(root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def inventory(root: Path, output_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    output_resolved = output_dir.resolve()
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = sorted(
            d for d in dirs
            if d not in EXCLUDED_DIRS
            and (current_path / d).resolve() != output_resolved
            and output_resolved not in (current_path / d).resolve().parents
        )
        for name in sorted(files):
            path = current_path / name
            if path.suffix.lower() in EXCLUDED_SUFFIXES or path.is_symlink():
                continue
            resolved = path.resolve()
            if resolved == output_resolved or output_resolved in resolved.parents:
                continue
            try:
                data = path.read_bytes()
                relative = path.relative_to(root).as_posix()
            except (OSError, ValueError):
                continue
            records.append({
                "artifact_id": "file:" + relative,
                "path": relative,
                "size_bytes": len(data),
                "sha256": sha256_bytes(data),
                "media_kind": "text" if b"\x00" not in data[:8192] else "binary",
            })
    return sorted(records, key=lambda item: item["path"])


def build_eir(repository: str, revision: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    evidence = [
        {
            "evidence_id": "EV-" + item["sha256"][:16],
            "kind": "repository_file_observation",
            "subject": item["artifact_id"],
            "source_revision": revision,
            "source_path": item["path"],
            "content_sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
            "epistemic_state": "OBSERVED",
        }
        for item in records
    ]
    core = {
        "schema": SCHEMA_VERSION,
        "repository": repository,
        "source_revision": revision,
        "evidence": evidence,
        "claims": [
            {
                "claim_id": "CL-" + item["sha256"][:16],
                "subject": item["artifact_id"],
                "statement": "The pinned source contains this artifact with the recorded SHA-256 digest.",
                "claim_state": "SUPPORTED_BY_SOURCE_HASH",
                "evidence_ids": ["EV-" + item["sha256"][:16]],
                "authority_state": "NOT_AUTHORIZED",
            }
            for item in records
        ],
        "uncertainties": [
            {
                "code": "RUNTIME_NOT_EXECUTED",
                "state": "MISSING",
                "detail": "Repository inventory alone does not prove runtime behavior or semantic correctness.",
            },
            {
                "code": "AUTHORITY_NOT_GRANTED",
                "state": "BLOCKED",
                "detail": "ARC-X reconstruction cannot authorize canonical changes.",
            },
        ],
    }
    return {**core, "eir_sha256": sha256_bytes(canonical_json(core))}


def reconstruct(root: Path, output_dir: Path, repository: str, revision: str) -> dict[str, Any]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    if not root.is_dir():
        raise ValueError(f"repository root is not a directory: {root}")
    if not revision.strip() or revision.strip().lower() in {"head", "latest", "unknown", "main"}:
        raise ValueError("source revision must be an immutable commit identifier, not a moving branch name")
    output_dir.mkdir(parents=True, exist_ok=True)
    records = inventory(root, output_dir)
    eir = build_eir(repository, revision, records)
    model = {
        "schema": "arc-x-repository-model-v1",
        "repository": repository,
        "source_revision": revision,
        "artifact_count": len(records),
        "artifacts": records,
        "model_sha256": sha256_bytes(canonical_json({
            "schema": "arc-x-repository-model-v1",
            "repository": repository,
            "source_revision": revision,
            "artifact_count": len(records),
            "artifacts": records,
        })),
    }
    receipt = {
        "schema": "arc-x-retrieval-receipt-v1",
        "tool_id": "ARC-X-OMEGA",
        "tool_version": "1.0.0",
        "repository": repository,
        "source_revision": revision,
        "observed_git_head": git_revision(root),
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "artifact_count": len(records),
        "eir_sha256": eir["eir_sha256"],
        "verification_state": "PARTIAL",
        "proof_status": "PENDING",
        "authority_decision": "BLOCKED",
        "notice": "Inventory and hashing only; no runtime or semantic correctness claim.",
    }
    for filename, value in (
        ("repository.model.json", model),
        ("eir.json", eir),
        ("source.receipt.json", receipt),
    ):
        target = output_dir / filename
        target.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {"artifact_count": len(records), "eir_sha256": eir["eir_sha256"], "output_dir": str(output_dir)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root to inventory")
    parser.add_argument("--output", default="arc-x-output", help="output directory (excluded from its own inventory)")
    parser.add_argument("--repository", required=True, help="stable repository identifier, e.g. owner/name")
    parser.add_argument("--revision", required=True, help="immutable source commit SHA or version identifier")
    args = parser.parse_args()
    try:
        result = reconstruct(Path(args.root), Path(args.output), args.repository, args.revision)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
