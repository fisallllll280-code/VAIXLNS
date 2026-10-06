#!/usr/bin/env python3
"""Validate the canonical external integration control manifest."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "registry/integration-control/external-integrations-policy-v1.json"

REQUIRED_CLASSES = {
    "MODEL", "API", "SERVER", "TOOL", "CONNECTOR", "REPOSITORY", "DATA_SOURCE",
}
REQUIRED_GATES = {
    "IDENTITY", "CONTRACT", "SANDBOX", "FUNCTIONAL_TEST", "FAILURE_RECOVERY",
    "REPLAY", "INDEPENDENT_VERIFICATION", "PROOF_FRESHNESS",
    "CAUSAL_IMPACT_BUDGET", "EXPLICIT_AUTHORITY",
}


def main() -> int:
    try:
        data = json.loads(POLICY.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"EXTERNAL_INTEGRATION_POLICY:FAIL:{exc}")
        return 1
    errors = []
    if data.get("default") != "DENY":
        errors.append("DEFAULT_NOT_DENY")
    if set(data.get("classes", [])) != REQUIRED_CLASSES:
        errors.append("CLASS_SET_MISMATCH")
    if not REQUIRED_GATES.issubset(set(data.get("mandatory_gates", []))):
        errors.append("MANDATORY_GATES_INCOMPLETE")
    if data.get("runtime_rule") != "ADMITTED + FRESH_PROOF + MATCHED_IDENTITY + ALLOWED_CAPABILITY":
        errors.append("RUNTIME_RULE_MISMATCH")
    print("EXTERNAL_INTEGRATION_POLICY:PASS" if not errors else "EXTERNAL_INTEGRATION_POLICY:FAIL")
    for error in errors:
        print(f"- {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
