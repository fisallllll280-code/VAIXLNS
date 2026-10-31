"""End-to-end engineering cycle: recover memory -> propose innovations -> plan work.

This module composes the deterministic MTIK reference kernel. It does not
perform a real literature search or claim novelty; candidates stay PROPOSAL
until prior-art review and reproducible tests exist.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable, Mapping, Sequence

from scripts.omega_memory_task_kernel import (
    KernelError,
    build_task_plan,
    digest_json,
    recover_context,
)


def _terms(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9_.:/+-]*", text.casefold()) if len(t) > 1}


def _validate_gap(gap: Mapping[str, Any]) -> None:
    for key in ("gap_id", "title", "description", "domain", "priority"):
        if not isinstance(gap.get(key), str) or not gap[key].strip():
            raise KernelError(f"gap.{key} must be a non-empty string")
    if gap["priority"] not in {"P0", "P1", "P2", "P3"}:
        raise KernelError(f"gap {gap['gap_id']}: priority must be P0-P3")
    criteria = gap.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria or any(
        not isinstance(item, str) or not item.strip() for item in criteria
    ):
        raise KernelError(f"gap {gap['gap_id']}: acceptance_criteria must be non-empty")
    for key in ("required_capabilities", "depends_on_gap_ids"):
        value = gap.get(key, [])
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            raise KernelError(f"gap {gap['gap_id']}: {key} must be an array of non-empty strings")


def derive_innovation_candidates(
    gaps: Sequence[Mapping[str, Any]],
    recovered_context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Turn explicit engineering gaps into bounded, source-linked hypotheses."""
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    memories = list(recovered_context.get("matches", []))
    for gap in gaps:
        _validate_gap(gap)
        gap_id = gap["gap_id"]
        if gap_id in seen:
            raise KernelError(f"duplicate gap_id: {gap_id}")
        seen.add(gap_id)
        gap_terms = _terms(" ".join([
            gap["title"], gap["description"], gap["domain"], *gap["acceptance_criteria"]
        ]))
        related: list[dict[str, Any]] = []
        for memory in memories:
            mem_terms = _terms(str(memory.get("subject", "")) + " " + str(memory.get("summary", "")))
            overlap = sorted(gap_terms & mem_terms)
            if overlap:
                related.append({
                    "record_id": memory["record_id"],
                    "record_hash": memory.get("record_hash"),
                    "repository": memory.get("repository"),
                    "revision": memory.get("revision"),
                    "path": memory.get("path"),
                    "matched_terms": overlap,
                })
        related.sort(key=lambda item: (-len(item["matched_terms"]), item["record_id"]))
        material = {
            "gap_id": gap_id,
            "title": " ".join(gap["title"].split()),
            "description": " ".join(gap["description"].split()),
            "domain": gap["domain"],
            "acceptance_criteria": gap["acceptance_criteria"],
        }
        candidate_id = "INNOV-" + hashlib.sha256(
            digest_json(material).encode("utf-8")
        ).hexdigest()[:16].upper()
        candidates.append({
            "candidate_id": candidate_id,
            "gap_id": gap_id,
            "title": gap["title"],
            "domain": gap["domain"],
            "hypothesis": gap["description"],
            "proposal_state": "PROPOSAL",
            "novelty_state": "UNASSESSED",
            "originality_claim": "NOT_CLAIMED",
            "prior_art_review_required": True,
            "related_memory": related,
            "source_memory_ids": [item["record_id"] for item in related],
            "acceptance_criteria": list(gap["acceptance_criteria"]),
            "known_unknowns": [
                "prior-art search has not been completed by this deterministic synthesizer",
                "candidate usefulness and engineering performance have not been measured",
            ],
            "recommended_next_step": (
                "search and compare prior art, attach source receipts, then design a reproducible test"
            ),
            "candidate_digest": digest_json({
                "candidate_id": candidate_id,
                "gap": material,
                "related_memory": related,
                "novelty_state": "UNASSESSED",
            }),
        })
    candidates.sort(key=lambda item: (item["gap_id"], item["candidate_id"]))
    return candidates


def build_engineering_cycle(
    *,
    goal: str,
    memory_records: Sequence[Mapping[str, Any]],
    gaps: Sequence[Mapping[str, Any]],
    available_capabilities: Iterable[str] = (),
    memory_limit: int = 8,
    verify_memory_chain: bool = True,
) -> dict[str, Any]:
    """Compose memory recovery, innovation candidates, and an actionable task DAG."""
    recovered = recover_context(
        memory_records, goal, limit=memory_limit, verify_chain=verify_memory_chain
    )
    candidates = derive_innovation_candidates(gaps, recovered)
    gap_to_task = {
        candidate["gap_id"]: "TASK-" + candidate["candidate_id"].removeprefix("INNOV-")
        for candidate in candidates
    }
    known_gaps = {candidate["gap_id"] for candidate in candidates}
    task_specs: list[dict[str, Any]] = []
    for gap in gaps:
        candidate = next(item for item in candidates if item["gap_id"] == gap["gap_id"])
        unknown_dependencies = sorted(set(gap.get("depends_on_gap_ids", [])) - known_gaps)
        if unknown_dependencies:
            raise KernelError(
                f"gap {gap['gap_id']} has missing gap dependencies: {unknown_dependencies}"
            )
        dependency_tasks = [gap_to_task[item] for item in gap.get("depends_on_gap_ids", [])]
        task_specs.append({
            "task_id": gap_to_task[gap["gap_id"]],
            "title": "Research and validate: " + gap["title"],
            "description": (
                gap["description"] + " Do not claim novelty before prior-art review. "
                "Record PASS, FAIL, or INCONCLUSIVE with source-bound evidence."
            ),
            "action": "research_innovation_candidate",
            "action_type": "READ_ONLY",
            "priority": gap["priority"],
            "depends_on": dependency_tasks,
            "required_capabilities": list(gap.get("required_capabilities", ["research.read"])),
            "source_memory_ids": candidate["source_memory_ids"],
            "acceptance_criteria": list(gap["acceptance_criteria"]) + [
                "Prior art is reviewed or explicitly marked INCONCLUSIVE",
                "Evidence records immutable sources and reproducible test conditions",
            ],
            "input": {
                "candidate_id": candidate["candidate_id"],
                "gap_id": candidate["gap_id"],
                "related_memory_ids": candidate["source_memory_ids"],
            },
        })
    recovered_ids = [item["record_id"] for item in recovered["matches"]]
    plan = build_task_plan(
        goal,
        task_specs,
        available_capabilities=available_capabilities,
        recovered_memory_ids=recovered_ids,
    ) if task_specs else None
    payload = {
        "schema_version": "1.0.0",
        "kernel": "VAIXLNS.OMEGA.MEMORY_TASK_INNOVATION.001",
        "goal": goal,
        "memory_recovery": recovered,
        "innovation_candidates": candidates,
        "task_plan": plan,
        "canonical_mutation": "DISABLED",
        "external_effects": "DISABLED",
        "verified_promotion": "NOT_PERFORMED",
        "state": "PLANNED",
    }
    payload["cycle_digest"] = digest_json(payload)
    return payload
