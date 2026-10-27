#!/usr/bin/env python3
"""VAIXLNS read-only continuous federation sync and innovation review projection.

This is a provenance-preserving metadata projector, NOT a repository mirror,
cross-account importer, model activation service, or canonical promotion engine.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SCHEMA = "VAIXLNS.ContinuousFederationSync.v1"
CONFIG_SCHEMA = "VAIXLNS.FederationSyncSources.v1"
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9_./-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
INNOVATION_TERMS = (
    "innovation", "invention", "research", "vcre", "architecture_lab",
    "proof", "scck", "model_registry", "model-gateway", "vx_federation",
    "zero_loss", "zero-loss", "index", "recovery", "agent", "genome",
)
CRITICAL_FILES = {
    "project.genome", "registry/omega/omega-000-master-index.json",
}

class SyncError(RuntimeError):
    """Invalid source configuration or unverifiable source response."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_sources(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or data.get("schema") != CONFIG_SCHEMA:
        raise SyncError("INVALID_CONFIG_SCHEMA")
    rows = data.get("repositories")
    if not isinstance(rows, list) or not rows or len(rows) > 50:
        raise SyncError("INVALID_REPOSITORY_LIST")
    seen: set[str] = set()
    result = []
    for item in rows:
        if not isinstance(item, dict):
            raise SyncError("INVALID_REPOSITORY_ENTRY")
        name, branch, baseline = item.get("repository"), item.get("branch"), item.get("baseline_commit")
        if not isinstance(name, str) or not REPO_RE.fullmatch(name) or name in seen:
            raise SyncError("INVALID_OR_DUPLICATE_REPOSITORY")
        if not isinstance(branch, str) or not BRANCH_RE.fullmatch(branch) or ".." in branch or branch.startswith("/"):
            raise SyncError("INVALID_BRANCH")
        if not isinstance(baseline, str) or not SHA_RE.fullmatch(baseline):
            raise SyncError("FULL_BASELINE_COMMIT_SHA_REQUIRED")
        if item.get("scope") != "PUBLIC_METADATA_ONLY":
            raise SyncError("ONLY_PUBLIC_METADATA_SCOPE_SUPPORTED")
        seen.add(name)
        result.append({"repository": name, "branch": branch, "baseline_commit": baseline,
                       "system_hint": item.get("system_hint", "UNRESOLVED")})
    return sorted(result, key=lambda x: x["repository"])


class GitHubReadOnly:
    """Pinned-domain GET interface; no writes and no user-controlled hostnames."""
    def __init__(self, *, timeout: int = 20):
        self.timeout = timeout

    def get(self, path: str) -> dict[str, Any]:
        if not path.startswith("/repos/") or "://" in path or "?" in path and not path.endswith("?recursive=1"):
            raise SyncError("API_PATH_NOT_ALLOWED")
        request = Request("https://api.github.com" + path, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "VAIXLNS-FederationSync-v1",
        })
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(12 * 1024 * 1024 + 1)
                if len(raw) > 12 * 1024 * 1024:
                    raise SyncError("REMOTE_RESPONSE_TOO_LARGE")
        except HTTPError as exc:
            # No response body, URL with embedded tokens, or credentials in diagnostics.
            raise SyncError("GITHUB_HTTP_STATUS_" + str(exc.code)) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise SyncError("GITHUB_NETWORK_FAILURE") from exc
        try:
            parsed = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as exc:
            raise SyncError("GITHUB_INVALID_JSON") from exc
        if not isinstance(parsed, dict):
            raise SyncError("GITHUB_NONOBJECT_RESPONSE")
        return parsed


class FixtureReadOnly:
    """Only for offline regression testing; never claims live connectivity."""
    def __init__(self, responses: dict[str, Any]):
        self.responses = responses

    def get(self, path: str) -> dict[str, Any]:
        if path not in self.responses:
            raise SyncError("FIXTURE_MISSING_RESPONSE")
        value = self.responses[path]
        if isinstance(value, dict) and value.get("_error"):
            raise SyncError(value["_error"])
        return value


def parse_commit(value: Any) -> tuple[str, str]:
    try:
        commit = value["sha"]
        tree = value["commit"]["tree"]["sha"]
    except (TypeError, KeyError):
        raise SyncError("COMMIT_RESPONSE_INCOMPLETE")
    if not isinstance(commit, str) or not SHA_RE.fullmatch(commit) or not isinstance(tree, str) or not SHA_RE.fullmatch(tree):
        raise SyncError("INVALID_GIT_SHA")
    return commit, tree


