#!/usr/bin/env python3
"""Mechanical first-pass admission gate for a VAIXLNS repository.

The gate validates canonical repository surfaces without requiring them to live
at the repository root. Structural presence is evidence of contract coverage,
not proof of runtime correctness.
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


def exists(root: Path, candidates: list[str]) -> bool:
    return any((root / path).is_file() for path in candidates)


def main() -> int:
    root = Path(os.getenv("VAIXLNS_REPOSITORY_ROOT", ".")).resolve()

    result: dict[str, str] = {}
    result["identity"] = "PASS" if exists(root, REQUIRED["identity"]) else "FAIL"
    result["contract"] = "PASS" if exists(root, REQUIRED["contract"]) else "FAIL"
    result["conformance"] = "PASS" if exists(root, REQUIRED["conformance"]) else "FAIL"

    has_src = any((root / path).is_dir() for path in ("src", "app", "lib"))
    has_tests = any((root / path).is_dir() for path in ("tests", "test"))
    has_workflow = (root / ".github" / "workflows").is_dir()

    result["source"] = "PASS" if has_src else "N/A"
    result["build"] = "PASS" if has_workflow else "FAIL"
    result["execution"] = "N/A" if not has_src else "PENDING_RUNTIME_EVIDENCE"
    result["tests"] = "PASS" if has_tests else ("N/A" if not has_src else "FAIL")
    result["security"] = "PENDING_EVIDENCE"
    result["performance"] = "PENDING_EVIDENCE"
    result["provenance"] = "PASS" if exists(root, ["docs", "registry"]) else "FAIL"
    result["recovery"] = "N/A" if not has_src else "PENDING_EVIDENCE"
    result["evidence"] = "PASS" if (root / "docs").is_dir() else "FAIL"

    hard = ["identity", "contract", "conformance", "build", "provenance", "evidence"]
    result["admission"] = (
        "ADMITTED" if all(result[key] == "PASS" for key in hard) else "BLOCKED"
    )

    print(json.dumps(result, indent=2))
    return 0 if result["admission"] == "ADMITTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
