#!/usr/bin/env python3
"""Evaluate a machine-readable candidate against the VAIXLNS admission gates."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MANDATORY_GATES = (
    "identity",
    "contract",
    "source",
    "build",
    "execution",
    "tests",
    "conformance",
    "security",
    "performance",
    "provenance",
    "recovery",
    "evidence",
)

PASS_VALUES = {"PASS", "N/A", "NOT_APPLICABLE"}


def evaluate(candidate: dict[str, Any]) -> dict[str, Any]:
    gates = candidate.get("gates")
    if not isinstance(gates, dict):
        raise ValueError("gates must be an object")

    failures: list[str] = []
    normalized: dict[str, str] = {}

    for gate in MANDATORY_GATES:
        value = gates.get(gate)
        if not isinstance(value, str):
            failures.append(f"MISSING_GATE:{gate}")
            normalized[gate] = "FAIL"
            continue

        normalized[gate] = value.upper()
        if normalized[gate] not in PASS_VALUES:
            failures.append(f"GATE_NOT_PASS:{gate}:{normalized[gate]}")

    if candidate.get("candidate_id") in {None, ""}:
        failures.append("CANDIDATE_ID_REQUIRED")

    provenance = candidate.get("provenance")
    if not isinstance(provenance, dict) or not provenance.get("canonical_ref"):
        failures.append("CANONICAL_PROVENANCE_REQUIRED")

    result = "ADMITTED" if not failures else "BLOCKED"
    return {
        "candidate_id": candidate.get("candidate_id", ""),
        "gates": normalized,
        "failures": failures,
        "admission": result,
    }


def main() -> int:
    rel = sys.argv[1] if len(sys.argv) > 1 else "registry/admission/golden-candidate.json"
    path = ROOT / rel
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
        verdict = evaluate(candidate)
    except Exception as exc:
        print(json.dumps({"admission": "BLOCKED", "failures": [str(exc)]}, indent=2))
        return 1

    print(json.dumps(verdict, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if verdict["admission"] == "ADMITTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
