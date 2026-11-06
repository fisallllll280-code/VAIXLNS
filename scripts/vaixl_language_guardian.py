#!/usr/bin/env python3
"""Deterministic Ω-Language Guardian for VAIXLNS semantic sources.

The Guardian compares declared meaning and capabilities with observed
capabilities and independent detector findings. It can block the current
admission candidate but cannot grant itself canonical authority.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

GUARDIAN_ID = "Ω-LANGUAGE-GUARDIAN-001"
SCHEMA_VERSION = "vaixl-language-guardian.v1"
REQUIRED_SECTIONS = ("SYSTEM", "PURPOSE", "CAPABILITY", "AUTHORITY", "MUST_NOT", "EVIDENCE", "ADMISSION")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_source(text: str) -> dict[str, Any]:
    """Parse a small deterministic, human-readable VAIXLNS source subset."""
    section = None
    result = {
        "SYSTEM": None, "PURPOSE": "", "CAPABILITY": [], "AUTHORITY": [],
        "MUST": [], "MUST_NOT": [], "BEHAVIOR": [], "EVIDENCE": [],
        "VERIFY": [], "SIMULATE": [], "RECOVER": [], "EVOLVE": [], "ADMISSION": [],
    }
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head, _, tail = line.partition(" ")
        key = head.upper()
        if key == "CAPABILITIES":
            key = "CAPABILITY"
        if key == "CONSTRAINTS":
            key = "MUST_NOT"
        if key == "SYSTEM":
            if not tail.strip():
                raise ValueError("SYSTEM requires an identifier")
            result["SYSTEM"] = tail.strip()
            section = None
            continue
        if key in result:
            section = key
            if tail.strip():
                result[section].append(tail.strip())
            continue
        if section == "PURPOSE":
            result["PURPOSE"] = (result["PURPOSE"] + " " + line).strip()
        elif section:
            result[section].append(line)
        else:
            raise ValueError("content_before_section:" + line)
    missing = [name for name in REQUIRED_SECTIONS if not result[name]]
    if missing:
        raise ValueError("missing_required_sections:" + ",".join(missing))
    return result


def semantic_source_hash(source: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(source).encode("utf-8")).hexdigest()


def normalized(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {str(value).strip().upper() for value in values if str(value).strip()}


def analyze(
    source: Mapping[str, Any],
    observed_capabilities: list[str] | None = None,
    external_detector: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    declared = normalized(source.get("CAPABILITY"))
    forbidden = normalized(source.get("MUST_NOT"))
    observed = normalized(observed_capabilities if observed_capabilities is not None else list(declared))
    unauthorized = sorted(observed - declared)
    forbidden_observed = sorted(observed & forbidden)
    findings: list[dict[str, Any]] = []

    if unauthorized:
        findings.append({
            "id": "CAPABILITY-DRIFT-001",
            "class": "CAPABILITY_DRIFT",
            "severity": "CRITICAL",
            "decision": "QUARANTINE",
            "details": unauthorized,
        })
    if forbidden_observed:
        findings.append({
            "id": "CONSTRAINT-VIOLATION-001",
            "class": "CONSTRAINT_VIOLATION",
            "severity": "CRITICAL",
            "decision": "QUARANTINE",
            "details": forbidden_observed,
        })

    authority_tokens = " ".join(str(x).upper() for x in source.get("AUTHORITY", []))
    if any(token in authority_tokens for token in ("ROOT", "UNRESTRICTED", "SELF_PROMOTE", "ADMIN:*")):
        findings.append({
            "id": "AUTHORITY-ESCALATION-001",
            "class": "AUTHORITY_ESCALATION",
            "severity": "CRITICAL",
            "decision": "QUARANTINE",
            "details": ["forbidden self-escalation authority token"],
        })

    external = dict(external_detector or {})
    external_items = external.get("findings", [])
    if not isinstance(external_items, list):
        external_items = []
    blocking_external = [
        dict(item) for item in external_items
        if isinstance(item, Mapping)
        and str(item.get("severity", "")).upper() in {"HIGH", "CRITICAL"}
    ]
    if blocking_external:
        findings.append({
            "id": "EXTERNAL-DETECTOR-001",
            "class": "EXTERNAL_THREAT_DETECTION",
            "severity": "HIGH",
            "decision": "QUARANTINE",
            "details": blocking_external,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "guardian_id": GUARDIAN_ID,
        "subject": {"system": source["SYSTEM"], "source_hash": semantic_source_hash(source)},
        "declared": {
            "capabilities": sorted(declared),
            "forbidden_capabilities": sorted(forbidden),
            "authority": source["AUTHORITY"],
        },
        "observed": {"capabilities": sorted(observed)},
        "findings": findings,
        "external_detector": {
            "provider": external.get("provider", "NONE"),
            "status": external.get("status", "NOT_PROVIDED"),
            "result_is_advisory": True,
        },
        "decision": "QUARANTINE" if findings else "ADMIT_CANDIDATE",
        "reason": "SECURITY_FINDINGS_PRESENT" if findings else "SEMANTIC_SECURITY_PASS",
        "history_preserved": True,
        "self_authority_grant": False,
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="VAIXLNS Ω-Language Guardian")
    parser.add_argument("command", choices=["guard"])
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", default="")
    parser.add_argument("--observed-capability", action="append", default=None)
    parser.add_argument("--external-result", default="")
    args = parser.parse_args()

    source = parse_source(Path(args.source).read_text(encoding="utf-8"))
    external = load_json(Path(args.external_result)) if args.external_result else None
    evidence = analyze(source, args.observed_capability, external)
    rendered = json.dumps(evidence, indent=2, ensure_ascii=False) + "\n"
    print(rendered, end="")
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0 if evidence["decision"] == "ADMIT_CANDIDATE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
