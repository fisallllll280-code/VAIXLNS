#!/usr/bin/env python3
"""Mechanical VAIXLNS control-plane admission gate."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(os.getenv("VAIXLNS_REPOSITORY_ROOT", Path(__file__).resolve().parents[1]))
BAD_PATH_CHARS = re.compile(r"[├└│╔╗╚╝║═]")
REQUIRED_FILES = {
    "identity": ["README.md"],
    "contract": [
        "VAIXLNS_REPOSITORY_CONTRACT.md",
        "registry/repository-orchestration/VAIXLNS_REPOSITORY_CONTRACT.md",
    ],
    "conformance": [
        ".github/workflows/vaixlns-conformance.yml",
        ".github/workflows/federation-integrity.yml",
    ],
    "genome": ["project.genome"],
    "master_index": ["registry/omega/omega-000-master-index.json"],
    "evidence_schema": ["schemas/evidence-record.schema.json"],
    "provenance_schema": ["schemas/provenance-record.schema.json"],
}
REQUIRED_CONTRACT_FIELDS = [
    "System ID:",
    "Repository:",
    "Role:",
    "Family:",
    "State:",
    "Golden Source:",
    "Authority Anchor:",
    "Master Registry:",
]
EPISTEMIC_STATES = {
    "PROPOSAL",
    "SPECIFIED",
    "IMPLEMENTED",
    "VERIFIED",
    "PARTIAL",
    "MISSING",
    "CONFLICT",
    "RECOVERED",
}

def find_first(candidates: list[str]) -> Path | None:
    for rel in candidates:
        candidate = ROOT / rel
        if candidate.is_file():
            return candidate
    return None

def canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

def genome_digest(genome: dict) -> str:
    normalized = json.loads(json.dumps(genome, ensure_ascii=False))
    normalized.setdefault("integrity", {})["canonical_hash"] = ""
    return hashlib.sha256(canonical_json(normalized)).hexdigest()

def path_hygiene() -> list[str]:
    errors: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        rel_path = path.relative_to(ROOT)
        rel = rel_path.as_posix()
        if len(rel) > 180:
            errors.append(f"PATH_TOO_LONG:{len(rel)}:{rel}")
        if BAD_PATH_CHARS.search(rel):
            errors.append(f"MALFORMED_PATH:{rel}")
        if any(
            part.startswith((" ", "\t")) or part.endswith((" ", "\t"))
            for part in rel_path.parts
        ):
            errors.append(f"PATH_WHITESPACE:{rel}")
    return errors

def verify_genome(errors: list[str]) -> None:
    path = ROOT / "project.genome"
    try:
        genome = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"GENOME_PARSE:{exc}")
        return
    expected = genome.get("integrity", {}).get("canonical_hash")
    actual = genome_digest(genome)
    if expected != actual:
        errors.append(f"GENOME_HASH_MISMATCH:expected={expected}:actual={actual}")
    source = genome.get("canonical_source", {})
    for key, value in {
        "type": "project.genome",
        "version": "1.0.0",
        "status": "CANONICAL",
        "authority": "Ω0_GENESIS_CORE",
    }.items():
        if source.get(key) != value:
            errors.append(f"GENOME_SOURCE_{key.upper()}_INVALID")

def verify_master_index(errors: list[str]) -> None:
    path = ROOT / "registry/omega/omega-000-master-index.json"
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"INDEX_PARSE:{exc}")
        return
    for key, value in {
        "index_id": "Ω.000",
        "golden_source": "project.genome::v1.0.0",
        "authority_anchor": "Ω0_GENESIS_CORE",
        "status": "CANONICAL",
    }.items():
        if index.get(key) != value:
            errors.append(f"INDEX_{key.upper()}_INVALID")
    for record in index.get("records", []):
        state = record.get("epistemic_state")
        if state not in EPISTEMIC_STATES:
            errors.append(f"INDEX_BAD_EPISTEMIC_STATE:{record.get('id')}:{state}")
        if state in {"VERIFIED", "CANONICAL"} and not record.get("evidence_refs"):
            errors.append(f"INDEX_UNEVIDENCED_PROMOTION:{record.get('id')}")

def main() -> int:
    result: dict[str, str] = {}
    errors = path_hygiene()

    for key, candidates in REQUIRED_FILES.items():
        result[key] = "PASS" if find_first(candidates) else "FAIL"
        if result[key] == "FAIL":
            errors.append(f"MISSING_REQUIRED:{key}")

    verify_genome(errors)
    verify_master_index(errors)

    contract = find_first(REQUIRED_FILES["contract"])
    if contract:
        content = contract.read_text(encoding="utf-8")
        missing = [field for field in REQUIRED_CONTRACT_FIELDS if field not in content]
        invalid = [
            marker
            for marker in ("System ID: TBD", "State: PROPOSAL")
            if marker in content
        ]
        result["contract_content"] = "PASS" if not missing and not invalid else "FAIL"
        if missing:
            errors.append(f"CONTRACT_FIELDS_MISSING:{','.join(missing)}")
        if invalid:
            errors.append(f"CONTRACT_INVALID_MARKERS:{','.join(invalid)}")
    else:
        result["contract_content"] = "FAIL"

    result["path_hygiene"] = (
        "PASS"
        if not any(
            e.startswith(("PATH_", "MALFORMED_")) for e in errors
        )
        else "FAIL"
    )
    result["execution"] = "PENDING_RUNTIME_EVIDENCE"
    result["security"] = "PENDING_EVIDENCE"
    result["performance"] = "PENDING_EVIDENCE"
    result["recovery"] = "PENDING_EVIDENCE"
    result["evidence"] = "CONTROL_SURFACE_PRESENT"
    result["provenance"] = "SCHEMA_PRESENT"

    hard = [
        "identity",
        "contract",
        "conformance",
        "genome",
        "master_index",
        "evidence_schema",
        "provenance_schema",
        "contract_content",
    ]
    result["admission"] = (
        "ADMITTED"
        if not errors and all(result[key] == "PASS" for key in hard)
        else "BLOCKED"
    )
    result["admission_scope"] = "control_surface_only"

    print(json.dumps(result, indent=2, sort_keys=True))
    if errors:
        print("ERRORS")
        for error in sorted(set(errors)):
            print(f"- {error}")
    return 0 if result["admission"] == "ADMITTED" else 1

if __name__ == "__main__":
    raise SystemExit(main())
