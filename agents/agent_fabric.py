"""Deterministic, governed multi-agent fabric for VAIXLNS."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import hashlib
import hmac
import json
from typing import Any, Mapping

from patterns.vaixl_pattern_factory import DIRECTIONS, PatternFactory


DEFAULT_HANDOFF_CHAIN = (
    "AG-001", "AG-002", "AG-003", "AG-004", "AG-005", "AG-006", "AG-007",
    "AG-008", "AG-009", "AG-010", "AG-013", "AG-011", "AG-012",
)


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    canonical_name: str
    role: str
    family: str
    capabilities: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    authority_scope: tuple[str, ...]
    handoff_targets: tuple[str, ...] = ()
    status: str = "ACTIVE"
    version: str = "1.0.0"


CORE_AGENT_SPECS = (
    AgentSpec("AG-001", "Index Archaeologist", "recovery", "knowledge", ("index-recovery", "provenance-recovery"), ("index.read",), ("read.index",), ("AG-002",)),
    AgentSpec("AG-002", "Identity & Lineage Resolver", "identity", "knowledge", ("identity-resolution", "lineage-resolution"), ("registry.read",), ("read.registry",), ("AG-003",)),
    AgentSpec("AG-003", "Capability Analyst", "capability", "architecture", ("capability-analysis", "gap-detection"), ("registry.read",), ("read.registry",), ("AG-004",)),
    AgentSpec("AG-004", "Architecture Analyst", "architecture", "architecture", ("architecture-analysis", "genome-comparison"), ("registry.read", "pattern.read"), ("read.registry", "pattern.select"), ("AG-005",)),
    AgentSpec("AG-005", "Research / Evidence Agent", "research", "evidence", ("research", "evidence-acquisition"), ("web.search", "repo.read"), ("read.external", "read.repository"), ("AG-006",)),
    AgentSpec("AG-006", "Contradiction & Reality Auditor", "audit", "assurance", ("contradiction-audit", "reality-audit"), ("repo.read", "runtime.observe"), ("read.repository", "observe.runtime"), ("AG-007",)),
    AgentSpec("AG-007", "Innovation Synthesizer", "innovation", "innovation", ("innovation-synthesis", "counterfactual-generation"), ("pattern.read",), ("pattern.select",), ("AG-008",)),
    AgentSpec("AG-008", "Architecture Search / Forge Agent", "forge", "architecture", ("architecture-search", "system-generation"), ("pattern.read", "code.generate"), ("pattern.select", "build.generate"), ("AG-009",)),
    AgentSpec("AG-009", "Adversarial / Security Agent", "security", "assurance", ("security-analysis", "adversarial-verification"), ("repo.read", "security.scan"), ("read.repository", "security.verify"), ("AG-010",)),
    AgentSpec("AG-010", "Verification & Proof Agent", "verification", "assurance", ("verification", "proof"), ("repo.read", "test.run"), ("read.repository", "verify.execute"), ("AG-013",)),
    AgentSpec("AG-011", "Runtime / Integration Agent", "runtime", "execution", ("runtime-integration", "governed-execution"), ("vx.execute", "event.write"), ("runtime.execute", "event.commit"), ("AG-012",)),
    AgentSpec("AG-012", "Operations / Recovery Agent", "operations", "execution", ("operations", "recovery"), ("runtime.observe", "recovery.execute"), ("observe.runtime", "recover.execute"), ("AG-001",)),
    AgentSpec("AG-013", "Meta-Evolution Judge", "governance", "governance", ("admission-judgment", "evolution-governance"), ("evidence.read", "admission.write"), ("govern.change",), ("AG-011",)),
)


class AgentRegistry:
    def __init__(self, specs: tuple[AgentSpec, ...] = CORE_AGENT_SPECS) -> None:
        self._agents = {spec.agent_id: spec for spec in specs}
        self._assert_integrity()

    def _assert_integrity(self) -> None:
        if len(self._agents) != len(DEFAULT_HANDOFF_CHAIN):
            raise AssertionError("agent_registry_cardinality_mismatch")
        for agent_id in DEFAULT_HANDOFF_CHAIN:
            if agent_id not in self._agents:
                raise AssertionError(f"missing_core_agent:{agent_id}")

    def get(self, agent_id: str) -> AgentSpec:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"unknown_agent:{agent_id}") from exc

    def select(self, capability: str) -> AgentSpec:
        candidates = [spec for spec in self._agents.values() if capability in spec.capabilities]
        if not candidates:
            raise LookupError(f"no_agent_for_capability:{capability}")
        return sorted(candidates, key=lambda spec: spec.agent_id)[0]

    def all(self) -> tuple[AgentSpec, ...]:
        return tuple(self._agents[key] for key in sorted(self._agents))


@dataclass(frozen=True)
class HandoffEnvelope:
    task_id: str
    source_agent: str
    target_agent: str
    reason: str
    required_capabilities: tuple[str, ...]
    input_artifact_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    constraints: tuple[str, ...]
    expected_output: str
    authority_scope: tuple[str, ...]
    expiry: str

    def payload(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "reason": self.reason,
            "required_capabilities": list(self.required_capabilities),
            "input_artifact_ids": list(self.input_artifact_ids),
            "evidence_refs": list(self.evidence_refs),
            "constraints": list(self.constraints),
            "expected_output": self.expected_output,
            "authority_scope": list(self.authority_scope),
            "expiry": self.expiry,
        }

    def signature(self, signing_key: bytes) -> str:
        if not signing_key:
            raise ValueError("signing_key_must_not_be_empty")
        material = json.dumps(self.payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hmac.new(signing_key, material, hashlib.sha256).hexdigest()

    def verify(self, signing_key: bytes, expected_signature: str) -> bool:
        return hmac.compare_digest(self.signature(signing_key), expected_signature)


class AgentPolicy:
    @staticmethod
    def authorize(spec: AgentSpec, *, capability: str, authority_scope: str, tool: str) -> dict[str, str]:
        if capability not in spec.capabilities:
            return {"state": "REJECT", "reason": "capability_not_registered"}
        if authority_scope not in spec.authority_scope:
            return {"state": "REJECT", "reason": "authority_scope_not_granted"}
        if tool not in spec.allowed_tools:
            return {"state": "REJECT", "reason": "tool_not_allowed"}
        if spec.agent_id == "AG-008" and tool == "vx.execute":
            return {"state": "REJECT", "reason": "forge_has_no_runtime_authority"}
        return {"state": "ALLOW", "reason": "policy_pass"}


def event_hash(event: Mapping[str, Any]) -> str:
    material = json.dumps(dict(event), sort_keys=True, separators=(",", ":"), default=str)
    return sha256(material.encode("utf-8")).hexdigest()


@dataclass
class AgentFabric:
    registry: AgentRegistry = field(default_factory=AgentRegistry)
    pattern_factory: PatternFactory = field(default_factory=lambda: PatternFactory(architectures=("agent-runtime",)))
    signing_key: bytes = b"vaixlns-test-signing-key"

    def dispatch(self, task: Mapping[str, Any], *, wallet: Any | None = None) -> dict[str, Any]:
        task_id = str(task.get("task_id", ""))
        capability = str(task.get("capability", ""))
        authority_scope = str(task.get("authority_scope", ""))
        tool = str(task.get("tool", ""))
        if not task_id or not capability or not authority_scope or not tool:
            return {"state": "HOLD", "reason": "missing_task_preconditions"}

        agent = self.registry.select(capability)
        policy = AgentPolicy.authorize(agent, capability=capability, authority_scope=authority_scope, tool=tool)
        events: list[dict[str, Any]] = []
        events.append(self._event("AGENT_SELECTED", {
            "task_id": task_id,
            "agent_id": agent.agent_id,
            "capability": capability,
        }))
        events.append(self._event("POLICY_DECISION", {
            "task_id": task_id,
            "agent_id": agent.agent_id,
            **policy,
        }))
        if policy["state"] != "ALLOW":
            return {"state": "REJECT", "agent_id": agent.agent_id, "policy": policy, "events": events}

        pattern_context = dict(task.get("pattern_context") or {})
        routes = self.pattern_factory.build(pattern_context)
        if not routes:
            return {
                "state": "HOLD",
                "agent_id": agent.agent_id,
                "reason": "pattern_context_not_admitted",
                "events": events,
            }
        if {route["direction"] for route in routes} != set(DIRECTIONS):
            return {
                "state": "HOLD",
                "agent_id": agent.agent_id,
                "reason": "four_direction_invariant_failed",
                "events": events,
            }
        events.append(self._event("PATTERN_SELECTED", {
            "task_id": task_id,
            "agent_id": agent.agent_id,
            "route_count": len(routes),
        }))

        reservation = None
        estimated_cost = str(task.get("estimated_cost", "0"))
        if wallet is not None and estimated_cost != "0":
            reservation = wallet.authorize(
                task_id=task_id,
                agent_id=agent.agent_id,
                amount=estimated_cost,
                asset=str(task.get("asset", "USD")),
            )
            events.append(self._event("WALLET_AUTHORIZED", {
                "task_id": task_id,
                "agent_id": agent.agent_id,
                "reservation_id": reservation.reservation_id,
            }))

        target = str(task.get("handoff_target", agent.handoff_targets[0] if agent.handoff_targets else agent.agent_id))
        if target not in agent.handoff_targets and target != agent.agent_id:
            return {
                "state": "REJECT",
                "agent_id": agent.agent_id,
                "reason": "handoff_target_not_authorized",
                "events": events,
            }

        envelope = HandoffEnvelope(
            task_id=task_id,
            source_agent=agent.agent_id,
            target_agent=target,
            reason=str(task.get("handoff_reason", "governed_task_progression")),
            required_capabilities=(capability,),
            input_artifact_ids=tuple(str(x) for x in task.get("input_artifact_ids", ())),
            evidence_refs=tuple(str(x) for x in task.get("evidence_refs", ())),
            constraints=tuple(str(x) for x in task.get("constraints", ())),
            expected_output=str(task.get("expected_output", "evidence_bundle")),
            authority_scope=(authority_scope,),
            expiry=str(task.get("expiry", "task-scope")),
        )
        signature = envelope.signature(self.signing_key)
        events.append(self._event("AGENT_HANDOFF", {
            "task_id": task_id,
            "source_agent": agent.agent_id,
            "target_agent": envelope.target_agent,
            "signature": signature,
        }))
        events.append(self._event("SIMULATION_COMPLETED", {
            "task_id": task_id,
            "route_count": len(routes),
            "real_side_effects": False,
        }))

        settlement = None
        if reservation is not None:
            actual_cost = str(task.get("actual_cost", estimated_cost))
            settlement = wallet.settle(reservation.reservation_id, actual_amount=actual_cost)
            events.append(self._event("WALLET_SETTLED", settlement))

        evidence = {
            "schema": "VAIXLNS.AGENT_EVIDENCE_BUNDLE.v1",
            "task_id": task_id,
            "agent_id": agent.agent_id,
            "policy": policy,
            "pattern": {
                "directions": list(DIRECTIONS),
                "route_count": len(routes),
                "binding_fingerprints_present": all(bool(r.get("binding_fingerprint")) for r in routes),
            },
            "handoff_signature": signature,
            "simulation": {"real_side_effects": False},
            "events_hash": event_hash({"events": events}),
        }
        evidence["evidence_hash"] = event_hash(evidence)
        return {
            "state": "SIMULATED",
            "verification_state": "VERIFIED",
            "final_disposition": "HOLD",
            "agent_id": agent.agent_id,
            "routes": routes,
            "handoff": envelope.payload(),
            "handoff_signature": signature,
            "wallet_settlement": settlement,
            "evidence": evidence,
            "events": events,
        }

    @staticmethod
    def _event(event_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        event = {"event_type": event_type, "payload": dict(payload)}
        event["event_hash"] = event_hash(event)
        return event


__all__ = [
    "AgentFabric",
    "AgentPolicy",
    "AgentRegistry",
    "AgentSpec",
    "HandoffEnvelope",
    "CORE_AGENT_SPECS",
    "DEFAULT_HANDOFF_CHAIN",
]
