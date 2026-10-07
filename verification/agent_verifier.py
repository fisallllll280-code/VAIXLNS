"""Independent deterministic checks for Agent Fabric proof bundles."""
from __future__ import annotations

from typing import Any, Mapping
import hashlib
import json

from agents.agent_fabric import HandoffEnvelope, event_hash
from agents.mind_federation import canonical_hash
from patterns.vaixl_pattern_factory import DIRECTIONS


class AgentVerifier:
    """Verify observable fabric invariants independently of dispatch logic."""

    @staticmethod
    def verify(
        *,
        routes: list[Mapping[str, Any]],
        handoff: Mapping[str, Any],
        signature: str,
        signing_key: bytes,
        events: list[Mapping[str, Any]],
        wallet_settlement: Mapping[str, Any] | None,
        mind_exchange: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        checks: dict[str, bool] = {}

        checks["four_directions_exact"] = (
            {str(route.get("direction")) for route in routes} == set(DIRECTIONS)
            and len(routes) >= len(DIRECTIONS)
        )
        checks["all_bindings_present"] = all(bool(route.get("binding_fingerprint")) for route in routes)

        envelope = HandoffEnvelope(
            task_id=str(handoff["task_id"]),
            source_agent=str(handoff["source_agent"]),
            target_agent=str(handoff["target_agent"]),
            reason=str(handoff["reason"]),
            required_capabilities=tuple(handoff.get("required_capabilities", ())),
            input_artifact_ids=tuple(handoff.get("input_artifact_ids", ())),
            evidence_refs=tuple(handoff.get("evidence_refs", ())),
            constraints=tuple(handoff.get("constraints", ())),
            expected_output=str(handoff["expected_output"]),
            authority_scope=tuple(handoff.get("authority_scope", ())),
            expiry=str(handoff["expiry"]),
        )
        checks["handoff_signature_valid"] = envelope.verify(signing_key, signature)

        event_checks = []
        for event in events:
            material = {
                "event_type": event.get("event_type"),
                "payload": event.get("payload"),
            }
            event_checks.append(event.get("event_hash") == event_hash(material))
        checks["event_hashes_valid"] = all(event_checks)

        if mind_exchange is None:
            checks["mind_exchange_hash_valid"] = False
        else:
            semantic_state = mind_exchange.get("semantic_state", {})
            checks["mind_exchange_hash_valid"] = (
                mind_exchange.get("state_hash") == canonical_hash(semantic_state)
                and bool(mind_exchange.get("exchange_id"))
                and bool(mind_exchange.get("source_agent"))
                and bool(mind_exchange.get("target_agent"))
            )

        if wallet_settlement is None:
            checks["wallet_real_value_guard"] = True
        else:
            checks["wallet_real_value_guard"] = wallet_settlement.get("real_value_moved") is False

        state = "PASS" if all(checks.values()) else "FAIL"
        proof_material = json.dumps(checks, sort_keys=True, separators=(",", ":"))
        return {
            "state": state,
            "checks": checks,
            "proof_hash": hashlib.sha256(proof_material.encode("utf-8")).hexdigest(),
        }
