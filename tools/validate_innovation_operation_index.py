#!/usr/bin/env python3
"""Fail-closed validation for the generated innovation operation index."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "registry/innovation-operation-index.v1.json"
SCHEMA = ROOT / "schemas/innovation-operation-index.schema.json"
ALLOWED = {"CANONICAL","VERIFIED","IMPLEMENTED","SPECIFIED","PARTIAL","MISSING","CONFLICT","PROPOSAL","RECOVERED","QUARANTINED","SOURCE-ASSERTED","UNKNOWN"}
QUALITY = {"SOURCE_BACKED","CURATED_DESIGN_DRAFT","RULE_DERIVED_DRAFT"}

def fail(message: str) -> None:
    print("INNOVATION_OPERATION_INDEX_FAIL: " + message, file=sys.stderr)
    raise SystemExit(1)

def main() -> int:
    if not INDEX.is_file() or not SCHEMA.is_file():
        fail("generated index or schema is missing")
    try:
        data = json.loads(INDEX.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON: {exc}")
    if data.get("schema") != "VAIXLNS.InnovationOperationIndex.v1":
        fail("schema identifier mismatch")
    if schema.get("title") != "VAIXLNS Innovation Operation Index":
        fail("schema title mismatch")
    items = data.get("items")
    if not isinstance(items, list) or data.get("summary", {}).get("record_count") != len(items):
        fail("record count does not match items")
    ids = [x.get("canonical_id") for x in items if isinstance(x, dict)]
    if len(ids) != len(items) or len(ids) != len(set(ids)):
        fail("duplicate IDs or non-object item")
    missing_sources = set()
    for item in items:
        for key in ("canonical_id","name","family","owner","status","description","description_basis","mechanism_basis","profile_quality"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                fail(f"missing required string {key}: {item.get('name')}")
        if not re.fullmatch(r"INNOV-[A-F0-9]{12}", item["canonical_id"]):
            fail("invalid deterministic ID: " + item["canonical_id"])
        if item["status"] not in ALLOWED:
            fail("invalid status for " + item["name"])
        if item["profile_quality"] not in QUALITY:
            fail("invalid profile quality for " + item["name"])
        if not isinstance(item.get("operating_mechanism"), list) or not item["operating_mechanism"] or any(not str(s).strip() for s in item["operating_mechanism"]):
            fail("missing operating mechanism for " + item["name"])
        if item.get("canonical_promotion_allowed") is not False:
            fail("generator must never grant canonical promotion: " + item["name"])
        if not isinstance(item.get("status_observations"), list):
            fail("status observations must be an array: " + item["name"])
        for source in item.get("source_refs", []):
            if source.startswith("http://") or source.startswith("https://"):
                continue
            if not (ROOT / source).is_file():
                missing_sources.add(source)
    if missing_sources:
        fail("source references missing from repository: " + ", ".join(sorted(missing_sources)[:20]))
    if data.get("generation", {}).get("state_promotion") != "DISABLED":
        fail("state promotion must remain disabled")
    if data.get("canonical_source") != "project.genome::v1.0.0" or data.get("master_index") != "Ω.000":
        fail("canonical authority references mismatch")
    print(f"INNOVATION_OPERATION_INDEX_PASS: {len(items)} records; promotion disabled; profile and source checks passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
