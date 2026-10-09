#!/usr/bin/env python3
"""Build a deterministic, evidence-gated innovation research network manifest.

This planner aggregates existing innovation records into role-specific work packets.
It does not call external models, start servers, or claim that agents are live.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "vaixlns.innovation-network.v1"
SYSTEMS = ("VAIXLNS", "VLNS", "VX", "NEXNET")
ROLE_LANES = (
    ("SOURCE_DISCOVERY", "Find primary sources, immutable revisions, and external prior art."),
    ("HISTORICAL_RECOVERY", "Recover prior formulations and preserve original identifiers and lineage."),
    ("NOVELTY_LINEAGE", "Detect aliases, duplicates, derivatives, supersession, and related records."),
    ("COUNTEREVIDENCE", "Search for refutations, failure cases, competing explanations, and limits."),
    ("ARCHITECTURE_SYNTHESIS", "Produce at least two competing designs with explicit trade-offs."),
    ("ENGINEERING_CONTRACT", "Specify invariants, interfaces, state transitions, dependencies, and failure behavior."),
    ("SECURITY_ADVERSARY", "Test privacy, authority boundaries, attack surface, and misuse cases."),
    ("TEST_REPLAY", "Create deterministic tests, reproducible experiments, and replay instructions."),
    ("PROOF_INTEGRITY", "Check provenance, hashes, evidence freshness, and whether claims exceed evidence."),
    ("GOVERNANCE_REVIEW", "Prepare an evidence-backed recommendation; never self-promote or directly adopt."),
)
STATUS_PRIORITY = {
    "CONFLICT": 100, "MISSING": 95, "SOURCE-ASSERTED": 90, "PROPOSAL": 85,
    "SPECIFIED": 75, "PARTIAL": 70, "RECOVERED": 60, "IMPLEMENTED": 45,
    "VERIFIED": 25, "CANONICAL": 20, "QUARANTINED": 80,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def stable_id(prefix: str, *parts: str) -> str:
    raw = "\\x1f".join(normalize(part) for part in parts)
    return prefix + "-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16].upper()


def load_items(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_items = source.get("items", source.get("records", []))
    if not isinstance(raw_items, list):
        raise ValueError("input must contain an 'items' or 'records' array")
    normalized = []
    for raw in raw_items:
        if not isinstance(raw, Mapping):
            continue
        name = str(raw.get("name") or raw.get("canonical_id") or "").strip()
        family = str(raw.get("family") or "UNCLASSIFIED").strip()
        owner = str(raw.get("owner") or "UNASSIGNED").strip()
        state = str(raw.get("state") or raw.get("status") or "SOURCE-ASSERTED").strip().upper()
        if not name:
            continue
        original = dict(raw)
        item_id = str(raw.get("canonical_id") or stable_id("INN", name, family, owner))
        normalized.append({
            "innovation_id": item_id,
            "name": name,
            "family": family,
            "owner": owner,
            "state": state,
            "source_repositories": sorted(set(str(x) for x in raw.get("source_repositories", []) if x)),
            "implementation_repositories": sorted(set(str(x) for x in raw.get("implementation_repositories", []) if x)),
            "evidence_class": str((raw.get("evidence") or {}).get("class", state)) if isinstance(raw.get("evidence", {}), Mapping) else state,
            "source_record_sha256": digest(original),
            "authority": "NOT_GRANTED",
        })
    return sorted(normalized, key=lambda x: (normalize(x["owner"]), normalize(x["family"]), normalize(x["name"]), x["innovation_id"]))


def build_network(source: Mapping[str, Any]) -> dict[str, Any]:
    items = load_items(source)
    packets: list[dict[str, Any]] = []
    for item in items:
        priority = STATUS_PRIORITY.get(item["state"], 80)
        tasks = []
        for index, (role, objective) in enumerate(ROLE_LANES, start=1):
            task_id = stable_id("TASK", item["innovation_id"], role)
            tasks.append({
                "task_id": task_id,
                "lane": role,
                "objective": objective,
                "input_refs": [item["innovation_id"], item["source_record_sha256"]],
                "required_outputs": ["findings.json", "source_refs.json", "counterevidence.json", "decision.json"],
                "dispatch_state": "PLANNED_NOT_DISPATCHED",
                "assigned_systems": list(SYSTEMS),
                "sequence": index,
                "authority_scope": "RESEARCH_AND_RECOMMENDATION_ONLY",
                "acceptance_rule": "Every material claim must cite a source or be explicitly marked as inference/unknown.",
            })
        packets.append({
            **item,
            "priority_score": priority,
            "work_packet_id": stable_id("WP", item["innovation_id"]),
            "research_state": "QUEUED",
            "research_lanes": tasks,
            "promotion_gate": {
                "verified_requires": ["reproducible_test_or_experiment", "source_provenance", "counterevidence_review"],
                "canonical_requires": ["verified_evidence", "explicit_authority_decision"],
                "self_promotion_allowed": False,
            },
        })
    core = {
        "schema": SCHEMA,
        "purpose": "Federated, evidence-first research planning across the VAIXLNS system family.",
        "input_sha256": digest(source),
        "systems": [
            {"system_id": system, "role": role, "connectivity": "NOT_ASSERTED"}
            for system, role in (
                ("VAIXLNS", "CANONICAL_GOVERNANCE_AND_REGISTRY"),
                ("VLNS", "MODEL_AND_SEMANTIC_ACTIVATION_BOUNDARY"),
                ("VX", "SANDBOX_EXECUTION_SIMULATION_AND_REPLAY"),
                ("NEXNET", "DISCOVERY_RESEARCH_AND_SYNTHESIS"),
            )
        ],
        "dispatch_contract": {
            "transport": "PROVIDER_NEUTRAL",
            "server_state": "NOT_CONNECTED_OR_DISPATCHED_BY_THIS_TOOL",
            "idempotency_key": "task_id",
            "retry_policy": "RETRY_ONLY_WITH_SAME_TASK_ID_AND_PINNED_INPUTS",
            "privacy": "Do not transmit secrets, credentials, private source contents, or unauthorized repository data.",
            "result_acceptance": "Validate schema, source identity, content hashes, counterevidence, and authority separation before merge.",
        },
        "summary": {
            "innovation_count": len(packets),
            "task_count": sum(len(packet["research_lanes"]) for packet in packets),
            "queued_count": len(packets),
            "dispatched_count": 0,
            "verified_count": sum(1 for packet in packets if packet["state"] == "VERIFIED"),
            "system_connectivity_verified": False,
        },
        "work_packets": packets,
    }
    return {**core, "network_sha256": digest(core)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Innovation federation JSON")
    parser.add_argument("--output", default="innovation-network.json", help="Output manifest path")
    args = parser.parse_args()
    try:
        source = json.loads(Path(args.input).read_text(encoding="utf-8"))
        network = build_network(source)
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(network, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"output": str(target), "innovation_count": network["summary"]["innovation_count"],
                      "task_count": network["summary"]["task_count"], "network_sha256": network["network_sha256"],
                      "dispatch_state": "NOT_DISPATCHED"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
