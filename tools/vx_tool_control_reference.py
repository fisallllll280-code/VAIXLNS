"""Fail-closed reference evaluator for VX tool-action envelopes.

This module evaluates a request; it does NOT execute tools or authenticate signatures.
The caller must supply actor/tool/approval registries loaded from trusted, admitted sources.
Do not expose this function as a security boundary until identity authentication, signature
verification, schema validation, atomic idempotency, durable event/ledger writes and the
actual adapter gate are integrated and independently tested.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

TIERS = {
    "A0_OBSERVE": 0,
    "A1_RESEARCH": 1,
    "A2_PROPOSE": 2,
    "A3_SANDBOX_MUTATE": 3,
    "A4_BRANCH_MUTATE": 4,
    "A5_RELEASE_PREPARE": 5,
    "A6_RELEASE_DEPLOY": 6,
    "A7_IRREVERSIBLE_OR_PHYSICAL": 7,
}
OPERATION_TIER = {
    "OBSERVE": "A0_OBSERVE",
    "RESEARCH": "A1_RESEARCH",
    "PROPOSE": "A2_PROPOSE",
    "SANDBOX_MUTATE": "A3_SANDBOX_MUTATE",
    "BRANCH_MUTATE": "A4_BRANCH_MUTATE",
    "RELEASE_PREPARE": "A5_RELEASE_PREPARE",
    "RELEASE_DEPLOY": "A6_RELEASE_DEPLOY",
    "IRREVERSIBLE_OR_PHYSICAL": "A7_IRREVERSIBLE_OR_PHYSICAL",
}
RISK_RANK = {
    "R0_INFORMATIONAL": 0,
    "R1_LOW": 1,
    "R2_MODERATE": 2,
    "R3_HIGH": 3,
    "R4_CRITICAL": 4,
}
BUDGET_KEYS = (
    "max_execution_seconds",
    "max_retries",
    "max_concurrency",
    "max_tokens",
    "max_network_calls",
    "max_write_bytes",
    "max_estimated_cost_usd",
)


def canonical_json(value: Any) -> bytes:
    """Stable UTF-8 canonical JSON for digest comparisons in this reference module."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def policy_digest(policy: Mapping[str, Any]) -> str:
    payload = dict(policy)
    payload.pop("digest", None)
    return sha256_digest(payload)


def approval_bound_action_digest(envelope: Mapping[str, Any]) -> str:
    """Bind approval to action intent/scope/budget; exclude approval metadata itself."""
    payload = dict(envelope)
    payload.pop("approval_requirement", None)
    return sha256_digest(payload)


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _min_tier(values: list[str]) -> str | None:
    if not values or any(value not in TIERS for value in values):
        return None
    return min(values, key=lambda item: TIERS[item])


