#!/usr/bin/env python3
"""Build a deterministic innovation catalog with descriptions and operation steps.

Rule-generated mechanisms are draft proposals, never implementation/verification proof.
"""
from __future__ import annotations
import argparse, hashlib, json, re, unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = Path("registry/innovation-operation-profiles.v1.json")
M = Path("docs/innovation/INNOVATION_SEPARATION_MATRIX_V1.md")
C = Path("docs/innovation/VAIXLNS_INNOVATION_CATALOG.md")
F = Path("docs/innovation/innovation-federation.json")
O = Path("registry/omega/omega-000-master-index.json")
R = Path("registry/innovation_measurement.v1.json")
I = Path("docs/indexes/INNOVATION_MASTER_INDEX.md")
OUTJ = Path("registry/innovation-operation-index.v1.json")
OUTM = Path("docs/innovation/INNOVATION_OPERATION_INDEX.md")
SOURCES = [str(x) for x in [M,C,F,O,R,I,P]]
WEIGHT = {"MISSING":0,"CONFLICT":0,"QUARANTINED":0,"PROPOSAL":1,"SOURCE-ASSERTED":1,
          "RECOVERED":2,"SPECIFIED":2,"PARTIAL":3,"IMPLEMENTED":4,"VERIFIED":5,"CANONICAL":5}