def classify_path(path: str) -> str:
    lowered = path.casefold()
    if path in CRITICAL_FILES:
        return "CANONICAL_GUARD_REVIEW"
    if any(term in lowered for term in INNOVATION_TERMS):
        return "INNOVATION_REVIEW_CANDIDATE"
    if lowered.startswith((".github/workflows/", "tests/", "test/")):
        return "TEST_OR_CI_CHANGE"
    return "SOURCE_CHANGE"


def safe_path(value: Any) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value or "\x00" in value or ".." in value.split("/"):
        raise SyncError("INVALID_SOURCE_PATH")
    return value


def observe_repository(item: dict[str, Any], api: Any) -> tuple[dict, list[dict]]:
    repo, branch, baseline = item["repository"], item["branch"], item["baseline_commit"]
    metadata = api.get(f"/repos/{repo}")
    if metadata.get("full_name", "").casefold() != repo.casefold():
        raise SyncError("REPOSITORY_IDENTITY_MISMATCH")
    if metadata.get("private") is not False:
        raise SyncError("PRIVATE_OR_UNVERIFIED_VISIBILITY")
    current, tree_sha = parse_commit(api.get(f"/repos/{repo}/commits/{branch}"))
    tree_resp = api.get(f"/repos/{repo}/git/trees/{tree_sha}?recursive=1")
    tree = tree_resp.get("tree")
    if not isinstance(tree, list) or tree_resp.get("truncated") is not False:
        raise SyncError("GIT_TREE_INCOMPLETE_OR_TRUNCATED")
    files = [x for x in tree if isinstance(x, dict) and x.get("type") == "blob"]
    paths = [safe_path(x.get("path")) for x in files]
    if len(paths) != len(set(paths)):
        raise SyncError("DUPLICATE_GIT_TREE_PATH")
    paths_set = set(paths)
    candidate_events: list[dict] = []
    comparison_status = "BASELINE_EQUALS_HEAD"
    if current != baseline:
        comparison = api.get(f"/repos/{repo}/compare/{baseline}...{current}")
        diff = comparison.get("files")
        if not isinstance(diff, list) or comparison.get("files_changed", len(diff)) > len(diff):
            raise SyncError("COMPARE_FILES_INCOMPLETE")
        if comparison.get("status") not in ("ahead", "identical", "diverged"):
            raise SyncError("COMPARE_STATUS_UNVERIFIED")
        comparison_status = "COMPARED_WITH_PINNED_BASELINE"
        if len(diff) > 300:
            raise SyncError("COMPARE_TOO_MANY_FILES")
        for file in diff:
            path = safe_path(file.get("filename"))
            action = file.get("status")
            if action not in ("added", "modified", "removed", "renamed", "copied", "changed"):
                raise SyncError("UNKNOWN_GIT_CHANGE_TYPE")
            kind = classify_path(path)
            previous = file.get("previous_filename")
            if previous is not None:
                previous = safe_path(previous)
            blob = file.get("sha")
            if blob is not None and (not isinstance(blob, str) or not SHA_RE.fullmatch(blob)):
                raise SyncError("INVALID_BLOB_SHA")
            record = {
                "record_id": "FSYNC-" + sha256(canonical_bytes([repo, current, path, action]))[:20],
                "source_repository": repo, "source_branch": branch,
                "source_commit_sha": current, "source_path": path,
                "source_git_blob_sha": blob,
                "source_bytes_sha256": None, "source_bytes_captured": False,
                "change_status": action, "previous_filename": previous,
                "category": kind, "system_hint": item["system_hint"],
                "lifecycle": "DISCOVERED", "implementation": "UNKNOWN",
                "running": "UNKNOWN", "verified": "UNKNOWN",
                "canonical_admission": "NOT_REQUESTED", "review_state": "REVIEW_REQUIRED",
            }
            candidate_events.append(record)
    return ({
        "repository": repo, "branch": branch, "baseline_commit_sha": baseline,
        "head_commit_sha": current, "head_tree_sha": tree_sha,
        "tree_file_count": len(files), "test_file_count": sum(p.startswith(("tests/", "test/")) for p in paths),
        "workflow_file_count": sum(p.startswith(".github/workflows/") for p in paths),
        "related_source_paths_observed": sorted(
            p for p in paths_set if classify_path(p) in ("INNOVATION_REVIEW_CANDIDATE", "CANONICAL_GUARD_REVIEW")
        ),
        "comparison": comparison_status, "repository_visibility": "PUBLIC",
        "source_observation": "GITHUB_API_REPOSITORY_TREE_AND_CHANGE_METADATA",
        "source_bytes_sha256": "NOT_CAPTURED_USE_PINNED_SNAPSHOT_ENGINE",
        "runtime_state": "UNKNOWN", "verification_state": "UNKNOWN",
        "status": "METADATA_OBSERVED",
    }, candidate_events)


