#!/usr/bin/env python3
"""Validate VCEF research provenance and admission boundaries, without network access."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "registry/computer-engineering/VCEF_INNOVATION_INDEX_V1.json"
TRACKS = {f"CE-{i:02d}" for i in range(1, 9)}
PRIORITIES = {"P0", "P1", "P2"}

def validate(data):
    errors = []
    if data.get("schema") != "vaixlns.vcef.innovation-index.v1":
        errors.append("schema mismatch")
    if data.get("status") != "RESEARCH_CANDIDATES_NOT_CANONICALLY_ADMITTED":
        errors.append("research must not be promoted without governance")
    policy = data.get("policy", {})
    for field in ("source_provenance_required", "licensing_review_required", "no_external_code_copy", "no_automatic_hardware_fabrication", "no_production_deployment"):
        if policy.get(field) is not True:
            errors.append("unsafe policy: " + field)
    track_ids = [x.get("id") for x in data.get("tracks", [])]
    if set(track_ids) != TRACKS or len(track_ids) != 8:
        errors.append("expected CE-01..CE-08 exactly once")
    ids = set()
    for entry in data.get("innovations", []):
        eid = entry.get("id")
        if eid in ids:
            errors.append("duplicate innovation: " + str(eid))
        ids.add(eid)
        if entry.get("track") not in TRACKS or entry.get("priority") not in PRIORITIES:
            errors.append("invalid track/priority: " + str(eid))
        if not entry.get("hypothesis") or not entry.get("toolchain"):
            errors.append("missing reproducibility plan: " + str(eid))
        if not entry.get("sources") or any(not s.startswith("https://") for s in entry["sources"]):
            errors.append("missing HTTPS provenance: " + str(eid))
        if not entry.get("maturity"):
            errors.append("missing maturity: " + str(eid))
    if not data.get("innovations"):
        errors.append("no innovations")
    return errors

if __name__ == "__main__":
    d = json.loads(INDEX.read_text(encoding="utf-8"))
    failures = validate(d)
    print(json.dumps({"status": "FAIL" if failures else "PASS", "innovations": len(d.get("innovations", [])), "tracks": len(d.get("tracks", [])), "errors": failures}, indent=2))
    raise SystemExit(bool(failures))
