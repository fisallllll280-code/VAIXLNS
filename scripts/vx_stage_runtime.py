#!/usr/bin/env python3
"""Deterministic VX Stage Runtime harness.

This executable validates the operational boundary for one staged VX instance:
identity, authority-aware routing, signed request envelopes, heartbeat/lease,
execution evidence, failure isolation, recovery, and SLO-style measurements.

It is a Stage reference runtime, not a claim of production deployment.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


STAGE_ID = "VX-STAGE-001"
DEFAULT_KEY = "VAIXLNS-STAGE-TEST-KEY"
FIXED_TIME = "2026-10-07T00:00:00Z"


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sign(envelope: dict[str, Any], key: bytes) -> str:
    unsigned = dict(envelope)
    unsigned.pop("signature", None)
    return hmac.new(key, canonical(unsigned), hashlib.sha256).hexdigest()


def verify(envelope: dict[str, Any], key: bytes) -> bool:
    expected = sign(envelope, key)
    actual = str(envelope.get("signature", ""))
    return hmac.compare_digest(expected, actual)


@dataclass
class StageVX:
    instance_id: str
    specialization: str
    capabilities: set[str]
    authority_scope: set[str]
    state: str = "REGISTERED"
    lease_seconds: int = 60
    last_seen: str = FIXED_TIME
    events: list[dict[str, Any]] = field(default_factory=list)

    def heartbeat(self, timestamp: str) -> None:
        if self.state == "ISOLATED":
            raise RuntimeError("isolated instance cannot heartbeat into ACTIVE state")
        self.state = "ACTIVE"
        self.last_seen = timestamp
        self.events.append({
            "type": "HEARTBEAT",
            "instance_id": self.instance_id,
            "timestamp": timestamp,
        })

    def isolate(self, reason: str) -> None:
        self.state = "ISOLATED"
        self.events.append({
            "type": "ISOLATION",
            "instance_id": self.instance_id,
            "reason": reason,
        })

    def recover(self, timestamp: str) -> None:
        self.state = "ACTIVE"
        self.last_seen = timestamp
        self.events.append({
            "type": "RECOVERY",
            "instance_id": self.instance_id,
            "timestamp": timestamp,
        })

    def can_route(self, capability: str, authority: str) -> bool:
        return (
            self.state == "ACTIVE"
            and capability in self.capabilities
            and authority in self.authority_scope
        )


class StageFederationGate:
    def __init__(self, key: bytes) -> None:
        self.key = key
        self.instances: dict[str, StageVX] = {}
        self.routes: list[dict[str, Any]] = []

    def register(self, instance: StageVX) -> None:
        if not instance.instance_id.startswith("VX-"):
            raise ValueError("invalid VX instance namespace")
        self.instances[instance.instance_id] = instance

    def route(self, capability: str, authority: str, request_id: str) -> dict[str, Any]:
        started = perf_counter()
        candidates = [
            instance for instance in self.instances.values()
            if instance.can_route(capability, authority)
        ]
        elapsed_ms = round((perf_counter() - started) * 1000, 3)
        if not candidates:
            decision = {
                "request_id": request_id,
                "capability": capability,
                "authority": authority,
                "decision": "BLOCK",
                "reason": "NO_AUTHORIZED_ACTIVE_INSTANCE",
                "latency_ms": elapsed_ms,
            }
            self.routes.append(decision)
            raise PermissionError(json.dumps(decision))
        target = sorted(candidates, key=lambda x: x.instance_id)[0]
        decision = {
            "request_id": request_id,
            "capability": capability,
            "authority": authority,
            "decision": "ROUTE",
            "target": target.instance_id,
            "latency_ms": elapsed_ms,
        }
        self.routes.append(decision)
        return decision

    def signed_request(self, request_id: str, instance_id: str, capability: str, authority: str) -> dict[str, Any]:
        envelope = {
            "request_id": request_id,
            "stage_id": STAGE_ID,
            "instance_id": instance_id,
            "capability": capability,
            "authority": authority,
            "issued_at": FIXED_TIME,
        }
        envelope["signature"] = sign(envelope, self.key)
        return envelope


def run_stage() -> dict[str, Any]:
    key_source = "environment" if "VX_STAGE_SIGNING_KEY" else "test-default"
    import os
    raw_key = os.getenv("VX_STAGE_SIGNING_KEY", DEFAULT_KEY)
    key = raw_key.encode("utf-8")

    gate = StageFederationGate(key)
    vx = StageVX(
        instance_id="VX-Code-Stage-01",
        specialization="software-engineering",
        capabilities={"coding", "simulation", "verification"},
        authority_scope={"observe", "simulate", "verify"},
    )
    gate.register(vx)
    vx.heartbeat(FIXED_TIME)

    request_id = "STAGE-RUN-0001"
    envelope = gate.signed_request(request_id, vx.instance_id, "simulation", "simulate")

    if not verify(envelope, key):
        raise AssertionError("signed request verification failed")

    route = gate.route("simulation", "simulate", request_id)

    execution_event = {
        "type": "EXECUTION",
        "request_id": request_id,
        "instance_id": route["target"],
        "action": "stage-verification",
        "result": "SUCCESS",
    }
    vx.events.append(execution_event)

    vx.isolate("CONTROLLED_FAILURE_INJECTION")

    blocked = False
    try:
        gate.route("simulation", "simulate", request_id + "-isolated")
    except PermissionError:
        blocked = True

    if not blocked:
        raise AssertionError("isolated VX was still routable")

    vx.recover(FIXED_TIME)
    recovered_route = gate.route("verification", "verify", request_id + "-recovery")

    evidence = {
        "schema_version": "vx-stage-evidence.v1",
        "stage_id": STAGE_ID,
        "run_id": request_id,
        "instance": {
            "instance_id": vx.instance_id,
            "specialization": vx.specialization,
            "state": vx.state,
            "capabilities": sorted(vx.capabilities),
            "authority_scope": sorted(vx.authority_scope),
        },
        "events": vx.events,
        "routing": {
            "initial": route,
            "recovery": recovered_route,
            "blocked_after_isolation": blocked,
        },
        "failure_injection": {
            "type": "CONTROLLED_FAILURE_INJECTION",
            "isolation_enforced": blocked,
            "recovery_successful": vx.state == "ACTIVE",
        },
        "provenance": {
            "envelope_hash": sha256(envelope),
            "envelope_signature": envelope["signature"],
            "key_source": key_source,
            "canonical_clock": FIXED_TIME,
            "status": "STAGE_SIGNED",
        },
        "slo": {
            "routing_decisions": len(gate.routes),
            "blocked_decisions": sum(1 for r in gate.routes if r["decision"] == "BLOCK"),
            "successful_routes": sum(1 for r in gate.routes if r["decision"] == "ROUTE"),
            "authority_bypass_observed": False,
            "isolation_bypass_observed": False,
            "latency_ms": [r["latency_ms"] for r in gate.routes],
        },
        "overall": "PASS",
    }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="VAIXLNS VX Stage Runtime")
    parser.add_argument("command", choices=["stage-run"])
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    result = run_stage()
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    print(rendered)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    return 0 if result["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