SECTION = {
 "discovery / synthesis":"Discovery / synthesis",
 "proof / causality / impact":"Proof / causality / impact",
 "failure / resilience / evolution":"Failure / resilience / evolution",
 "knowledge / reality / meta-control":"Knowledge / reality / meta-control",
 "core architectural fabrics":"Core architectural fabrics",
 "economy / interoperability":"Economy / interoperability",
 "2026-10-07 context additions":"Context / federation / patterns",
 "2026-10-07 operational additions":"Runtime operations / evidence",
 "2026-10-09 research-to-engineering decision additions":"Research / engineering decision",
 "2026-10-09 saudi-first launch and capital-governance additions":"Commercial / governance",
}
RULES = [
 (("proof","verify","verif","conformance","assurance","integrity"),"This capability makes requirements and claims checkable against explicit obligations and reproducible evidence.",["Map requirements/invariants to explicit proof or test obligations.","Run approved checks against a pinned revision and capture tool/version metadata.","Compare outcomes with acceptance criteria; preserve failures and unknowns.","Emit evidence-linked results and block readiness when a critical obligation is unresolved."],["requirements","invariants","artifact revision"],["verification report","evidence bundle","unresolved obligations"]),
 (("causal","counterfactual","blast-radius","impact","temporal"),"This capability analyzes relationships among changes, dependencies, events, and outcomes; inferred relations remain distinct from observed evidence.",["Collect versioned changes, dependency edges, traces, and observations.","Construct a typed graph and attach provenance to every edge.","Separate explicit evidence from inferred or temporal associations.","Trace impact or evaluate a counterfactual against a declared baseline.","Report uncertainty and missing evidence; correlation alone is not causal proof."],["change records","dependency graph","event traces"],["impact/causal graph","trace paths","uncertainty report"]),
 (("replay","event","ledger","deterministic"),"This capability preserves and reconstructs execution history, then checks whether replay yields equivalent state and outputs.",["Capture inputs, initial state, runtime/dependency versions, and event identities.","Store canonical event records with sequence/causal references and hashes.","Replay the recorded sequence in a controlled environment.","Compare state snapshots and output digests with the reference.","Report first divergence and preserve evidence."],["input hashes","event log","runtime configuration"],["replay trace","state/output comparison","divergence report"]),
 (("identity","lineage","nexus","master registry","index","indexer","discovery","semantic linking"),"This capability discovers, identifies, and relates records across sources while preserving original names, provenance, and unresolved identity conflicts.",["Enumerate authorized source scope and capture revisions or content digests.","Extract records, IDs, aliases, interfaces, and references.","Normalize matching keys while preserving original names and lineage.","Build typed dependency, alias, composition, and conflict relations.","Emit a deterministic index plus a queue for ambiguous or missing links."],["repository inventory","source records","IDs/aliases"],["normalized registry","relationship graph","gap/conflict report"]),
 (("semantic","ontology","v-ir","vamm","fingerprint","canonicalization"),"This capability converts supported artifacts into a typed canonical representation under explicit versioned rules.",["Parse inputs against a declared schema or grammar.","Normalize fields using a versioned canonicalization contract.","Check semantic invariants and reject ambiguous forms.","Serialize deterministically and calculate a stable fingerprint.","Compare forms and report differences with source references."],["source artifacts","schema/grammar","canonicalization rules"],["canonical representation","fingerprint","difference report"]),
 (("security","trust","authority","policy","adversarial"),"This capability enforces trust and authority boundaries using explicit policy and controlled adversarial checks.",["Identify assets, trust boundaries, actors, and permitted authority.","Evaluate policy, contracts, dependencies, and threat scenarios.","Run approved checks in a bounded environment.","Record findings, severity, evidence, and mitigations.","Fail closed on critical violations and require separate admission authority."],["threat model","authority policy","artifact/dependency set"],["security findings","policy decision","mitigation obligations"]),
 (("failure","recovery","self-heal","resilience","survival"),"This capability detects and classifies failures, applies bounded recovery, and verifies recovery without erasing the incident history.",["Bind a failure signal to the affected run, component, and revision.","Classify failure type, impact radius, and recovery preconditions.","Isolate unsafe paths and choose an authorized recovery contract.","Execute bounded recovery and verify invariants and health.","Record incident, residual risk, and evidence before resuming."],["failure signals","runtime state","recovery contract"],["incident record","recovery result","residual-risk report"]),
 (("agent","mind","intelligence","coordination","skill"),"This capability coordinates specialist roles through typed handoffs, explicit authority scopes, and evidence-bearing outputs.",["Decompose intent into tasks and capability requirements.","Select eligible roles using declared contracts and authority envelopes.","Dispatch typed handoffs with context, constraints, and evidence links.","Validate returned artifacts and reconcile disagreements or gaps.","Route results through verification and admission gates."],["intent","task graph","agent registry","authority policy"],["handoff graph","agent artifacts","reconciliation report"]),
 (("architecture","genome","compiler","synthesis","laboratory","recombination","generation","forge"),"This capability represents, composes, generates, or compares architecture candidates under explicit requirements and contracts.",["Translate outcomes into capabilities, constraints, invariants, and acceptance criteria.","Load compatible components with contracts and lineage.","Compose or mutate candidates without modifying the canonical baseline.","Evaluate candidates using static checks, simulations, tests, and declared metrics.","Publish assumptions, trade-offs, gaps, and an admission plan."],["requirements","capability records","constraints","tests"],["candidate architecture","dependency graph","comparison report"]),
 (("knowledge","context","memory","reality","world","provenance","evidence"),"This capability preserves source-linked knowledge and exposes stale, conflicting, or unsupported claims.",["Ingest an authorized source with revision, timestamp, and digest.","Extract claims or observations and link them to source evidence.","Connect records to entities, prior versions, supporting and refuting evidence.","Reassess freshness and contradiction when sources/observations change.","Emit an updated graph and unresolved-claim queue."],["versioned sources","claims","runtime observations"],["knowledge graph","provenance links","freshness/contradiction report"]),
 (("contract","interface","fabric","integration","interoperability","boundary","runtime"),"This capability connects components through explicit contracts and validates compatibility at system boundaries.",["Register interface versions, inputs, outputs, and invariants.","Resolve ownership, permissions, dependencies, and compatibility rules.","Validate schemas and preconditions before handoff.","Capture results and events against the contract version.","Hold incompatible transitions until a verified repair or migration exists."],["interface contracts","schemas","version metadata"],["compatibility results","handoff records","migration obligations"]),
 (("decision","governance","evolution","lifecycle","admission","readiness"),"This capability evaluates actions and changes against policy, authority, evidence maturity, lifecycle rules, and rollback conditions.",["Capture request, baseline, owner, and allowed scope.","Gather constraints, evidence, counterevidence, risk, and dependency impact.","Evaluate mandatory gates separately from advisory scores.","Return ADMIT, HOLD, REJECT, or RETURN_FOR_RESEARCH with reasons.","Record decision and lineage; prohibit self-promotion and silent overwrite."],["change request","policy","evidence","baseline"],["decision record","gate results","blockers","rollback obligations"]),
 (("resource","economic","financial","exchange","treasury","capital"),"This capability tracks resources and permitted exchanges against ownership, budget, obligations, approvals, and reconciliation evidence.",["Register each event with owner, unit, timestamp, and source evidence.","Reconcile available resources against obligations and reserves.","Evaluate actions against approved authority and budget envelopes.","Record approval, execution result, and reconciliation artifacts.","Block double counting and unapproved distribution."],["resource records","budgets","obligations","approval evidence"],["resource ledger","reconciliation report","audit record"]),
]

