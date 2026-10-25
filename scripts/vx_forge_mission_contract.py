"""Fail-closed research and finance agent mission contracts.

Pure planner only: no trading, bank actions, network, spending, or execution.
"""
from __future__ import annotations
import hashlib
import json

ROLES = frozenset({"research", "mathematics", "physics", "software", "innovation", "finance_analysis", "risk_review", "independent_verification"})
FORBIDDEN = frozenset({"transfer", "trade", "purchase", "withdraw", "deposit", "publish", "merge", "deploy", "execute_payment"})

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

def plan_mission(mission, agents):
    if not isinstance(mission, dict) or not isinstance(agents, list):
        raise ValueError("invalid mission or agent registry")
    mission_id = mission.get("mission_id")
    goal = mission.get("goal")
    if not isinstance(mission_id, str) or not mission_id.strip() or not isinstance(goal, str) or not goal.strip():
        raise ValueError("mission identity and goal required")
    action = mission.get("action", "research")
    if action in FORBIDDEN or action not in {"research", "design", "simulate", "compare", "audit"}:
        raise ValueError("action not permitted")
    seen = set()
    for agent in agents:
        if not isinstance(agent, dict):
            raise ValueError("agent must be object")
        ident, role = agent.get("id"), agent.get("role")
        if not isinstance(ident, str) or not ident.strip() or ident in seen or role not in ROLES:
            raise ValueError("invalid or duplicate agent")
        seen.add(ident)
    requested = mission.get("roles", ["research", "independent_verification"])
    if not isinstance(requested, list) or not requested or any(role not in ROLES for role in requested):
        raise ValueError("invalid requested roles")
    selected = []
    for role in dict.fromkeys(requested):
        matches = sorted((a["id"] for a in agents if a["role"] == role))
        if not matches:
            raise ValueError("missing role: " + role)
        selected.append({"role": role, "agent_id": matches[0], "execution": "DISABLED"})
    if mission.get("budget_sar", 0) != 0:
        raise ValueError("external spending requires separate approval")
    payload = {"schema": "VX.ForgeMission.v1", "mission_id": mission_id, "goal": goal,
               "action": action, "agents": selected, "status": "PLANNED",
               "authority": "NONE", "external_effects": "DISABLED",
               "finance_mode": "ANALYSIS_ONLY", "admission": "HOLD",
               "evidence_required": ["source_commit", "input_digest", "test_receipt", "independent_review"]}
    payload["digest"] = digest(payload)
    return payload
