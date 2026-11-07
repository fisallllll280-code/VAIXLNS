#!/usr/bin/env python3
"""Fail-closed checks for the MTIK manifest and authority boundaries."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry/omega/proposals/omega-memory-task-innovation-kernel.v1.json"
SCHEMA = ROOT / "schemas/omega-memory-task-innovation.v1.schema.json"
EXPECTED_CAPABILITIES = {"MTIK-001", "MTIK-002", "MTIK-003", "MTIK-004"}


def validate(manifest: dict, schema: dict) -> list[str]:
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("schema draft declaration missing")
    if manifest.get("schema_version") != "1.0.0":
        errors.append("unsupported schema_version")
    if manifest.get("kernel_id") != "VAIXLNS.OMEGA.MEMORY_TASK_INNOVATION.001":
        errors.append("kernel ID mismatch")
    if manifest.get("parent") != "VAIXLNS":
        errors.append("kernel must remain a VAIXLNS child subsystem")

    expected_authority = {
        "canonical_source": "project.genome::v1.0.0",
        "authority_anchor": "Ω0_GENESIS_CORE",
        "master_index": "Ω.000",
        "canonical_writes": "DISABLED",
        "self_promotion": "FORBIDDEN",
    }
    for key, expected in expected_authority.items():
        if manifest.get("authority", {}).get(key) != expected:
            errors.append(f"authority.{key} must remain {expected}")

    policies = manifest.get("policies", {})
    policy_expected = {
        "memory_is_read_only": True,
        "task_planning_is_not_execution": True,
        "external_effects_enabled": False,
        "independent_verification_required": True,
        "history_preserved": True,
    }
    for key, expected in policy_expected.items():
        if policies.get(key) != expected:
            errors.append(f"policies.{key} must remain {expected}")

    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list):
        return errors + ["capabilities must be an array"]
    ids = [item.get("id") for item in capabilities if isinstance(item, dict)]
    if set(ids) != EXPECTED_CAPABILITIES or len(ids) != len(EXPECTED_CAPABILITIES):
        errors.append("MTIK-001 through MTIK-004 must appear exactly once")
    for item in capabilities:
        if not isinstance(item, dict):
            errors.append("each capability must be an object")
            continue
        if item.get("state") == "VERIFIED":
            errors.append(f"{item.get('id')}: proposal cannot mark capability VERIFIED")
        for key in ("inputs", "outputs", "acceptance"):
            if not isinstance(item.get(key), list) or not item[key]:
                errors.append(f"{item.get('id')}: {key} must be non-empty")

    if manifest.get("status") == "VERIFIED":
        errors.append("kernel proposal cannot self-promote to VERIFIED")
    if schema.get("properties", {}).get("authority", {}).get("properties", {}).get("canonical_writes", {}).get("const") != "DISABLED":
        errors.append("schema must freeze canonical writes as disabled")
    return errors


def main() -> int:
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"MTIK_FAIL: cannot load JSON input: {exc}", file=sys.stderr)
        return 2

    errors = validate(manifest, schema)
    if errors:
        print("MTIK_FAIL: proposal integrity")
        for error in errors:
            print(f"- {error}")
        return 1

    print("MTIK_PASS: authority, lifecycle, and capability invariants")
    print("LIMIT: these checks do not prove production execution, OS isolation, or cross-repository integration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