def norm(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", value).split())

def state(value):
    s = str(value or "").upper().replace("_", " ").strip()
    # Match complete state tokens, not accidental substrings such as IMPLEMENTEDIFIED.
    if re.search(r"\bCONFLICT\b", s): return "CONFLICT"
    if re.search(r"\bQUARANTINED\b", s): return "QUARANTINED"
    if re.search(r"\bMISSING\b", s): return "MISSING"
    if re.search(r"\bUNKNOWN\b|\bUNSPECIFIED\b", s): return "UNKNOWN"
    if re.search(r"\b(PARTIAL)\b", s) and re.search(r"\b(VERIFIED|IMPLEMENTED|SPECIFIED)\b", s): return "PARTIAL"
    if re.search(r"\bVERIFIED\b", s): return "VERIFIED"
    if re.search(r"\bIMPLEMENTED\b", s): return "IMPLEMENTED"
    if re.search(r"\bPARTIAL\b", s): return "PARTIAL"
    if re.search(r"\bSPECIFIED\b", s): return "SPECIFIED"
    if re.search(r"\bPROPOS(AL|ED)\b", s): return "PROPOSAL"
    if re.search(r"\bSOURCE[ -]+ASSERTED\b", s): return "SOURCE-ASSERTED"
    if re.search(r"\bRECOVERED\b", s) and re.search(r"\bCANONICAL\b", s): return "CANONICAL"
    if re.search(r"\bCANONICAL\b", s): return "CANONICAL"
    if re.search(r"\bRECOVERED\b", s): return "RECOVERED"
    return "SOURCE-ASSERTED"

def rid(name, family):
    return "INNOV-" + hashlib.sha256((norm(name)+"::"+norm(family)).encode()).hexdigest()[:12].upper()

def readj(root, path):
    f = root / path
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}

def splitrow(line):
    return [x.strip() for x in line.strip().strip("|").split("|")]

def tables(root, path):
    f = root / path
    if not f.is_file(): return []
    lines, found, i = f.read_text(encoding="utf-8").splitlines(), [], 0
    while i + 1 < len(lines):
        if not lines[i].lstrip().startswith("|") or not re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i+1]):
            i += 1; continue
        h = [x.casefold().replace("*","").strip() for x in splitrow(lines[i])]
        rows, i = [], i + 2
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            row = splitrow(lines[i]); row += [""] * max(0, len(h)-len(row)); rows.append(row); i += 1
        found.append((h, rows))
    return found

