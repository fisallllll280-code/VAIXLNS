#!/usr/bin/env python3
"""Mechanical first-pass admission gate for a VAIXLNS repository.

The gate checks required structure and validates the canonical contract content.
Structural presence alone never proves runtime correctness.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

REQUIRED = {
    "identity": ["README.md"],
    "contract": [
        "VAIXLNS_REPOSITORY_CONTRACT.md",
        "registry/repository-orchestration/VAIXLNS_REPOSITORY_CONTRACT.md",
    ],
    "conformance": [
        ".github/workflows/vaixlns-conformance.yml",
        ".github/workflows/federation-integrity.yml",
    ],
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

def find_first(root: Path, candidates: list[str]) -> Path | None:
    for path in candidates:
        candidate = root / path
        if candidate.exists():
            return candidate
    return None

def main() -> int:
    root = Path(os.getenv("VAIXLNS_REPOSITORY_ROOT", ".")).resolve()
    result: dict[str, str] = {}

    result["identity"] = "PASS" if (root / "README.md").exists() else "FAIL"

    contract = find_first(root, REQUIRED["contract"])
    if contract is None:
        result["contract"] = "FAIL"
    else:
        content = contract.read_text(encoding="utf-8")
        missing = [field for field in REQUIRED_CONTRACT_FIELDS if field not in content]
        invalid_markers = [marker for marker in ("System ID: TBD", "State: PROPOSAL") if marker in content]
        result["contract"] = "PASS" if not missing and not invalid_markers else "FAIL"

    result["conformance"] = (
        "PASS"
        if find_first(root, REQUIRED["conformance"]) is not None
        else "FAIL"
    )

    has_src = any((root / p).exists() for p in ("src", "app", "lib"))
    has_tests = any((root / p).exists() for p in ("tests", "test"))
    has_workflow = (root / ".github" / "workflows").exists()

    result["source"] = "PASS" if has_src else "N/A"
    result["build"] = "PASS" if has_workflow else "FAIL"
    result["execution"] = "N/A" if not has_src else "PENDING_RUNTIME_EVIDENCE"
    result["tests"] = "PASS" if has_tests else ("N/A" if not has_src else "FAIL")
    result["security"] = "PENDING_EVIDENCE"
    result["performance"] = "PENDING_EVIDENCE"
    result["provenance"] = "PASS" if (root / "docs").exists() and (root / "registry").exists() else "FAIL"
    result["recovery"] = "N/A" if not has_src else "PENDING_EVIDENCE"
    result["evidence"] = "PASS" if (root / "docs").exists() else "FAIL"

    hard = ["identity", "contract", "conformance", "build", "provenance", "evidence"]
    result["admission"] = "ADMITTED" if all(result[k] == "PASS" for k in hard) else "BLOCKED"

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["admission"] == "ADMITTED" else 1

if __name__ == "__main__":
    raise SystemExit(main())
