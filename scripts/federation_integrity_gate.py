#!/usr/bin/env python3
"""VAIXLNS deterministic federation integrity gate."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

JSON_FILES = [
    "schemas/atomic-system-record.schema.json",
    "schemas/innovation-federation.schema.json",
    "registry/repository-orchestration/REPOSITORY_FACTORY_MANIFEST_V1.json",
]

REQUIRED_FILES = [
    "docs/indexes/REPOSITORY_FEDERATION_INDEX.md",
    "docs/indexes/REPOSITORY_RUNTIME_STATUS_V1.md",
    "docs/indexes/INNOVATION_MASTER_INDEX.md",
    "docs/recovery/VAIXLNS_MASTER_RECOVERY_AUDIT.md",
    "docs/indexes/MASTER_RECOVERY_STATUS.md",
    "docs/canonical/REPOSITORY_SYSTEM_MAP_V1.md",
    "schemas/atomic-system-record.schema.json",
]

ROLE_ASSERTIONS = {
    "docs/indexes/REPOSITORY_FEDERATION_INDEX.md": [
        "VAIXLNS", "NEXENT", "VAIXLNS-unified",
    ],
    "docs/canonical/REPOSITORY_SYSTEM_MAP_V1.md": [
        "NEXENT", "DISCOVER", "VAIXLNS", "CANONICAL OWNER",
    ],
    "docs/indexes/MASTER_RECOVERY_STATUS.md": [
        "VAIXLNS", "CANONICALIZE",
    ],
}

def fail(message: str) -> None:
    print(f"INTEGRITY_FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)

def load_json(rel: str) -> object:
    try:
        with (ROOT / rel).open(encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        fail(f"invalid JSON: {rel}: {exc}")

def read(rel: str) -> str:
    try:
        return (ROOT / rel).read_text(encoding="utf-8")
    except Exception as exc:
        fail(f"cannot read {rel}: {exc}")

def main() -> None:
    checks = 0

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            fail(f"required control surface missing: {rel}")
        checks += 1

    parsed = {}
    for rel in JSON_FILES:
        parsed[rel] = load_json(rel)
        checks += 1

    for rel, needles in ROLE_ASSERTIONS.items():
        body = read(rel)
        for needle in needles:
            if needle not in body:
                fail(f"required canonical assertion missing: {needle!r} in {rel}")
            checks += 1

    manifest = parsed["registry/repository-orchestration/REPOSITORY_FACTORY_MANIFEST_V1.json"]
    if not isinstance(manifest, dict):
        fail("repository factory manifest must be an object")
    if manifest.get("schema") != "vaixlns.repository-factory.v1":
        fail("repository factory manifest schema identifier mismatch")
    if manifest.get("canonical_repository") != "fisallllll280-code/VAIXLNS":
        fail("factory manifest canonical repository mismatch")

    policy = manifest.get("policy")
    if not isinstance(policy, dict):
        fail("factory manifest policy is missing")
    required_policy = {
        "continuous_pulse": True,
        "auto_create_requires_explicit_manifest_flag": True,
        "never_overwrite_unclassified": True,
        "require_contract_seed": True,
        "require_verification_after_seed": True,
    }
    for key, expected in required_policy.items():
        if policy.get(key) is not expected:
            fail(f"factory policy violation: {key} must be {expected!r}")
        checks += 1

    repositories = manifest.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        fail("factory manifest repositories must be a non-empty list")
    names = [item.get("name") for item in repositories if isinstance(item, dict)]
    if len(names) != len(set(names)):
        fail("factory manifest contains duplicate repository names")
    checks += 1

    federation = read("docs/indexes/REPOSITORY_FEDERATION_INDEX.md")
    canonical_rows = [
        line for line in federation.splitlines()
        if line.startswith("| `VAIXLNS` |") and "| CANONICAL |" in line
    ]
    if len(canonical_rows) != 1:
        fail(
            "expected exactly one CANONICAL repository row in federation index; "
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
        digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        evidence_lines.append(f"sha256 {digest} {rel}")

    out = ROOT / "federation-integrity-evidence.txt"
    out.write_text("\n".join(evidence_lines) + "\n", encoding="utf-8")
    print("\n".join(evidence_lines))
    print("INTEGRITY_PASS: VAIXLNS federation control surfaces verified")

if __name__ == "__main__":
    main()
