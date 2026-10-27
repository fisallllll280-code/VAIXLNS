#!/usr/bin/env python3
"""Validate federation CI evidence and propose NON-canonical innovation review files.

This is a trusted-branch CI publication step. It must never run code from an
untrusted pull request with a write token, merge a PR or grant authorization.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.continuous_federation_sync import (
    CONFIG_SCHEMA, SCHEMA, canonical_bytes, sha256, validate_sources,
)

class ReviewError(ValueError):
    pass


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReviewError("INVALID_EVIDENCE_OBJECT")
    return value


def validate_evidence(input_dir: Path, config: dict) -> tuple[dict, dict, dict]:
    if config.get("schema") != CONFIG_SCHEMA:
        raise ReviewError("CONFIG_INVALID")
    authorized = {x["repository"] for x in validate_sources(config)}
    manifest_path = input_dir / "federation-sync.v1.json"
    queue_path = input_dir / "innovation-intake-queue.v1.json"
    receipt_path = input_dir / "sync-receipt.v1.json"
    events_path = input_dir / "all-changes.v1.jsonl"
    manifest, queue, receipt = map(read_json, [manifest_path, queue_path, receipt_path])
    if manifest.get("schema") != SCHEMA or manifest.get("decision") != "REVIEW_READY":
        raise ReviewError("SOURCE_NOT_READY")
    stamp = manifest.get("captured_at_utc")
    if not isinstance(stamp, str) or not stamp.endswith(("+00:00", "Z")):
        raise ReviewError("NONLIVE_SOURCE_TIMESTAMP")
    if manifest.get("canonical_promotion_count") != 0 or manifest.get("source_files_modified") != 0:
        raise ReviewError("MUTATION_OR_PROMOTION_PROHIBITED")
    if manifest.get("model_or_external_account_connections_verified") is not False:
        raise ReviewError("INVALID_EXTERNAL_CONNECTION_CLAIM")
    digest = manifest.get("manifest_sha256")
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if not isinstance(digest, str) or sha256(canonical_bytes(unsigned)) != digest:
        raise ReviewError("MANIFEST_DIGEST_MISMATCH")
    repos = manifest.get("repositories")
    if not isinstance(repos, list) or {x.get("repository") for x in repos} != authorized:
        raise ReviewError("REPOSITORY_SCOPE_MISMATCH")
    if not all(x.get("repository_visibility") == "PUBLIC" and x.get("status") == "METADATA_OBSERVED" for x in repos):
        raise ReviewError("PRIVATE_OR_UNVERIFIED_SOURCE")
    if manifest.get("failures") or manifest.get("source_repositories_unavailable") != 0:
        raise ReviewError("PARTIAL_CAPTURE_BLOCKED")
    changes = manifest.get("changes")
    if not isinstance(changes, list):
        raise ReviewError("CHANGES_LIST_INVALID")
    for e in changes:
        if e.get("source_repository") not in authorized or e.get("review_state") != "REVIEW_REQUIRED":
            raise ReviewError("UNAUTHORIZED_EVENT")
        if e.get("verified") != "UNKNOWN" or e.get("canonical_admission") != "NOT_REQUESTED":
            raise ReviewError("ILLEGAL_STATUS_PROMOTION")
        if e.get("source_bytes_captured") is not False:
            raise ReviewError("SOURCE_BYTES_CAPTURE_CLAIM_UNVERIFIED")
    if queue.get("schema") != "VAIXLNS.InnovationIntakeQueue.v1" or queue.get("authority_granted") is not False:
        raise ReviewError("INNOVATION_AUTHORITY_INVALID")
    if queue.get("upstream_manifest_sha256") != digest:
        raise ReviewError("QUEUE_SOURCE_MISMATCH")
    selected = [e for e in changes if e["category"] in ("INNOVATION_REVIEW_CANDIDATE", "CANONICAL_GUARD_REVIEW")]
    if queue.get("items") != selected:
        raise ReviewError("INNOVATION_QUEUE_NOT_SOURCE_DERIVED")
    if receipt.get("schema") != "VAIXLNS.FederationSyncReceipt.v1" or receipt.get("upstream_manifest_sha256") != digest:
        raise ReviewError("RECEIPT_SOURCE_MISMATCH")
    if receipt.get("status") != "REVIEW_READY" or receipt.get("canon_mutation") != "NONE":
        raise ReviewError("RECEIPT_STATE_MISMATCH")
    if receipt.get("innovation_queue_sha256") != sha256(queue_path.read_bytes()) or receipt.get("changes_jsonl_sha256") != sha256(events_path.read_bytes()):
        raise ReviewError("RECEIPT_CONTENT_DIGEST_MISMATCH")
    return manifest, queue, receipt


def render_review(root: Path, input_dir: Path) -> tuple[Path, Path]:
    config = read_json(root / "registry/federation/continuous-sync-sources.v1.json")
    manifest, queue, receipt = validate_evidence(input_dir, config)
    evidence = {
        "schema": "VAIXLNS.FederatedSyncEvidenceReview.v1",
        "state": "OBSERVED_NEEDS_HUMAN_REVIEW",
        "captured_at_utc": manifest["captured_at_utc"],
        "source_manifest_sha256": manifest["manifest_sha256"],
        "source_repositories": [x["repository"] for x in manifest["repositories"]],
        "observed_repo_count": manifest["source_repositories_observed"],
        "changes_count": len(manifest["changes"]),
        "innovation_review_count": len(queue["items"]),
        "canonical_promotion": "PROHIBITED",
        "verified_implementation": "UNKNOWN",
        "full_byte_level_recovery": "NOT_PERFORMED",
        "receipt": receipt,
    }
    proposed = {
        "schema": "VAIXLNS.FederationInnovationReview.v1",
        "state": "PROPOSED_NOT_ADMITTED",
        "source_manifest_sha256": manifest["manifest_sha256"],
        "review_items": queue["items"],
        "identity_conflicts_are_preserved": True,
        "model_execution": "NOT_RUN",
        "approval": "REQUIRED",
    }
    e_path = root / "docs/evidence/federation-sync-current-review.v1.json"
    i_path = root / "registry/innovation/review/federation-sync-current.v1.json"
    for p, value in [(e_path, evidence), (i_path, proposed)]:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return e_path, i_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--inputs", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    inputs = args.inputs.resolve()
    try:
        a, b = render_review(root, inputs)
    except (ReviewError, OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, "FEDERATION_REVIEW_BLOCKED:" + type(exc).__name__ + ":" + str(exc)[:120] + "\n")
    print(json.dumps({"state": "REVIEW_ONLY", "evidence": str(a.relative_to(root)),
                      "innovation": str(b.relative_to(root))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
