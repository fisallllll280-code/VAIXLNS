"""Ω Memory–Task–Innovation Kernel (MTIK) v1.

Deterministic reference implementation for evidence-backed context recovery,
dependency-aware task planning, and tightly scoped registered-handler execution.

This module does not call model providers, run shell commands, access networks,
grant its own authority, write the canonical genome/index, or assert production
readiness. External and production effects are intentionally disabled.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Callable, Iterable, Mapping, Sequence


GENESIS_HASH = "0" * 64
MEMORY_STATES = {
    "PROPOSAL", "SPECIFIED", "IMPLEMENTED", "VERIFIED",
    "PARTIAL", "MISSING", "CONFLICT", "RECOVERED",
}
TASK_STATES = {
    "PROPOSED", "READY", "WAITING", "BLOCKED", "RUNNING",
    "PLAN_ONLY", "COMPLETED", "FAILED", "HELD", "REJECTED",
}
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
ALLOWED_ACTION_TYPES = {"READ_ONLY", "SANDBOX_MUTATION", "EXTERNAL_EFFECT"}
DISABLED_ACTION_TYPES = {"EXTERNAL_EFFECT"}


class KernelError(ValueError):
    """Raised when an input violates the evidence or execution contract."""


def canonical_json(value: Any) -> str:
    """Stable UTF-8 JSON representation used for fingerprints."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    )


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _without(record: Mapping[str, Any], key: str) -> dict[str, Any]:
    return {name: value for name, value in record.items() if name != key}


