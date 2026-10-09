#!/usr/bin/env python3
"""Bounded, provenance-first research and system-proposal processor.

The default mode is repository-local and deterministic. Optional public-source
mode reads GitHub repository trees from an explicit allow-list; it never fetches
or executes foreign source code. Generated items remain proposals and cannot
authorize execution, adoption, deployment, or canonical promotion.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.agent_fabric import AgentRegistry  # noqa: E402
from scripts.omega_pattern_foundry import build_candidate, gate, sha256_hex  # noqa: E402


QUEUE_SCHEMA = "VAIXLNS-AUTONOMOUS-FOUNDRY-QUEUE-1"
CYCLE_SCHEMA = "VAIXLNS-AUTONOMOUS-RESEARCH-CYCLE-1"
PROCESSOR_VERSION = "1.0.0"
MAX_TASKS_PER_CYCLE = 8
MAX_PUBLIC_REPOSITORIES = 8
MAX_LOCAL_SOURCE_FILES = 96
MAX_LOCAL_FILE_BYTES = 512_000
MAX_LOCAL_TOTAL_BYTES = 3_000_000
MAX_API_RESPONSE_BYTES = 6_000_000
HTTP_TIMEOUT_SECONDS = 5
SIGNAL_PATTERN = re.compile(
    r"\b(PROPOSED|SPECIFIED|UNRESOLVED|CONFLICT|UNKNOWN|STALE|TODO|FIXME|"
    r"NOT_CLAIMED|NOT_YET_PROVEN|MISSING|INSUFFICIENT_EVIDENCE)\b",
    re.IGNORECASE,
)
RELEVANT_PATH_PATTERN = re.compile(
    r"(research|agent|system|architect|processor|runtime|compiler|proof|"
    r"innovation|foundry|genome|experiment|simulation|evidence|kernel)",
    re.IGNORECASE,
)
REPO_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REF_PATTERN = re.compile(r"^[A-Za-z0-9_./-]+$")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _inside_root(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_repo_path(root: Path, relative: str) -> Path | None:
    if not isinstance(relative, str) or not relative.strip():
        return None
    raw = Path(relative)
    if raw.is_absolute() or ".." in raw.parts:
        return None
    resolved = (root / raw).resolve()
    if not _inside_root(root.resolve(), resolved):
        return None
    return resolved


def _validate_queue(queue: Mapping[str, Any]) -> list[dict[str, Any]]:
    if queue.get("schema") != QUEUE_SCHEMA:
        raise ValueError("QUEUE_SCHEMA_UNSUPPORTED")
    tasks = queue.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("QUEUE_TASKS_REQUIRED")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in tasks:
        if not isinstance(item, dict):
            raise ValueError("QUEUE_TASK_MUST_BE_OBJECT")
        task_id = item.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("QUEUE_TASK_ID_REQUIRED")
        if task_id in seen:
            raise ValueError(f"DUPLICATE_TASK_ID:{task_id}")
        seen.add(task_id)
        for field in ("problem", "objective"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"TASK_{field.upper()}_REQUIRED:{task_id}")
        try:
            priority = int(item.get("priority", 1))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"TASK_PRIORITY_INVALID:{task_id}") from exc
        if not 1 <= priority <= 10:
            raise ValueError(f"TASK_PRIORITY_OUT_OF_RANGE:{task_id}")
        for field in ("constraints", "capabilities", "local_source_paths"):
            if not isinstance(item.get(field, []), list):
                raise ValueError(f"TASK_{field.upper()}_MUST_BE_LIST:{task_id}")
        task = dict(item)
        task["priority"] = priority
        normalized.append(task)

    approved = queue.get("approved_public_repositories", [])
    if not isinstance(approved, list) or len(approved) > MAX_PUBLIC_REPOSITORIES:
        raise ValueError("APPROVED_PUBLIC_REPOSITORIES_INVALID")
    for source in approved:
        if not isinstance(source, dict):
            raise ValueError("PUBLIC_SOURCE_MUST_BE_OBJECT")
        slug = source.get("repository", "")
        ref = source.get("ref", "main")
        if not isinstance(slug, str) or not REPO_SLUG_PATTERN.fullmatch(slug):
            raise ValueError("PUBLIC_SOURCE_REPOSITORY_INVALID")
        if not isinstance(ref, str) or not REF_PATTERN.fullmatch(ref) or ".." in ref.split("/"):
            raise ValueError("PUBLIC_SOURCE_REF_INVALID")
    return normalized


def _read_local_sources(root: Path, tasks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    requested = sorted({
        path
        for task in tasks
        for path in task.get("local_source_paths", [])
        if isinstance(path, str)
    })
    manifest: dict[str, dict[str, Any]] = {}
    total_bytes = 0

    for index, relative in enumerate(requested):
        if index >= MAX_LOCAL_SOURCE_FILES:
            manifest[relative] = {"path": relative, "state": "SKIPPED_FILE_COUNT_LIMIT"}
            continue
        source_path = _safe_repo_path(root, relative)
        if source_path is None:
            manifest[relative] = {"path": relative, "state": "INVALID_PATH"}
            continue
        if not source_path.is_file():
            manifest[relative] = {"path": relative, "state": "MISSING"}
            continue
        try:
            size = source_path.stat().st_size
            if size > MAX_LOCAL_FILE_BYTES:
                manifest[relative] = {
                    "path": relative, "state": "SKIPPED_FILE_SIZE_LIMIT", "bytes": size
                }
                continue
            if total_bytes + size > MAX_LOCAL_TOTAL_BYTES:
                manifest[relative] = {
                    "path": relative, "state": "SKIPPED_TOTAL_SIZE_LIMIT", "bytes": size
                }
                continue
            raw = source_path.read_bytes()
        except OSError:
            manifest[relative] = {"path": relative, "state": "READ_ERROR"}
            continue

        total_bytes += len(raw)
        text = raw.decode("utf-8", errors="replace")
        signals = Counter(match.upper() for match in SIGNAL_PATTERN.findall(text))
        manifest[relative] = {
            "path": relative,
            "state": "READ",
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "signal_counts": dict(sorted(signals.items())),
            "content_executed": False,
        }

    return manifest


def scan_public_repository(source: Mapping[str, Any]) -> dict[str, Any]:
    """Inventory one allow-listed public GitHub tree; never download source blobs."""
    repository = str(source["repository"])
    ref = str(source.get("ref", "main"))
    if not REPO_SLUG_PATTERN.fullmatch(repository) or not REF_PATTERN.fullmatch(ref) or ".." in ref.split("/"):
        return {"repository": repository, "ref": ref, "state": "INVALID_SOURCE_CONFIG"}

    encoded_ref = quote(ref, safe="/")
    url = f"https://api.github.com/repos/{repository}/git/trees/{encoded_ref}?recursive=1"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "VAIXLNS-Autonomous-Research-Foundry/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_API_RESPONSE_BYTES + 1)
            if len(raw) > MAX_API_RESPONSE_BYTES:
                return {"repository": repository, "ref": ref, "state": "RESPONSE_SIZE_LIMIT"}
            payload = json.loads(raw.decode("utf-8"))
    except HTTPError as exc:
        state = "RATE_LIMITED" if exc.code == 403 or exc.code == 429 else f"HTTP_{exc.code}"
        return {"repository": repository, "ref": ref, "state": state}
    except (URLError, TimeoutError, OSError):
        return {"repository": repository, "ref": ref, "state": "NETWORK_UNAVAILABLE"}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"repository": repository, "ref": ref, "state": "INVALID_RESPONSE"}

    tree = payload.get("tree")
    if not isinstance(tree, list):
        return {"repository": repository, "ref": ref, "state": "INVALID_TREE_RESPONSE"}

    blob_entries = [
        entry for entry in tree
        if isinstance(entry, dict) and entry.get("type") == "blob" and isinstance(entry.get("path"), str)
    ]
    inventory = [
        {"path": entry["path"], "sha": entry.get("sha", ""), "size": entry.get("size")}
        for entry in sorted(blob_entries, key=lambda item: item["path"])
    ]
    relevant = [
        entry["path"] for entry in inventory
        if RELEVANT_PATH_PATTERN.search(entry["path"])
    ][:40]
    truncated = bool(payload.get("truncated"))
    return {
        "repository": repository,
        "ref": ref,
        "state": "PARTIAL_INVENTORY" if truncated else "DISCOVERED",
        "tree_sha": str(payload.get("sha", "")),
        "file_count": len(blob_entries),
        "relevant_path_count": sum(1 for entry in inventory if RELEVANT_PATH_PATTERN.search(entry["path"])),
        "relevant_paths_sample": relevant,
        "inventory_sha256": hashlib.sha256(canonical_json(inventory).encode("utf-8")).hexdigest(),
        "content_fetched": False,
        "code_executed": False,
        "novelty_assessed": False,
    }


def _scan_public_sources(queue: Mapping[str, Any]) -> list[dict[str, Any]]:
    sources = queue.get("approved_public_repositories", [])
    if not sources:
        return []
    worker_count = min(3, len(sources))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        return list(pool.map(scan_public_repository, sources))


def _agent_roster_summary() -> dict[str, Any]:
    try:
        registry = AgentRegistry()
        errors = list(registry.validate_handoff_chain())
        return {
            "state": "VALID" if not errors else "DEGRADED",
            "registered_agent_count": len(registry.all()),
            "handoff_errors": errors,
        }
    except Exception as exc:
        return {"state": "UNAVAILABLE", "registered_agent_count": 0, "handoff_errors": [type(exc).__name__]}


def _source_refs_for_task(
    task: Mapping[str, Any],
    local_manifest: Mapping[str, Mapping[str, Any]],
    public_manifest: list[Mapping[str, Any]],
) -> list[str]:
    refs: list[str] = []
    for relative in task.get("local_source_paths", []):
        item = local_manifest.get(relative, {})
        if item.get("state") == "READ":
            refs.append(f"repo-file:{relative}#sha256={item['sha256']}")
    for item in public_manifest:
        if item.get("state") in {"DISCOVERED", "PARTIAL_INVENTORY"} and item.get("tree_sha"):
            refs.append(f"github-tree:{item['repository']}@{item['ref']}#sha={item['tree_sha']}")
    return sorted(set(refs))


def _signal_total(task: Mapping[str, Any], local_manifest: Mapping[str, Mapping[str, Any]]) -> int:
    total = 0
    for relative in task.get("local_source_paths", []):
        item = local_manifest.get(relative, {})
        total += sum(item.get("signal_counts", {}).values())
    return total


def run_cycle(
    repo_root: str | Path,
    queue_path: str | Path = "registry/research/autonomous-foundry-queue.v1.json",
    *,
    public_sources: bool = False,
    max_tasks: int | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    configured_queue = Path(queue_path)
    resolved_queue = configured_queue.resolve() if configured_queue.is_absolute() else (root / configured_queue).resolve()
    if not _inside_root(root, resolved_queue):
        raise ValueError("QUEUE_PATH_MUST_REMAIN_INSIDE_REPOSITORY")
    if not resolved_queue.is_file():
        raise FileNotFoundError(f"QUEUE_NOT_FOUND:{resolved_queue.relative_to(root)}")

    queue_raw = resolved_queue.read_bytes()
    queue = json.loads(queue_raw.decode("utf-8"))
    tasks = _validate_queue(queue)
    local_manifest = _read_local_sources(root, tasks)
    public_manifest = _scan_public_sources(queue) if public_sources else []
    queue_hash = hashlib.sha256(queue_raw).hexdigest()

    configured_max = int(queue.get("limits", {}).get("max_tasks_per_cycle", 4))
    if configured_max < 1:
        raise ValueError("MAX_TASKS_PER_CYCLE_MUST_BE_POSITIVE")
    requested_max = configured_max if max_tasks is None else max(1, int(max_tasks))
    effective_max = min(requested_max, configured_max, MAX_TASKS_PER_CYCLE)
    ordered_tasks = sorted(tasks, key=lambda task: (-task["priority"], task["task_id"]))[:effective_max]

    cycle_identity = {
        "processor_version": PROCESSOR_VERSION,
        "queue_id": queue.get("queue_id", "UNNAMED_QUEUE"),
        "queue_sha256": queue_hash,
        "local_sources": local_manifest,
        "public_sources": [
            {
                "repository": item.get("repository"),
                "ref": item.get("ref"),
                "state": item.get("state"),
                "tree_sha": item.get("tree_sha"),
                "inventory_sha256": item.get("inventory_sha256"),
            }
            for item in public_manifest
        ],
        "selected_tasks": [task["task_id"] for task in ordered_tasks],
    }
    cycle_id = "RFOUND-" + hashlib.sha256(canonical_json(cycle_identity).encode("utf-8")).hexdigest()[:16]
    agent_summary = _agent_roster_summary()
    candidate_reports: list[dict[str, Any]] = []

    for task in ordered_tasks:
        source_refs = _source_refs_for_task(task, local_manifest, public_manifest)
        signals = _signal_total(task, local_manifest)
        priority_score = min(100, task["priority"] * 10 + min(20, signals * 2))

        candidate = build_candidate({
            "problem": task["problem"],
            "objective": task["objective"],
            "constraints": list(task.get("constraints", [])) + [
                "No self-authorization or automatic promotion",
                "Preserve source lineage and counterevidence",
                "Treat novelty as unassessed until prior-art search is documented",
            ],
            "capabilities": list(task.get("capabilities", [])),
        })
        provenance = candidate.setdefault("provenance", {})
        provenance["creator"] = "VAIXLNS-AUTONOMOUS-RESEARCH-FOUNDRY"
        provenance["research_cycle_id"] = cycle_id
        provenance["source_refs"] = source_refs
        provenance["genome_hash"] = ""
        provenance["genome_hash"] = sha256_hex(candidate)

        gate_report = gate(candidate)
        reviewable = bool(gate_report.get("valid")) and int(gate_report.get("blocking_findings", 1)) == 0
        task_source_states = {
            path: local_manifest.get(path, {}).get("state", "NOT_SCANNED")
            for path in task.get("local_source_paths", [])
        }
        candidate_reports.append({
            "task_id": task["task_id"],
            "priority": task["priority"],
            "priority_score": priority_score,
            "problem": task["problem"],
            "objective": task["objective"],
            "source_states": task_source_states,
            "source_refs": source_refs,
            "local_state_signal_count": signals,
            "candidate_state": "READY_FOR_HUMAN_REVIEW" if reviewable else "QUARANTINED",
            "novelty_state": "UNASSESSED",
            "evidence_state": "REPOSITORY_CONTEXT_ONLY",
            "admission_state": "NOT_AUTHORIZED",
            "automatic_promotion": False,
            "foundry_gate": gate_report,
            "candidate": candidate,
            "next_action": (
                "Review the proposed architecture, search relevant prior art, then define tests and a sandbox plan."
                if reviewable else
                "Inspect blocking findings, repair the candidate, and rerun the bounded foundry checks."
            ),
        })

    ready_count = sum(item["candidate_state"] == "READY_FOR_HUMAN_REVIEW" for item in candidate_reports)
    return {
        "schema": CYCLE_SCHEMA,
        "processor_version": PROCESSOR_VERSION,
        "cycle_id": cycle_id,
        "generated_at": utc_now(),
        "mode": "LOCAL_PLUS_PUBLIC_REPOSITORY_INVENTORY" if public_sources else "LOCAL_ONLY",
        "queue_id": queue.get("queue_id", "UNNAMED_QUEUE"),
        "queue_sha256": queue_hash,
        "agent_roster": agent_summary,
        "processing_budget": {
            "selected_tasks": len(ordered_tasks),
            "configured_task_limit": configured_max,
            "hard_task_limit": MAX_TASKS_PER_CYCLE,
            "local_file_limit": MAX_LOCAL_SOURCE_FILES,
            "local_file_byte_limit": MAX_LOCAL_FILE_BYTES,
            "local_total_byte_limit": MAX_LOCAL_TOTAL_BYTES,
            "public_repository_limit": MAX_PUBLIC_REPOSITORIES,
            "parallel_public_repository_scans": min(3, len(queue.get("approved_public_repositories", []))) if public_sources else 0,
            "network_timeout_seconds": HTTP_TIMEOUT_SECONDS,
        },
        "source_coverage": {
            "local_source_count": len(local_manifest),
            "local_sources_read": sum(item.get("state") == "READ" for item in local_manifest.values()),
            "public_repositories_requested": len(public_manifest),
            "public_repositories_discovered": sum(item.get("state") in {"DISCOVERED", "PARTIAL_INVENTORY"} for item in public_manifest),
            "local_manifest": local_manifest,
            "public_repository_inventory": public_manifest,
            "source_content_execution": False,
        },
        "summary": {
            "task_count": len(candidate_reports),
            "reviewable_candidate_count": ready_count,
            "quarantined_candidate_count": len(candidate_reports) - ready_count,
            "novelty_assessed_count": 0,
            "implementation_count": 0,
            "verified_count": 0,
            "automatic_admissions": 0,
        },
        "tasks": candidate_reports,
        "explicit_non_claims": [
            "This is not a full-text global web or scientific literature search.",
            "Public repository scans inventory file paths and blob identifiers; foreign source code is not fetched or executed.",
            "Novelty remains UNASSESSED until domain-specific prior-art searches and human review are recorded.",
            "A structurally valid candidate is a proposal, not an implemented, verified, or canonical system.",
            "No repository write, pull-request merge, deployment, spending, or runtime mutation is performed by this processor.",
            "No live language-model backend is invoked; the current generator is the deterministic reference backend.",
        ],
    }


def _write_json_inside_root(root: Path, relative_output: str, payload: Mapping[str, Any]) -> Path:
    output = _safe_repo_path(root, relative_output)
    if output is None:
        raise ValueError("OUTPUT_PATH_MUST_REMAIN_INSIDE_REPOSITORY")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded VAIXLNS autonomous research and system-foundry cycle")
    parser.add_argument("--root", default=str(ROOT), help="Repository root")
    parser.add_argument("--queue", default="registry/research/autonomous-foundry-queue.v1.json")
    parser.add_argument("--output", default="artifacts/autonomous-research-cycle.json")
    parser.add_argument("--max-tasks", type=int, default=None)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--public-sources", action="store_true", help="Inventory approved public GitHub repository trees")
    mode.add_argument("--local-only", action="store_true", help="Use repository-local sources only (default)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    report = run_cycle(root, args.queue, public_sources=args.public_sources, max_tasks=args.max_tasks)
    output = _write_json_inside_root(root, args.output, report)
    print(json.dumps({
        "cycle_id": report["cycle_id"],
        "mode": report["mode"],
        "output": str(output.relative_to(root)),
        "summary": report["summary"],
        "agent_roster": report["agent_roster"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
