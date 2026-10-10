"""Deterministic scale simulation and obstacle-learning engine.

This module diagnoses growth constraints from observed repository metadata. It
never mutates canonical files, starts workers, calls model providers, or claims
production execution. Findings are recommendations until separately verified.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable


SCHEMA_VERSION = "1.0.0"
SUPPORTED_SCENARIOS = ("all", "growth", "federation", "agent-capacity", "knowledge", "security")


def _digest(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Finding:
    finding_id: str
    severity: str
    area: str
    obstacle: str
    observation: str
    recommended_action: str
    promotion_gate: str


@dataclass(frozen=True)
class ScaleRun:
    schema_version: str
    scenario: str
    outcome: str
    scale_readiness_score: int
    observed_facts: dict[str, Any]
    findings: tuple[Finding, ...]
    learning_rules: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    trace_hash: str
    epistemic_state: str = "SPECIFIED"


class ScaleEngine:
    """Build deterministic, evidence-labelled scale diagnoses from local facts."""

    def simulate(self, scenario: str, facts: dict[str, Any]) -> ScaleRun:
        key = scenario.strip().casefold()
        if key not in SUPPORTED_SCENARIOS:
            raise ValueError("Unsupported scenario. Choose: " + ", ".join(SUPPORTED_SCENARIOS))
        normalized = {
            "agent_count": _bounded_int(facts.get("agent_count"), 0, 100000),
            "system_count": _bounded_int(facts.get("system_count"), 0, 10000),
            "connection_count": _bounded_int(facts.get("connection_count"), 0, 100000),
            "verified_connections": _bounded_int(facts.get("verified_connections"), 0, 100000),
            "authenticated_connections": _bounded_int(facts.get("authenticated_connections"), 0, 100000),
            "genome_available": facts.get("genome_available") is True,
            "index_available": facts.get("index_available") is True,
            "runtime_configured": facts.get("runtime_configured") is True,
            "provider_configured": facts.get("provider_configured") is True,
            "allowlisted_commands": facts.get("allowlisted_commands") is True,
            "durable_learning_store": facts.get("durable_learning_store") is True,
        }
        findings: list[Finding] = []

        def add(code: str, severity: str, area: str, obstacle: str, observation: str,
                action: str, gate: str) -> None:
            findings.append(Finding(code, severity, area, obstacle, observation, action, gate))

        scenarios: Iterable[str] = ("growth", "federation", "agent-capacity", "knowledge", "security") if key == "all" else (key,)
        for current in scenarios:
            if current == "growth":
                if normalized["agent_count"] < 5:
                    add("SCALE-GROWTH-001", "WARNING", "growth", "Low registered-agent diversity",
                        f"Only {normalized['agent_count']} agent definitions are visible to this simulation.",
                        "Expand roles only when a measured task gap cannot be covered by existing agents.",
                        "New role has a unique capability contract and passing tests.")
                else:
                    add("SCALE-GROWTH-002", "OBSERVATION", "growth", "Agent count is not execution throughput",
                        f"{normalized['agent_count']} definitions are registered; this does not measure parallel workers or throughput.",
                        "Benchmark completed tasks, queue wait, failure rate, and cost before increasing concurrency.",
                        "Repeatable benchmark against a documented baseline.")
                if normalized["system_count"] > 1 and normalized["verified_connections"] < normalized["system_count"] - 1:
                    add("SCALE-GROWTH-003", "BLOCKER", "growth", "Federation connectivity lags declared system count",
                        f"{normalized['system_count']} systems are inventoried but only {normalized['verified_connections']} connections are marked verified.",
                        "Prioritize identity, authentication, contract, and health checks for one edge at a time.",
                        "Connection passes authenticated end-to-end contract tests.")
            elif current == "federation":
                if normalized["connection_count"] == 0:
                    add("SCALE-FED-001", "BLOCKER", "federation", "No connection records are available",
                        "The simulator received no declared federation edges.",
                        "Populate the federation index from source-backed contracts; do not infer live links.",
                        "Every edge has endpoints, contract version, evidence references, and a probe result.")
                elif normalized["verified_connections"] < normalized["connection_count"]:
                    add("SCALE-FED-002", "BLOCKER", "federation", "Unverified federation edges",
                        f"{normalized['verified_connections']} of {normalized['connection_count']} declared edges are verified.",
                        "Probe each edge for authentication, schema compatibility, timeout behavior, and failure isolation.",
                        "Authenticated contract tests and captured probe evidence pass.")
                if normalized["authenticated_connections"] < normalized["verified_connections"]:
                    add("SCALE-FED-003", "BLOCKER", "federation", "Verification without authentication",
                        "At least one edge is marked verified without authenticated transport.",
                        "Require identity-bound authentication and replay protection before exchanging trusted payloads.",
                        "Authenticated handshake and negative-authentication tests pass.")
            elif current == "agent-capacity":
                if normalized["agent_count"] and not normalized["provider_configured"]:
                    add("SCALE-AGENT-001", "BLOCKER", "agent-capacity", "Registered agents have no configured model provider",
                        "Registry definitions are available, but no model-provider connection is confirmed.",
                        "Add a provider adapter with bounded credentials, timeouts, quotas, redaction, and offline tests.",
                        "Adapter contract tests pass; credentials are never stored in the repository.")
                if not normalized["runtime_configured"]:
                    add("SCALE-AGENT-002", "BLOCKER", "agent-capacity", "VX runtime is not connected",
                        "No configured VX runtime endpoint is available to this simulation.",
                        "Connect through the approved runtime adapter and preserve VX admission controls.",
                        "Authenticated health check plus a harmless end-to-end execution receipt.")
                add("SCALE-AGENT-003", "WARNING", "agent-capacity", "Concurrency and queue capacity are unmeasured",
                    "No throughput, queue latency, token cost, or retry data was supplied.",
                    "Run a bounded load test and establish concurrency, budget, back-pressure, and circuit-breaker limits.",
                    "Load test meets latency, cost, and failure-rate budgets.")
            elif current == "knowledge":
                if not normalized["genome_available"]:
                    add("SCALE-KNOW-001", "BLOCKER", "knowledge", "Canonical genome unavailable",
                        "The canonical project genome could not be confirmed in the supplied facts.",
                        "Restore or resolve the canonical genome before proposing canonical knowledge changes.",
                        "Canonical path and digest validation pass.")
                if not normalized["index_available"]:
                    add("SCALE-KNOW-002", "BLOCKER", "knowledge", "Master index unavailable",
                        "The Ω.000 master index could not be confirmed in the supplied facts.",
                        "Restore the canonical index and validate all referenced identities and evidence paths.",
                        "Index schema, identity uniqueness, and reference-integrity tests pass.")
                if not normalized["durable_learning_store"]:
                    add("SCALE-KNOW-003", "WARNING", "knowledge", "Simulation learning is not durable",
                        "This run has no confirmed durable store for cross-session findings.",
                        "Persist proposed findings in a versioned, append-only candidate ledger; require review before canonical admission.",
                        "Restart/replay test preserves provenance and hash-chain integrity.")
            elif current == "security":
                if not normalized["allowlisted_commands"]:
                    add("SCALE-SEC-001", "BLOCKER", "security", "Command allow-list is not confirmed",
                        "The supplied facts do not establish a restricted command surface.",
                        "Fail closed on unknown commands; never pass raw user text to a shell.",
                        "Negative tests prove shell metacharacters and unknown commands cannot execute.")
                else:
                    add("SCALE-SEC-002", "OBSERVATION", "security", "Command allow-list is declared",
                        "The local command engine reports a bounded command surface; this is not a full security audit.",
                        "Retain origin checks, loopback binding, path containment, output redaction, and dependency review.",
                        "Security regression tests and a reviewed threat model pass.")

        severity_penalty = {"BLOCKER": 18, "WARNING": 7, "OBSERVATION": 2, "OBSERVATION_UNUSED": 0}
        score = max(0, min(100, 100 - sum(severity_penalty.get(item.severity, 0) for item in findings)))
        blockers = sum(1 for item in findings if item.severity == "BLOCKER")
        warnings = sum(1 for item in findings if item.severity == "WARNING")
        outcome = "BLOCKED" if blockers else ("CAUTION" if warnings else "READY_FOR_NEXT_MEASURED_STEP")
        evidence_refs = tuple(sorted(str(item) for item in facts.get("evidence_refs", []) if isinstance(item, str)))
        payload = {
            "schema_version": SCHEMA_VERSION,
            "scenario": key,
            "outcome": outcome,
            "scale_readiness_score": score,
            "observed_facts": normalized,
            "findings": [asdict(item) for item in findings],
            "learning_rules": [
                "A declared capability is not proof of a running worker.",
                "A simulation finding becomes reusable knowledge only after evidence and review.",
                "No automatic canonical promotion or production mutation is allowed.",
                "A scale score is a heuristic diagnosis, not a measured production SLO.",
            ],
            "evidence_refs": list(evidence_refs),
            "epistemic_state": "SPECIFIED",
        }
        return ScaleRun(
            schema_version=SCHEMA_VERSION,
            scenario=key,
            outcome=outcome,
            scale_readiness_score=score,
            observed_facts=normalized,
            findings=tuple(findings),
            learning_rules=tuple(payload["learning_rules"]),
            evidence_refs=evidence_refs,
            trace_hash=_digest(payload),
        )


def _bounded_int(value: Any, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        return minimum
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return minimum
    return max(minimum, min(maximum, parsed))
