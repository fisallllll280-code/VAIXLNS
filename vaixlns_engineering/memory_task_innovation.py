"""VAIXLNS Ω Memory–Task–Innovation kernel (proposal implementation).

Deterministic local primitives only: append-only hash-linked memory, retrieval,
dependency-aware task planning, and evidence-bounded innovation hypotheses.
No network, shell, repository mutation, or external side effect is performed.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

GENESIS = "0" * 64
ALLOWED_MEMORY_KINDS = {
    "decision", "constraint", "idea", "task_result", "source", "failure",
    "architecture", "preference", "open_question",
}
TASK_STATES = {"PROPOSED", "READY", "RUNNING", "BLOCKED", "DONE", "FAILED", "CANCELLED"}
TERMINAL_STATES = {"DONE", "FAILED", "CANCELLED"}
TRANSITIONS = {
    "PROPOSED": {"READY", "BLOCKED", "CANCELLED"},
    "READY": {"RUNNING", "BLOCKED", "CANCELLED"},
    "RUNNING": {"DONE", "FAILED", "BLOCKED"},
    "BLOCKED": {"READY", "CANCELLED"},
    "DONE": set(), "FAILED": {"READY", "CANCELLED"}, "CANCELLED": set(),
}
TOKEN_RE = re.compile(r"[\wΩ.-]+", re.UNICODE)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def tokens(text: str) -> set[str]:
    return {t.casefold() for t in TOKEN_RE.findall(text) if len(t) > 1}


class MemoryLedger:
    """Append-only JSONL ledger with a SHA-256 hash chain.

    Hash chaining detects edits/reordering when verified against a trusted head;
    it does not prove that a memory statement is true or protect against an
    attacker who can rewrite the whole file and trusted head.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        for number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at ledger line {number}") from exc
            rows.append(row)
        return rows

    def verify(self) -> dict[str, Any]:
        previous = GENESIS
        rows = self._read()
        ids: set[str] = set()
        for index, row in enumerate(rows, 1):
            claimed = row.get("record_hash")
            body = {k: v for k, v in row.items() if k != "record_hash"}
            expected = digest(canonical_json(body))
            if row.get("previous_hash") != previous:
                return {"valid": False, "records": len(rows), "bad_record": index, "reason": "previous_hash_mismatch"}
            if claimed != expected:
                return {"valid": False, "records": len(rows), "bad_record": index, "reason": "record_hash_mismatch"}
            if row.get("record_id") in ids:
                return {"valid": False, "records": len(rows), "bad_record": index, "reason": "duplicate_record_id"}
            ids.add(row.get("record_id"))
            previous = claimed
        return {"valid": True, "records": len(rows), "head_hash": previous}

    def append(self, *, kind: str, content: str, source_ref: str,
               state: str = "SPECIFIED", tags: Iterable[str] = (),
               related_ids: Iterable[str] = (), timestamp: str | None = None) -> dict[str, Any]:
        if kind not in ALLOWED_MEMORY_KINDS:
            raise ValueError(f"unsupported memory kind: {kind}")
        if not content.strip() or not source_ref.strip():
            raise ValueError("content and source_ref are required")
        status = self.verify()
        if not status["valid"]:
            raise ValueError(f"ledger integrity failure: {status}")
        rows = self._read()
        body = {
            "record_id": "MEM-" + str(uuid.uuid4()),
            "timestamp": timestamp or utc_now(),
            "kind": kind,
            "content": content.strip(),
            "source_ref": source_ref.strip(),
            "state": state,
            "tags": sorted(set(tags)),
            "related_ids": sorted(set(related_ids)),
            "previous_hash": status["head_hash"],
        }
        row = {**body, "record_hash": digest(canonical_json(body))}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Append one complete line; concurrent writers must be externally serialized.
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(row) + "\n")
        return row

    def retrieve(self, query: str, limit: int = 10,
                 kinds: Iterable[str] | None = None) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be positive")
        status = self.verify()
        if not status["valid"]:
            raise ValueError(f"ledger integrity failure: {status}")
        query_tokens = tokens(query)
        allowed = set(kinds) if kinds is not None else ALLOWED_MEMORY_KINDS
        ranked = []
        for row in self._read():
            if row.get("kind") not in allowed:
                continue
            searchable = " ".join([
                row.get("content", ""), row.get("kind", ""),
                " ".join(row.get("tags", [])), " ".join(row.get("related_ids", [])),
            ])
            record_tokens = tokens(searchable)
            overlap = len(query_tokens & record_tokens)
            if not overlap:
                continue
            # Simple deterministic ranking, not a semantic-relevance guarantee.
            score = overlap / max(1, len(query_tokens)) + 0.15 * overlap / max(1, len(record_tokens))
            ranked.append((score, row.get("timestamp", ""), row.get("record_id", ""), row))
        ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
        return [
            {**row, "retrieval_score": round(score, 6),
             "retrieval_method": "deterministic_lexical_overlap"}
            for score, _, _, row in ranked[:limit]
        ]


