"""Generate a bounded compute plan; never contacts a cloud provider."""
from __future__ import annotations
import hashlib,json
from typing import Any

def plan_compute(workload: dict[str,Any], policy: dict[str,Any]) -> dict[str,Any]:
 blockers=[]
 if not isinstance(workload,dict) or not isinstance(policy,dict):
  return {"state":"BLOCKED","blockers":["INVALID_INPUT_SHAPE"],"execution_performed":False}
 cpu=workload.get("cpu"); memory=workload.get("memory_gib"); duration=workload.get("duration_minutes"); cost=workload.get("estimated_cost")
 def number(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and v>=0
 if not isinstance(cpu,int) or isinstance(cpu,bool) or cpu<1: blockers.append("INVALID_CPU_REQUEST")
 if not number(memory) or memory<=0: blockers.append("INVALID_MEMORY_REQUEST")
 if not isinstance(duration,int) or isinstance(duration,bool) or duration<1: blockers.append("INVALID_DURATION")
 if not number(cost): blockers.append("INVALID_COST_ESTIMATE")
 if workload.get("region") not in policy.get("allowed_regions",[]): blockers.append("REGION_NOT_ALLOWED")
 if workload.get("image_digest") not in policy.get("approved_image_digests",[]): blockers.append("IMAGE_NOT_APPROVED")
 if number(cost) and number(policy.get("max_cost")) and cost>policy["max_cost"]: blockers.append("BUDGET_LIMIT_EXCEEDED")
 if not isinstance(policy.get("max_cost"),(int,float)) or isinstance(policy.get("max_cost"),bool): blockers.append("INVALID_POLICY_BUDGET")
 if not isinstance(policy.get("max_concurrency"),int) or isinstance(policy.get("max_concurrency"),bool) or policy.get("max_concurrency",0)<1: blockers.append("INVALID_CONCURRENCY_LIMIT")
 if policy.get("ttl_enforced") is not True: blockers.append("TTL_ENFORCEMENT_REQUIRED")
 if policy.get("public_ingress_allowed") is not False: blockers.append("PUBLIC_INGRESS_MUST_BE_DISABLED")
 state="BLOCKED" if blockers else "PLAN_ONLY"
 plan={"schema_version":"arcx-compute-plan-v1","state":state,"workload":workload,"limits":{"max_cost":policy.get("max_cost"),"max_concurrency":policy.get("max_concurrency"),"ttl_enforced":policy.get("ttl_enforced"),"public_ingress_allowed":policy.get("public_ingress_allowed")},"blockers":sorted(set(blockers)),"human_approval_required":True,"approved":False,"provider_called":False,"execution_performed":False}
 plan["plan_sha256"]=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
 return plan
