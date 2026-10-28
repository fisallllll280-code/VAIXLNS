"""VX Reality & Conflict Simulator — deterministic reference implementation.

Consumes explicitly supplied snapshots/contracts and reports conflicts without
mutating source systems. It does not claim runtime-wide visibility or auto-fix.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


SEVERITY_ORDER = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


@dataclass(frozen=True)
class Finding:
    finding_id: str
    kind: str
    severity: str
    systems: tuple[str, ...]
    summary: str
    evidence: tuple[str, ...]
    recommendation: str
    status: str = "PENDING_REVIEW"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["systems"] = list(self.systems)
        result["evidence"] = list(self.evidence)
        return result


def _finding(kind: str, severity: str, systems: Iterable[str], summary: str,
             evidence: Iterable[str], recommendation: str) -> Finding:
    systems_tuple = tuple(sorted(set(systems)))
    evidence_tuple = tuple(sorted(set(evidence)))
    stable = json.dumps([kind, severity, systems_tuple, summary, evidence_tuple],
                        ensure_ascii=False, separators=(",", ":"))
    finding_id = "VXCF-" + hashlib.sha256(stable.encode("utf-8")).hexdigest()[:12].upper()
    return Finding(finding_id, kind, severity, systems_tuple, summary,
                   evidence_tuple, recommendation)


def detect_duplicate_ids(records: Iterable[Mapping[str, Any]]) -> list[Finding]:
    """Detect repeated IDs in a registry snapshot."""
    seen: dict[str, list[str]] = {}
    for index, record in enumerate(records):
        item_id = record.get("id") or record.get("system_id") or record.get("instance_id")
        if isinstance(item_id, str) and item_id.strip():
            seen.setdefault(item_id.strip(), []).append(f"record[{index}]")
    return [_finding("DUPLICATE_ID", "HIGH", (item_id,),
                     f"Identifier {item_id!r} appears more than once.", locations,
                     "Reconcile the registry entries; do not delete either record without provenance.")
            for item_id, locations in sorted(seen.items()) if len(locations) > 1]


def detect_version_conflicts(systems: Iterable[Mapping[str, Any]]) -> list[Finding]:
    """Find incompatible explicit version constraints for a shared dependency.

    Input shape: {"system_id": "...", "dependencies": {"package": "1.2.0"}}.
    This intentionally compares exact declared versions only; it does not guess
    semantic-version ranges or fetch external package metadata.
    """
    owners: dict[str, list[tuple[str, str]]] = {}
    for system in systems:
        system_id = str(system.get("system_id", "UNKNOWN"))
        dependencies = system.get("dependencies", {})
        if not isinstance(dependencies, Mapping):
            continue
        for package, version in dependencies.items():
            if isinstance(package, str) and isinstance(version, str):
                owners.setdefault(package, []).append((system_id, version))
    findings: list[Finding] = []
    for package, entries in sorted(owners.items()):
        versions = sorted({version for _, version in entries})
        if len(versions) > 1:
            evidence = [f"{system_id} requires {package}=={version}"
                        for system_id, version in entries]
            findings.append(_finding("DEPENDENCY_VERSION_CONFLICT", "HIGH",
                (system_id for system_id, _ in entries),
                f"Systems declare different exact versions of dependency {package!r}: {versions}.",
                evidence, "Simulate a compatible version set in isolation and run integration/regression tests."))
    return findings


def detect_contract_conflicts(contracts: Iterable[Mapping[str, Any]]) -> list[Finding]:
    """Detect conflicting values for a shared explicit contract key.

    Input shape: {"system_id": "...", "invariants": {"key": "value"}}.
    Only identical invariant keys are compared; absence is not treated as conflict.
    """
    declarations: dict[str, list[tuple[str, str]]] = {}
    for contract in contracts:
        system_id = str(contract.get("system_id", "UNKNOWN"))
        invariants = contract.get("invariants", {})
        if not isinstance(invariants, Mapping):
            continue
        for key, value in invariants.items():
            if isinstance(key, str) and isinstance(value, (str, int, float, bool)):
                declarations.setdefault(key, []).append((system_id, str(value)))
    findings: list[Finding] = []
    for key, entries in sorted(declarations.items()):
        values = sorted({value for _, value in entries})
        if len(values) > 1:
            evidence = [f"{system_id} declares {key}={value}" for system_id, value in entries]
            findings.append(_finding("CONTRACT_INVARIANT_CONFLICT", "CRITICAL",
                (system_id for system_id, _ in entries),
                f"Shared invariant {key!r} has incompatible declared values: {values}.",
                evidence, "Block promotion; have the contract owner reconcile the invariant, then rerun simulation."))
    return findings


def simulate(systems: Iterable[Mapping[str, Any]],
             contracts: Iterable[Mapping[str, Any]] = (),
             registry: Iterable[Mapping[str, Any]] = ()) -> dict[str, Any]:
    """Run deterministic checks on supplied snapshots and return an auditable report."""
    systems_list = list(systems)
    contracts_list = list(contracts)
    registry_list = list(registry)
    findings = (detect_duplicate_ids(registry_list)
                + detect_version_conflicts(systems_list)
                + detect_contract_conflicts(contracts_list))
    findings.sort(key=lambda item: (-SEVERITY_ORDER[item.severity], item.finding_id))
    blocked = any(item.severity in {"HIGH", "CRITICAL"} for item in findings)
    report: dict[str, Any] = {
        "engine": "VX-REALITY-CONFLICT-SIMULATOR",
        "status": "CONFLICTS_FOUND" if findings else "NO_CONFLICTS_DETECTED_IN_SUPPLIED_SNAPSHOT",
        "promotion_blocked": blocked,
        "scope": {
            "systems_examined": len(systems_list),
            "contracts_examined": len(contracts_list),
            "registry_records_examined": len(registry_list),
        },
        "finding_count": len(findings),
        "findings": [item.to_dict() for item in findings],
        "limitations": [
            "A clean report means only that these checks found no conflicts in the supplied snapshot.",
            "This engine does not discover unprovided systems, prove runtime behavior, or apply repairs.",
            "Promotion decisions require independent tests, evidence review, and VX approval.",
        ],
    }
    report["report_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return report


def load_json_list(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{path}: expected a JSON array of objects")
    return value


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simulate conflicts across supplied VX snapshots")
    parser.add_argument("--systems", help="JSON array: system_id and dependencies")
    parser.add_argument("--contracts", help="JSON array: system_id and invariants")
    parser.add_argument("--registry", help="JSON array of registry records")
    parser.add_argument("--output", help="Optional path for the JSON report")
    args = parser.parse_args()
    report = simulate(
        load_json_list(args.systems) if args.systems else [],
        load_json_list(args.contracts) if args.contracts else [],
        load_json_list(args.registry) if args.registry else [],
    )
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(rendered + "\n")
    print(rendered)
    raise SystemExit(1 if report["promotion_blocked"] else 0)