def make(name, family, owner, status, source, **extra):
    name = re.sub(r"\s+", " ", str(name or "")).strip().strip(chr(96))
    if not name or name.casefold() in {"innovation","family","name","system","concept"}: return {}
    return {"name":name,"family":str(family or "").strip() or "Unclassified / needs review",
            "owner":str(owner or "").strip() or "UNRESOLVED_OWNER","state":state(status),"source":source,**extra}

def parse_matrix(root):
    path, out = str(M), []
    for h, rows in tables(root, path):
        p = {x:i for i,x in enumerate(h)}
        if "innovation" in p and "owner" in p:
            for r in rows:
                x = make(r[p["innovation"]], r[p["family"]] if "family" in p else "", r[p["owner"]],
                         r[p["state"]] if "state" in p else r[p["status"]] if "status" in p else "", path)
                if x: out.append(x)
        elif "family" in p and "representative innovations" in p and "owner" in p:
            for r in rows:
                for name in r[p["representative innovations"]].split(","):
                    x = make(name, r[p["family"]], r[p["owner"]],
                             r[p["state"]] if "state" in p else r[p["status"]] if "status" in p else "", path)
                    if x: out.append(x)
    return out

def parse_catalog(root):
    path, out = str(C), []
    for h, rows in tables(root, path):
        p = {x:i for i,x in enumerate(h)}
        if {"family","system","role"}.issubset(p):
            for r in rows:
                x = make(r[p["system"]], r[p["family"]], r[p.get("canonical owner",p.get("owner",0))],
                         r[p.get("status",p.get("state",0))] if ("status" in p or "state" in p) else "", path,
                         source_description=r[p["role"]])
                if x: out.append(x)
        elif "innovation" in p and "canonical placement" in p:
            for r in rows:
                x = make(r[p["innovation"]], r[p["canonical placement"]], "VAIXLNS (catalog placement; owner review)",
                         "SOURCE-ASSERTED", path, source_description="Canonical placement: "+r[p["canonical placement"]],
                         relationship=r[p["relationship"]] if "relationship" in p else "")
                if x: out.append(x)
    return out

def parse_master(root):
    path, f, out, section = str(I), root / I, [], ""
    if not f.is_file(): return out
    for line in f.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m: section = m.group(1).strip(); continue
        if section.casefold() not in SECTION: continue
        m = re.match(r"^\s*\d+\.\s+(.+?)\s*$", line)
        if m:
            x = make(m.group(1), SECTION[section.casefold()], "VAIXLNS (index-derived; owner review)",
                     "UNKNOWN", path)
            if x: out.append(x)
    return out

def parse_items_json(root, path, default_family=""):
    d, out = readj(root, str(path)), []
    for r in d.get("items",[]) if isinstance(d,dict) else []:
        x = make(r.get("name"), r.get("family") or r.get("category") or default_family,
                 r.get("owner") or r.get("canonical_owner"), r.get("state") or r.get("status"),
                 str(path), native_id=r.get("innovation_index_id",r.get("canonical_id","")),
                 evidence_refs=r.get("evidence_refs",[]))
        if x: out.append(x)
    return out

def parse_omega(root):
    path, d, out = str(O), readj(root,str(O)), []
    for r in d.get("records",[]) if isinstance(d,dict) else []:
        if str(r.get("type","")).upper() not in {"CAPABILITY","INNOVATION","PATTERN","ENGINE","ALGORITHM","PROTOCOL"}: continue
        x = make(r.get("name") or r.get("id"), r.get("family") or r.get("domain") or r.get("parent") or r.get("type"),
                 r.get("canonical_owner") or r.get("owner"), r.get("epistemic_state") or r.get("status"),
                 path, native_id=r.get("id",""), source_description=str(r.get("role","")).replace("_"," "),
                 evidence_refs=r.get("evidence_refs",[]), dependencies=r.get("depends_on",r.get("dependencies",[])))
        if x: out.append(x)
    return out

