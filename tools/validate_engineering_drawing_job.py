"""Validate engineering-drawing job contracts and enforce a fail-closed release gate.

This module checks job specification completeness and release evidence. It is not
a CAD kernel, engineering solver, code-compliance certification, or seal.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

DISCIPLINES = {
    "architectural", "civil_structural", "mechanical", "electrical",
    "process_piping", "robotics", "scientific", "other",
}
ADAPTERS = {"freecad", "opencascade", "autodesk_aps", "ifc_bim", "custom", "not_selected"}
FORMATS = {"svg", "dxf", "dwg", "step", "iges", "ifc", "rvt", "stl", "glb", "pdf", "json"}
CONSTRAINT_TYPES = {
    "dimension", "parametric_equation", "clearance", "collision_free", "load_case",
    "code_rule", "topology", "tolerance", "accessibility", "egress", "electrical_rating", "other",
}
CONSTRAINT_STATES = {"NOT_CHECKED", "PASSED", "FAILED", "NOT_APPLICABLE_WITH_EVIDENCE"}
STANDARD_STATES = {"SELECTED", "NEEDS_REVIEW", "NOT_APPLICABLE_WITH_RATIONALE"}


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_one_of(value: object, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _is_https_uri(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme == "https" and bool(parsed.netloc)
    except ValueError:
        return False


def validate_job(job: object) -> dict[str, object]:
    errors: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    if not isinstance(job, dict):
        return {"valid": False, "release_eligible": False, "errors": ["job must be a JSON object"], "release_blockers": ["JOB_NOT_AN_OBJECT"]}

    required = {
        "schema_version", "job_id", "discipline", "jurisdiction", "intent", "units",
        "coordinate_system", "constraints", "standards", "geometry_backend",
        "deliverables", "validation_policy",
    }
    missing = sorted(required - set(job))
    extra = sorted(set(job) - required)
    errors.extend(f"missing required field: {field}" for field in missing)
    errors.extend(f"unknown top-level field: {field}" for field in extra)
    if errors:
        return {"valid": False, "release_eligible": False, "errors": errors, "release_blockers": ["JOB_CONTRACT_INVALID"]}

    if job["schema_version"] != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if not isinstance(job["job_id"], str) or not re.fullmatch(r"ED-[A-Z0-9][A-Z0-9._-]{1,70}", job["job_id"]):
        errors.append("job_id must match ED- plus a stable uppercase identity")
    if not _is_one_of(job["discipline"], DISCIPLINES):
        errors.append("discipline is not supported by this contract")
    if not _is_nonempty_string(job["jurisdiction"]):
        errors.append("jurisdiction must be explicit; do not infer a governing code")
    if not _is_nonempty_string(job["intent"]) or len(job["intent"]) < 10:
        errors.append("intent must describe the engineering objective (at least 10 characters)")

    units = job["units"]
    if not isinstance(units, dict):
        errors.append("units must be an object")
    else:
        if not _is_one_of(units.get("length"), {"mm", "cm", "m", "in", "ft"}):
            errors.append("units.length must be explicit")
        if not _is_one_of(units.get("angle"), {"deg", "rad"}):
            errors.append("units.angle must be explicit")
        if set(units) - {"length", "angle", "force", "pressure"}:
            errors.append("units contains unsupported fields")
        if "force" in units and not _is_one_of(units["force"], {"N", "kN", "lbf", "kip"}):
            errors.append("units.force is unsupported")
        if "pressure" in units and not _is_one_of(units["pressure"], {"Pa", "kPa", "MPa", "bar", "psi"}):
            errors.append("units.pressure is unsupported")

    coordinate = job["coordinate_system"]
    if not isinstance(coordinate, dict):
        errors.append("coordinate_system must be an object")
    else:
        if not _is_one_of(coordinate.get("handedness"), {"right", "left"}):
            errors.append("coordinate_system.handedness must be explicit")
        if not _is_nonempty_string(coordinate.get("origin")):
            errors.append("coordinate_system.origin must be explicit")
        if set(coordinate) - {"handedness", "origin", "axis_convention"}:
            errors.append("coordinate_system contains unsupported fields")

    constraints = job["constraints"]
    constraint_ids: set[str] = set()
    if not isinstance(constraints, list) or not constraints:
        errors.append("constraints must be a non-empty array")
        constraints = []
    else:
        for index, constraint in enumerate(constraints):
            prefix = f"constraints[{index}]"
            if not isinstance(constraint, dict):
                errors.append(f"{prefix} must be an object")
                continue
            cid = constraint.get("id")
            if not isinstance(cid, str) or not re.fullmatch(r"C-[A-Z0-9][A-Z0-9._-]{1,40}", cid):
                errors.append(f"{prefix}.id is invalid")
            elif cid in constraint_ids:
                errors.append(f"duplicate constraint id: {cid}")
            else:
                constraint_ids.add(cid)
            if not _is_one_of(constraint.get("type"), CONSTRAINT_TYPES):
                errors.append(f"{prefix}.type is unsupported")
            if not _is_nonempty_string(constraint.get("description")):
                errors.append(f"{prefix}.description is required")
            if not isinstance(constraint.get("mandatory"), bool):
                errors.append(f"{prefix}.mandatory must be boolean")
            state = constraint.get("verification_state")
            if not _is_one_of(state, CONSTRAINT_STATES):
                errors.append(f"{prefix}.verification_state is invalid")
            elif state == "FAILED":
                blockers.append(f"CONSTRAINT_FAILED:{cid}")
            elif constraint.get("mandatory") is True and state not in {"PASSED", "NOT_APPLICABLE_WITH_EVIDENCE"}:
                blockers.append(f"MANDATORY_CONSTRAINT_NOT_PROVEN:{cid}")
            if set(constraint) - {"id", "type", "description", "mandatory", "verification_state", "evidence_ref"}:
                errors.append(f"{prefix} contains unsupported fields")
            if state in {"PASSED", "NOT_APPLICABLE_WITH_EVIDENCE"} and not _is_nonempty_string(constraint.get("evidence_ref")):
                errors.append(f"{prefix}: PASSED requires evidence_ref")

    standards = job["standards"]
    standard_keys: set[tuple[str, str, str]] = set()
    if not isinstance(standards, list) or not standards:
        errors.append("standards must be a non-empty array")
        standards = []
    else:
        for index, standard in enumerate(standards):
            prefix = f"standards[{index}]"
            if not isinstance(standard, dict):
                errors.append(f"{prefix} must be an object")
                continue
            code, edition, jurisdiction = standard.get("code"), standard.get("edition"), standard.get("jurisdiction")
            for name, value in (("code", code), ("edition", edition), ("jurisdiction", jurisdiction)):
                if not _is_nonempty_string(value):
                    errors.append(f"{prefix}.{name} is required")
            key = (str(code).casefold(), str(edition).casefold(), str(jurisdiction).casefold())
            if key in standard_keys:
                errors.append(f"duplicate standard identity: {code}/{edition}/{jurisdiction}")
            standard_keys.add(key)
            uri = standard.get("source_uri")
            if not _is_https_uri(uri):
                errors.append(f"{prefix}.source_uri must be an HTTPS source")
            state = standard.get("selection_state")
            if not _is_one_of(state, STANDARD_STATES):
                errors.append(f"{prefix}.selection_state is invalid")
            elif state == "NEEDS_REVIEW":
                if isinstance(job.get("validation_policy"), dict) and job["validation_policy"].get("block_on_unknown_standards") is True:
                    blockers.append(f"STANDARD_SELECTION_UNCONFIRMED:{code}")
                else:
                    warnings.append(f"STANDARD_SELECTION_UNCONFIRMED:{code}")
            elif state == "NOT_APPLICABLE_WITH_RATIONALE" and not _is_nonempty_string(standard.get("selection_rationale")):
                errors.append(f"{prefix}: non-applicability requires selection_rationale")
            if set(standard) - {"code", "edition", "jurisdiction", "source_uri", "selection_state", "selection_rationale"}:
                errors.append(f"{prefix} contains unsupported fields")

    backend = job["geometry_backend"]
    if not isinstance(backend, dict):
        errors.append("geometry_backend must be an object")
    else:
        if not _is_one_of(backend.get("adapter"), ADAPTERS):
            errors.append("geometry_backend.adapter is unsupported")
        if not _is_nonempty_string(backend.get("version")):
            errors.append("geometry_backend.version must be pinned or explicitly marked")
        if set(backend) - {"adapter", "version", "capability_contract_ref"}:
            errors.append("geometry_backend contains unsupported fields")
        if backend.get("adapter") == "not_selected":
            blockers.append("GEOMETRY_BACKEND_NOT_SELECTED")
        if not _is_one_of(backend.get("capability_state"), {"NOT_CHECKED", "AVAILABLE", "VERIFIED", "UNAVAILABLE"}):
            errors.append("geometry_backend.capability_state is invalid")
        elif backend.get("capability_state") != "VERIFIED":
            blockers.append("BACKEND_CAPABILITY_NOT_VERIFIED")
        if backend.get("capability_state") == "VERIFIED" and not _is_nonempty_string(backend.get("capability_contract_ref")):
            errors.append("VERIFIED backend capability requires capability_contract_ref")

    deliverables = job["deliverables"]
    deliverable_keys: set[tuple[str, str]] = set()
    if not isinstance(deliverables, list) or not deliverables:
        errors.append("deliverables must be a non-empty array")
        deliverables = []
    else:
        for index, item in enumerate(deliverables):
            prefix = f"deliverables[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            fmt, purpose = item.get("format"), item.get("purpose")
            if not _is_one_of(fmt, FORMATS):
                errors.append(f"{prefix}.format is unsupported")
            if not _is_nonempty_string(purpose):
                errors.append(f"{prefix}.purpose is required")
            key = (str(fmt), str(purpose))
            if key in deliverable_keys:
                errors.append(f"duplicate deliverable format/purpose: {fmt}/{purpose}")
            deliverable_keys.add(key)
            if not isinstance(item.get("required"), bool):
                errors.append(f"{prefix}.required must be boolean")
            if set(item) - {"format", "purpose", "required", "profile_ref"}:
                errors.append(f"{prefix} contains unsupported fields")

    policy = job["validation_policy"]
    policy_keys = {
        "require_independent_checker", "require_human_release", "block_on_unknown_standards",
        "independent_check_state", "human_approval_state", "simulation_required", "simulation_state",
        "independent_check_evidence_ref", "human_approval_evidence_ref", "simulation_evidence_ref",
    }
    if not isinstance(policy, dict):
        errors.append("validation_policy must be an object")
    else:
        if set(policy) != policy_keys:
            errors.append("validation_policy has missing or unsupported fields")
        for key in ("require_independent_checker", "require_human_release", "block_on_unknown_standards", "simulation_required"):
            if not isinstance(policy.get(key), bool):
                errors.append(f"validation_policy.{key} must be boolean")
        if not _is_one_of(policy.get("independent_check_state"), {"NOT_RUN", "PASSED", "FAILED"}):
            errors.append("validation_policy.independent_check_state is invalid")
        if not _is_one_of(policy.get("human_approval_state"), {"NOT_GRANTED", "APPROVED", "REJECTED"}):
            errors.append("validation_policy.human_approval_state is invalid")
        if not _is_one_of(policy.get("simulation_state"), {"NOT_RUN", "PASSED", "FAILED", "NOT_APPLICABLE_WITH_EVIDENCE"}):
            errors.append("validation_policy.simulation_state is invalid")
        if policy.get("require_independent_checker") is True and policy.get("independent_check_state") != "PASSED":
            blockers.append("INDEPENDENT_CHECK_NOT_PASSED")
        if policy.get("independent_check_state") == "PASSED" and not _is_nonempty_string(policy.get("independent_check_evidence_ref")):
            errors.append("PASSED independent check requires independent_check_evidence_ref")
        if policy.get("require_human_release") is True and policy.get("human_approval_state") != "APPROVED":
            blockers.append("HUMAN_RELEASE_NOT_APPROVED")
        if policy.get("human_approval_state") == "APPROVED" and not _is_nonempty_string(policy.get("human_approval_evidence_ref")):
            errors.append("APPROVED human release requires human_approval_evidence_ref")
        if policy.get("human_approval_state") == "REJECTED":
            blockers.append("HUMAN_RELEASE_REJECTED")
        if policy.get("simulation_required") is True and policy.get("simulation_state") != "PASSED":
            blockers.append("REQUIRED_SIMULATION_NOT_PASSED")
        if policy.get("simulation_state") == "PASSED" and not _is_nonempty_string(policy.get("simulation_evidence_ref")):
            errors.append("PASSED simulation requires simulation_evidence_ref")
        if policy.get("simulation_state") == "FAILED":
            blockers.append("SIMULATION_FAILED")

    errors = sorted(set(errors))
    blockers = sorted(set(blockers))
    return {
        "schema": "VAIXLNS.EngineeringDrawingJobValidation.v1",
        "job_id": job.get("job_id"),
        "valid": not errors,
        "release_eligible": not errors and not blockers,
        "errors": errors,
        "release_blockers": blockers,
        "warnings": sorted(set(warnings)),
        "scope_notice": (
            "Structural validity of this request is not engineering/code compliance. "
            "Release eligibility requires cited evidence, the specified independent checks, "
            "simulation when required, and human approval when configured."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path, help="Path to engineering-drawing job JSON")
    parser.add_argument("--require-release", action="store_true", help="Exit non-zero unless all release gates pass")
    args = parser.parse_args()
    try:
        job = json.loads(args.job.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2), file=sys.stderr)
        return 2

    report = validate_job(job)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["valid"]:
        return 2
    if args.require_release and not report["release_eligible"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
