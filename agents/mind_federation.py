"""Provider-agnostic VX mind federation for governed agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping


def canonical_hash(value: object) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MindIdentity:
    mind_id: str
    domain: str
    capabilities: tuple[str, ...]
    provider: str = "ABSTRACT"
    model_id: str = "logical-mind"
    status: str = "ACTIVE"


@dataclass(frozen=True)
class MindExchange:
    exchange_id: str
    source_agent: str
    target_agent: str
    semantic_state: dict[str, Any]
    evidence_refs: tuple[str, ...]
    authority_scope: tuple[str, ...]
    state_hash: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "exchange_id": self.exchange_id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "semantic_state": self.semantic_state,
            "evidence_refs": list(self.evidence_refs),
            "authority_scope": list(self.authority_scope),
            "state_hash": self.state_hash,
        }


@dataclass
class MindFederation:
    minds: dict[str, MindIdentity] = field(default_factory=dict)
    links: dict[str, tuple[str, ...]] = field(default_factory=dict)
    history: list[MindExchange] = field(default_factory=list)

    @classmethod
    def from_registry(cls, agent_ids: tuple[str, ...], handoff_chain: tuple[str, ...]) -> "MindFederation":
        federation = cls()
        for agent_id in agent_ids:
            federation.register(
                MindIdentity(
                    mind_id=f"VM-{agent_id}",
                    domain=f"agent:{agent_id}",
                    capabilities=(),
                ),
                agent_id=agent_id,
            )
        for source, target in zip(handoff_chain, handoff_chain[1:]):
            federation.connect(source, target)
        return federation

    def register(self, mind: MindIdentity, *, agent_id: str) -> None:
        if not agent_id or not mind.mind_id:
            raise ValueError("agent_and_mind_ids_required")
        if mind.mind_id in self.minds:
            raise ValueError("duplicate_mind_id")
        self.minds[mind.mind_id] = mind
        self.links.setdefault(agent_id, ())

    def connect(self, source_agent: str, target_agent: str) -> None:
        if source_agent == target_agent:
            raise ValueError("self_link_not_allowed")
        existing = list(self.links.get(source_agent, ()))
        if target_agent not in existing:
            existing.append(target_agent)
        self.links[source_agent] = tuple(sorted(existing))

    def connected(self, source_agent: str, target_agent: str) -> bool:
        return target_agent in self.links.get(source_agent, ())

    def exchange(
        self,
        *,
        source_agent: str,
        target_agent: str,
        semantic_state: Mapping[str, Any],
        evidence_refs: tuple[str, ...] = (),
        authority_scope: tuple[str, ...] = (),
    ) -> MindExchange:
        if not self.connected(source_agent, target_agent):
            raise PermissionError("mind_link_not_established")
        state = dict(semantic_state)
        required = {
            "intent",
            "requested_capability",
            "assumptions",
            "risk",
            "evidence_refs",
            "requested_action",
            "authority_scope",
        }
        missing = sorted(required.difference(state))
        if missing:
            raise ValueError(f"semantic_state_missing:{','.join(missing)}")
        state_hash = canonical_hash(state)
        exchange_id = canonical_hash({
            "source_agent": source_agent,
            "target_agent": target_agent,
            "state_hash": state_hash,
            "sequence": len(self.history) + 1,
        })[:24]
        exchange = MindExchange(
            exchange_id=exchange_id,
            source_agent=source_agent,
            target_agent=target_agent,
            semantic_state=state,
            evidence_refs=tuple(evidence_refs),
            authority_scope=tuple(authority_scope),
            state_hash=state_hash,
        )
        self.history.append(exchange)
        return exchange

    def state(self) -> dict[str, Any]:
        return {
            "mind_count": len(self.minds),
            "link_count": sum(len(targets) for targets in self.links.values()),
            "exchange_count": len(self.history),
            "history_hash": canonical_hash([item.as_dict() for item in self.history]),
        }
