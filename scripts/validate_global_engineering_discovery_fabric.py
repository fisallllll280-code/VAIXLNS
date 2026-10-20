#!/usr/bin/env python3
"""Fail-closed, dependency-free integrity checks for GEDF v1 proposal."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry/omega/proposals/global-engineering-discovery-fabric.v1.json"
SCHEMA = ROOT / "schemas/global-engineering-discovery-fabric.v1.schema.json"
EXPECTED_CAPABILITIES = {f"GEDF-{i:03d}" for i in range(1, 9)}
SCORING_DIMENSIONS = {
    "evidence_quality": 25,
    "engineering_utility": 20,
    "integration_fit": 15,
    "reliability_and_reproducibility": 15,
    "security_and_governance": 15,
    "novelty_after_prior_art_review": 10,
}


def validate(data: dict, schema: dict | None = None) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if data.get("record_id") != "VAIXLNS.GLOBAL_ENGINEERING_DISCOVERY_FABRIC.V1":
        errors.append("record_id must be stable")

    system = data.get("system", {})
    if system.get("id") != "VAIXLNS.GEDF" or system.get("parent") != "VAIXLNS":
        errors.append("GEDF must remain a child subsystem of VAIXLNS")

    authority = data.get("authority", {})
    expected_authority = {
        "canonical_source": "project.genome::v1.0.0",
        "authority_anchor": "Ω0_GENESIS_CORE",
        "master_index": "Ω.000",
        "canonical_mutation": "NOT_AUTHORIZED",
        "state_promotion": "DISABLED",
    }
    for key, expected in expected_authority.items():
        if authority.get(key) != expected:
            errors.append(f"authority.{key} must remain {expected}")

    if data.get("status") not in {"PROPOSAL", "SPECIFIED", "PARTIAL"}:
        errors.append("top-level status must remain non-verified")
    if data.get("evidence_state") != "NO_RUNTIME_EVIDENCE_YET":
        errors.append("runtime evidence must not be claimed by a design-only proposal")

    capabilities = data.get("capabilities")
    if not isinstance(capabilities, list):
        return errors + ["capabilities must be an array"]
    ids = [item.get("id") for item in capabilities if isinstance(item, dict)]
    if set(ids) != EXPECTED_CAPABILITIES or len(ids) != len(EXPECTED_CAPABILITIES):
        errors.append("GEDF-001 through GEDF-008 must each occur exactly once")

    for item in capabilities:
        if not isinstance(item, dict):
            errors.append("every capability must be an object")
            continue
        cid = item.get("id", "<missing>")
        if item.get("state") == "VERIFIED":
            errors.append(f"{cid}: no capability may be VERIFIED in this proposal")
        if item.get("state") not in {"PROPOSAL", "SPECIFIED", "IMPLEMENTED", "PARTIAL", "QUARANTINED", "SUPERSEDED"}:
            errors.append(f"{cid}: invalid state")
        if item.get("priority") not in {"P0", "P1", "P2"}:
            errors.append(f"{cid}: invalid priority")
        for key in ("inputs", "outputs", "acceptance"):
            if not isinstance(item.get(key), list) or not item[key]:
                errors.append(f"{cid}: {key} must be a non-empty list")

    scoring = data.get("innovation_scoring", {})
    dimensions = scoring.get("dimensions", [])
    weights = {d.get("id"): d.get("weight") for d in dimensions if isinstance(d, dict)}
    if weights != SCORING_DIMENSIONS:
        errors.append("score dimensions and weights must match the declared 100-point rubric")
    if scoring.get("total") != 100:
        errors.append("score total must be 100")

    sources = data.get("candidate_interoperability_sources", [])
    if not isinstance(sources, list) or not sources:
        errors.append("at least one interoperability research source is required")
    else:
        for source in sources:
            if not isinstance(source, dict):
                errors.append("each interoperability source must be an object")
                continue
            parsed = urlparse(source.get("official_reference", ""))
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append("interoperability references must be HTTPS URLs")
            if source.get("relationship_state") != "NO_PARTNERSHIP_CLAIM":
                errors.append("interoperability must not imply an unverified partnership")

    if not isinstance(data.get("design_constraints"), list) or len(data["design_constraints"]) < 5:
        errors.append("at least five design constraints are required")
    if not isinstance(data.get("initial_delivery_plan"), list) or len(data["initial_delivery_plan"]) < 5:
        errors.append("initial delivery plan must list at least five phases")

    if schema is not None:
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                errors.append(f"schema-required root field is missing: {key}")
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}))
            unexpected = set(data) - allowed
            if unexpected:
                errors.append("unexpected root fields: " + ", ".join(sorted(unexpected)))
    return errors


def main() -> int:
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"GEDF_FAIL: cannot load JSON inputs: {exc}", file=sys.stderr)
        return 2

    errors = validate(data, schema)
    if errors:
        print("GEDF_FAIL: Global Engineering Discovery Fabric proposal integrity")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GEDF_PASS: proposal integrity and evidence boundaries")
    print("LIMIT: structural integrity does not prove runtime implementation, tool quality, partnership, or production readiness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