def get_profiles(root):
    d = readj(root,str(P)); profiles = d.get("profiles",[]) if isinstance(d,dict) else []
    by, aliases = {}, {}
    for profile in profiles:
        n = profile.get("canonical_name","")
        if not n: continue
        by[norm(n)] = profile; aliases[norm(n)] = n
        for alias in profile.get("aliases",[]): aliases[norm(alias)] = n
    return profiles, by, aliases

def draft_rule(name, family):
    text = (family+" "+name).casefold()
    for keys, description, steps, inputs, outputs in RULES:
        if any(k in text for k in keys):
            # Family rules provide draft mechanics only; admission remains evidence-gated.
            return {
                "description": description,
                "steps": steps,
                "inputs": inputs,
                "outputs": outputs,
                "gates": ["source provenance", "explicit contract/constraints", "acceptance criteria", "independent verification"],
                "failures": ["missing specification", "unsupported claim", "unknown dependency", "unresolved conflict", "missing evidence"],
            }
    return {"description":f"{name} is listed under {family}. Current source catalogs do not contain a reviewed functional specification.",
            "steps":["Capture the source identity, revision, and provenance.","Extract declared purpose, inputs, outputs, dependencies, and authority scope.","Link every substantive claim to a source or mark it unknown.","Run available contract, security, and verification checks.","Publish the profile with gaps visible; do not promote without implementation evidence."],
            "inputs":["source records","requirements","evidence references"],"outputs":["innovation profile","lineage","engineering gaps"],
            "gates":["identity","provenance","contract completeness","verification"],"failures":["missing specification","unresolved owner","status conflict","missing evidence"]}

