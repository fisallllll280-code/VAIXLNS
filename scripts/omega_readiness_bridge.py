"""Evidence-gated readiness evaluator for the VAIXLNS Omega bridge.

Pure local logic only: no network, cloud provider, system probes, or external actions.
A PASS means only that the supplied, timestamped input contract passes evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUSES = {"PASS", "DEGRADED", "FAIL", "UNKNOWN", "STALE", "NOT_APPLICABLE"}
DEFAULT_HARD_GATES = (
    "availability", "integrity", "dependencies", "capacity",
    "security", "recovery", "governance", "evidence_quality",
)
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical_hash(value: dict[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def evaluate_readiness(payload: Any, *, now: datetime | None = None) -> dict[str, Any]:
    """Evaluate a supplied capability packet; never infer missing evidence as success."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    blockers: list[str] = []
    if not isinstance(payload, dict):
        payload = {}
        blockers.append("INVALID_INPUT_SHAPE")

    capability_id = payload.get("capability_id")
    if not isinstance(capability_id, str) or not capability_id.strip():
        capability_id = "UNKNOWN"
        blockers.append("CAPABILITY_ID_MISSING")

    max_age = payload.get("max_age_seconds", 300)
    if not isinstance(max_age, int) or isinstance(max_age, bool) or max_age < 1:
        max_age = 300
        blockers.append("INVALID_MAX_AGE_SECONDS")

    observed_at = _parse_time(payload.get("observed_at"))
    if observed_at is None:
        blockers.append("OBSERVATION_TIME_MISSING_OR_INVALID")
        observation_status = "UNKNOWN"
    elif (now - observed_at).total_seconds() > max_age:
        blockers.append("OBSERVATION_STALE")
        observation_status = "STALE"
    elif (observed_at - now).total_seconds() > 30:
        blockers.append("OBSERVATION_FROM_FUTURE")
        observation_status = "UNKNOWN"
    else:
        observation_status = "PASS"

    checks = payload.get("checks")
    if not isinstance(checks, dict):
        checks = {}
        blockers.append("CHECKS_MISSING_OR_INVALID")

    hard_gates = payload.get("hard_gates", list(DEFAULT_HARD_GATES))
    if (not isinstance(hard_gates, list) or not hard_gates
            or any(not isinstance(g, str) or not g for g in hard_gates)):
        hard_gates = list(DEFAULT_HARD_GATES)
        blockers.append("HARD_GATES_INVALID")

    safe_check_keys = [key for key in checks if isinstance(key, str) and key]
    if len(safe_check_keys) != len(checks):
        blockers.append("CHECK_KEYS_INVALID")
    normalized_checks: dict[str, str] = {}
    all_gates = set(DEFAULT_HARD_GATES) | set(hard_gates) | set(safe_check_keys)
    for gate in sorted(all_gates):
        value = checks.get(gate, "UNKNOWN")
        if not isinstance(value, str) or value not in STATUSES:
            value = "UNKNOWN"
            blockers.append(f"INVALID_STATUS:{gate}")
        normalized_checks[gate] = value
        if gate in hard_gates and value != "PASS":
            blockers.append(f"HARD_GATE_{value}:{gate}")

    dependencies_declared = payload.get("dependencies_declared") is True
    if not dependencies_declared:
        blockers.append("DEPENDENCY_CLOSURE_NOT_ATTESTED")
    if "dependencies" not in payload:
        blockers.append("DEPENDENCIES_NOT_DECLARED")
    dependencies = payload.get("dependencies", [])
    if not isinstance(dependencies, list):
        dependencies = []
        blockers.append("DEPENDENCIES_INVALID")
    dependency_ids: set[str] = set()
    for item in dependencies:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
            blockers.append("DEPENDENCY_RECORD_INVALID")
            continue
        dep_id = item["id"].strip()
        if dep_id in dependency_ids:
            blockers.append(f"DUPLICATE_DEPENDENCY:{dep_id}")
        dependency_ids.add(dep_id)
        dep_status = item.get("status", "UNKNOWN")
        if not isinstance(dep_status, str) or dep_status not in STATUSES:
            dep_status = "UNKNOWN"
        if dep_status != "PASS":
            blockers.append(f"DEPENDENCY_{dep_status}:{dep_id}")
        dep_time = _parse_time(item.get("observed_at"))
        if dep_time is None:
            blockers.append(f"DEPENDENCY_TIME_UNKNOWN:{dep_id}")
        elif (now - dep_time).total_seconds() > max_age:
            blockers.append(f"DEPENDENCY_STALE:{dep_id}")
        elif (dep_time - now).total_seconds() > 30:
            blockers.append(f"DEPENDENCY_TIME_FUTURE:{dep_id}")

    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []
        blockers.append("EVIDENCE_INVALID")
    valid_evidence = 0
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            blockers.append(f"EVIDENCE_RECORD_INVALID:{index}")
            continue
        ref = item.get("ref")
        digest = item.get("sha256")
        if not isinstance(ref, str) or not ref.strip():
            blockers.append(f"EVIDENCE_REF_MISSING:{index}")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            blockers.append(f"EVIDENCE_HASH_INVALID:{index}")
        if item.get("verified") is not True:
            blockers.append(f"EVIDENCE_NOT_VERIFIED:{index}")
        evidence_time = _parse_time(item.get("observed_at"))
        if evidence_time is None:
            blockers.append(f"EVIDENCE_TIME_UNKNOWN:{index}")
        elif (now - evidence_time).total_seconds() > max_age:
            blockers.append(f"EVIDENCE_STALE:{index}")
        elif (evidence_time - now).total_seconds() > 30:
            blockers.append(f"EVIDENCE_TIME_FUTURE:{index}")
        if (isinstance(ref, str) and ref.strip()
                and isinstance(digest, str) and SHA256_RE.fullmatch(digest)
                and item.get("verified") is True and evidence_time is not None
                and 0 <= (now - evidence_time).total_seconds() <= max_age):
            valid_evidence += 1

    if valid_evidence == 0:
        blockers.append("NO_VALID_EVIDENCE")
    if observation_status != "PASS":
        blockers.append(f"OBSERVATION_{observation_status}")

    blockers = sorted(set(blockers))
    if blockers:
        overall = "NOT_READY"
    elif any(value in {"DEGRADED", "FAIL", "UNKNOWN", "STALE"}
             for value in normalized_checks.values()):
        overall = "DEGRADED"
    else:
        overall = "READY"

    report: dict[str, Any] = {
        "schema_version": "omega-readiness-report-v1",
        "capability_id": capability_id,
        "evaluated_at": _iso(now),
        "observation_status": observation_status,
        "status": overall,
        "checks": normalized_checks,
        "dependency_count": len(dependencies),
        "valid_evidence_count": valid_evidence,
        "evidence_verification_mode": "caller_attested_only_digest_format_checked_not_recomputed",
        "blockers": blockers,
        "execution_performed": False,
        "external_calls_performed": False,
        "human_approval_required": True,
        "scope_note": (
            "Evaluation of supplied evidence only; digest format is checked but artifact bytes "
            "are not fetched or re-hashed here; the verified flag is caller-attested. "
            "This is not proof of live runtime or deployment."
        ),
    }
    report["report_sha256"] = _canonical_hash(report)
    return report