def evaluate_action(
    envelope: Mapping[str, Any],
    *,
    actors: Mapping[str, Mapping[str, Any]],
    tools: Mapping[str, Mapping[str, Any]],
    policy: Mapping[str, Any],
    approvals: Mapping[str, Mapping[str, Any]] | None = None,
    now: datetime | None = None,
    environment_ceiling: str = "A3_SANDBOX_MUTATE",
    emergency_stop: bool = False,
    idempotency_records: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate a proposed action, returning a decision record without invoking a tool.

    Actor, tool, policy, and approval mappings are trusted inputs and must not be taken
    from the submitted envelope itself. The environment ceiling represents a separately
    governed deployment profile. Unknown/missing information is denied or held.
    """
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    approvals = approvals or {}
    idempotency_records = idempotency_records or {}
    if not isinstance(envelope, Mapping):
        envelope = {}
    action_id = str(envelope.get("action_id", "unknown-action"))
    created_at = now.isoformat().replace("+00:00", "Z")
    requested_expiry = _timestamp(envelope.get("expires_at"))
    decision_expiry = min(requested_expiry or (now + timedelta(seconds=30)),
                          now + timedelta(seconds=60))
    reasons: list[str] = []
    gates: list[dict[str, Any]] = []
    selected_tier = "NONE"

    def gate(gate_id: str, status: str, reason: str) -> None:
        gates.append({"gate_id": gate_id, "status": status, "reason": reason})

    def finish(decision: str, reason_codes: list[str], next_action: str) -> dict[str, Any]:
        nonlocal selected_tier
        payload: dict[str, Any] = {
            "schema_version": "1.0.0",
            "decision_id": "VD-" + hashlib.sha256(
                (action_id + "|" + created_at + "|" + decision).encode("utf-8")
            ).hexdigest()[:20],
            "action_id": action_id,
            "evaluated_at": created_at,
            "expires_at": decision_expiry.isoformat().replace("+00:00", "Z"),
            "policy_binding": {
                "policy_id": str(policy.get("policy_id", "unknown")),
                "version": str(policy.get("version", "unknown")),
                "digest": policy_digest(policy),
            },
            "decision": decision,
            "reason_codes": list(dict.fromkeys(reason_codes)) or ["INVALID_CONTRACT"],
            "effective_authority": selected_tier if decision == "ALLOW" else "NONE",
            "gate_results": gates or [{
                "gate_id": "request-validation",
                "status": "HOLD",
                "reason": "No policy gate completed.",
            }],
            "next_action": next_action,
        }
        if decision == "ALLOW":
            payload["granted_budget"] = dict(envelope.get("budget", {}))
            payload["execution_permit_id"] = "VP-" + hashlib.sha256(
                (action_id + "|" + payload["policy_binding"]["digest"] + "|" +
                 envelope.get("idempotency_key", "")).encode("utf-8")
            ).hexdigest()[:20]
        payload["decision_digest"] = sha256_digest(payload)
        return payload

    # Emergency stop outranks every other check.
    if emergency_stop:
        gate("emergency-stop", "FAIL", "Emergency stop is active; no new tool action may start.")
        return finish("REJECT", ["EMERGENCY_STOP"], "ABORT")

    if not isinstance(envelope, Mapping):
        gate("envelope", "FAIL", "Action envelope must be an object.")
        return finish("REJECT", ["INVALID_CONTRACT"], "NO_ACTION")

    required_top = (
        "schema_version", "action_id", "task_id", "correlation_id", "requested_at",
        "expires_at", "idempotency_key", "actor", "tool", "operation", "scope",
        "policy_binding", "budget", "risk", "verification", "approval_requirement",
    )
    missing = [key for key in required_top if key not in envelope]
    if missing or envelope.get("schema_version") != "1.0.0":
        gate("envelope", "FAIL", "Missing required fields or unsupported schema version: " +
             ", ".join(missing or ["schema_version"]))
        return finish("HOLD", ["INVALID_CONTRACT"], "REPAIR_ENVELOPE")

    expiry = _timestamp(envelope.get("expires_at"))
    requested_at = _timestamp(envelope.get("requested_at"))
    if expiry is None or requested_at is None:
        gate("time-bound", "FAIL", "requested_at and expires_at must be timezone-aware timestamps.")
        return finish("REJECT", ["INVALID_CONTRACT"], "NO_ACTION")
    if expiry <= now:
        gate("time-bound", "FAIL", "Action envelope has expired.")
        return finish("REJECT", ["EXPIRED_ENVELOPE"], "NO_ACTION")
    if requested_at > now + timedelta(minutes=1):
        gate("time-bound", "FAIL", "Action request timestamp is implausibly in the future.")
        return finish("REJECT", ["INVALID_CONTRACT"], "NO_ACTION")
    gate("time-bound", "PASS", "Envelope timestamp and expiry checks passed.")

    if policy.get("status") not in {"ADMITTED", "ACTIVE"} or policy.get("enforcement_status") not in {"ACTIVE", "ENFORCED"}:
        gate("policy-admission", "HOLD", "Policy is not admitted and active for runtime enforcement.")
        return finish("HOLD", ["POLICY_NOT_ADMITTED"], "NO_ACTION")

    binding = envelope.get("policy_binding", {})
    if (binding.get("policy_id") != policy.get("policy_id")
            or binding.get("version") != policy.get("version")
            or binding.get("digest") != policy_digest(policy)):
        gate("policy-binding", "FAIL", "Action is not bound to the exact active policy version and digest.")
        return finish("REJECT", ["POLICY_VERSION_MISMATCH"], "REVERIFY")
    gate("policy-binding", "PASS", "Action references the active policy digest.")

    actor_request = envelope.get("actor", {})
    actor_id = actor_request.get("identity_id")
    actor = actors.get(str(actor_id)) if actor_id is not None else None
    if actor is None:
        gate("actor-identity", "FAIL", "Actor identity is unknown to the trusted registry.")
        return finish("REJECT", ["MISSING_IDENTITY"], "NO_ACTION")
    if actor.get("status") == "REVOKED":
        gate("actor-identity", "FAIL", "Actor identity has been revoked.")
        return finish("REJECT", ["MISSING_IDENTITY"], "NO_ACTION")
    if actor.get("status") not in {"ADMITTED", "ACTIVE"}:
        gate("actor-identity", "HOLD", "Actor profile is not admitted.")
        return finish("HOLD", ["MISSING_IDENTITY"], "REVERIFY")
    if (actor_request.get("role") != actor.get("role")
            or actor_request.get("authority_ceiling") != actor.get("authority_ceiling")):
        gate("actor-authority", "FAIL", "Envelope role/ceiling differs from trusted actor profile.")
        return finish("REJECT", ["MISSING_AUTHORITY"], "NO_ACTION")
    if actor.get("authority_ceiling") not in TIERS:
        gate("actor-authority", "HOLD", "Trusted actor profile has no valid authority ceiling.")
        return finish("HOLD", ["MISSING_AUTHORITY"], "REVERIFY")
    gate("actor-authority", "PASS", "Actor identity and claimed authority ceiling match trusted profile.")

    tool_request = envelope.get("tool", {})
    tool_id = str(tool_request.get("tool_id", ""))
    tool = tools.get(tool_id)
    if tool is None:
        gate("tool-admission", "FAIL", "Tool is absent from the trusted tool registry.")
        return finish("QUARANTINE", ["UNKNOWN_TOOL"], "QUARANTINE_TOOL")
    if tool.get("status") == "QUARANTINED":
        gate("tool-admission", "FAIL", "Tool is quarantined.")
        return finish("QUARANTINE", ["TOOL_QUARANTINED"], "QUARANTINE_TOOL")
    if tool.get("status") not in {"ADMITTED", "ACTIVE"}:
        gate("tool-admission", "HOLD", "Tool is not admitted for execution.")
        return finish("HOLD", ["CAPABILITY_NOT_ADMITTED"], "REVERIFY")
    identity_fields = ("version", "adapter_id", "adapter_digest", "capability_id")
    if any(tool_request.get(field) != tool.get(field) for field in identity_fields):
        gate("tool-identity", "FAIL", "Tool version, adapter digest, or capability does not match registry.")
        return finish("QUARANTINE", ["TOOL_QUARANTINED"], "QUARANTINE_TOOL")
    if tool.get("max_authority") not in TIERS:
        gate("tool-authority", "HOLD", "Tool registry has no valid authority ceiling.")
        return finish("HOLD", ["MISSING_AUTHORITY"], "REVERIFY")
    gate("tool-identity", "PASS", "Tool identity/version/digest/capability match trusted registry.")

    operation = envelope.get("operation", {})
    operation_class = operation.get("class")
    required_tier = OPERATION_TIER.get(str(operation_class))
    if required_tier is None:
        gate("operation", "FAIL", "Unknown operation class.")
        return finish("REJECT", ["INVALID_CONTRACT"], "NO_ACTION")
    if operation_class not in actor.get("allowed_operation_classes", []):
        gate("actor-operation", "FAIL", "Operation class is not allowed for this actor.")
        return finish("REJECT", ["MISSING_AUTHORITY"], "NO_ACTION")
    if operation_class not in tool.get("allowed_operation_classes", []):
        gate("tool-operation", "FAIL", "Operation class is not allowed for this tool adapter.")
        return finish("REJECT", ["MISSING_AUTHORITY"], "NO_ACTION")

    default_ceiling = policy.get("default_max_authority", "A3_SANDBOX_MUTATE")
    ceilings = [
        actor.get("authority_ceiling"),
        tool.get("max_authority"),
        environment_ceiling,
        default_ceiling,
    ]
    selected_tier = _min_tier(ceilings) or "NONE"
    if selected_tier == "NONE" or TIERS[required_tier] > TIERS[selected_tier]:
        gate("authority-intersection", "FAIL", "Requested operation exceeds the intersection of actor, tool, environment and policy ceilings.")
        return finish("REJECT", ["MISSING_AUTHORITY"], "NO_ACTION")
    gate("authority-intersection", "PASS", "Operation is within the strictest configured authority ceiling.")

    scope = envelope.get("scope", {})
    resources = set(scope.get("resource_ids", []))
    if not resources:
        gate("scope", "HOLD", "Resource scope is missing.")
        return finish("HOLD", ["SCOPE_MISMATCH"], "REPAIR_ENVELOPE")
    for boundary_name, boundary in (
        ("actor", actor.get("allowed_resource_ids")),
        ("tool", tool.get("allowed_resource_ids")),
    ):
        if not isinstance(boundary, list) or not resources.issubset(set(boundary)):
            gate("scope", "FAIL", f"Requested resource scope exceeds or is unknown to the {boundary_name} allowlist.")
            return finish("REJECT", ["SCOPE_MISMATCH"], "NO_ACTION")
    environment = scope.get("environment")
    for boundary_name, allowed in (
        ("actor", actor.get("allowed_environments")),
        ("tool", tool.get("allowed_environments")),
    ):
        if not isinstance(allowed, list) or environment not in allowed:
            gate("environment", "FAIL", f"Environment is not allowlisted by the {boundary_name} profile.")
            return finish("REJECT", ["SCOPE_MISMATCH"], "NO_ACTION")
    requested_classes = set(scope.get("data_classes", []))
    if not requested_classes or not requested_classes.issubset(set(actor.get("allowed_data_classes", []))):
        gate("data-class", "FAIL", "Requested data class is absent from or exceeds the actor allowlist.")
        return finish("REJECT", ["SCOPE_MISMATCH"], "NO_ACTION")
    if not requested_classes.issubset(set(tool.get("allowed_data_classes", []))):
        gate("data-class", "FAIL", "Requested data class exceeds the tool allowlist.")
        return finish("REJECT", ["SCOPE_MISMATCH"], "NO_ACTION")
    gate("scope", "PASS", "Resource, environment and data scope remain within registered allowlists.")

    budget = envelope.get("budget", {})
    caps = dict(policy.get("initial_nonproduction_budget_ceiling", {}))
    for key in BUDGET_KEYS:
        requested = budget.get(key)
        cap = caps.get(key)
        actor_cap = actor.get("budget", {}).get(key)
        tool_cap = tool.get("budget", {}).get(key)
        if not isinstance(requested, (int, float)) or isinstance(requested, bool) or requested < 0:
            gate("budget", "FAIL", f"Budget field {key} is missing or invalid.")
            return finish("HOLD", ["BUDGET_EXCEEDED"], "REPAIR_ENVELOPE")
        for label, limit in (("policy", cap), ("actor", actor_cap), ("tool", tool_cap)):
            if limit is None or requested > limit:
                gate("budget", "HOLD", f"Requested {key} exceeds or is not bounded by {label} budget.")
                return finish("HOLD", ["BUDGET_EXCEEDED"], "REPAIR_ENVELOPE")
    gate("budget", "PASS", "All requested budget dimensions fit policy, actor and tool limits.")

    idempotency_key = str(envelope.get("idempotency_key", ""))
    if len(idempotency_key) < 16:
        gate("idempotency", "FAIL", "Idempotency key is too short.")
        return finish("HOLD", ["INVALID_CONTRACT"], "REPAIR_ENVELOPE")
    bound_digest = approval_bound_action_digest(envelope)
    previous = idempotency_records.get(idempotency_key)
    if previous:
        gate("idempotency", "FAIL", "Idempotency key has already been recorded; runtime must retrieve the prior result rather than execute again.")
        return finish("HOLD", ["IDEMPOTENCY_CONFLICT"], "NO_ACTION")
    gate("idempotency", "PASS", "Idempotency key is not present in the supplied trusted record set.")

    risk = envelope.get("risk", {})
    risk_tier = risk.get("tier")
    if risk_tier not in RISK_RANK:
        gate("risk", "FAIL", "Unknown risk tier.")
        return finish("HOLD", ["INVALID_CONTRACT"], "REPAIR_ENVELOPE")

    verification = envelope.get("verification", {})
    requires_proof = bool(tool.get("requires_fresh_proof")) or RISK_RANK[risk_tier] >= 3 or operation_class in {
        "RELEASE_PREPARE", "RELEASE_DEPLOY", "IRREVERSIBLE_OR_PHYSICAL"
    }
    if requires_proof:
        proof_expiry = _timestamp(verification.get("proof_valid_until"))
        if (not verification.get("proof_refs") or not verification.get("proof_digest")
                or proof_expiry is None or proof_expiry <= now):
            gate("proof-freshness", "HOLD", "This operation requires current, referenced proof.")
            return finish("HOLD", ["STALE_PROOF"], "REVERIFY")
    gate("proof-freshness", "PASS" if requires_proof else "NOT_REQUIRED",
         "Fresh proof is valid." if requires_proof else "No additional proof-freshness rule applies to this action class.")

    approval_req = envelope.get("approval_requirement", {})
    approval_rules = policy.get("approval_rules", {})
    needs_approval = (
        approval_req.get("human_approval_required") is True
        or RISK_RANK[risk_tier] >= RISK_RANK.get(
            approval_rules.get("require_human_approval_from_risk_tier", "R3_HIGH"), 3
        )
        or operation_class in {"RELEASE_DEPLOY", "IRREVERSIBLE_OR_PHYSICAL"}
    )
    if needs_approval:
        refs = approval_req.get("approval_refs", [])
        if (approval_req.get("human_approval_required") is not True or not refs
                or not approval_req.get("approval_digest")):
            gate("approval", "HOLD", "A separate human approval bound to this exact action is required.")
            return finish("HOLD", ["APPROVAL_REQUIRED"], "REQUEST_APPROVAL")
        valid_approval = None
        for ref in refs:
            candidate = approvals.get(str(ref))
            if not candidate or candidate.get("status") != "APPROVED":
                continue
            valid_until = _timestamp(candidate.get("valid_until"))
            if (candidate.get("approved_action_digest") != bound_digest
                    or candidate.get("approval_digest") != approval_req.get("approval_digest")
                    or valid_until is None or valid_until <= now):
                continue
            if candidate.get("approver_identity_id") == actor_id:
                continue
            if (approval_rules.get("independent_approver_for_high_risk", True)
                    and RISK_RANK[risk_tier] >= 3
                    and candidate.get("independent") is not True):
                continue
            valid_approval = candidate
            break
        if valid_approval is None:
            gate("approval", "HOLD", "No active, exact-action, non-self approval satisfies the approval contract.")
            return finish("HOLD", ["APPROVAL_INVALID"], "REQUEST_APPROVAL")
        gate("approval", "PASS", "Approval is valid, action-bound, unexpired and independent where required.")
    else:
        gate("approval", "NOT_REQUIRED", "Action class and risk do not require additional human approval.")

    gate("execution-boundary", "PASS", "Evaluator authorizes only the exact envelope; this module does not invoke an adapter.")
    return finish("ALLOW", ["POLICY_ACCEPTED"], "EXECUTE_EXACT_ACTION")
