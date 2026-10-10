"""Policy-only model routing planner. Does not call providers or execute tools."""
from __future__ import annotations
import hashlib, json
from typing import Any

def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def plan_route(request: dict[str, Any], registry: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    blockers=[]
    if not isinstance(request, dict) or not isinstance(registry, list) or not isinstance(policy, dict):
        return {"state":"BLOCKED","blockers":["INVALID_INPUT_SHAPE"],"candidates":[],"execution_performed":False}
    required={"task_class","required_capabilities","data_class","tenant_id"}
    if not required.issubset(request) or not isinstance(request.get("required_capabilities"),list):
        blockers.append("INVALID_REQUEST_CONTRACT")
    allowed_providers=policy.get("allowed_providers",[])
    allowed_models=policy.get("allowed_models",[])
    allowed_data=policy.get("allowed_data_classes",[])
    allowed_tasks=policy.get("allowed_task_classes",[])
    if not all(isinstance(x,list) for x in (allowed_providers,allowed_models,allowed_data,allowed_tasks)):
        blockers.append("INVALID_POLICY_ALLOWLIST")
        allowed_providers=allowed_models=allowed_data=allowed_tasks=[]
    if request.get("data_class") not in allowed_data: blockers.append("DATA_CLASS_NOT_ALLOWED")
    if request.get("task_class") not in allowed_tasks: blockers.append("TASK_CLASS_NOT_ALLOWED")
    if not isinstance(request.get("tenant_id"),str) or not request.get("tenant_id","").strip(): blockers.append("TENANT_ID_REQUIRED")
    candidates=[]
    if not blockers:
        for entry in registry:
            if not isinstance(entry,dict): continue
            if entry.get("state") not in {"AUTHORIZED","ACTIVE"}: continue
            if entry.get("metadata_state")!="VERIFIED": continue
            if entry.get("provider_id") not in allowed_providers: continue
            if entry.get("model_id") not in allowed_models: continue
            if not set(request["required_capabilities"]).issubset(set(entry.get("capabilities",[]))): continue
            if entry.get("data_policy_allows") is not True: continue
            if entry.get("tenant_isolation_verified") is not True: continue
            candidates.append({"provider_id":entry["provider_id"],"model_id":entry["model_id"],"revision":entry.get("revision"),"contract_sha256":entry.get("contract_sha256")})
    candidates.sort(key=lambda x:(x["provider_id"],x["model_id"],str(x["revision"])))
    state="BLOCKED" if blockers else ("ROUTE_CANDIDATES_READY" if candidates else "NO_ELIGIBLE_MODEL")
    result={"schema_version":"arcx-model-route-plan-v1","state":state,"blockers":sorted(set(blockers)),"tenant_id":request.get("tenant_id"),"candidates":candidates,"fallback_rechecks_policy":True,"provider_called":False,"tool_execution_performed":False,"secrets_accessed":False}
    result["plan_sha256"]=_digest(result)
    return result
