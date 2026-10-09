#!/usr/bin/env python3
"""Validate the evidence-linked VLNS federation/capability index using stdlib only."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "registry/federation/vlns-capability-index.v1.json"


def validate(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["document_must_be_object"]
    if not isinstance(document.get("catalog_id"), str) or not document["catalog_id"]:
        errors.append("catalog_id_required")

    list_specs = [
        ("systems", "system_id"),
        ("connections", "connection_id"),
        ("capability_catalog", "capability_id"),
        ("properties", "property_id"),
        ("attribute_families", "family_id"),
        ("engineering_panels", "panel_id"),
        ("gaps", "gap_id"),
    ]
    arrays: dict[str, list[dict[str, Any]]] = {}
    for field, id_key in list_specs:
        values = document.get(field)
        if not isinstance(values, list):
            errors.append(f"{field}_must_be_array")
            arrays[field] = []
            continue
        arrays[field] = []
        seen: set[str] = set()
        for position, item in enumerate(values):
            if not isinstance(item, dict):
                errors.append(f"{field}[{position}]_must_be_object")
                continue
            arrays[field].append(item)
            identity = item.get(id_key)
            if not isinstance(identity, str) or not identity.strip():
                errors.append(f"{field}[{position}]_{id_key}_required")
                continue
            if identity in seen:
                errors.append(f"duplicate_{field}_{id_key}:{identity}")
            seen.add(identity)

    expected_systems = {"VAIXLNS", "VLNS", "VX", "NEXNET"}
    actual_systems = {row.get("system_id") for row in arrays["systems"]}
    if actual_systems != expected_systems:
        errors.append("federation_system_identity_set_mismatch")
    known_systems = actual_systems
    for edge in arrays["connections"]:
        source, target = edge.get("source_system"), edge.get("target_system")
        if source not in known_systems:
            errors.append(f"connection_source_unknown:{edge.get('connection_id')}:{source}")
        if target not in known_systems:
            errors.append(f"connection_target_unknown:{edge.get('connection_id')}:{target}")
        if edge.get("live_state") == "VERIFIED" and edge.get("authenticated") is not True:
            errors.append(f"verified_live_link_requires_authentication:{edge.get('connection_id')}")

    # Preserve unresolved identity mappings; name similarity is not identity evidence.
    for system_id, candidate in (("VLNS", "NAXLNS"), ("NEXNET", "NEXENT")):
        record = next((row for row in arrays["systems"] if row.get("system_id") == system_id), None)
        if record:
            if record.get("identity_status") != "UNVERIFIED":
                errors.append(f"candidate_identity_must_remain_unverified:{system_id}")
            surfaces = json.dumps(record.get("repository_surfaces", []), ensure_ascii=False)
            if candidate not in surfaces:
                errors.append(f"candidate_repository_reference_missing:{system_id}:{candidate}")

    families = arrays["attribute_families"]
    for family in families:
        fields = family.get("fields")
        family_id = family.get("family_id", "UNKNOWN")
        if not isinstance(fields, list) or not fields:
            errors.append(f"attribute_family_fields_required:{family_id}")
            continue
        if any(not isinstance(field, str) or not field.strip() for field in fields):
            errors.append(f"invalid_attribute_field:{family_id}")
        valid_fields = [field for field in fields if isinstance(field, str)]
        if len(valid_fields) != len(set(valid_fields)):
            errors.append(f"duplicate_attribute_field:{family_id}")
        refs = family.get("source_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"attribute_family_source_refs_required:{family_id}")

    depth = document.get("catalog_depth")
    if not isinstance(depth, dict):
        errors.append("catalog_depth_must_be_object")
        depth = {}

    for field, rows, expected_key in [
        ("identity_records", arrays["systems"], "systems"),
        ("connection_edges", arrays["connections"], "connections"),
        ("declared_capabilities", arrays["capability_catalog"], "capability_catalog"),
        ("atomic_properties", arrays["properties"], "properties"),
        ("attribute_families", arrays["attribute_families"], "attribute_families"),
        ("engineering_panels", arrays["engineering_panels"], "engineering_panels"),
        ("evidence_backed_gaps", arrays["gaps"], "gaps"),
    ]:
        if depth.get(field) != len(rows):
            errors.append(f"catalog_depth_mismatch:{field}")
    expected_field_total = sum(
        len(row.get("fields", [])) for row in families if isinstance(row.get("fields"), list)
    )
    if depth.get("indexed_attribute_fields") != expected_field_total:
        errors.append(
            "catalog_depth_mismatch:indexed_attribute_fields:"
            f"declared={depth.get('indexed_attribute_fields')}:actual={expected_field_total}"
        )

    # Reject accidentally stored raw credentials while allowing credential references/field names.
    forbidden_keys = {"api_key", "access_token", "password_value", "secret_value", "private_key"}
    def visit(value: Any, path: str = "$") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.casefold() in forbidden_keys:
                    errors.append(f"raw_credential_field_forbidden:{path}.{key}")
                visit(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")
    visit(document)
    return errors


def main() -> int:
    path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_INDEX
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"result": "FAIL", "path": str(path), "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1
    errors = validate(document)
    depth = document.get("catalog_depth", {}) if isinstance(document, dict) else {}
    if not isinstance(depth, dict):
        depth = {}
    result = {
        "result": "PASS" if not errors else "FAIL",
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "systems": len(document.get("systems", [])) if isinstance(document, dict) else 0,
        "connections": len(document.get("connections", [])) if isinstance(document, dict) else 0,
        "capabilities": len(document.get("capability_catalog", [])) if isinstance(document, dict) else 0,
        "attribute_families": len(document.get("attribute_families", [])) if isinstance(document, dict) else 0,
        "indexed_attribute_fields": depth.get("indexed_attribute_fields"),
        "gaps": len(document.get("gaps", [])) if isinstance(document, dict) else 0,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
