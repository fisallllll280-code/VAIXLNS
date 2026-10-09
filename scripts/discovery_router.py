"""Policy-driven discovery routing for VAIXLNS.

This module creates routing proposals only. It never authorizes execution and does
not infer family identity or parent authority from discovery text.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

DESTINATIONS = {"VX-FINANCIAL", "VX-ENGINEERING"}
HOLD_DESTINATIONS = {"PARENT_REVIEW", "CLASSIFICATION_HOLD"}


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _stable_id(prefix: str, value: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:24]}"


def _hold_route(discovery: Mapping[str, Any], status: str, destination: str, reason: str) -> dict[str, Any]:
    policy_version = str(discovery.get("policy_version") or "UNRESOLVED")
    route_material = {
        "discovery_id": discovery.get("discovery_id"),
        "destination": destination,
        "policy_version": policy_version,
        "reason": reason,
    }
    return {
        "route_id": _stable_id("route", route_material),
        "destination": destination,
        "status": status,
        "required_capabilities": [],
        "priority_policy": policy_version,
        "priority_score": None,
        "priority_rationale": reason,
        "handoff_event_ref": None,
        "output_refs": [],
        "decision_ref": None,
    }


def route_discovery(
    discovery: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a deterministic routing decision using an explicit parent policy.

    Required policy shape:
      directive_id: registered parent directive ID
      version: immutable policy version
      family_routes: {family_id: [VX-FINANCIAL, VX-ENGINEERING]}
      domain_routes: {FINANCIAL: [VX-FINANCIAL], ENGINEERING: [VX-ENGINEERING]}

    Unresolved identity, missing authority, incomplete classification, security
    concerns, or license uncertainty produce a hold route. execution_authorization
    is always false; a separate admission mechanism owns authorization.
    """
    discovery_id = discovery.get("discovery_id")
    if not isinstance(discovery_id, str) or not discovery_id.strip():
        raise ValueError("discovery_id is required")

    policy_version = policy.get("version")
    directive_id = policy.get("directive_id")
    if not directive_id or not policy_version:
        route = _hold_route(
            discovery, "PARENT_REVIEW", "PARENT_REVIEW",
            "Missing registered parent directive or immutable policy version",
        )
        return {
            "discovery_id": discovery_id,
            "decision_id": _stable_id("decision", {"discovery_id": discovery_id, "route": route}),
            "policy_version": "UNRESOLVED",
            "routes": [route],
            "execution_authorization": False,
            "decision_status": "HOLD",
        }

    if discovery.get("parent_directive_id") != directive_id:
        route = _hold_route(
            discovery, "PARENT_REVIEW", "PARENT_REVIEW",
            "Discovery parent directive does not match the supplied policy",
        )
        return {
            "discovery_id": discovery_id,
            "decision_id": _stable_id("decision", {"discovery_id": discovery_id, "route": route}),
            "policy_version": str(policy_version),
            "routes": [route],
            "execution_authorization": False,
            "decision_status": "HOLD",
        }

    classification = discovery.get("classification") or {}
    if classification.get("status") != "CONFIRMED":
        route = _hold_route(
            discovery, "CLASSIFICATION_PENDING", "CLASSIFICATION_HOLD",
            "Classification must be confirmed by an authorized process before routing",
        )
        return {
            "discovery_id": discovery_id,
            "decision_id": _stable_id("decision", {"discovery_id": discovery_id, "route": route}),
            "policy_version": str(policy_version),
            "routes": [route],
            "execution_authorization": False,
            "decision_status": "HOLD",
        }

    families = discovery.get("candidate_families") or []
    if not families:
        route = _hold_route(
            discovery, "PARENT_REVIEW", "PARENT_REVIEW",
            "No registered family relationship is supplied",
        )
        return {
            "discovery_id": discovery_id,
            "decision_id": _stable_id("decision", {"discovery_id": discovery_id, "route": route}),
            "policy_version": str(policy_version),
            "routes": [route],
            "execution_authorization": False,
            "decision_status": "HOLD",
        }

    family_routes = policy.get("family_routes") or {}
    allowed_by_family: set[str] = set()
    for family in families:
        family_id = family.get("family_id")
        identity_status = family.get("identity_status")
        if identity_status != "VERIFIED" or family_id not in family_routes:
            route = _hold_route(
                discovery, "PARENT_REVIEW", "PARENT_REVIEW",
                f"Family identity or route policy is unresolved: {family_id or 'missing family_id'}",
            )
            return {
                "discovery_id": discovery_id,
                "decision_id": _stable_id("decision", {"discovery_id": discovery_id, "route": route}),
                "policy_version": str(policy_version),
                "routes": [route],
                "execution_authorization": False,
                "decision_status": "HOLD",
            }
        family_destinations = family_routes[family_id]
        if not isinstance(family_destinations, list):
            raise ValueError(f"family_routes[{family_id!r}] must be a list")
        if any(destination not in DESTINATIONS for destination in family_destinations):
            raise ValueError(f"family_routes[{family_id!r}] contains an unsupported destination")
        allowed_by_family.update(family_destinations)

    domain_routes = policy.get("domain_routes") or {}
    domains = classification.get("domains") or []
    if not domains:
        route = _hold_route(
            discovery, "CLASSIFICATION_PENDING", "CLASSIFICATION_HOLD",
            "Confirmed classification must include at least one domain",
        )
        return {
            "discovery_id": discovery_id,
            "decision_id": _stable_id("decision", {"discovery_id": discovery_id, "route": route}),
            "policy_version": str(policy_version),
            "routes": [route],
            "execution_authorization": False,
            "decision_status": "HOLD",
        }

    relevant: set[str] = set()
    for domain in domains:
        destinations = domain_routes.get(domain)
        if destinations is None:
            continue
        if not isinstance(destinations, list):
            raise ValueError(f"domain_routes[{domain!r}] must be a list")
        if any(destination not in DESTINATIONS for destination in destinations):
            raise ValueError(f"domain_routes[{domain!r}] contains an unsupported destination")
        relevant.update(destinations)

    destinations = sorted(allowed_by_family.intersection(relevant))
    if not destinations:
        route = _hold_route(
            discovery, "PARENT_REVIEW", "PARENT_REVIEW",
            "No destination is jointly permitted by family policy and domain classification",
        )
        return {
            "discovery_id": discovery_id,
            "decision_id": _stable_id("decision", {"discovery_id": discovery_id, "route": route}),
            "policy_version": str(policy_version),
            "routes": [route],
            "execution_authorization": False,
            "decision_status": "HOLD",
        }

    security = discovery.get("security_status", "PENDING")
    license_status = discovery.get("license_status", "PENDING")
    evidence = discovery.get("evidence") or {}
    evidence_status = evidence.get("verification_status", "UNVERIFIED")
    if security in {"RISK_FOUND", "SECURITY_HOLD"}:
        route_status, reason = "SECURITY_HOLD", "Security review is required before further action"
    elif license_status in {"RESTRICTED", "LICENSE_HOLD"}:
        route_status, reason = "LICENSE_HOLD", "License review is required before further action"
    elif evidence_status in {"UNVERIFIED", "INSUFFICIENT", "CONTRADICTED"}:
        route_status, reason = "WAITING_FOR_EVIDENCE", "Evidence must be evaluated before admission"
    else:
        route_status, reason = "ROUTED", "Destination permitted by parent policy, family, and confirmed domain"

    routes = []
    for destination in destinations:
        route_material = {
            "discovery_id": discovery_id,
            "destination": destination,
            "directive_id": directive_id,
            "policy_version": policy_version,
        }
        routes.append({
            "route_id": _stable_id("route", route_material),
            "destination": destination,
            "status": route_status,
            "required_capabilities": [],
            "priority_policy": str(policy_version),
            "priority_score": None,
            "priority_rationale": reason,
            "handoff_event_ref": None,
            "output_refs": [],
            "decision_ref": None,
        })

    decision_material = {
        "discovery_id": discovery_id,
        "directive_id": directive_id,
        "policy_version": policy_version,
        "routes": routes,
    }
    return {
        "discovery_id": discovery_id,
        "decision_id": _stable_id("decision", decision_material),
        "policy_version": str(policy_version),
        "routes": routes,
        "execution_authorization": False,
        "decision_status": "ROUTED" if route_status == "ROUTED" else "HOLD",
    }
