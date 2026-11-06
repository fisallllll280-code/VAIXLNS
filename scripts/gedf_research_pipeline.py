#!/usr/bin/env python3
"""Compile a pinned GEDF research capsule into a deterministic review plan; never executes or promotes."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA = "vaixl.gedf.research-capsule.v1"
SOURCE_TYPES = {"PAPER","REPOSITORY","STANDARD","OFFICIAL_DOCS","BENCHMARK","DATASET"}
EVIDENCE_LEVELS = {"ABSTRACT_ONLY","FULL_TEXT_REVIEWED","SOURCE_CODE_INSPECTED","TEST_EXECUTED","MEASURED"}
DOMAINS = {"mathematics","computation","software","physics"}
TASKS = [
 ("SOURCE_INTEGRITY", []), ("CLAIM_SOURCE_MAPPING", ["SOURCE_INTEGRITY"]),
 ("PRIOR_ART_AND_COUNTEREVIDENCE", ["CLAIM_SOURCE_MAPPING"]),
 ("MATHEMATICAL_AND_DIMENSIONAL_REVIEW", ["CLAIM_SOURCE_MAPPING"]),
 ("COMPUTATIONAL_STABILITY_AND_UNCERTAINTY", ["MATHEMATICAL_AND_DIMENSIONAL_REVIEW"]),
 ("SOFTWARE_AND_SUPPLY_CHAIN_REVIEW", ["CLAIM_SOURCE_MAPPING"]),
 ("PHYSICS_INVARIANTS_AND_VALIDITY_DOMAIN", ["MATHEMATICAL_AND_DIMENSIONAL_REVIEW"]),
 ("INTEGRATION_CONFORMANCE", ["SOFTWARE_AND_SUPPLY_CHAIN_REVIEW","COMPUTATIONAL_STABILITY_AND_UNCERTAINTY"]),
 ("SANDBOX_TEST_SIMULATION", ["INTEGRATION_CONFORMANCE","PHYSICS_INVARIANTS_AND_VALIDITY_DOMAIN"]),
 ("INDEPENDENT_FALSIFICATION", ["SANDBOX_TEST_SIMULATION","PRIOR_ART_AND_COUNTEREVIDENCE"]),
 ("HUMAN_GOVERNANCE_REVIEW", ["INDEPENDENT_FALSIFICATION"])
]

def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=False, allow_nan=False).encode()

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def validate_capsule(c: Any) -> list[str]:
    e=[]
    if not isinstance(c,dict): return ["capsule must be an object"]
    if c.get("schema") != SCHEMA: e.append("invalid schema")
    for k in ("mission_id","research_question","domains","sources","claims","hypotheses"):
        if k not in c: e.append("missing field: "+k)
    for k in ("mission_id","research_question"):
        if not isinstance(c.get(k),str) or not c[k].strip(): e.append(k+" required")
    ds=c.get("domains")
    if not isinstance(ds,list) or not ds or any(not isinstance(x,str) for x in ds): e.append("domains must be a non-empty string list"); ds=[]
    else:
        if len(set(ds)) != len(ds): e.append("domains must be unique")
        if DOMAINS-set(ds): e.append("core domains missing: "+",".join(sorted(DOMAINS-set(ds))))
    srcs=c.get("sources")
    if not isinstance(srcs,list) or not srcs: e.append("sources must be non-empty"); srcs=[]
    ids=set()
    for i,s in enumerate(srcs):
        if not isinstance(s,dict): e.append(f"sources[{i}] must be an object"); continue
        sid=s.get("source_id")
        if not isinstance(sid,str) or not sid.strip(): e.append(f"sources[{i}].source_id required"); continue
        if sid in ids: e.append("duplicate source_id: "+sid)
        ids.add(sid)
        if s.get("source_type") not in SOURCE_TYPES: e.append(sid+": invalid source_type")
        u=urlparse(s.get("url",""))
        if u.scheme!="https" or not u.netloc: e.append(sid+": URL must be HTTPS")
        if s.get("evidence_level") not in EVIDENCE_LEVELS: e.append(sid+": invalid evidence_level")
        text=s.get("captured_text"); digest=s.get("captured_text_sha256")
        if not isinstance(text,str) or not isinstance(digest,str): e.append(sid+": captured text and SHA-256 required")
        elif sha(text.encode())!=digest: e.append(sid+": captured text SHA-256 mismatch")
        if not isinstance(s.get("retrieved_at_utc"),str) or not s["retrieved_at_utc"].strip(): e.append(sid+": retrieval time required")
    claims=c.get("claims")
    if not isinstance(claims,list) or not claims: e.append("claims must be non-empty"); claims=[]
    claim_ids=set()
    for i,cl in enumerate(claims):
        if not isinstance(cl,dict): e.append(f"claims[{i}] must be an object"); continue
        cid=cl.get("claim_id")
        if not isinstance(cid,str) or not cid.strip(): e.append(f"claims[{i}].claim_id required"); continue
        if cid in claim_ids: e.append("duplicate claim_id: "+cid)
        claim_ids.add(cid)
        if not isinstance(cl.get("statement"),str) or not cl["statement"].strip(): e.append(cid+": statement required")
        refs=cl.get("source_ids")
        if not isinstance(refs,list) or not refs: e.append(cid+": source_ids required")
        else:
            for ref in refs:
                if ref not in ids: e.append(cid+": unknown source_id "+str(ref))
        if cl.get("epistemic_state") not in {"OBSERVATION","SOURCE_ASSERTION","INFERENCE","HYPOTHESIS","COUNTEREVIDENCE"}: e.append(cid+": invalid epistemic_state")
        if cl.get("independent_confirmation") not in {True,False,None}: e.append(cid+": invalid independent_confirmation")
    hyps=c.get("hypotheses")
    if not isinstance(hyps,list) or not hyps: e.append("hypotheses must be non-empty"); hyps=[]
    for i,h in enumerate(hyps):
        if not isinstance(h,dict): e.append(f"hypotheses[{i}] must be an object"); continue
        for k in ("hypothesis_id","mechanism","falsification_method","baseline_comparison"):
            if not isinstance(h.get(k),str) or not h[k].strip(): e.append(f"hypotheses[{i}].{k} required")
        if not isinstance(h.get("alternatives"),list) or not h["alternatives"] or any(not isinstance(x,str) or not x.strip() for x in h["alternatives"]): e.append(f"hypotheses[{i}].alternatives required")
    return e

def compile_capsule(c: dict[str,Any], candidate: dict[str,Any]|None=None) -> dict[str,Any]:
    errors=validate_capsule(c)
    if errors: raise ValueError("; ".join(errors))
    sources=sorted(c["sources"],key=lambda x:x["source_id"])
    claims=sorted(c["claims"],key=lambda x:x["claim_id"])
    hypotheses=sorted(c["hypotheses"],key=lambda x:x["hypothesis_id"])
    tasks=[{"task_id":name,"depends_on":deps,"state":"PLANNED_NOT_EXECUTED"} for name,deps in TASKS]
    assessment=None
    if candidate is not None:
        from vcre.synthesis import assess_candidate
        assessment=assess_candidate(candidate).to_dict()
    material={"schema":"vaixl.gedf.research-engineering-plan.v1","mission_id":c["mission_id"],"research_question":c["research_question"],"domains":sorted(c["domains"]),
      "source_receipts":[{k:s[k] for k in ("source_id","url","source_type","evidence_level","captured_text_sha256","retrieved_at_utc")} for s in sources],
      "claims":claims,"hypotheses":hypotheses,"verification_tasks":tasks,"vcre_assessment":assessment}
    return {**material,"plan_sha256":sha(canon(material)),"status":"PENDING_HUMAN_REVIEW","execution_performed":False,
      "external_sources_fetched":False,"canonical_promotion_allowed":False,
      "epistemic_boundary":["SHA-256 validates captured bytes, not source authenticity or claim truth.","Abstract-only is not full-text review.",
      "A plan is not proof that a task ran.","VCRE reviewability is not scientific validation or deployment authority.","Novelty remains provisional until prior-art review."]}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--capsule",required=True,type=Path); p.add_argument("--candidate",type=Path); p.add_argument("--output",required=True,type=Path); a=p.parse_args()
    try:
        c=json.loads(a.capsule.read_text(encoding="utf-8")); candidate=json.loads(a.candidate.read_text(encoding="utf-8")) if a.candidate else None
        result=compile_capsule(c,candidate)
    except (OSError,json.JSONDecodeError,ValueError) as ex:
        print("GEDF_HOLD: "+str(ex)); return 2
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(f"GEDF_PLAN_READY_FOR_REVIEW: {a.output} sha256={result['plan_sha256']}"); return 0
if __name__=="__main__": raise SystemExit(main())
