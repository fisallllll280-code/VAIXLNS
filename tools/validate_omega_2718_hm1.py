"""Validate Ω.2718/HM-1 without external dependencies."""
import json, sys
from pathlib import Path

EXPECTED_LAYERS = [f"Ω2718-HM1-L{i:02d}" for i in range(1, 12)]
EXPECTED_GATES = {"STRUCTURAL_VALIDATION","SOURCE_PROVENANCE","CRYPTOGRAPHIC_TRUST","TEMPORAL_VALIDITY","SEMANTIC_DRIFT","CONFLICT_RESOLUTION","INDEPENDENT_AUDIT","FAULT_INJECTION_RECOVERY","REPRODUCIBILITY","AUTHORIZED_RATIFICATION"}

def validate(m):
    errors = []
    if m.get("domain_id") != "Ω.2718": errors.append("DOMAIN_ID_MISMATCH")
    if m.get("canonical_source") != {"path":"project.genome","mutation":"FORBIDDEN"}: errors.append("CANONICAL_SOURCE_NOT_READ_ONLY")
    if m.get("master_index") != {"id":"Ω.000","path":"registry/omega/omega-000-master-index.json","mutation":"FORBIDDEN"}: errors.append("MASTER_INDEX_NOT_READ_ONLY")
    layers = m.get("layers", [])
    ids = [x.get("id") for x in layers if isinstance(x, dict)]
    if ids != EXPECTED_LAYERS: errors.append("LAYER_SET_OR_ORDER_INVALID")
    if len({x.get("name") for x in layers if isinstance(x,dict)}) != 11: errors.append("LAYER_NAMES_NOT_UNIQUE")
    if m.get("state") not in {"PROPOSAL","SPECIFIED","IMPLEMENTED","VERIFIED","CONFLICT","PARTIAL"}: errors.append("INVALID_STATE")
    if m.get("closure_state") != "BLOCKED_NOT_VERIFIED" and m.get("closure_state") != "OPEN":
        if m.get("closure_state") == "CLOSED_VERIFIED":
            errors.append("CLOSED_REQUIRES_EXTERNAL_EVIDENCE_VERIFIER_NOT_IMPLEMENTED")
        else: errors.append("INVALID_CLOSURE_STATE")
    if m.get("ratification_policy", {}).get("state") == "POLICY_NOT_CONFIGURED":
        if m.get("ratification_policy", {}).get("approval_threshold") is not None: errors.append("UNCONFIGURED_THRESHOLD_MUST_BE_NULL")
    if m.get("trust_roots") != []: errors.append("TRUST_ROOTS_REQUIRE_EXTERNAL_CRYPTOGRAPHIC_VALIDATION")
    if m.get("ratification_ledger", {}).get("state") == "VERIFIED" and not m.get("ratification_ledger", {}).get("external_immutability_evidence"): errors.append("LEDGER_IMMUTABILITY_EVIDENCE_MISSING")
    if m.get("independent_audit", {}).get("state") == "PASS" and m.get("independent_audit", {}).get("self_audit_forbidden") is not True: errors.append("INDEPENDENT_AUDIT_RULE_BROKEN")
    gates = set(m.get("acceptance_gates", []))
    if gates != EXPECTED_GATES: errors.append("ACCEPTANCE_GATE_SET_MISMATCH")
    if m.get("state") == "VERIFIED" and m.get("closure_state") != "CLOSED_VERIFIED": errors.append("VERIFIED_STATE_WITHOUT_CLOSED_EVIDENCE")
    return errors

def main():
    root = Path(__file__).resolve().parents[1]
    path = root / "registry/omega/omega-2718-hm1-closure.v1.json"
    try: manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"valid":False,"errors":[f"LOAD_FAILED:{e}"]}, ensure_ascii=False)); return 2
    errors = validate(manifest)
    print(json.dumps({"valid":not errors,"errors":errors,"domain_id":manifest.get("domain_id"),"state":manifest.get("state"),"closure_state":manifest.get("closure_state"),"layer_count":len(manifest.get("layers",[]))}, ensure_ascii=True, indent=2))
    return 1 if errors else 0
if __name__ == "__main__": sys.exit(main())
