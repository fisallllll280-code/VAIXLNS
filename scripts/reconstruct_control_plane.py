#!/usr/bin/env python3
"""Deterministically reconstruct the VAIXLNS control-plane model."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    "project.genome",
    "registry/omega/omega-000-master-index.json",
    "registry/repository-orchestration/VAIXLNS_REPOSITORY_CONTRACT.md",
    "schemas/evidence-record.schema.json",
    "schemas/provenance-record.schema.json",
    "schemas/proof-record.schema.json",
]

def sha256_file(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()

def genome_integrity() -> bool:
    genome = json.loads((ROOT / "project.genome").read_text(encoding="utf-8"))
    expected = genome["integrity"]["canonical_hash"]
    normalized = json.loads(json.dumps(genome, ensure_ascii=False))
    normalized["integrity"]["canonical_hash"] = ""
    actual = hashlib.sha256(
        json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return actual == expected

def index_integrity() -> bool:
    index = json.loads(
        (ROOT / "registry/omega/omega-000-master-index.json").read_text(encoding="utf-8")
    )
    return (
        index.get("index_id") == "Ω.000"
        and index.get("golden_source") == "project.genome::v1.0.0"
        and index.get("authority_anchor") == "Ω0_GENESIS_CORE"
        and index.get("status") == "CANONICAL"
    )

def contract_integrity() -> bool:
    contract = (
        ROOT / "registry/repository-orchestration/VAIXLNS_REPOSITORY_CONTRACT.md"
    ).read_text(encoding="utf-8")
    return all(
        marker in contract
        for marker in (
            "System ID: VAIXLNS",
            "Repository: fisallllll280-code/VAIXLNS",
            "Golden Source: project.genome::v1.0.0",
            "Authority Anchor: Ω0_GENESIS_CORE",
            "Master Registry: Ω.000",
        )
    )

def main() -> int:
    checks = {
        "genome_integrity": genome_integrity(),
        "master_index_integrity": index_integrity(),
        "repository_contract": contract_integrity(),
        "required_inputs_present": all((ROOT / rel).is_file() for rel in INPUTS),
    }

    material_digests = {
        rel: sha256_file(rel)
        for rel in INPUTS
        if (ROOT / rel).is_file()
    }
    model_material = json.dumps(
        material_digests,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    model_digest = hashlib.sha256(model_material).hexdigest()
    passed = sum(1 for value in checks.values() if value)
    score = passed / len(checks)

    output = {
        "reconstruction_id": model_digest,
        "scope": "VAIXLNS control-plane",
        "checks": checks,
        "checks_passed": passed,
        "checks_total": len(checks),
        "equivalence_score": score,
        "status": "PASS" if passed == len(checks) else "FAIL",
        "epistemic_state": "VERIFIED" if passed == len(checks) else "PARTIAL",
        "materials": material_digests,
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if passed == len(checks) else 1

if __name__ == "__main__":
    raise SystemExit(main())
