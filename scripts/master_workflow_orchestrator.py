"""Deterministic, evidence-gated planner for the VAIXLNS master workflow.

This module composes existing index, agent, and repository-factory registries into a
reviewable execution plan. It does not call tools, mutate repositories, deploy systems,
or authorize production execution. Those actions remain behind separate admission gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

STAGES: tuple[dict[str, Any], ...] = (
    {"key": "SOURCE_INTAKE", "needs": ("source", "archive", "repository"), "gate": "SOURCE_PINNED"},
    {"key": "INDEX_RECONCILIATION", "needs": ("index", "identity", "lineage"), "gate": "IDENTITY_AND_LINEAGE_RECONCILED"},
    {"key": "ATOMIC_DECOMPOSITION", "needs": ("claim", "capability", "schema"), "gate": "ATOMIC_RECORDS_TRACEABLE"},
    {"key": "NOVELTY_AND_GAP_ANALYSIS", "needs": ("novelty", "capability", "research"), "gate": "DUPLICATE_AND_GAP_REPORT_PRESENT"},
    {"key": "ARCHITECTURE_SYNTHESIS", "needs": ("architecture", "design", "contract"), "gate": "CANDIDATE_DESIGN_REVIEWABLE"},
    {"key": "IMPLEMENTATION_PLAN", "needs": ("implementation", "dependency", "rollback"), "gate": "BOUNDED_CHANGE_PLAN_PRESENT"},
    {"key": "SECURITY_AND_AUTHORITY_REVIEW", "needs": ("security", "authority", "adversarial"), "gate": "AUTHORITY_AND_BLAST_RADIUS_REVIEWED"},
    {"key": "SANDBOX_BUILD", "needs": ("build", "implementation", "sandbox"), "gate": "ISOLATED_BUILD_EVIDENCE_PRESENT"},
    {"key": "TEST_REPLAY_AND_RECOVERY", "needs": ("test", "verification", "replay", "recovery"), "gate": "DETERMINISTIC_TEST_AND_RECOVERY_EVIDENCE"},
    {"key": "PROOF_AND_PROVENANCE", "needs": ("proof", "evidence", "provenance"), "gate": "FRESH_PROOF_PACKAGE_COMPLETE"},
    {"key": "GOVERNANCE_ADMISSION", "needs": ("governance", "admission", "authority"), "gate": "SEPARATE_AUTHORIZED_DECISION"},
    {"key": "COMMIT_OR_HOLD", "needs": ("commit", "lifecycle", "registry"), "gate": "COMMIT_ONLY_AFTER_ALL_PRIOR_GATES"},
)

ALIASES = {
    "source": {"source", "search", "archive", "repository", "fetch_file", "web_search", "github_search"},
    "archive": {"archive", "recovery", "index", "repository"},
    "index": {"index", "registry", "memory"},
    "identity": {"identity", "lineage", "naming"},
    "lineage": {"lineage", "alias", "supersession", "identity"},
    "claim": {"claim", "evidence", "provenance"},
    "capability": {"capability", "genome", "gap"},
    "schema": {"schema", "contract", "registry"},
    "novelty": {"novelty", "duplicate", "innovation", "research"},
    "research": {"research", "discovery", "search"},
    "architecture": {"architecture", "topology", "design"},
    "design": {"design", "synthesis", "architecture"},
    "contract": {"contract", "interface", "schema"},
    "implementation": {"implementation", "engineering", "build", "code"},
    "dependency": {"dependency", "graph", "integration"},
    "rollback": {"rollback", "recovery", "replay"},
    "security": {"security", "adversarial", "threat"},
    "authority": {"authority", "governance", "policy"},
    "adversarial": {"adversarial", "security", "counterevidence"},
    "build": {"build", "implementation", "engineering"},
    "sandbox": {"sandbox", "isolation", "test"},
    "test": {"test", "verification", "replay"},
    "verification": {"verification", "test", "proof"},
    "replay": {"replay", "determinism", "recovery"},
    "recovery": {"recovery", "archive", "replay"},
    "proof": {"proof", "assurance", "verification"},
    "evidence": {"evidence", "provenance", "source"},
    "provenance": {"provenance", "lineage", "evidence"},
    "governance": {"governance", "authority", "policy"},
    "admission": {"admission", "governance", "verification"},
    "commit": {"commit", "finality", "governance"},
    "lifecycle": {"lifecycle", "registry", "state"},
    "registry": {"registry", "index", "repository"},
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _id(prefix: str, value: Any) -> str:
    return f"{prefix}-{hashlib.sha256(_canonical(value).encode('utf-8')).hexdigest()[:20]}"


def _load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _records(index: Mapping[str, Any]) -> list[dict[str, Any]]:
    records = index.get("records")
    if not isinstance(records, list):
        raise ValueError("MASTER_INDEX_RECORDS_MUST_BE_A_LIST")
    if not records:
        raise ValueError("MASTER_INDEX_HAS_NO_RECORDS")
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record["id"].strip():
            raise ValueError("EVERY_INDEX_RECORD_REQUIRES_A_NONEMPTY_ID")
        if record["id"] in seen:
            raise ValueError(f"DUPLICATE_MASTER_INDEX_ID:{record['id']}")
        seen.add(record["id"])
    return records


def _agent_capabilities(agent: Mapping[str, Any]) -> set[str]:
    raw = agent.get("capabilities", [])
    if isinstance(raw, str):
        raw = [raw]
    return {str(item).strip().lower().replace(" ", "_") for item in raw if str(item).strip()}


def _eligible_agents(agents: Sequence[Mapping[str, Any]], needs: Sequence[str]) -> list[str]:
    eligible: list[str] = []
    for agent in agents:
        agent_id = agent.get("agent_id") or agent.get("id")
        if not isinstance(agent_id, str) or not agent_id.strip():
            continue
        if agent.get("may_promote") is True or agent.get("can_promote") is True:
            continue
        caps = _agent_capabilities(agent)
        if any(
            cap in caps or any(alias in cap for alias in ALIASES.get(need, {need}))
            for need in needs for cap in caps
        ):
            eligible.append(agent_id)
    return sorted(set(eligible))


def build_plan(
    index: Mapping[str, Any],
    agent_registry: Mapping[str, Any],
    factory_manifest: Mapping[str, Any],
    request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic plan. A plan is never execution authorization."""
    request = dict(request or {})
    records = _records(index)
    agents_raw = agent_registry.get("agents", [])
    if not isinstance(agents_raw, list):
        raise ValueError("AGENT_REGISTRY_AGENTS_MUST_BE_A_LIST")
    agents = [agent for agent in agents_raw if isinstance(agent, dict)]
    repo_entries = factory_manifest.get("repositories", [])
    if not isinstance(repo_entries, list):
        raise ValueError("FACTORY_MANIFEST_REPOSITORIES_MUST_BE_A_LIST")

    unresolved = [
        str(record.get("id")) for record in records
        if str(record.get("epistemic_state", "")).upper() in {"CONFLICT", "MISSING", "UNVERIFIED"}
        or str(record.get("lifecycle_state", "")).upper() == "QUARANTINED"
    ]
    tasks: list[dict[str, Any]] = []
    prior_task_id: str | None = None
    for ordinal, stage in enumerate(STAGES, start=1):
        task_material = {
            "stage": stage["key"],
            "index_id": index.get("index_id", "Ω.000"),
            "request": request,
            "record_ids": sorted(str(record["id"]) for record in records),
            "ordinal": ordinal,
        }
        task_id = _id("VXTASK", task_material)
        eligible = _eligible_agents(agents, stage["needs"])
        blockers: list[str] = []
        if stage["key"] == "SOURCE_INTAKE" and not index.get("index_id"):
            blockers.append("MASTER_INDEX_ID_MISSING")
        if stage["key"] == "INDEX_RECONCILIATION" and unresolved:
            blockers.append("UNRESOLVED_INDEX_RECORDS_REQUIRE_RECONCILIATION")
        if stage["key"] in {"SANDBOX_BUILD", "TEST_REPLAY_AND_RECOVERY", "PROOF_AND_PROVENANCE", "GOVERNANCE_ADMISSION", "COMMIT_OR_HOLD"} and not eligible:
            blockers.append("NO_REGISTERED_AGENT_MATCHES_STAGE_CAPABILITIES")
        tasks.append({
            "task_id": task_id,
            "ordinal": ordinal,
            "stage": stage["key"],
            "status": "BLOCKED" if blockers else "PLANNED",
            "depends_on": [prior_task_id] if prior_task_id else [],
            "required_gate": stage["gate"],
            "required_capabilities": list(stage["needs"]),
            "eligible_agent_ids": eligible,
            "input_index_id": index.get("index_id", "Ω.000"),
            "input_record_count": len(records),
            "factory_candidate_count": sum(
                1 for repo in repo_entries
                if isinstance(repo, dict) and repo.get("auto_create") is True
            ),
            "blockers": blockers,
            "outputs_expected": [f"{stage['key'].lower()}_report", "evidence_refs", "status"],
            "authority_scope": "PLAN_ONLY",
            "execution_authorization": False,
            "canonical_promotion_allowed": False,
        })
        prior_task_id = task_id

    blocked = any(task["status"] == "BLOCKED" for task in tasks)
    material = {
        "index_id": index.get("index_id", "Ω.000"),
        "record_ids": sorted(str(record["id"]) for record in records),
        "request": request,
        "tasks": tasks,
    }
    return {
        "schema": "vaixlns.master-workflow-plan.v1",
        "plan_id": _id("VXPLAN", material),
        "status": "HOLD_FOR_RECONCILIATION" if blocked else "READY_FOR_REVIEW",
        "source_index_id": index.get("index_id", "Ω.000"),
        "source_record_count": len(records),
        "source_record_ids": sorted(str(record["id"]) for record in records),
        "request": request,
        "task_count": len(tasks),
        "blocked_task_count": sum(task["status"] == "BLOCKED" for task in tasks),
        "execution_authorization": False,
        "canonical_promotion_allowed": False,
        "invariants": [
            "NO_SOURCE_EVIDENCE_NO_VERIFIED",
            "NO_AGENT_SELF_PROMOTION",
            "NO_PRODUCTION_MUTATION_FROM_PLAN",
            "NO_DESTRUCTIVE_MERGE_ON_NAME_SIMILARITY",
            "NO_COMMIT_BEFORE_INDEPENDENT_VERIFICATION_AND_AUTHORIZED_GOVERNANCE",
            "PRESERVE_LEGACY_IDS_AND_LINEAGE",
        ],
        "tasks": tasks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", required=True, help="Path to Ω.000 master-index JSON")
    parser.add_argument("--agents", required=True, help="Path to agent registry JSON")
    parser.add_argument("--factory", required=True, help="Path to repository factory manifest JSON")
    parser.add_argument("--request", default="", help="Optional mission/request label")
    parser.add_argument("--output", default="-", help="Output JSON path or '-' for stdout")
    args = parser.parse_args()

    plan = build_plan(
        _load_json(args.index),
        _load_json(args.agents),
        _load_json(args.factory),
        {"mission": args.request} if args.request else {},
    )
    rendered = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output == "-":
        print(rendered, end="")
    else:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
