"""Local-only agent activation with explicit allowlist and evidence receipts.

Activation means deterministic in-process research jobs, NOT remote LLMs or finance execution.
"""
from __future__ import annotations
import hashlib
import json
from scripts.vx_forge_mission_contract import plan_mission
from tools.impossibility_engine.engine import assess

ALLOWED_ROLES = frozenset({"research", "mathematics", "physics", "software", "innovation", "finance_analysis", "risk_review", "independent_verification"})

def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

def execute_local(mission, agents, *, approved=False):
    plan = plan_mission(mission, agents)
    if approved is not True:
        return {"status": "HOLD", "reason": "explicit local activation required", "plan_digest": plan["digest"], "executed": 0}
    if mission.get("action", "research") not in {"research", "design", "simulate", "compare", "audit"}:
        raise ValueError("forbidden action")
    results = []
    for assignment in plan["agents"]:
        role = assignment["role"]
        if role not in ALLOWED_ROLES:
            raise ValueError("unapproved role")
        if role in {"research", "innovation", "independent_verification", "software", "mathematics", "physics", "risk_review", "finance_analysis"}:
            result = {"role": role, "agent_id": assignment["agent_id"],
                      "state": "LOCAL_ANALYSIS_ONLY",
                      "finding": "No external evidence or solver execution; manual validation required"}
            if role in {"research", "innovation", "mathematics", "physics"}:
                triage = assess({"title": mission["mission_id"], "goal": mission["goal"],
                                 "constraints": mission.get("constraints", []),
                                 "evidence": mission.get("evidence", []),
                                 "resources": []})
                result["triage_status"] = triage["status"]
            results.append(result)
    receipt = {"schema": "VX.LocalAgentReceipt.v1", "status": "LOCAL_COMPLETED",
               "scope": "IN_PROCESS_ONLY", "financial_actions": 0, "provider_calls": 0,
               "plan_digest": plan["digest"], "results": results,
               "verified": False, "admission": "HOLD"}
    receipt["receipt_digest"] = _hash(receipt)
    return receipt

if __name__ == "__main__":
    agents = [{"id": "research-local", "role": "research"}, {"id": "review-local", "role": "independent_verification"}]
    mission = {"mission_id": "VX-LOCAL-SMOKE-001", "goal": "Inspect a proposed indexing optimization",
               "roles": ["research", "independent_verification"]}
    print(json.dumps(execute_local(mission, agents, approved=True), sort_keys=True))
