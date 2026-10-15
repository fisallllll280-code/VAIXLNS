#!/usr/bin/env python3
"""Read-only readiness preflight for the deep-index VAIXLNS/VX agent path.

This tool validates repository contracts and reports blockers. It never activates
providers, mutates canonical registries, admits roles, or authorizes production.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Mapping

REQUIRED_ARTIFACTS = (
    "project.genome",
    "registry/omega/omega-000-master-index.json",
    "agents/agent_fabric.py",
    "registry/agent_registry.v1.json",
    "registry/vx-agent-runtime-profiles.v1.json",
    "registry/vx-runtime-role-binding-map.v1.json",
    "registry/vx-agents-fabric.integration.v1.json",
    "docs/audits/VAIXLNS_DEEP_AGENT_AND_INNOVATION_AUDIT_2026-10-10.md",
)
PROTECTED_OUTPUTS = {
    Path("project.genome"),
    Path("registry/omega/omega-000-master-index.json"),
    Path("registry/agent_registry.v1.json"),
    Path("registry/vx-agent-runtime-profiles.v1.json"),
    Path("registry/vx-runtime-role-binding-map.v1.json"),
    Path("registry/vx-agents-fabric.integration.v1.json"),
}
ADMITTED_STATES = {"ADMITTED", "ACTIVE"}
FAMILY_MODEL_ENV = {
    "research": "VX_RESEARCH_MODEL",
    "finance": "VX_FINANCE_MODEL",
    "engineering": "VX_ENGINEERING_MODEL",
    "governance": "VX_GOVERNANCE_MODEL",
}
MIND_IDS = (
    "MIND-SYS-ARCH",
    "MIND-RESEARCH",
    "MIND-FINANCE",
    "MIND-SECURITY",
    "MIND-PROOF",
)


def _fragment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(root: Path, relative: str) -> tuple[Any, str]:
    path = root / relative
    if not path.is_file():
        raise ValueError("REQUIRED_ARTIFACT_MISSING:" + relative)
    raw = path.read_bytes()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("REQUIRED_ARTIFACT_INVALID_JSON:" + relative) from exc
    return parsed, _sha256(raw)


def _read_bytes(root: Path, relative: str) -> tuple[bytes, str]:
    path = root / relative
    if not path.is_file():
        raise ValueError("REQUIRED_ARTIFACT_MISSING:" + relative)
    raw = path.read_bytes()
    return raw, _sha256(raw)


def _extract_handoff_chain(source: bytes) -> tuple[str, ...]:
    try:
        tree = ast.parse(source.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as exc:
        raise ValueError("AGENT_FABRIC_SOURCE_INVALID") from exc
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "DEFAULT_HANDOFF_CHAIN" in names:
                value = ast.literal_eval(node.value)
                if not isinstance(value, (tuple, list)):
                    raise ValueError("DEFAULT_HANDOFF_CHAIN_MUST_BE_SEQUENCE")
                if not all(isinstance(item, str) for item in value):
                    raise ValueError("DEFAULT_HANDOFF_CHAIN_ITEMS_MUST_BE_STRINGS")
                return tuple(value)
    raise ValueError("DEFAULT_HANDOFF_CHAIN_NOT_FOUND")


def _add_check(checks: list[dict[str, str]], code: str, status: str, detail: str) -> None:
    checks.append({"check": code, "status": status, "detail": detail})


def build_report(
    root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic-status report without network access or file mutation."""
    project_root = Path(root or Path(__file__).resolve().parents[1]).resolve()
    env = os.environ if environ is None else environ
    checks: list[dict[str, str]] = []
    blockers: list[str] = []
    hard_errors: list[str] = []
    artifact_hashes: dict[str, str] = {}
    data: dict[str, Any] = {}

    for relative in REQUIRED_ARTIFACTS:
        try:
            if relative.endswith(".json") or relative == "project.genome":
                data[relative], artifact_hashes[relative] = _read_json(project_root, relative)
            else:
                _, artifact_hashes[relative] = _read_bytes(project_root, relative)
        except ValueError as exc:
            hard_errors.append(str(exc))

    if hard_errors:
        _add_check(checks, "required_artifacts", "REJECT", "Required input files are missing or invalid.")
        material = {"artifact_hashes": artifact_hashes, "errors": sorted(hard_errors)}
        return {
            "schema_version": "1.0.0",
            "report_type": "VAIXLNS_DEEP_INDEX_AGENT_EXECUTION_PREFLIGHT",
            "report_id": _sha256(_canonical_bytes(material)),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "REJECT",
            "checks": checks,
            "hard_errors": sorted(hard_errors),
            "blockers": [],
            "artifact_sha256": dict(sorted(artifact_hashes.items())),
            "live_provider_handshake": "NOT_RUN",
            "agent_execution_performed": False,
            "canonical_mutation_performed": False,
            "production_authorized": False,
        }

    index = data["registry/omega/omega-000-master-index.json"]
    agent_json = data["registry/agent_registry.v1.json"]
    profiles = data["registry/vx-agent-runtime-profiles.v1.json"]
    binding = data["registry/vx-runtime-role-binding-map.v1.json"]
    integration = data["registry/vx-agents-fabric.integration.v1.json"]

    # Golden-source and Ω.000 authority invariants.
    index_ok = (
        index.get("index_id") == "Ω.000"
        and index.get("status") == "CANONICAL"
        and index.get("authority") == "VAIXLNS"
        and index.get("golden_source") == "project.genome::v1.0.0"
        and index.get("authority_anchor") == "Ω0_GENESIS_CORE"
        and isinstance(index.get("records"), list)
        and bool(index.get("records"))
    )
    _add_check(
        checks, "canonical_index", "PASS" if index_ok else "REJECT",
        "Ω.000 authority and golden-source fields validated." if index_ok
        else "Ω.000 identity, authority, golden source, anchor, or records are invalid.",
    )
    if not index_ok:
        hard_errors.append("OMEGA_000_CANONICAL_AUTHORITY_INVARIANT_FAILED")

    # Parse the Python roster statically: importing project code is not required.
    try:
        source, _ = _read_bytes(project_root, "agents/agent_fabric.py")
        chain = _extract_handoff_chain(source)
        chain_ok = len(chain) == 13 and len(chain) == len(set(chain))
    except ValueError as exc:
        chain, chain_ok = (), False
        hard_errors.append(str(exc))
    _add_check(
        checks, "typed_handoff_chain", "PASS" if chain_ok else "REJECT",
        "13 unique canonical handoff roles found." if chain_ok
        else "The canonical handoff chain is missing, malformed, or not 13 unique roles.",
    )
    if not chain_ok and not any(item.startswith("DEFAULT_HANDOFF_CHAIN") or item == "AGENT_FABRIC_SOURCE_INVALID" for item in hard_errors):
        hard_errors.append("CANONICAL_HANDOFF_CHAIN_INVARIANT_FAILED")

    # Validate the separately indexed 13-agent registry without merging its identities
    # into the 13-role typed handoff chain.
    indexed_agents = agent_json.get("agents")
    indexed_ids = [
        item.get("agent_id") for item in indexed_agents if isinstance(item, dict)
    ] if isinstance(indexed_agents, list) else []
    registry_ok = (
        agent_json.get("canonical_owner") == "VAIXLNS"
        and isinstance(indexed_agents, list)
        and len(indexed_agents) == 13
        and len(indexed_ids) == len(set(indexed_ids))
        and all(
            isinstance(item, dict)
            and all(item.get(key) for key in (
                "agent_id", "canonical_name", "capabilities",
                "authority_scope", "lifecycle"
            ))
            and item.get("may_promote") is not True
            and item.get("can_promote") is not True
            for item in indexed_agents
        )
    )
    _add_check(
        checks, "canonical_agent_registry", "PASS" if registry_ok else "REJECT",
        "13 indexed agent records have unique IDs and required fields." if registry_ok
        else "The indexed agent registry has duplicate IDs, missing fields, or unsafe promotion fields.",
    )
    if not registry_ok:
        hard_errors.append("CANONICAL_AGENT_REGISTRY_INVARIANT_FAILED")

    # Check VX templates and binding guardrails, keeping design-time records distinct
    # from admitted/active runtime identities.
    runtime_profiles = profiles.get("agent_profiles")
    profile_ids = [
        item.get("agent_role_id") for item in runtime_profiles if isinstance(item, dict)
    ] if isinstance(runtime_profiles, list) else []
    profiles_ok = (
        profiles.get("invariant") == "EVERY_AGENT_USES_VX"
        and isinstance(runtime_profiles, list)
        and len(runtime_profiles) == profiles.get("agent_role_count")
        and len(profile_ids) == len(set(profile_ids))
        and all(
            isinstance(item, dict)
            and item.get("vx_binding", {}).get("required") is True
            and item.get("vx_binding", {}).get("direct_tool_calls_allowed") is False
            for item in runtime_profiles
        )
    )
    _add_check(
        checks, "vx_profile_guardrails", "PASS" if profiles_ok else "REJECT",
        "VX profile count and no-direct-tool-call invariants validated." if profiles_ok
        else "VX profile catalog is malformed or a profile bypasses the VX boundary.",
    )
    if not profiles_ok:
        hard_errors.append("VX_PROFILE_GUARDRAIL_INVARIANT_FAILED")

    role_bindings = binding.get("role_bindings")
    version_entries = [
        version
        for role in role_bindings if isinstance(role, dict)
        for version in role.get("versions", []) if isinstance(version, dict)
    ] if isinstance(role_bindings, list) else []
    declared_versions = binding.get("runtime_role_identity_count")
    declared_roles = binding.get("logical_role_id_count")
    binding_ids = [
        role.get("runtime_role_id") for role in role_bindings if isinstance(role, dict)
    ] if isinstance(role_bindings, list) else []
    invariants = binding.get("invariants", {})
    binding_shape_ok = (
        isinstance(role_bindings, list)
        and len(role_bindings) == declared_roles
        and len(binding_ids) == len(set(binding_ids))
        and len(version_entries) == declared_versions
        and invariants.get("all_agent_execution_orchestration_through_vx") is True
        and invariants.get("direct_agent_tool_calls_allowed") is False
        and invariants.get("self_approval_allowed") is False
        and invariants.get("child_scope_may_exceed_parent") is False
        and invariants.get("automatic_canonical_promotion") is False
        and invariants.get("mapping_is_admission") is False
    )
    _add_check(
        checks, "runtime_binding_map_shape", "PASS" if binding_shape_ok else "REJECT",
        "Role/version counts and deny-by-default binding invariants validated." if binding_shape_ok
        else "Binding-map shape or a mandatory safety invariant is invalid.",
    )
    if not binding_shape_ok:
        hard_errors.append("RUNTIME_BINDING_MAP_INVARIANT_FAILED")

    # Validate references from candidate mappings without treating candidates as admission.
    missing_profiles = sorted({
        str(profile_id)
        for role in (role_bindings if isinstance(role_bindings, list) else [])
        if isinstance(role, dict)
        for profile_id in role.get("candidate_profile_ids", [])
        if profile_id not in set(profile_ids)
    })
    if missing_profiles:
        hard_errors.append("UNKNOWN_CANDIDATE_PROFILE_IDS:" + ",".join(missing_profiles))
    _add_check(
        checks, "candidate_profile_references",
        "PASS" if not missing_profiles else "REJECT",
        "All candidate profile references resolve." if not missing_profiles
        else "Unknown profile IDs: " + ",".join(missing_profiles),
    )

    # Model configuration is presence-only here. No credentials or endpoint requests
    # are emitted by this preflight.
    base_configured = bool(env.get("VX_OPENAI_COMPAT_BASE_URL", "").strip())
    api_key_configured = bool(env.get("VX_OPENAI_COMPAT_API_KEY", "").strip())
    missing_role_models: list[str] = []
    for role in (role_bindings if isinstance(role_bindings, list) else []):
        if not isinstance(role, dict):
            continue
        role_id = str(role.get("runtime_role_id", ""))
        family_key = FAMILY_MODEL_ENV.get(str(role.get("family", "")).lower())
        role_model = env.get("VX_AGENT_MODEL_" + _fragment(role_id), "").strip()
        role_version_models = [
            env.get("VX_AGENT_MODEL_" + _fragment(str(version.get("source_identity", ""))), "").strip()
            for version in role.get("versions", []) if isinstance(version, dict)
        ]
        family_model = env.get(family_key, "").strip() if family_key else ""
        if not role_model and not family_model and not any(role_version_models):
            missing_role_models.append(role_id)
    mind_models_present = [
        mind_id for mind_id in MIND_IDS
        if env.get("VX_MIND_MODEL_" + _fragment(mind_id), "").strip()
    ]
    missing_minds = sorted(set(MIND_IDS) - set(mind_models_present))
    provider_configured = base_configured and not missing_role_models and not missing_minds
    provider_detail = (
        "Endpoint variable and every mapped specialist/reviewer model variable are present; "
        "live connectivity has not been tested."
        if provider_configured else
        "Provider setup is incomplete: base_url_present="
        + str(base_configured).lower()
        + ", specialist_models_missing=" + str(len(missing_role_models))
        + ", reviewer_minds_missing=" + str(len(missing_minds)) + "."
    )
    _add_check(
        checks, "provider_configuration", "PASS" if provider_configured else "HOLD",
        provider_detail,
    )
    if not provider_configured:
        blockers.append("MODEL_PROVIDER_CONFIGURATION_INCOMPLETE")
    # Record presence only; never copy secret or URL values to evidence.
    environment_summary = {
        "openai_compatible_base_url_present": base_configured,
        "openai_compatible_api_key_present": api_key_configured,
        "configured_specialist_model_variable_count": len(binding_ids) - len(missing_role_models),
        "missing_specialist_model_role_ids": sorted(missing_role_models),
        "configured_reviewer_minds": sorted(mind_models_present),
        "missing_reviewer_minds": missing_minds,
    }

    # The approved map and the integration receipt remain explicit blockers until the
    # governance and runtime evidence says otherwise.
    mapping_active = (
        str(binding.get("status", "")).upper() in ADMITTED_STATES
        and all(
            str(role.get("mapping_status", "")).upper() in ADMITTED_STATES
            and all(
                str(version.get("admission_status", "")).upper() in ADMITTED_STATES
                for version in role.get("versions", []) if isinstance(version, dict)
            )
            for role in (role_bindings if isinstance(role_bindings, list) else [])
            if isinstance(role, dict)
        )
    )
    _add_check(
        checks, "binding_admission", "PASS" if mapping_active else "HOLD",
        "Every runtime role/version has an admitted binding." if mapping_active
        else "Runtime role/version mapping remains proposed or design-only.",
    )
    if not mapping_active:
        blockers.append("RUNTIME_ROLE_BINDINGS_NOT_ADMITTED")

    profiles_active = (
        str(profiles.get("status", "")).upper() in ADMITTED_STATES
        and all(
            str(profile.get("status", "")).upper() in ADMITTED_STATES
            for profile in (runtime_profiles if isinstance(runtime_profiles, list) else [])
            if isinstance(profile, dict)
        )
    )
    _add_check(
        checks, "runtime_profile_admission", "PASS" if profiles_active else "HOLD",
        "VX runtime profiles are admitted." if profiles_active
        else "VX role profiles remain design templates, not deployed agents.",
    )
    if not profiles_active:
        blockers.append("VX_RUNTIME_PROFILES_NOT_ADMITTED")

    repository_record = integration.get("repository", {})
    operational = integration.get("operational_status", {})
    external_gate = integration.get("external_integration_gate", {})
    manifest_admitted = (
        str(repository_record.get("disposition", "")).upper() in ADMITTED_STATES
        and str(external_gate.get("status", "")).upper() in {"COMPLETED", "ADMITTED", "ACTIVE"}
    )
    _add_check(
        checks, "external_integration_gate", "PASS" if manifest_admitted else "HOLD",
        "External integration gate is admitted." if manifest_admitted
        else "External integration gate is not yet completed/admitted.",
    )
    if not manifest_admitted:
        blockers.append("EXTERNAL_INTEGRATION_GATE_NOT_ADMITTED")

    unavailable_services = []
    for key in ("model_providers", "durable_vaixl_event_ledger",
                "internet_search_adapter", "repository_tool_adapter", "code_sandbox_adapter",
                "crash_resume_controller"):
        value = operational.get(key, integration.get("model_binding", {}).get(key, "UNDECLARED"))
        normalized = str(value).upper()
        if any(marker in normalized for marker in (
            "NOT_CONNECTED", "NOT_INCLUDED", "NOT_IMPLEMENTED", "NOT_CONFIGURED", "UNDECLARED"
        )):
            unavailable_services.append(key)
    _add_check(
        checks, "required_runtime_services",
        "PASS" if not unavailable_services else "HOLD",
        "Required service bindings are declared available." if not unavailable_services
        else "Unavailable or unverified runtime services: " + ", ".join(sorted(unavailable_services)),
    )
    if unavailable_services:
        blockers.append("REQUIRED_RUNTIME_SERVICES_UNAVAILABLE:" + ",".join(sorted(unavailable_services)))

    if hard_errors:
        status = "REJECT"
    elif blockers:
        status = "HOLD"
    else:
        status = "PRECHECK_PASSED_NOT_LIVE_VERIFIED"

    # Report identity is deterministic for identical artifacts and environment-presence
    # state; generated_at is metadata and is excluded from the identity.
    material = {
        "artifact_sha256": dict(sorted(artifact_hashes.items())),
        "status": status,
        "checks": checks,
        "blockers": sorted(set(blockers)),
        "hard_errors": sorted(set(hard_errors)),
        "environment_summary": environment_summary,
    }
    return {
        "schema_version": "1.0.0",
        "report_type": "VAIXLNS_DEEP_INDEX_AGENT_EXECUTION_PREFLIGHT",
        "report_id": _sha256(_canonical_bytes(material)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "index_authority": {
            "index_id": index.get("index_id"),
            "golden_source": index.get("golden_source"),
            "authority_anchor": index.get("authority_anchor"),
            "index_record_count": len(index.get("records", [])),
        },
        "agent_surfaces": {
            "typed_handoff_role_count": len(chain),
            "indexed_agent_record_count": len(indexed_agents or []),
            "vx_profile_count": len(runtime_profiles or []),
            "runtime_logical_role_count": len(role_bindings or []),
            "runtime_role_version_count": len(version_entries),
        },
        "checks": checks,
        "blockers": sorted(set(blockers)),
        "hard_errors": sorted(set(hard_errors)),
        "artifact_sha256": dict(sorted(artifact_hashes.items())),
        "environment_summary": environment_summary,
        "live_provider_handshake": "NOT_RUN",
        "agent_execution_performed": False,
        "canonical_mutation_performed": False,
        "production_authorized": False,
    }


def _write_report(path_value: str, report: Mapping[str, Any], root: Path) -> None:
    target = Path(path_value).expanduser()
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()
    protected = {(root / item).resolve() for item in PROTECTED_OUTPUTS}
    if target in protected:
        raise ValueError("REPORT_OUTPUT_MUST_NOT_OVERWRITE_CANONICAL_ARTIFACT")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(target.parent),
            prefix=target.name + ".", suffix=".tmp", delete=False
        ) as handle:
            temporary_name = handle.name
            json.dump(report, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
        temporary_name = None
    finally:
        if temporary_name:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output", help="Optional JSON report path; canonical files are protected.")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    try:
        report = build_report(root)
        rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output:
            _write_report(args.output, report, root)
        else:
            sys.stdout.write(rendered)
    except (OSError, ValueError) as exc:
        sys.stderr.write("agent_execution_preflight_error:" + str(exc) + "\n")
        return 4
    if report["status"] == "PRECHECK_PASSED_NOT_LIVE_VERIFIED":
        return 0
    if report["status"] == "REJECT":
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
