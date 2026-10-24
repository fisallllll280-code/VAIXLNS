"""Policy-only comparison for LiteLLM and OmniRoute behind VX.

This module never calls a provider, loads credentials, or changes canonical state.
Candidates must already be admitted by scripts.arcx_model_router.plan_route.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

GATEWAYS = frozenset({"litellm", "omniroute"})


def _hash(data: dict[str, Any]) -> str:
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def compare_gateways(
    route_plan: dict[str, Any], gateways: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Return an auditable proposal, never an authorization to dispatch."""
    blockers: list[str] = []
    if not isinstance(route_plan, dict) or not isinstance(gateways, list) or not isinstance(policy, dict):
        blockers.append("INVALID_INPUT")
        route_plan, gateways, policy = {}, [], {}
    if route_plan.get("state") != "ROUTE_CANDIDATES_READY" or not route_plan.get("candidates"):
        blockers.append("NO_AUTHORIZED_MODEL_ROUTE")
    if route_plan.get("provider_called") is not False:
        blockers.append("ROUTE_PLAN_NOT_POLICY_ONLY")
    if policy.get("allow_live_requests") is not False:
        blockers.append("LIVE_REQUESTS_MUST_BE_DISABLED")
    if policy.get("max_external_spend_sar") != 0:
        blockers.append("ZERO_SPEND_POLICY_REQUIRED")
    allowed = policy.get("allowed_gateways")
    if not isinstance(allowed, list) or not allowed or any(not isinstance(x, str) or x not in GATEWAYS for x in allowed):
        blockers.append("INVALID_GATEWAY_ALLOWLIST")
        allowed = []
    candidates = []
    for entry in gateways:
        if not isinstance(entry, dict):
            continue
        name = entry.get("gateway_id")
        if not isinstance(name, str) or name not in allowed or name not in GATEWAYS:
            continue
        if entry.get("contract_verified") is not True or entry.get("tenant_isolation_verified") is not True:
            continue
        if entry.get("credential_mode") != "external_secret_store":
            continue
        if entry.get("estimated_request_cost_sar") != 0:
            continue
        if entry.get("egress_enabled") is not False:
            continue
        candidates.append({"gateway_id": name, "status": "ELIGIBLE_FOR_OFFLINE_TEST"})
    candidates.sort(key=lambda x: x["gateway_id"])
    if not candidates:
        blockers.append("NO_VERIFIED_OFFLINE_GATEWAY")
    result = {
        "schema_version": "vx.gateway-comparison.v1",
        "status": "BLOCKED" if blockers else "OFFLINE_COMPARISON_READY",
        "blockers": sorted(set(blockers)),
        "gateways": candidates if not blockers else [],
        "model_route_plan_sha256": route_plan.get("plan_sha256"),
        "external_spend_sar": 0,
        "execution_performed": False,
        "live_provider_called": False,
        "canonical_mutation_performed": False,
        "verified_performance_claim": False,
    }
    result["receipt_sha256"] = _hash(result)
    return result