def build(root=ROOT):
    profiles, by_profile, aliases = get_profiles(root)
    candidates = parse_matrix(root)+parse_catalog(root)+parse_items_json(root,F)+parse_items_json(root,R)+parse_omega(root)+parse_master(root)
    found = {aliases.get(norm(x["name"]),norm(x["name"])) for x in candidates if x.get("name")}
    for p in profiles:
        if p.get("canonical_name") and norm(p["canonical_name"]) not in found:
            candidates.append(make(p["canonical_name"],p.get("family",""),p.get("canonical_owner",""),"PROPOSAL",str(P),
                                   source_description=p.get("description",""),evidence_refs=p.get("evidence_refs",[])))
    merged = {}
    for x in candidates:
        if not x: continue
        name = aliases.get(norm(x["name"]),x["name"]); key = norm(name)
        z = merged.setdefault(key,{"name":name,"families":[],"owners":[],"states":[],"sources":[],"descriptions":[],
                                   "evidence":[],"native_ids":[],"dependencies":[],"relations":[],"family":"","owner":"","priority":999})
        priority = 0 if x["source"] == str(O) else 1 if x["source"] == str(M) else 2
        if priority < z["priority"]: z.update({"family":x["family"],"owner":x["owner"],"priority":priority})
        for field,value in [("families",x.get("family")),("owners",x.get("owner"))]:
            if value and value not in z[field]: z[field].append(value)
        obs = {"source":x["source"],"state":x["state"]}
        if obs not in z["states"]: z["states"].append(obs)
        if x["source"] not in z["sources"]: z["sources"].append(x["source"])
        desc = str(x.get("source_description","")).strip()
        if desc and {"source":x["source"],"text":desc} not in z["descriptions"]: z["descriptions"].append({"source":x["source"],"text":desc})
        for ref in x.get("evidence_refs",[]) or []:
            if isinstance(ref,str) and ref and ref not in z["evidence"]: z["evidence"].append(ref)
        for val in [x.get("native_id","")]+list(x.get("dependencies",[]) or []):
            target = "native_ids" if val == x.get("native_id","") else "dependencies"
            if val and val not in z[target]: z[target].append(val)
        if x.get("relationship") and x["relationship"] not in z["relations"]: z["relations"].append(x["relationship"])
    result=[]
    for z in merged.values():
        p=by_profile.get(norm(z["name"]),{})
        family=p.get("family") or z["family"] or (z["families"][0] if z["families"] else "Unclassified / needs review")
        owner=p.get("canonical_owner") or z["owner"] or (z["owners"][0] if z["owners"] else "UNRESOLVED_OWNER")
        all_statuses=sorted({a["state"] for a in z["states"]},key=lambda s:(WEIGHT.get(s,1),s))
        # UNKNOWN index membership is not implementation evidence and must not downgrade status.
        statuses=[s for s in all_statuses if s not in {"UNKNOWN","SOURCE-ASSERTED"}] or all_statuses
        status="CONFLICT" if "CONFLICT" in statuses else (min(statuses,key=lambda s:WEIGHT.get(s,1)) if statuses else "UNKNOWN")
        if any(s in {"IMPLEMENTED","VERIFIED","CANONICAL"} for s in statuses) and any(s in {"PROPOSAL","MISSING","QUARANTINED"} for s in statuses): status="CONFLICT"
        if p:
            description=p.get("description",""); mechanism=p.get("mechanism",[]); inputs=p.get("inputs",[]); outputs=p.get("outputs",[])
            gates=p.get("gates",[]); failures=p.get("failure_modes",[]); basis=p.get("basis","CURATED_PROFILE")
            quality="SOURCE_BACKED" if basis=="REPOSITORY_SPECIFICATION" else "CURATED_DESIGN_DRAFT"
            mechanism_basis=p.get("mechanism_state","DESIGN_DRAFT"); evidence=p.get("evidence_refs",[])
        else:
            rule=draft_rule(z["name"],family)
            source_desc=z["descriptions"][0]["text"] if z["descriptions"] else ""
            description=source_desc or rule["description"]; basis="SOURCE_TEXT" if source_desc else "RULE_DERIVED_DRAFT"
            mechanism,inputs,outputs,gates,failures=(rule[k] for k in ["steps","inputs","outputs","gates","failures"])
            quality="RULE_DERIVED_DRAFT"; mechanism_basis="RULE_DERIVED_DRAFT"; evidence=[]
        source_refs=sorted(set(z["sources"]+evidence))
        result.append({"canonical_id":rid(z["name"],family),"name":z["name"],"family":family,"owner":owner,
            "status":status,"source_statuses":statuses,"status_observations":sorted(z["states"],key=lambda x:(x["source"],x["state"])),
            "status_disagreement":len(statuses)>1 or status=="CONFLICT","description":description,"description_basis":basis,
            "operating_mechanism":list(mechanism),"mechanism_basis":mechanism_basis,"profile_quality":quality,
            "inputs":list(inputs),"outputs":list(outputs),"admission_gates":list(gates),"failure_modes":list(failures),
            "dependencies":sorted(set(z["dependencies"])),"relationships":sorted(set(z["relations"])),"native_ids":sorted(set(z["native_ids"])),
            "source_refs":source_refs,"evidence_refs":sorted(set(z["evidence"]+evidence)),
            "review_required":quality!="SOURCE_BACKED" or status=="CONFLICT","canonical_promotion_allowed":False})
    return sorted(result,key=lambda x:(x["owner"].casefold(),x["family"].casefold(),x["name"].casefold()))

def payload(items):
    return {"schema":"VAIXLNS.InnovationOperationIndex.v1","canonical_source":"project.genome::v1.0.0",
        "authority_anchor":"Ω0_GENESIS_CORE","master_index":"Ω.000",
        "generation":{"mode":"deterministic","generator":"tools/build_innovation_operation_index.py",
          "profile_source":str(P),"source_files":SOURCES,"generated_timestamp":None,"state_promotion":"DISABLED"},
        "summary":{"record_count":len(items),"status_counts":dict(sorted(Counter(x["status"] for x in items).items())),
          "profile_quality_counts":dict(sorted(Counter(x["profile_quality"] for x in items).items())),
          "manual_review_required":sum(1 for x in items if x["review_required"])}, "items":items}

