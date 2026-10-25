"""Read-only validator for proposed VX Engineering Forge domain registry."""
import json
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "registry/research/vx-engineering-forge-domains.v1.json"

def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ["root must be object"]
    if data.get("activation") != "DISABLED":
        errors.append("activation must remain DISABLED")
    if data.get("status") != "PROPOSED":
        errors.append("status must be PROPOSED")
    domains = data.get("domains")
    if not isinstance(domains, list) or not domains:
        return errors + ["domains must be nonempty list"]
    seen = set()
    for i, entry in enumerate(domains):
        if not isinstance(entry, dict):
            errors.append(f"domains[{i}] must be object")
            continue
        for key in ("id", "name"):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                errors.append(f"domains[{i}].{key} required")
        ident = entry.get("id")
        if isinstance(ident, str):
            if ident in seen:
                errors.append(f"duplicate domain id: {ident}")
            seen.add(ident)
        if not isinstance(entry.get("methods"), list) or not entry["methods"] or any(not isinstance(m, str) or not m.strip() for m in entry["methods"]):
            errors.append(f"domains[{i}].methods invalid")
    p = data.get("policies", {})
    if not isinstance(p, dict) or p.get("external_spend_sar") != 0 or p.get("auto_merge") is not False or p.get("auto_publish") is not False or p.get("no_proof_no_commit") is not True:
        errors.append("unsafe policies")
    if not isinstance(p, dict) or not {"project.genome", "Ω.000"}.issubset(set(p.get("protected_files", []))):
        errors.append("protected files missing")
    return errors

if __name__ == "__main__":
    errors = validate(json.loads(REGISTRY.read_text(encoding="utf-8")))
    print(json.dumps({"status": "FAIL" if errors else "PASS", "errors": errors}, ensure_ascii=False))
    raise SystemExit(bool(errors))
