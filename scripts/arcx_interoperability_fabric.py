"""ARC-X connector contract validation and route planning.

No network calls, tool invocation, or permission grants are performed here.
"""
import hashlib
import json

SCHEMA_VERSION = "arcx-tool-contract/v1"
VALID_STATES = {"PROPOSED", "REGISTERED", "CONNECTED", "VERIFIED", "DISABLED", "QUARANTINED"}
VALID_RISKS = {"READ", "ANALYSIS", "WRITE", "PRIVILEGED", "DESTRUCTIVE"}


def stable_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def validate_connector(manifest):
    errors = []
    if not isinstance(manifest, dict):
        return {"valid": False, "errors": ["MANIFEST_NOT_OBJECT"]}
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("SCHEMA_VERSION_UNSUPPORTED")
    for field in ("tool_id", "provider", "adapter_version", "contract_version"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            errors.append(field.upper() + "_REQUIRED")
    if manifest.get("state") not in VALID_STATES:
        errors.append("STATE_INVALID")
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("CAPABILITIES_REQUIRED")
        capabilities = []
    for index, capability in enumerate(capabilities):
        if not isinstance(capability, dict):
            errors.append(f"CAPABILITY_{index}_INVALID")
            continue
        if not capability.get("name"):
            errors.append(f"CAPABILITY_{index}_NAME_REQUIRED")
        if capability.get("risk") not in VALID_RISKS:
            errors.append(f"CAPABILITY_{index}_RISK_INVALID")
        if not capability.get("input_schema_ref") or not capability.get("output_schema_ref"):
            errors.append(f"CAPABILITY_{index}_SCHEMA_REFS_REQUIRED")
    auth = manifest.get("authorization")
    if not isinstance(auth, dict):
        errors.append("AUTHORIZATION_REQUIRED")
        auth = {}
    if not isinstance(auth.get("granted_scopes"), list):
        errors.append("GRANTED_SCOPES_INVALID")
    if auth.get("credential_mode") not in {"SECRET_REFERENCE_ONLY", "NO_CREDENTIALS"}:
        errors.append("CREDENTIAL_MODE_UNSAFE")
    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict) or not provenance.get("source") or not provenance.get("digest"):
        errors.append("PROVENANCE_INCOMPLETE")
    errors = sorted(set(errors))
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_id": manifest.get("tool_id"),
        "valid": not errors,
        "errors": errors,
        "manifest_digest": stable_digest(manifest),
    }


def plan_route(manifests, required_capabilities, allow_write=False):
    candidates = []
    unresolved = []
    for required in required_capabilities:
        found = []
        for manifest in manifests:
            check = validate_connector(manifest)
            if not check["valid"] or manifest.get("state") != "VERIFIED":
                continue
            auth = manifest.get("authorization", {})
            if auth.get("policy_admitted") is not True:
                continue
            for capability in manifest.get("capabilities", []):
                risk = capability.get("risk")
                if capability.get("name") != required:
                    continue
                if risk in {"WRITE", "PRIVILEGED", "DESTRUCTIVE"} and not allow_write:
                    continue
                found.append({
                    "tool_id": manifest["tool_id"],
                    "capability": required,
                    "risk": risk,
                    "manifest_digest": check["manifest_digest"],
                    "execution": "NOT_PERFORMED",
                })
        found.sort(key=lambda item: (item["risk"], item["tool_id"]))
        if found:
            candidates.extend(found)
        else:
            unresolved.append(required)
    result = {
        "schema_version": SCHEMA_VERSION,
        "state": "CANDIDATES_AVAILABLE" if not unresolved else "CAPABILITY_GAPS",
        "candidates": candidates,
        "unresolved_capabilities": sorted(set(unresolved)),
        "execution_performed": False,
    }
    result["result_digest"] = stable_digest(result)
    return result