def cell(x): return str(x).replace("|","&#124;").replace("\n"," ")
def markdown(d):
    items,s=d["items"],d["summary"]
    lines=["# VAIXLNS — Innovation Operation Index","","AUTO-GENERATED. Edit the source catalogs or registry/innovation-operation-profiles.v1.json, not this file.",
      "RULE_DERIVED_DRAFT mechanisms are candidate explanations, not verified behavior.",
      "This generator never upgrades implementation, verification, or canonical authority state.","",
      "## Generation summary","",f"- Records: {s['record_count']}",f"- Requires review: {s['manual_review_required']}",
      "- Canonical promotion by this generator: DISABLED","","| State | Count |","|---|---:|"]
    lines += [f"| {k} | {v} |" for k,v in s["status_counts"].items()]
    lines += ["","| Profile quality | Count |","|---|---:|"]
    lines += [f"| {k} | {v} |" for k,v in s["profile_quality_counts"].items()]
    lines += ["","## Innovation records","","| ID | Innovation | Family | Owner | State | Profile |","|---|---|---|---|---|---|"]
    lines += ["| "+" | ".join(cell(x[k]) for k in ["canonical_id","name","family","owner","status","profile_quality"])+" |" for x in items]
    for x in items:
        lines += ["",f"### {x['canonical_id']} — {x['name']}","",f"- Family: {x['family']}",f"- Owner: {x['owner']}",
          f"- State: {x['status']}",f"- Profile quality: {x['profile_quality']}",f"- Description basis: {x['description_basis']}",
          f"- Mechanism basis: {x['mechanism_basis']}",f"- Review required: {'YES' if x['review_required'] else 'NO'}","",x["description"],"","Operating mechanism",""]
        lines += [f"{i}. {step}" for i,step in enumerate(x["operating_mechanism"],1)]
        for label,key in [("Inputs","inputs"),("Outputs","outputs"),("Admission gates","admission_gates"),("Failure modes","failure_modes"),
                          ("Dependencies","dependencies"),("Relationships","relationships"),("Source references","source_refs"),("Evidence references","evidence_refs"),("Native/legacy IDs","native_ids")]:
            lines += ["",label]
            lines += [f"- {v}" for v in x[key]] if x[key] else ["- Not recorded in available sources."]
        if x["status_disagreement"]: lines += ["","WARNING: source states differ or a conflict is explicitly recorded. Review observations before promotion."]
        lines += ["","---"]
    lines += ["","## Automatic update contract","",
      "1. Read the innovation index, separation matrix, catalog, federation JSON, Ω.000 capability records, and measurement registry.",
      "2. Normalize identity keys while preserving source IDs and status observations.",
      "3. Enrich from curated profiles; draft family-specific operating mechanics when a reviewed profile is absent.",
      "4. Generate JSON and Markdown deterministically, then validate source references and status boundaries.",
      "5. Expose unresolved identities and status differences; block silent promotion.",""]
    return "\n".join(lines)

def outputs(root=ROOT):
    d=payload(build(root))
    return {root/OUTJ:json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n",root/OUTM:markdown(d)}

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--check",action="store_true")
    args=parser.parse_args(); files=outputs()
    if args.check:
        stale=[str(p.relative_to(ROOT)) for p,c in files.items() if not p.is_file() or p.read_text(encoding="utf-8")!=c]
        if stale: print("INNOVATION_INDEX_STALE: "+", ".join(stale)); return 1
        print("INNOVATION_INDEX_CURRENT"); return 0
    for p,c in files.items():
        p.parent.mkdir(parents=True,exist_ok=True); p.write_text(c,encoding="utf-8")
        print(f"GENERATED {p.relative_to(ROOT)} ({len(c.encode('utf-8'))} bytes)")
    print(f"INNOVATION_INDEX_BUILT: {len(json.loads(files[ROOT/OUTJ])['items'])} records")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
