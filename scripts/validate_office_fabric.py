#!/usr/bin/env python3
"""Validate the VAIXLNS Operational Office Fabric registry and its cross-references."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "registry" / "office_fabric.integration.v1.json"
DEFAULT_SCHEMA = ROOT / "schemas" / "office-fabric-registry.schema.json"


def _unique_index(items: list[dict[str, Any]], key: str, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for position, item in enumerate(items):
        value = item.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"{label}[{position}] is missing a non-empty {key}")
            continue
        if value in index:
            errors.append(f"duplicate {label} {key}: {value}")
        else:
            index[value] = item
    return index


def validate_registry(registry: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Return all schema and semantic-integrity errors; an empty list means pass."""
    errors: list[str] = []

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["dependency missing: install jsonschema==4.24.0 to run validation"]

    try:
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        for issue in sorted(validator.iter_errors(registry), key=lambda e: list(map(str, e.absolute_path))):
            location = ".".join(str(part) for part in issue.absolute_path) or "$"
            errors.append(f"schema violation at {location}: {issue.message}")
    except Exception as exc:  # Keep CI failures understandable, including invalid schemas.
        errors.append(f"schema validator failed: {type(exc).__name__}: {exc}")
        return errors

    offices = registry.get("offices", [])
    systems = registry.get("systems", [])
    tools = registry.get("tool_integrations", [])
    edges = registry.get("edges", [])
    sources = registry.get("sources", [])

    office_index = _unique_index(offices, "office_id", "office", errors)
    system_index = _unique_index(systems, "system_id", "system", errors)
    tool_index = _unique_index(tools, "tool_id", "tool", errors)
    edge_index = _unique_index(edges, "edge_id", "edge", errors)
    source_index = _unique_index(sources, "source_id", "source", errors)

    coverage = registry.get("coverage", {})
    declared_counts = {
        "offices_count": len(offices),
        "system_surfaces_count": len(systems),
        "tool_integrations_count": len(tools),
    }
    for count_key, actual in declared_counts.items():
        declared = coverage.get(count_key)
        if declared != actual:
            errors.append(f"coverage.{count_key}={declared!r}, actual count={actual}")

    for office in offices:
        office_id = office.get("office_id", "<missing>")
        for system_id in office.get("owner_system_ids", []):
            if system_id not in system_index:
                errors.append(f"{office_id} references unknown owner system {system_id}")
        for tool_id in office.get("tool_ids", []):
            if tool_id not in tool_index:
                errors.append(f"{office_id} references unknown tool {tool_id}")
        for source_id in office.get("source_refs", []):
            if source_id not in source_index:
                errors.append(f"{office_id} references unknown source {source_id}")

    for system in systems:
        system_id = system.get("system_id", "<missing>")
        for office_id in system.get("office_ids", []):
            if office_id not in office_index:
                errors.append(f"{system_id} references unknown office {office_id}")
        for source_id in system.get("evidence_refs", []):
            if source_id in source_index:
                # Source IDs are valid references, but source_refs/evidence_refs may also be repository paths.
                continue
            if not isinstance(source_id, str) or not source_id:
                errors.append(f"{system_id} has an invalid evidence reference")
        if system_id in {"SYS-VLNS", "SYS-NEXNET"} and system.get("status") != "IDENTITY_UNVERIFIED":
            errors.append(f"{system_id} must remain IDENTITY_UNVERIFIED until explicit identity evidence is approved")

    for tool in tools:
        tool_id = tool.get("tool_id", "<missing>")
        owner_system_id = tool.get("owner_system_id")
        office_id = tool.get("office_id")
        if owner_system_id not in system_index:
            errors.append(f"{tool_id} references unknown owner system {owner_system_id}")
        if office_id not in office_index:
            errors.append(f"{tool_id} references unknown office {office_id}")
        for source_id in tool.get("source_refs", []):
            if source_id not in source_index:
                errors.append(f"{tool_id} references unknown source {source_id}")
        if tool.get("status") == "NOT_CONFIGURED" and tool.get("access_mode") == "GOVERNED_EXECUTION":
            errors.append(f"{tool_id} is NOT_CONFIGURED but has GOVERNED_EXECUTION access")
        if tool.get("kind") in {"external_api_adapter", "protocol_adapter", "data_adapter", "device_adapter"}:
            security = tool.get("security", {})
            if not security.get("authentication") or not security.get("egress_policy"):
                errors.append(f"{tool_id} external adapter must declare authentication and egress policy")
        if tool.get("office_id") == "OFF-FINANCIAL-ANALYSIS":
            forbidden = {"external_payment", "transfer_funds", "execute_trade", "execute_payment"}
            capabilities = set(tool.get("capabilities", []))
            if capabilities.intersection(forbidden):
                errors.append(f"{tool_id} violates the analysis-only financial authority boundary")

    for edge in edges:
        edge_id = edge.get("edge_id", "<missing>")
        endpoint_maps = {"OFFICE": office_index, "SYSTEM": system_index, "TOOL": tool_index}
        for side in ("from", "to"):
            endpoint_type = edge.get(f"{side}_type")
            endpoint_id = edge.get(f"{side}_id")
            target_index = endpoint_maps.get(endpoint_type)
            if target_index is None or endpoint_id not in target_index:
                errors.append(f"{edge_id} has unresolved {side} endpoint {endpoint_type}:{endpoint_id}")
        for source_id in edge.get("source_refs", []):
            if source_id not in source_index:
                errors.append(f"{edge_id} references unknown source {source_id}")

    # The registry may document these families, but must not claim live physical control.
    for tool in tools:
        if tool.get("kind") == "device_adapter" and tool.get("access_mode") != "OBSERVE_OR_SIMULATE_ONLY":
            errors.append(f"{tool.get('tool_id')} physical/device adapter must default to OBSERVE_OR_SIMULATE_ONLY")

    if registry.get("semantics", {}).get("zero_loss") is not True:
        errors.append("semantics.zero_loss must be true")
    if registry.get("semantics", {}).get("no_implicit_admission") is not True:
        errors.append("semantics.no_implicit_admission must be true")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)

    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not load registry/schema: {exc}", file=sys.stderr)
        return 2

    errors = validate_registry(registry, schema)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"Office fabric validation failed: {len(errors)} issue(s).", file=sys.stderr)
        return 1

    print(
        "Office fabric validation PASS: "
        f"{len(registry['offices'])} offices, "
        f"{len(registry['systems'])} system surfaces, "
        f"{len(registry['tool_integrations'])} tool integrations, "
        f"{len(registry['edges'])} edges."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
