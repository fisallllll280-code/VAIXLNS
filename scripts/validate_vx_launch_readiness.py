"""Read-only launch audit. Never issues release permits or calls external providers."""
import argparse
import json
from pathlib import Path

MARKETS = {"owned-web","v-exchange","github-marketplace","google-play","apple-app-store"}
PROTECTED = {"project.genome","registry/omega/omega-000-master-index.json"}
GATES = {"runtime_end_to_end","agent_authority","index_restore","provider_live_connection","zero_spend_enforcement","independent_verification","privacy_security","rollback","store_assets","human_approval"}

def inspect(data):
    if not isinstance(data,dict):
        return {"status":"INVALID","release_allowed":False,"errors":["MANIFEST_NOT_OBJECT"]}
    errors=[]
    p=data.get("release_policy")
    if not isinstance(p,dict): p={};errors.append("POLICY_MISSING")
    if isinstance(p.get("max_external_spend_sar"),bool) or p.get("max_external_spend_sar")!=0:errors.append("ZERO_SPEND_REQUIRED")
    for field,value in (("each_release_requires_explicit_approval",True),("main_merge_allowed",False),("auto_publish_allowed",False)):
        if p.get(field) is not value: errors.append("POLICY_"+field.upper())
    paths=p.get("protected_files")
    if not isinstance(paths,list) or not PROTECTED.issubset(set(x for x in paths if isinstance(x,str))):errors.append("PROTECTED_SOURCES")
    if data.get("schema_version")!="1.0.0":errors.append("SCHEMA_VERSION")
    idx=data.get("source_indexes")
    if not isinstance(idx,list) or not idx or not all(isinstance(x,str) and x for x in idx):errors.append("SOURCE_PROVENANCE_MISSING")
    models=data.get("models")
    if not isinstance(models,list):models=[];errors.append("MODELS_MISSING")
    for m in models:
        if not isinstance(m,dict) or not isinstance(m.get("provider"),str):errors.append("BAD_MODEL_RECORD");continue
        if m.get("admission")=="READY" and (m.get("connection")!="LIVE_VERIFIED" or m.get("cost")!="VERIFIED_ZERO"):
            errors.append("UNVERIFIED_MODEL_PROMOTED:"+m["provider"])
    markets=data.get("markets")
    if not isinstance(markets,list) or not markets:markets=[];errors.append("MARKETS_MISSING")
    seen=set()
    for m in markets:
        if not isinstance(m,dict) or m.get("id") not in MARKETS:errors.append("UNKNOWN_MARKET");continue
        if m["id"] in seen:errors.append("DUPLICATE_MARKET")
        seen.add(m["id"])
        if m.get("status")!="HOLD":errors.append("RELEASE_NEEDS_INDEPENDENT_APPROVAL:"+m["id"])
    gates=data.get("gates")
    if not isinstance(gates,dict) or set(gates)!=GATES or not all(type(x) is bool for x in gates.values()):
        errors.append("GATE_SCHEMA");gates={}
    missing=sorted(x for x in GATES if gates.get(x) is not True)
    return {"status":"INVALID" if errors else ("HOLD" if missing else "INDEPENDENT_APPROVAL_REQUIRED"),"errors":errors,"outstanding":missing,"release_allowed":False}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--manifest",type=Path,default=Path("registry/vx-launch-readiness.v1.json"));args=p.parse_args()
    try:result=inspect(json.loads(args.manifest.read_text(encoding="utf-8")))
    except (OSError,ValueError) as exc:result={"status":"INVALID","release_allowed":False,"errors":[str(exc)]}
    print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(2 if result["status"]=="INVALID" else 0)
