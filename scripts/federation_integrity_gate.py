#!/usr/bin/env python3
"""VAIXLNS federation integrity gate with canonical-source validation."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "project.genome",
    "registry/omega/omega-000-master-index.json",
    "docs/indexes/REPOSITORY_FEDERATION_INDEX.md",
    "docs/indexes/REPOSITORY_RUNTIME_STATUS_V1.md",
    "docs/indexes/INNOVATION_MASTER_INDEX.md",
    "docs/recovery/VAIXLNS_MASTER_RECOVERY_AUDIT.md",
    "docs/indexes/MASTER_RECOVERY_STATUS.md",
    "docs/canonical/REPOSITORY_SYSTEM_MAP_V1.md",
    "schemas/atomic-system-record.schema.json",
]

JSON_FILES = [
    "project.genome",
    "registry/omega/omega-000-master-index.json",
    "schemas/atomic-system-record.schema.json",
    "schemas/innovation-federation.schema.json",
    "registry/repository-orchestration/REPOSITORY_FACTORY_MANIFEST_V1.json",
]

def fail(message: str) -> None:
    print(f"INTEGRITY_FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)

def read(rel: str) -> str:
    try:
        return (ROOT / rel).read_text(encoding="utf-8")
    except Exception as exc:
        fail(f"cannot read {rel}: {exc}")

def load_json(rel: str) -> object:
    try:
        return json.loads(read(rel))
    except Exception as exc:
        fail(f"invalid JSON: {rel}: {exc}")

def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

def verify_genome(genome: dict) -> None:
    normalized = json.loads(json.dumps(genome, ensure_ascii=False))
    expected = normalized.get("integrity", {}).get("canonical_hash")
    normalized.setdefault("integrity", {})["canonical_hash"] = ""
    actual = digest(normalized)
    if expected != actual:
        fail(f"project.genome digest mismatch: expected={expected}, actual={actual}")
    if genome.get("canonical_source", {}).get("status") != "CANONICAL":
        fail("project.genome is not canonical")
    if genome.get("master_index", {}).get("id") != "Ω.000":
        fail("project.genome master index identity mismatch")

def main() -> None:
    checks = 0

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            fail(f"required control surface missing: {rel}")
        checks += 1

    parsed = {rel: load_json(rel) for rel in JSON_FILES}
    checks += len(JSON_FILES)

    genome = parsed["project.genome"]
    if not isinstance(genome, dict):
        fail("project.genome must be an object")
    verify_genome(genome)

    index = parsed["registry/omega/omega-000-master-index.json"]
    if not isinstance(index, dict):
        fail("Ω.000 master index must be an object")
    for field, expected in {
        "index_id": "Ω.000",
        "status": "CANONICAL",
        "golden_source": "project.genome::v1.0.0",
        "authority_anchor": "Ω0_GENESIS_CORE",
    }.items():
        if index.get(field) != expected:
            fail(f"Ω.000 field {field!r} mismatch")
        checks += 1

    manifest = parsed[
        "registry/repository-orchestration/REPOSITORY_FACTORY_MANIFEST_V1.json"
    ]
    if not isinstance(manifest, dict):
        fail("repository factory manifest must be an object")
    if manifest.get("schema") != "vaixlns.repository-factory.v1":
        fail("repository factory manifest schema identifier mismatch")
    if manifest.get("canonical_repository") != "fisallllll280-code/VAIXLNS":
        fail("factory manifest canonical repository mismatch")
    checks += 2

    federation = read("docs/indexes/REPOSITORY_FEDERATION_INDEX.md")
    canonical_marker = chr(96) + "VAIXLNS" + chr(96)
    canonical_rows = [
        line
        for line in federation.splitlines()
        if line.startswith("| " + canonical_marker + " |") and "| CANONICAL |" in line
    ]
    if len(canonical_rows) != 1:
        fail(
            "expected exactly one CANONICAL VAIXLNS row, "
            f"found {len(canonical_rows)}"
        )
    checks += 1

    evidence_lines = [
        "VAIXLNS Federation Integrity Evidence",
        f"commit={os.environ.get('GITHUB_SHA', 'local')}",
        f"event={os.environ.get('GITHUB_EVENT_NAME', 'local')}",
        f"checks={checks}",
    ]
    for rel in dict.fromkeys(REQUIRED_FILES + JSON_FILES):
        file_digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        evidence_lines.append(f"sha256 {file_digest} {rel}")

    out = ROOT / "federation-integrity-evidence.txt"
    out.write_text("\n".join(evidence_lines) + "\n", encoding="utf-8")
    print("\n".join(evidence_lines))
    print("INTEGRITY_PASS: VAIXLNS federation control surfaces verified")

if __name__ == "__main__":
    main()