def evaluate_vx_stage_instance(
    instance: Any,
    *,
    required_capability: str,
    required_authority: str,
    evidence: list[dict[str, Any]],
    dependencies: list[dict[str, Any]] | None = None,
    dependencies_declared: bool = False,
    integrity_verified: bool = False,
    capacity_available: bool = False,
    recovery_verified: bool = False,
    governance_approved: bool = False,
    max_age_seconds: int = 300,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Adapt an in-process VX Stage instance into the readiness contract.

    The caller must supply independent integrity/recovery/governance/capacity
    assertions and evidence. Merely being ACTIVE never satisfies those gates.
    """
    state = getattr(instance, "state", None)
    last_seen = getattr(instance, "last_seen", None)
    capabilities = getattr(instance, "capabilities", ())
    authority_scope = getattr(instance, "authority_scope", ())
    active = state == "ACTIVE"
    has_capability = required_capability in capabilities
    has_authority = required_authority in authority_scope
    deps = dependencies if isinstance(dependencies, list) else []
    dependency_state = (
        "PASS" if dependencies_declared and all(
            isinstance(dep, dict) and dep.get("status") == "PASS" for dep in deps
        ) else "UNKNOWN"
    )
    packet = {
        "capability_id": f"{getattr(instance, 'instance_id', 'unknown')}:{required_capability}",
        "observed_at": last_seen,
        "max_age_seconds": max_age_seconds,
        "checks": {
            "availability": "PASS" if active else "FAIL",
            "integrity": "PASS" if integrity_verified is True else "UNKNOWN",
            "dependencies": dependency_state,
            "capacity": "PASS" if capacity_available is True else "UNKNOWN",
            "security": "PASS" if has_capability and has_authority else "FAIL",
            "recovery": "PASS" if recovery_verified is True else "UNKNOWN",
            "governance": "PASS" if governance_approved is True else "UNKNOWN",
            "evidence_quality": "PASS" if isinstance(evidence, list) and evidence else "UNKNOWN",
        },
        "dependencies": deps,
        "dependencies_declared": dependencies_declared,
        "evidence": evidence if isinstance(evidence, list) else [],
    }
    return evaluate_readiness(packet, now=now)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON input packet; use - for stdin")
    parser.add_argument("--output", default="-", help="output JSON path (default: stdout)")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    report = evaluate_readiness(payload)
    rendered = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output == "-":
        sys.stdout.write(rendered)
    else:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0 if report["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
