#!/usr/bin/env python3
"""Deterministic VAIXLNS semantic code corrector.

Repairs only mechanically safe source-level defects. It never changes declared
authority/capability/constraints to make an implementation pass.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any, Mapping

CORRECTOR_ID = "VAIXLNS-CODE-CORRECTOR-001"
SCHEMA_VERSION = "vaixlns.code_corrector.v1"

def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()

def correct_source(source: str) -> dict[str, Any]:
    original = source
    repaired = source
    findings: list[dict[str, Any]] = []
    # Safe lexical repairs only; semantic/security violations are never silently rewritten.
    replacements = [
        (r"\bCAPABILITIES\b", "CAPABILITY", "SECTION_ALIAS"),
        (r"\bCONSTRAINTS\b", "MUST_NOT", "SECTION_ALIAS"),
    ]
    for pattern, replacement, kind in replacements:
        repaired, count = re.subn(pattern, replacement, repaired)
        if count:
            findings.append({"class": kind, "count": count, "action": "REPAIR"})
    changed = repaired != original
    return {
        "schema_version": SCHEMA_VERSION,
        "corrector_id": CORRECTOR_ID,
        "input_hash": hashlib.sha256(original.encode("utf-8")).hexdigest(),
        "output_hash": hashlib.sha256(repaired.encode("utf-8")).hexdigest(),
        "changed": changed,
        "findings": findings,
        "repair_class": "MECHANICAL_SAFE" if changed else "NONE",
        "authority_mutation": False,
        "constraint_mutation": False,
        "semantic_escalation": False,
        "replay_required": True,
        "verification_required": True,
        "repaired_source": repaired,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["correct"])
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    result = correct_source(Path(args.source).read_text(encoding="utf-8"))
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    print(rendered, end="")
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
