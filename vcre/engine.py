from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Any, Callable, Iterable

SCIENTIFIC_STATES = {
    "MEASURED", "FORMALLY_PROVEN", "NUMERICALLY_VERIFIED",
    "SIMULATED", "INFERRED", "HYPOTHESIZED"
}

def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def digest(value: Any) -> str:
    return sha256(canonical(value).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class ScientificObject:
    identity: str
    domain: str
    units: str
    value: Any
    scientific_state: str = "SIMULATED"

    def validate(self) -> None:
        if self.scientific_state not in SCIENTIFIC_STATES:
            raise ValueError(f"unknown scientific state: {self.scientific_state}")
        if not self.identity or not self.domain:
            raise ValueError("scientific object identity/domain are required")

@dataclass(frozen=True)
class RealityState:
    world_id: str
    t: float
    state: dict[str, Any]
    model_id: str
    model_version: str
    state_hash: str

    @staticmethod
    def create(world_id: str, t: float, state: dict[str, Any], model_id: str, model_version: str) -> "RealityState":
        payload = {"world_id": world_id, "t": t, "state": state, "model_id": model_id, "model_version": model_version}
        return RealityState(world_id, t, state, model_id, model_version, digest(payload))

@dataclass(frozen=True)
class Event:
    sequence: int
    kind: str
    payload: dict[str, Any]
    prev_hash: str
    event_hash: str

    @staticmethod
    def create(sequence: int, kind: str, payload: dict[str, Any], prev_hash: str) -> "Event":
        body = {"sequence": sequence, "kind": kind, "payload": payload, "prev_hash": prev_hash}
        return Event(sequence, kind, payload, prev_hash, digest(body))

class EvidenceLedger:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def append(self, kind: str, payload: dict[str, Any]) -> Event:
        prev = self.events[-1].event_hash if self.events else "GENESIS"
        event = Event.create(len(self.events) + 1, kind, payload, prev)
        self.events.append(event)
        return event

    def verify(self) -> bool:
        prev = "GENESIS"
        for index, event in enumerate(self.events, start=1):
            if event.sequence != index or event.prev_hash != prev:
                return False
            recomputed = Event.create(event.sequence, event.kind, event.payload, event.prev_hash)
            if recomputed.event_hash != event.event_hash:
                return False
            prev = event.event_hash
        return True

@dataclass(frozen=True)
class Invariant:
    name: str
    check: Callable[[dict[str, Any]], bool]
    failure_reason: str

@dataclass(frozen=True)
class Transition:
    before_hash: str
    after_hash: str
    observation: dict[str, Any]
    intervention: dict[str, Any] | None
    rule: str
    uncertainty: dict[str, float]
    evidence_event_hash: str

class RealityEngine:
    def __init__(self, model_id: str, model_version: str = "1.0.0") -> None:
        self.model_id = model_id
        self.model_version = model_version
        self.ledger = EvidenceLedger()
        self.invariants: list[Invariant] = []
        self.transitions: list[Transition] = []
        self.worlds: dict[str, RealityState] = {}

    def register_invariant(self, invariant: Invariant) -> None:
        self.invariants.append(invariant)

    def create_world(self, world_id: str, state: dict[str, Any], t: float = 0.0) -> RealityState:
        world = RealityState.create(world_id, t, dict(state), self.model_id, self.model_version)
        self.worlds[world_id] = world
        self.ledger.append("WORLD_CREATED", asdict(world))
        return world

    def transition(
        self,
        world_id: str,
        rule: str,
        step: Callable[[dict[str, Any]], dict[str, Any]],
        observation: dict[str, Any] | None = None,
        intervention: dict[str, Any] | None = None,
        uncertainty: dict[str, float] | None = None,
        dt: float = 1.0,
    ) -> RealityState:
        before = self.worlds[world_id]
        next_state = step(dict(before.state))
        failures = [inv.failure_reason for inv in self.invariants if not inv.check(next_state)]
        if failures:
            self.ledger.append("QUARANTINED_TRANSITION", {"world_id": world_id, "before": before.state_hash, "failures": failures})
            raise ValueError("invariant violation: " + "; ".join(failures))
        after = RealityState.create(world_id, before.t + dt, next_state, self.model_id, self.model_version)
        event = self.ledger.append("STATE_TRANSITION", {
            "world_id": world_id,
            "before_hash": before.state_hash,
            "after_hash": after.state_hash,
            "observation": observation or {},
            "intervention": intervention,
            "rule": rule,
            "uncertainty": uncertainty or {},
        })
        self.transitions.append(Transition(before.state_hash, after.state_hash, observation or {}, intervention, rule, uncertainty or {}, event.event_hash))
        self.worlds[world_id] = after
        return after

    def branch(self, source_world_id: str, branch_world_id: str, intervention: dict[str, Any]) -> RealityState:
        source = self.worlds[source_world_id]
        branched = RealityState.create(branch_world_id, source.t, dict(source.state), self.model_id, self.model_version)
        self.worlds[branch_world_id] = branched
        self.ledger.append("COUNTERFACTUAL_BRANCH", {
            "source_world_id": source_world_id,
            "branch_world_id": branch_world_id,
            "source_hash": source.state_hash,
            "intervention": intervention,
        })
        return branched

    def replay(self, world_id: str, initial_state: dict[str, Any], transitions: Iterable[tuple[str, Callable[[dict[str, Any]], dict[str, Any]], float]]) -> RealityState:
        replayed = RealityState.create(world_id, 0.0, dict(initial_state), self.model_id, self.model_version)
        for rule, step, dt in transitions:
            next_state = step(dict(replayed.state))
            failures = [inv.failure_reason for inv in self.invariants if not inv.check(next_state)]
            if failures:
                raise ValueError("replay invariant violation: " + "; ".join(failures))
            replayed = RealityState.create(world_id, replayed.t + dt, next_state, self.model_id, self.model_version)
        return replayed

    def certificate(self, result: Any, assumptions: list[str], errors: dict[str, float], uncertainty: dict[str, float], status: str) -> dict[str, Any]:
        if status not in SCIENTIFIC_STATES:
            raise ValueError("invalid certificate state")
        cert = {
            "result": result,
            "model": {"id": self.model_id, "version": self.model_version},
            "assumptions": assumptions,
            "invariants": [i.name for i in self.invariants],
            "error": errors,
            "uncertainty": uncertainty,
            "provenance": {"ledger_head": self.ledger.events[-1].event_hash if self.ledger.events else "GENESIS"},
            "replay_manifest": [{"rule": t.rule, "before_hash": t.before_hash, "after_hash": t.after_hash} for t in self.transitions],
            "scientific_state": status,
        }
        cert["certificate_hash"] = digest(cert)
        self.ledger.append("CERTIFICATE", cert)
        return cert

    def impossibility(self, reason: str, scope: str, evidence: list[str]) -> dict[str, Any]:
        record = {"status": "IMPOSSIBLE_OR_INVALID", "reason": reason, "scope": scope, "evidence": evidence}
        record["certificate_hash"] = digest(record)
        self.ledger.append("IMPOSSIBILITY_CERTIFICATE", record)
        return record

    def evidence_bundle(self) -> dict[str, Any]:
        return {
            "ledger_valid": self.ledger.verify(),
            "event_count": len(self.ledger.events),
            "transition_count": len(self.transitions),
            "worlds": {wid: asdict(world) for wid, world in self.worlds.items()},
            "ledger_head": self.ledger.events[-1].event_hash if self.ledger.events else "GENESIS",
        }
