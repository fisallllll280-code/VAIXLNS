"""ARC-X connector contract validation and deterministic route-candidate planning.

This module validates declarations only. It never invokes tools, grants authority,
retrieves secrets, or treats a manifest's self-asserted state as cryptographic proof.
"""
import hashlib
import json
import re

SCHEMA_VERSION = "arcx-tool-contract/v1"
VALID_STATES = {"PROPOSED", "REGISTERED", "CONNECTED", "VERIFIED", "DISABLED", "QUARANTINED"}
VALID_RISKS = {"READ", "ANALYSIS", "WRITE", "PRIVILEGED", "DESTRUCTIVE"}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def stable_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _string_list(value):
    return isinstance(value, list) and all(_nonempty_string(item) for item in value) and len(value) == len(set(value))


def _valid_digest(value):
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def validate_connector(manifest):
    errors = []
    if not isinstance(manifest, dict):
        return {"valid": False, "errors": ["MANIFEST_NOT_OBJECT"]}

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("SCHEMA_VERSION_UNSUPPORTED")
    for field in ("tool_id", "provider", "adapter_version", "contract_version", "policy_version"):
        if not _nonempty_string(manifest.get(field)):
            errors.append(field.upper() + "_REQUIRED")
    if manifest.get("state") not in VALID_STATES:
        errors.append("STATE_INVALID")

    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("CAPABILITIES_REQUIRED")
        capabilities = []
    seen_names = set()
    for index, capability in enumerate(capabilities):
        if not isinstance(capability, dict):
            errors.append(f"CAPABILITY_{index}_INVALID")
            continue
        name = capability.get("name")
        if not _nonempty_string(name):
            errors.append(f"CAPABILITY_{index}_NAME_REQUIRED")
        elif name in seen_names:
            errors.append(f"CAPABILITY_{index}_DUPLICATE")
        else:
            seen_names.add(name)
        if capability.get("risk") not in VALID_RISKS:
            errors.append(f"CAPABILITY_{index}_RISK_INVALID")
        if not _nonempty_string(capability.get("input_schema_ref")) or not _nonempty_string(capability.get("output_schema_ref")):
            errors.append(f"CAPABILITY_{index}_SCHEMA_REFS_REQUIRED")
        if not _string_list(capability.get("required_scopes")):
            errors.append(f"CAPABILITY_{index}_REQUIRED_SCOPES_INVALID")

    auth = manifest.get("authorization")
    if not isinstance(auth, dict):
        errors.append("AUTHORIZATION_REQUIRED")
        auth = {}
    if not _string_list(auth.get("granted_scopes")):
        errors.append("GRANTED_SCOPES_INVALID")
    if not isinstance(auth.get("policy_admitted"), bool):
        errors.append("POLICY_ADMISSION_INVALID")
    if auth.get("credential_mode") not in {"SECRET_REFERENCE_ONLY", "NO_CREDENTIALS"}:
        errors.append("CREDENTIAL_MODE_UNSAFE")
    if auth.get("credential_mode") == "SECRET_REFERENCE_ONLY":
        from scripts.arcx_secret_boundary import validate_secret_reference
        secret_ref = auth.get("secret_ref")
        if not validate_secret_reference(secret_ref)["valid"]:
            errors.append("SECRET_REFERENCE_INVALID")
    elif "secret_ref" in auth:
        errors.append("SECRET_REFERENCE_UNEXPECTED")

    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("PROVENANCE_INCOMPLETE")
    else:
        if not _nonempty_string(provenance.get("source")):
            errors.append("PROVENANCE_SOURCE_REQUIRED")
        if not _valid_digest(provenance.get("digest")):
            errors.append("PROVENANCE_DIGEST_INVALID")

    # A VERIFIED label is only a declaration. Route eligibility additionally
    # requires a verifier receipt reference; cryptographic receipt verification
    # is deliberately left to a trusted verifier integration.
    verification = manifest.get("verification")
    if manifest.get("state") == "VERIFIED":
        if not isinstance(verification, dict):
            errors.append("VERIFICATION_RECEIPT_REQUIRED")
        else:
            if not _nonempty_string(verification.get("verifier_id")):
                errors.append("VERIFIER_ID_REQUIRED")
            if not _valid_digest(verification.get("receipt_digest")):
                errors.append("VERIFICATION_RECEIPT_DIGEST_INVALID")

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
    if not isinstance(manifests, list) or not isinstance(required_capabilities, list):
        return {
            "schema_version": SCHEMA_VERSION,
            "state": "INVALID_REQUEST",
            "candidates": [],
            "unresolved_capabilities": [],
            "execution_performed": False,
        }

    for required in required_capabilities:
        found = []
        for manifest in manifests:
            check = validate_connector(manifest)
            if not check["valid"] or manifest.get("state") != "VERIFIED":
                continue
            auth = manifest["authorization"]
            if auth.get("policy_admitted") is not True:
                continue
            for capability in manifest["capabilities"]:
                if not isinstance(capability, dict) or capability.get("name") != required:
                    continue
                risk = capability.get("risk")
                if risk in {"WRITE", "PRIVILEGED", "DESTRUCTIVE"} and not allow_write:
                    continue
                required_scopes = set(capability["required_scopes"])
                granted_scopes = set(auth["granted_scopes"])
                if not required_scopes.issubset(granted_scopes):
                    continue
                found.append({
                    "tool_id": manifest["tool_id"],
                    "capability": required,
                    "risk": risk,
                    "required_scopes": sorted(required_scopes),
                    "manifest_digest": check["manifest_digest"],
                    "verification_receipt_digest": manifest["verification"]["receipt_digest"],
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
        "authority_granted": False,
    }
    result["result_digest"] = stable_digest(result)
    return result