def build(config: dict, api: Any, *, captured_at: str = "UNSPECIFIED") -> dict:
    sources = validate_sources(config)
    snapshot: list[dict] = []
    events: list[dict] = []
    failures: list[dict] = []
    for item in sources:
        try:
            observed, changes = observe_repository(item, api)
            snapshot.append(observed)
            events.extend(changes)
        except (SyncError, ValueError, TypeError, KeyError) as exc:
            # Fail this source visibly, continue other independent repositories.
            failures.append({
                "repository": item["repository"], "baseline_commit_sha": item["baseline_commit"],
                "status": "UNAVAILABLE_OR_INCOMPLETE", "reason_code": str(exc)[:120],
                "source_state": "UNKNOWN",
            })
    snapshot.sort(key=lambda r: r["repository"])
    events.sort(key=lambda r: (r["source_repository"], r["source_path"], r["record_id"]))
    body = {
        "schema": SCHEMA, "scope": "PUBLIC_GITHUB_METADATA_ONLY",
        "captured_at_utc": captured_at,
        "source_repositories_requested": len(sources),
        "source_repositories_observed": len(snapshot),
        "source_repositories_unavailable": len(failures),
        "repositories": snapshot, "changes": events, "failures": failures,
        "decision": "PARTIAL_BLOCKED" if failures else "REVIEW_READY",
        "canonical_promotion_count": 0, "source_files_modified": 0,
        "model_or_external_account_connections_verified": False,
        "requires_independent_tests_and_review": True,
    }
    body["manifest_sha256"] = sha256(canonical_bytes(body))
    return body


def create_outputs(result: dict, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    (out / "federation-sync.v1.json").write_text(
        json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    queue = {
        "schema": "VAIXLNS.InnovationIntakeQueue.v1",
        "upstream_manifest_sha256": result["manifest_sha256"],
        "state": "REVIEW_ONLY_NOT_CANONICAL",
        "items": [event for event in result["changes"] if event["category"] in (
            "INNOVATION_REVIEW_CANDIDATE", "CANONICAL_GUARD_REVIEW")],
        "candidate_count": sum(event["category"] == "INNOVATION_REVIEW_CANDIDATE" for event in result["changes"]),
        "authority_granted": False, "tests_passed_by_this_queue": False,
    }
    (out / "innovation-intake-queue.v1.json").write_text(
        json.dumps(queue, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (out / "all-changes.v1.jsonl").open("w", encoding="utf-8") as stream:
        for event in result["changes"]:
            stream.write(json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
    receipt = {
        "schema": "VAIXLNS.FederationSyncReceipt.v1",
        "upstream_manifest_sha256": result["manifest_sha256"],
        "status": result["decision"],
        "innovation_queue_sha256": sha256((out / "innovation-intake-queue.v1.json").read_bytes()),
        "changes_jsonl_sha256": sha256((out / "all-changes.v1.jsonl").read_bytes()),
        "verification": "METADATA_SYNC_ONLY",
        "canon_mutation": "NONE", "repository_writes": "NONE",
        "other_accounts_connected": "NOT_VERIFIED",
        "zero_loss_archive_integrity": "SEPARATE_EXISTING_ENGINE_REQUIRED",
    }
    (out / "sync-receipt.v1.json").write_text(
        json.dumps(receipt, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("registry/federation/continuous-sync-sources.v1.json"))
    parser.add_argument("--out", type=Path, default=Path("build/federation-sync"))
    parser.add_argument("--fixture", type=Path, help="Offline fixture responses, NEVER live proof")
    parser.add_argument("--strict", action="store_true", help="Fail when any repository cannot be observed")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        if args.fixture:
            api = FixtureReadOnly(json.loads(args.fixture.read_text(encoding="utf-8")))
            stamp = "FIXTURE_ONLY_NOT_LIVE"
        else:
            api = GitHubReadOnly()
            stamp = datetime.now(timezone.utc).isoformat()
        result = build(config, api, captured_at=stamp)
        receipt = create_outputs(result, args.out)
    except (OSError, ValueError, SyncError, json.JSONDecodeError) as exc:
        print("FEDERATION_SYNC_ERROR:" + type(exc).__name__ + ":" + str(exc)[:160], file=sys.stderr)
        return 2
    print(json.dumps({
        "status": receipt["status"], "observed_repositories": result["source_repositories_observed"],
        "unavailable_repositories": result["source_repositories_unavailable"],
        "changed_files": len(result["changes"]), "innovation_review_candidates":
            sum(e["category"] == "INNOVATION_REVIEW_CANDIDATE" for e in result["changes"]),
        "manifest_sha256": result["manifest_sha256"],
    }, sort_keys=True))
    return 2 if args.strict and result["decision"] != "REVIEW_READY" else 0


if __name__ == "__main__":
    raise SystemExit(main())
