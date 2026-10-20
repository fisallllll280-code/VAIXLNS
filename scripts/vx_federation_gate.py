#!/usr/bin/env python3
"""Deterministic reference VX Federation Gate.

This is a contract/reference implementation for registration and routing.
It does not claim live production federation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Any, Mapping


ACTIVE_STATES = {"REGISTERED", "ACTIVE", "DEGRADED"}
ROUTABLE_STATES = {"ACTIVE", "DEGRADED"}


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def registration_hash(record: Mapping[str, Any]) -> str:
    body = {k: v for k, v in record.items() if k != "registration_hash"}
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


@dataclass
class Instance:
    instance_id: str
    specialization: str
    capabilities: tuple[str, ...]
    state: str
    authority_scope: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["capabilities"] = list(self.capabilities)
        record["authority_scope"] = list(self.authority_scope)
        record["evidence_refs"] = list(self.evidence_refs)
        record["system_id"] = "VX"
        record["registration_hash"] = registration_hash(record)
        return record


class FederationGate:
    def __init__(self) -> None:
        self._instances: dict[str, dict[str, Any]] = {}

    def register(self, instance: Instance) -> dict[str, Any]:
        if not instance.instance_id.startswith("VX-"):
            raise ValueError("instance_id must use VX-* namespace")
        if instance.state not in ACTIVE_STATES:
            raise ValueError("instance must register in an active-compatible state")
        record = instance.to_record()
        self._instances[instance.instance_id] = record
        return record

    def set_state(self, instance_id: str, state: str) -> None:
        if instance_id not in self._instances:
            raise KeyError("unknown instance")
        if state not in {"REGISTERED", "ACTIVE", "DEGRADED", "ISOLATED", "RECOVERING", "RETIRED"}:
            raise ValueError("invalid state")
        self._instances[instance_id]["state"] = state
        self._instances[instance_id]["registration_hash"] = registration_hash(self._instances[instance_id])

    def discover(self, capability: str) -> list[dict[str, Any]]:
        candidates = [
            item for item in self._instances.values()
            if item["state"] in ROUTABLE_STATES
            and capability in item["capabilities"]
        ]
        return sorted(candidates, key=lambda item: item["instance_id"])

    def route(self, capability: str, authority_scope: str | None = None) -> dict[str, Any]:
        candidates = self.discover(capability)
        if authority_scope is not None:
            candidates = [
                item for item in candidates
                if authority_scope in item["authority_scope"]
            ]
        if not candidates:
            raise LookupError("no routable VX instance satisfies capability and authority")
        selected = candidates[0]
        return {
            "system_id": "VX",
            "route_target": selected["instance_id"],
            "specialization": selected["specialization"],
            "capability": capability,
            "state": selected["state"],
            "registration_hash": selected["registration_hash"],
        }

    def snapshot(self) -> list[dict[str, Any]]:
        return [self._instances[key] for key in sorted(self._instances)]


def main() -> int:
    parser = argparse.ArgumentParser(description="VX Federation Gate reference implementation")
    parser.add_argument("capability", nargs="?", default="simulation")
    args = parser.parse_args()

    gate = FederationGate()
    gate.register(Instance(
        "VX-Code-01", "software-engineering",
        ("coding", "simulation", "verification"),
        "ACTIVE", ("observe", "simulate", "verify")
    ))
    gate.register(Instance(
        "VX-Computer-01", "computer-engineering",
        ("hardware-analysis", "simulation", "verification"),
        "ACTIVE", ("observe", "simulate", "verify")
    ))
    result = {
        "gate": "VX-FEDERATION-GATE",
        "registered_instances": gate.snapshot(),
        "route": gate.route(args.capability) if args.capability in {"simulation", "coding", "hardware-analysis", "verification"} else None,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
