#!/usr/bin/env python3
"""Validate the additive four-system federation manifest using only stdlib."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry/federation/four_system_unification.v1.json"
EXPECTED_SYSTEMS = {"VAIXLNS", "VLNS", "VX", "NEXNET"}
ALLOWED_IDENTITY_STATES = {
    "CANONICAL",
    "CANONICAL_SYSTEM_MULTI_REPOSITORY",
    "UNVERIFIED",
}
ALLOWED_IMPLEMENTATION_STATES = {
    "PROPOSAL", "SPECIFIED", "IMPLEMENTED", "PARTIAL", "MISSING", "CONFLICT"
}


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if data.get("authority", {}).get("canonical_source") != "project.genome":
        errors.append("canonical_source must remain project.genome")
    if data.get("authority", {}).get("master_index") != "Ω.000":
        errors.append("master_index must remain Ω.000")

    policy = data.get("policy", {})
    for key in (
        "preserve_repository_history",
        "preserve_original_ideas",
        "verified_requires_reproducible_evidence",
        "unresolved_identity_blocks_canonical_admission",
    ):
        if policy.get(key) is not True:
            errors.append(f"policy.{key} must be true")
    if policy.get("allow_destructive_merge") is not False:
        errors.append("allow_destructive_merge must be false")
    if policy.get("allow_identity_inference_from_repository_name") is not False:
        errors.append("repository name must not establish system identity")

    systems = data.get("systems")
    if not isinstance(systems, list):
        return errors + ["systems must be a list"]
    ids = [item.get("system_id") for item in systems if isinstance(item, dict)]
    if set(ids) != EXPECTED_SYSTEMS or len(ids) != len(EXPECTED_SYSTEMS):
        errors.append("systems must contain each of VAIXLNS, VLNS, VX, NEXNET exactly once")

    for item in systems:
        if not isinstance(item, dict):
            errors.append("every system record must be an object")
            continue
        sid = item.get("system_id", "<missing>")
        if not item.get("repository_surfaces"):
            errors.append(f"{sid}: repository_surfaces must not be empty")
        if item.get("identity_state") not in ALLOWED_IDENTITY_STATES:
            errors.append(f"{sid}: invalid identity_state")
        if item.get("implementation_state") not in ALLOWED_IMPLEMENTATION_STATES:
            errors.append(f"{sid}: invalid implementation_state")
        if item.get("implementation_state") == "VERIFIED":
            errors.append(f"{sid}: VERIFIED is not an implementation_state; use evidence-gated admission")
        if item.get("identity_state") == "UNVERIFIED" and not item.get("unresolved_mapping"):
            errors.append(f"{sid}: unresolved identity must name its unresolved mapping")
        if not item.get("evidence"):
            errors.append(f"{sid}: at least one source/evidence reference is required")

    if data.get("status") not in {"PROPOSAL", "SPECIFIED", "PARTIAL"}:
        errors.append("manifest status must remain non-verified until independent validation")
    return errors


def main() -> int:
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot load manifest: {exc}", file=sys.stderr)
        return 2
    errors = validate(data)
    if errors:
        print("FAIL: four-system federation manifest")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: four-system federation manifest structural invariants")
    print("LIMIT: this check does not prove repository identity, runtime health, or implementation correctness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
