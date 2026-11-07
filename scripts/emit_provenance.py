#!/usr/bin/env python3
"""Emit a deterministic VAIXLNS build/conformance provenance envelope."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATERIALS = [
    "project.genome",
    "registry/omega/omega-000-master-index.json",
    "registry/repository-orchestration/VAIXLNS_REPOSITORY_CONTRACT.md",
    "schemas/evidence-record.schema.json",
    "schemas/provenance-record.schema.json",
    "schemas/proof-record.schema.json",
]

def digest(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()

def main() -> int:
    missing = [rel for rel in MATERIALS if not (ROOT / rel).is_file()]
    if missing:
        print("PROVENANCE_FAIL")
        for rel in missing:
            print(f"- missing:{rel}")
        return 1

    provenance = {
        "schema_version": "1.0.0",
        "subject": [{"name": rel, "digest": digest(rel)} for rel in MATERIALS],
        "source": {
            "repository": os.getenv("GITHUB_REPOSITORY", "fisallllll280-code/VAIXLNS"),
            "revision": os.getenv("GITHUB_SHA", "local"),
        },
        "builder": {"id": os.getenv("GITHUB_WORKFLOW", "local")},
        "invocation": {"command": "python scripts/emit_provenance.py"},
        "materials": [{"uri": rel, "digest": digest(rel)} for rel in MATERIALS],
        "metadata": {
            "run_id": os.getenv("GITHUB_RUN_ID", "local"),
            "scope": "control-plane-conformance",
        },
    }
    output = ROOT / "provenance.json"
    output.write_text(
        json.dumps(provenance, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"PROVENANCE_PASS:{output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
