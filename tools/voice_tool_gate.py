"""VAIXLNS voice tool safety gate (local decision logic, not realtime connectivity)."""
from dataclasses import dataclass
from typing import FrozenSet

READ_TOOLS=frozenset({"search_knowledge_base","get_order_status"})
MUTATING_TOOLS=frozenset({"create_support_ticket","request_human_handoff"})
KNOWN_TOOLS=READ_TOOLS|MUTATING_TOOLS

@dataclass(frozen=True)
class VoiceToolRequest:
    session_id: str
    principal_id: str
    tool: str
    request_id: str
    environment: str
    scope: str
    confirmation_ref: str = ""
    confirmation_request_id: str = ""
    consent_to_record: bool = False

@dataclass(frozen=True)
class ToolPolicy:
    allowed: FrozenSet[str]
    grant_active: bool
    scope: str
    environment: str = "isolated"

def evaluate(request: VoiceToolRequest, policy: ToolPolicy) -> dict:
    """Pure fail-closed eligibility decision; never executes tool calls."""
    if not all((request.session_id,request.principal_id,request.request_id,request.scope)):
        return {"decision":"HOLD","reason":"INCOMPLETE_IDENTITY"}
    if request.tool not in KNOWN_TOOLS:
        return {"decision":"REJECT","reason":"UNKNOWN_TOOL"}
    if not policy.grant_active or request.tool not in policy.allowed:
        return {"decision":"HOLD","reason":"TOOL_NOT_AUTHORIZED"}
    if request.scope!=policy.scope or request.environment!=policy.environment:
        return {"decision":"HOLD","reason":"SCOPE_MISMATCH"}
    if request.tool in MUTATING_TOOLS and (not request.confirmation_ref or request.confirmation_request_id!=request.request_id):
        return {"decision":"HOLD","reason":"BOUND_CONFIRMATION_REQUIRED"}
    return {"decision":"ELIGIBLE_FOR_BACKEND_CHECK","reason":"NO_EXECUTION_PERFORMED"}

def audit_projection(request:VoiceToolRequest,decision:dict)->dict:
    """Minimal metadata: no audio, transcript, credentials or customer PII."""
    return {"session_id":request.session_id,"request_id":request.request_id,
            "tool":request.tool,"decision":decision["decision"],"reason":decision["reason"],
            "recording_consent":request.consent_to_record}