def plan_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate a task DAG and return a deterministic topological order."""
    by_id: dict[str, dict[str, Any]] = {}
    for task in tasks:
        task_id = task.get("task_id")
        if not task_id or task_id in by_id:
            raise ValueError(f"missing or duplicate task_id: {task_id}")
        if task.get("state", "PROPOSED") not in TASK_STATES:
            raise ValueError(f"invalid state for task {task_id}")
        if not task.get("goal", "").strip():
            raise ValueError(f"task {task_id} has no goal")
        by_id[task_id] = task
    for task_id, task in by_id.items():
        for dependency in task.get("depends_on", []):
            if dependency not in by_id:
                raise ValueError(f"task {task_id} references missing dependency {dependency}")
            if dependency == task_id:
                raise ValueError(f"task {task_id} depends on itself")

    indegree = {task_id: 0 for task_id in by_id}
    children = {task_id: [] for task_id in by_id}
    for task_id, task in by_id.items():
        for dependency in set(task.get("depends_on", [])):
            indegree[task_id] += 1
            children[dependency].append(task_id)
    ready = sorted(task_id for task_id, degree in indegree.items() if degree == 0)
    order = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    if len(order) != len(by_id):
        cyclic = sorted(task_id for task_id, degree in indegree.items() if degree)
        raise ValueError("dependency cycle detected: " + ", ".join(cyclic))

    completed = {task_id for task_id, task in by_id.items() if task.get("state") == "DONE"}
    schedule = []
    for task_id in order:
        task = by_id[task_id]
        deps = task.get("depends_on", [])
        state = task.get("state", "PROPOSED")
        if state not in TERMINAL_STATES and not all(dep in completed for dep in deps):
            derived_state = "BLOCKED"
        elif state == "PROPOSED":
            derived_state = "READY"
        else:
            derived_state = state
        schedule.append({
            "task_id": task_id, "goal": task["goal"],
            "depends_on": sorted(set(deps)), "state": derived_state,
            "required_evidence": task.get("required_evidence", []),
            "risk": task.get("risk", "UNASSESSED"),
        })
    return {"valid_dag": True, "order": order, "tasks": schedule}


def transition_task(task: dict[str, Any], new_state: str,
                    evidence: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    old = task.get("state", "PROPOSED")
    if new_state not in TRANSITIONS.get(old, set()):
        raise ValueError(f"illegal task transition: {old} -> {new_state}")
    updated = dict(task)
    if new_state == "DONE":
        required = task.get("required_evidence", [])
        evidence = evidence or []
        covered = {item.get("type") for item in evidence if item.get("source_ref") and item.get("digest")}
        missing = sorted(set(required) - covered)
        if missing:
            raise ValueError("cannot complete task; missing evidence types: " + ", ".join(missing))
        if not evidence:
            raise ValueError("cannot complete task without evidence records")
        updated["completion_evidence"] = evidence
    updated["state"] = new_state
    updated["state_changed_at"] = utc_now()
    return updated


def propose_innovations(goal: str, retrieved_memories: list[dict[str, Any]],
                        constraints: list[str] | None = None) -> list[dict[str, Any]]:
    """Create testable, explicitly unverified hypotheses from retrieved context."""
    if not goal.strip():
        raise ValueError("goal is required")
    constraints = constraints or []
    ideas = [
        ("INNO-001", "Evidence-linked memory retrieval",
         "Bind each retrieved design decision to its source, revision, confidence boundary, and related task; show contradictory memories instead of silently selecting one.",
         ["retrieval relevance benchmark", "source-link completeness", "contradiction recall"]),
        ("INNO-002", "Dependency-aware task execution",
         "Compile requested work into a dependency DAG with preconditions, required evidence, failure states, and explicit approval gates before side effects.",
         ["cycle rejection", "blocked dependency behavior", "unauthorized-effect denial"]),
        ("INNO-003", "Counterexample-driven engineering synthesis",
         "Generate multiple design candidates from relevant prior work, state assumptions, search for conflicts, and derive falsifiable acceptance tests before implementation.",
         ["independent test pass rate", "counterexample detection", "baseline comparison"]),
        ("INNO-004", "Memory-to-recovery replay",
         "Reconstruct a prior task's inputs, decisions, source revisions, failures, and evidence bundle so interrupted work can resume without inventing missing state.",
         ["replay consistency", "missing-evidence detection", "recovery time"]),
    ]
    context_ids = sorted({m.get("record_id", "") for m in retrieved_memories if m.get("record_id")})
    return [{
        "innovation_id": ident, "name": name, "state": "PROPOSAL",
        "goal": goal.strip(), "hypothesis": hypothesis,
        "derived_from_memory_ids": context_ids,
        "constraints": constraints,
        "acceptance_tests": tests,
        "evidence_state": "NO_VALIDATION_EVIDENCE",
        "promotion_authorized": False,
    } for ident, name, hypothesis, tests in ideas]


def snapshot(path: str | Path) -> dict[str, Any]:
    """Return safe status without reading or executing any external system."""
    ledger = MemoryLedger(path)
    return {"memory_ledger": ledger.verify(), "execution_mode": "PLAN_AND_LOCAL_MEMORY_ONLY",
            "external_effects_enabled": False, "verified_claims_created": 0}