def verify_memory_snapshot(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate a complete, ordered PEM snapshot before retrieval.

    Expected input is the full append-only ledger in original order, not a
    filtered search result. A snapshot with broken links or duplicate IDs fails
    closed; the function never repairs or rewrites the supplied records.
    """
    previous = GENESIS_HASH
    seen: set[str] = set()
    for idx, record in enumerate(records, start=1):
        rid = record.get("record_id")
        if not isinstance(rid, str) or not rid.strip():
            raise KernelError(f"memory record {idx}: record_id is required")
        if rid in seen:
            raise KernelError(f"memory record {idx}: duplicate record_id {rid}")
        if record.get("previous_record_hash") != previous:
            raise KernelError(f"memory record {idx}: hash-chain link mismatch")
        record_hash = record.get("record_hash")
        if not isinstance(record_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", record_hash):
            raise KernelError(f"memory record {idx}: invalid record_hash")
        computed = digest_json(_without(record, "record_hash"))
        if computed != record_hash:
            raise KernelError(f"memory record {idx}: record hash mismatch")
        _validate_memory_shape(record, idx)
        previous = record_hash
        seen.add(rid)
    return {"valid": True, "records": len(records), "head_hash": previous}


def _validate_memory_shape(record: Mapping[str, Any], idx: int = 0) -> None:
    prefix = f"memory record {idx}: " if idx else ""
    for key in ("subject", "summary", "epistemic_state"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise KernelError(prefix + f"{key} is required")
    if record["epistemic_state"] not in MEMORY_STATES:
        raise KernelError(prefix + "unknown epistemic_state")
    provenance = record.get("provenance")
    if not isinstance(provenance, Mapping):
        raise KernelError(prefix + "provenance object is required")
    for key in ("repository", "revision", "path", "content_sha256"):
        if not isinstance(provenance.get(key), str) or not provenance[key].strip():
            raise KernelError(prefix + f"provenance.{key} is required")
    if not re.fullmatch(r"[0-9a-f]{64}", provenance["content_sha256"]):
        raise KernelError(prefix + "provenance.content_sha256 must be SHA-256")
    evidence = record.get("evidence")
    if not isinstance(evidence, list):
        raise KernelError(prefix + "evidence must be a list")
    for evidence_idx, item in enumerate(evidence):
        if not isinstance(item, Mapping):
            raise KernelError(prefix + f"evidence[{evidence_idx}] must be an object")
        for key in ("kind", "ref", "digest"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise KernelError(prefix + f"evidence[{evidence_idx}].{key} is required")
        if not re.fullmatch(r"[0-9a-f]{64}", item["digest"]):
            raise KernelError(prefix + f"evidence[{evidence_idx}].digest must be SHA-256")


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9_.:/+-]*", text.casefold()) if len(t) > 1}


def recover_context(
    records: Sequence[Mapping[str, Any]],
    query: str,
    *,
    limit: int = 8,
    verify_chain: bool = True,
) -> dict[str, Any]:
    """Recover source-bound memories with explainable lexical ranking.

    This is deliberately lexical and deterministic, not semantic search. Scores
    prioritize retrieval only; they do not alter evidence state or truth.
    """
    if not isinstance(query, str) or not query.strip():
        raise KernelError("query must be non-empty")
    if limit < 1 or limit > 100:
        raise KernelError("limit must be between 1 and 100")
    snapshot = verify_memory_snapshot(records) if verify_chain else {
        "valid": False, "records": len(records), "head_hash": None,
    }
    query_tokens = _tokens(query)
    phrase = " ".join(query.casefold().split())
    ranked: list[dict[str, Any]] = []
    state_weight = {
        "VERIFIED": 1.0,
        "IMPLEMENTED": 0.85,
        "SPECIFIED": 0.7,
        "RECOVERED": 0.6,
        "PARTIAL": 0.5,
        "PROPOSAL": 0.4,
        "CONFLICT": 0.25,
        "MISSING": 0.2,
    }
    for record in records:
        searchable = " ".join(str(record.get(k, "")) for k in (
            "subject", "summary", "memory_type", "epistemic_state"
        ))
        tokens = _tokens(searchable)
        matched = sorted(query_tokens & tokens)
        exact_phrase = phrase in searchable.casefold() if phrase else False
        if not matched and not exact_phrase:
            continue
        # Fully explainable ranking: lexical coverage plus exact phrase boost;
        # state weight adjusts retrieval priority, never epistemic state.
        lexical = len(matched) / max(1, len(query_tokens))
        score = round((lexical + (1.0 if exact_phrase else 0.0)) *
                      state_weight.get(str(record["epistemic_state"]), 0.3), 6)
        provenance = record["provenance"]
        ranked.append({
            "record_id": record["record_id"],
            "subject": record["subject"],
            "summary": record["summary"],
            "epistemic_state": record["epistemic_state"],
            "score": score,
            "matched_terms": matched,
            "exact_phrase_match": exact_phrase,
            "repository": provenance["repository"],
            "revision": provenance["revision"],
            "path": provenance["path"],
            "content_sha256": provenance["content_sha256"],
            "evidence_refs": [
                {"kind": e["kind"], "ref": e["ref"], "digest": e["digest"]}
                for e in record.get("evidence", [])
            ],
            "record_hash": record.get("record_hash"),
        })
    ranked.sort(key=lambda item: (-item["score"], item["record_id"]))
    return {
        "operation": "RECOVER_CONTEXT",
        "query": query,
        "retrieval_method": "DETERMINISTIC_LEXICAL",
        "snapshot": snapshot,
        "matches": ranked[:limit],
        "matched_count": len(ranked),
        "empty_reason": None if ranked else "NO_MATCHING_MEMORY; no facts were fabricated",
        "truth_boundary": "ranking is not verification and does not change memory state",
    }


def _validate_task(task: Mapping[str, Any]) -> None:
    for key in ("task_id", "title", "description", "action", "action_type", "priority"):
        if not isinstance(task.get(key), str) or not task[key].strip():
            raise KernelError(f"task.{key} must be non-empty")
    if task["priority"] not in PRIORITY_RANK:
        raise KernelError(f"task {task['task_id']}: priority must be P0-P3")
    if task["action_type"] not in ALLOWED_ACTION_TYPES:
        raise KernelError(f"task {task['task_id']}: invalid action_type")
    for key in ("depends_on", "required_capabilities", "source_memory_ids", "acceptance_criteria"):
        value = task.get(key, [])
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            raise KernelError(f"task {task['task_id']}: {key} must be an array of non-empty strings")
    if not task.get("acceptance_criteria"):
        raise KernelError(f"task {task['task_id']}: at least one acceptance criterion is required")


def build_task_plan(
    goal: str,
    tasks: Sequence[Mapping[str, Any]],
    *,
    available_capabilities: Iterable[str] = (),
    recovered_memory_ids: Iterable[str] = (),
    plan_id: str | None = None,
) -> dict[str, Any]:
    """Create a deterministic dependency-aware plan; never runs its tasks."""
    if not isinstance(goal, str) or not goal.strip():
        raise KernelError("goal must be non-empty")
    if not tasks:
        raise KernelError("at least one task is required")
    normalized = [dict(task) for task in tasks]
    ids: dict[str, dict[str, Any]] = {}
    for task in normalized:
        _validate_task(task)
        if task["task_id"] in ids:
            raise KernelError(f"duplicate task_id: {task['task_id']}")
        ids[task["task_id"]] = task

    for task in normalized:
        missing = sorted(set(task.get("depends_on", [])) - set(ids))
        if missing:
            raise KernelError(f"task {task['task_id']} has missing dependencies: {missing}")

    # Deterministic topological order (Kahn); cycle detection is fail-closed.
    indegree = {tid: len(set(t.get("depends_on", []))) for tid, t in ids.items()}
    followers: dict[str, list[str]] = defaultdict(list)
    for tid, task in ids.items():
        for dep in set(task.get("depends_on", [])):
            followers[dep].append(tid)
    ready = sorted(
        (tid for tid, degree in indegree.items() if degree == 0),
        key=lambda tid: (PRIORITY_RANK[ids[tid]["priority"]], tid),
    )
    ordered: list[str] = []
    while ready:
        tid = ready.pop(0)
        ordered.append(tid)
        for follower in sorted(followers[tid]):
            indegree[follower] -= 1
            if indegree[follower] == 0:
                ready.append(follower)
        ready.sort(key=lambda item: (PRIORITY_RANK[ids[item]["priority"]], item))
    if len(ordered) != len(ids):
        cyclic = sorted(tid for tid, degree in indegree.items() if degree > 0)
        raise KernelError(f"dependency cycle detected: {cyclic}")

    caps = set(available_capabilities)
    memory_ids = set(recovered_memory_ids)
    by_id: dict[str, dict[str, Any]] = {}
    for tid in ordered:
        task = ids[tid]
        missing_caps = sorted(set(task.get("required_capabilities", [])) - caps)
        missing_memory = sorted(set(task.get("source_memory_ids", [])) - memory_ids)
        deps = task.get("depends_on", [])
        dependency_blockers = [
            dep for dep in deps if by_id[dep]["status"] not in {"READY", "PLAN_ONLY"}
        ]
        if missing_caps or missing_memory or dependency_blockers:
            status = "BLOCKED"
        elif task["action_type"] == "EXTERNAL_EFFECT":
            status = "BLOCKED"
        elif task["action_type"] == "SANDBOX_MUTATION":
            status = "PLAN_ONLY"  # requires explicit runtime admission later
        else:
            status = "READY"
        by_id[tid] = {
            **task,
            "status": status,
            "missing_capabilities": missing_caps,
            "missing_memory_ids": missing_memory,
            "dependency_blockers": dependency_blockers,
        }

    body = {
        "schema_version": "1.0.0",
        "kernel": "VAIXLNS.OMEGA.MEMORY_TASK_INNOVATION.001",
        "goal": goal,
        "tasks": [by_id[tid] for tid in ordered],
        "execution_policy": {
            "planning_is_not_execution": True,
            "external_effects_enabled": False,
            "sandbox_mutations_require_runtime_admission": True,
            "self_promotion_allowed": False,
        },
        "summary": {
            "task_count": len(ordered),
            "ready_count": sum(t["status"] == "READY" for t in by_id.values()),
            "blocked_count": sum(t["status"] == "BLOCKED" for t in by_id.values()),
            "plan_only_count": sum(t["status"] == "PLAN_ONLY" for t in by_id.values()),
        },
        "status": "PLANNED",
    }
    body["plan_id"] = plan_id or ("MTIK-" + digest_json(body)[:16].upper())
    body["plan_digest"] = digest_json(body)
    return body


def execute_registered_task(
    task: Mapping[str, Any],
    *,
    handler_registry: Mapping[str, Callable[[Mapping[str, Any]], Any]],
    granted_capabilities: Iterable[str] = (),
    dry_run: bool = True,
    authorization_ref: str | None = None,
) -> dict[str, Any]:
    """Execute only an injected, named handler under narrow capabilities.

    No arbitrary shell, network, subprocess, or provider actions exist here.
    External effects are permanently denied by this reference kernel. Sandbox
    mutations require a non-dry-run request and an explicit decision reference.
    The handler's output is recorded as a result, not auto-verified.
    """
    _validate_task(task)
    action_type = task["action_type"]
    if action_type == "EXTERNAL_EFFECT":
        return {
            "task_id": task["task_id"], "status": "REJECTED",
            "reason": "EXTERNAL_EFFECT_DISABLED_BY_KERNEL",
        }
    needed = set(task.get("required_capabilities", []))
    missing = sorted(needed - set(granted_capabilities))
    if missing:
        return {
            "task_id": task["task_id"], "status": "HELD",
            "reason": "CAPABILITY_NOT_GRANTED", "missing_capabilities": missing,
        }
    if task["action"] not in handler_registry:
        return {
            "task_id": task["task_id"], "status": "HELD",
            "reason": "NO_REGISTERED_HANDLER",
        }
    if dry_run:
        return {
            "task_id": task["task_id"], "status": "PLAN_ONLY",
            "action": task["action"], "action_type": action_type,
            "input_digest": digest_json(task.get("input", {})),
            "reason": "DRY_RUN_NO_HANDLER_INVOKED",
        }
    if action_type == "SANDBOX_MUTATION" and not (
        isinstance(authorization_ref, str) and authorization_ref.startswith("decision://")
    ):
        return {
            "task_id": task["task_id"], "status": "HELD",
            "reason": "SANDBOX_MUTATION_REQUIRES_AUTHORIZATION_REFERENCE",
        }

    started_at = datetime.now(timezone.utc).isoformat()
    input_value = task.get("input", {})
    try:
        output = handler_registry[task["action"]](input_value)
        output_digest = digest_json(output)
        return {
            "task_id": task["task_id"], "status": "COMPLETED",
            "action": task["action"], "action_type": action_type,
            "started_at": started_at,
            "input_digest": digest_json(input_value),
            "output_digest": output_digest,
            "output": output,
            "verification_state": "NOT_VERIFIED",
            "authorization_ref": authorization_ref,
        }
    except Exception as exc:  # handler errors become explicit failures, not success
        return {
            "task_id": task["task_id"], "status": "FAILED",
            "action": task["action"], "action_type": action_type,
            "started_at": started_at,
            "input_digest": digest_json(input_value),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "verification_state": "NOT_VERIFIED",
            "authorization_ref": authorization_ref,
        }


def evaluate_completion(
    task: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    independent_verifier_id: str | None,
    producer_id: str | None,
    source_revision: str,
    evidence_digest: str | None,
    reproduction_command: str | None,
    independent_check_passed: bool,
) -> dict[str, Any]:
    """Return an admission verdict; never edits the input task/result."""
    blockers: list[str] = []
    if result.get("status") != "COMPLETED":
        blockers.append("task result is not COMPLETED")
    if result.get("verification_state") == "NOT_VERIFIED":
        # A handler output is not automatically a verified outcome.
        blockers.append("handler result has not been independently verified")
    if not source_revision.strip():
        blockers.append("immutable source revision is missing")
    if not isinstance(evidence_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", evidence_digest):
        blockers.append("evidence digest is missing or invalid")
    if not isinstance(reproduction_command, str) or not reproduction_command.strip():
        blockers.append("reproduction command is missing")
    if not independent_verifier_id or not independent_verifier_id.strip():
        blockers.append("independent verifier is missing")
    if not producer_id or independent_verifier_id == producer_id:
        blockers.append("producer/verifier separation-of-duties violated")
    if not independent_check_passed:
        blockers.append("independent check did not pass")
    return {
        "task_id": task.get("task_id"),
        "decision": "ELIGIBLE_FOR_GOVERNANCE_REVIEW" if not blockers else "HOLD",
        "epistemic_state": "IMPLEMENTED" if not blockers else "PARTIAL",
        "requested_epistemic_state": "VERIFIED" if not blockers else None,
        "canonical_promotion": "NOT_PERFORMED",
        "blockers": blockers,
        "source_revision": source_revision,
        "evidence_digest": evidence_digest,
        "reproduction_command": reproduction_command,
        "independent_verifier_id": independent_verifier_id,
        "producer_id": producer_id,
        "promotion_authority": "SEPARATE_CANONICAL_GOVERNANCE_REQUIRED",
    }
