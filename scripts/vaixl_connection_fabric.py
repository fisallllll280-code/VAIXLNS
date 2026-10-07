#!/usr/bin/env python3
"""VAIXLNS Semantic Connection Fabric.

Deterministic reference fabric for lightweight, multi-path semantic transport.
It prevents one blocked channel from stalling unrelated semantic flows by using
independent queues, bounded capacity, priority routing, isolation, and replayable
event evidence. This is a reference/conformance component, not a production mesh.
"""
from __future__ import annotations
import argparse, hashlib, json
from dataclasses import dataclass, field
from typing import Any

FABRIC_ID = "VAIXLNS-CONNECTION-FABRIC-001"
SCHEMA_VERSION = "vaixlns.connection_fabric.v1"
VALID_STATES = {"READY", "ACTIVE", "BLOCKED", "ISOLATED", "DRAINING", "CLOSED"}

def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()

@dataclass
class Channel:
    channel_id: str
    purpose: str
    priority: int = 50
    capacity: int = 64
    state: str = "READY"
    queue: list[dict[str, Any]] = field(default_factory=list)
    delivered: int = 0
    rejected: int = 0

    def enqueue(self, message: dict[str, Any]) -> bool:
        if self.state not in {"READY", "ACTIVE"}:
            self.rejected += 1
            return False
        if len(self.queue) >= self.capacity:
            self.state = "BLOCKED"
            self.rejected += 1
            return False
        self.queue.append(message)
        self.state = "ACTIVE"
        return True

    def deliver_one(self) -> dict[str, Any] | None:
        if not self.queue:
            if self.state == "ACTIVE":
                self.state = "READY"
            return None
        item = self.queue.pop(0)
        self.delivered += 1
        if not self.queue:
            self.state = "READY"
        return item

    def isolate(self) -> None:
        self.state = "ISOLATED"

    def recover(self) -> None:
        if self.state == "ISOLATED":
            self.state = "READY"

class SemanticConnectionFabric:
    def __init__(self) -> None:
        self.channels: dict[str, Channel] = {}
        self.events: list[dict[str, Any]] = []
        self.sequence = 0

    def add_channel(self, channel_id: str, purpose: str, priority: int = 50, capacity: int = 64) -> None:
        if channel_id in self.channels:
            raise ValueError("duplicate_channel:" + channel_id)
        if capacity < 1:
            raise ValueError("capacity_must_be_positive")
        self.channels[channel_id] = Channel(channel_id, purpose, priority, capacity)
        self._event("CHANNEL_CREATED", {"channel_id": channel_id, "purpose": purpose})

    def _event(self, kind: str, data: dict[str, Any]) -> None:
        self.sequence += 1
        event = {"seq": self.sequence, "kind": kind, "data": data}
        event["event_hash"] = digest(event)
        self.events.append(event)

    def route(self, message: dict[str, Any]) -> str:
        purpose = str(message.get("purpose", "")).upper()
        candidates = [
            c for c in self.channels.values()
            if c.purpose.upper() == purpose and c.state in {"READY", "ACTIVE"}
        ]
        if not candidates:
            self._event("ROUTE_REJECTED", {"purpose": purpose})
            raise RuntimeError("no_available_channel:" + purpose)
        channel = sorted(candidates, key=lambda c: (-c.priority, len(c.queue), c.channel_id))[0]
        if not channel.enqueue(message):
            self._event("BACKPRESSURE", {"channel_id": channel.channel_id})
            raise RuntimeError("channel_backpressure:" + channel.channel_id)
        self._event("MESSAGE_ROUTED", {
            "channel_id": channel.channel_id,
            "message_id": message.get("message_id"),
            "purpose": purpose,
        })
        return channel.channel_id

    def deliver(self, channel_id: str) -> dict[str, Any] | None:
        channel = self.channels[channel_id]
        item = channel.deliver_one()
        if item is not None:
            self._event("MESSAGE_DELIVERED", {
                "channel_id": channel_id,
                "message_id": item.get("message_id"),
            })
        return item

    def isolate(self, channel_id: str, reason: str) -> None:
        channel = self.channels[channel_id]
        channel.isolate()
        self._event("CHANNEL_ISOLATED", {"channel_id": channel_id, "reason": reason})

    def recover(self, channel_id: str) -> None:
        channel = self.channels[channel_id]
        channel.recover()
        self._event("CHANNEL_RECOVERED", {"channel_id": channel_id})

    def evidence(self) -> dict[str, Any]:
        state = {
            "fabric_id": FABRIC_ID,
            "schema_version": SCHEMA_VERSION,
            "channels": {
                key: {
                    "purpose": value.purpose,
                    "priority": value.priority,
                    "capacity": value.capacity,
                    "state": value.state,
                    "queued": len(value.queue),
                    "delivered": value.delivered,
                    "rejected": value.rejected,
                }
                for key, value in sorted(self.channels.items())
            },
            "events": self.events,
        }
        state["evidence_hash"] = digest(state)
        return state

def golden_fabric() -> SemanticConnectionFabric:
    fabric = SemanticConnectionFabric()
    fabric.add_channel("C-SPEC", "SPEC", priority=100, capacity=2)
    fabric.add_channel("C-AUTH", "AUTHORITY", priority=90, capacity=2)
    fabric.add_channel("C-EXEC", "EXECUTION", priority=80, capacity=2)
    fabric.add_channel("C-EVIDENCE", "EVIDENCE", priority=70, capacity=2)
    fabric.add_channel("C-SECURITY", "SECURITY", priority=110, capacity=2)
    return fabric

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["golden"])
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    fabric = golden_fabric()
    fabric.route({"message_id": "m-001", "purpose": "SPEC", "payload": "meaning"})
    fabric.route({"message_id": "m-002", "purpose": "SECURITY", "payload": "guard"})
    fabric.deliver("C-SPEC")
    fabric.deliver("C-SECURITY")
    result = fabric.evidence()
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    print(rendered, end="")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
