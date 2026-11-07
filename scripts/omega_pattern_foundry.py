#!/usr/bin/env python3
"""Deterministic reference engine for Ω-Pattern Foundry.

This module intentionally exposes a provider-neutral generator boundary.
A private model/router can implement GeneratorBackend without placing
proprietary prompts or model internals in the public repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol


ALLOWED_STATUSES = {
    "PROPOSAL",
    "EXPERIMENTAL",
    "SIMULATED",
    "IMPLEMENTED",
    "PARTIAL",
    "VERIFIED",
    "CANONICAL",
    "SUPERSEDED",
    "REJECTED",
    "QUARANTINED",
    "ARCHIVED",
}

CRITICAL_ATTACKS = {"CRITICAL"}
REQUIRED_FIELDS = {
    "pattern_id",
    "version",
    "status",
    "intent",
    "problem_class",
    "invariants",
    "capability_contract",
    "failure_model",
    "verification",
    "evidence_requirements",
    "provenance",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...]


@dataclass(frozen=True)
class AttackFinding:
    attack_id: str
    attack_class: str
    result: str
    severity: str
    finding: str
    counterexample: str = ""
    recommended_mutation: str = ""


class GeneratorBackend(Protocol):
    def generate(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        ...


class ReferenceGenerator:
    """Deterministic backend for CI and local conformance tests."""

    def generate(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        problem = str(request.get("problem", "")).strip()
        objective = str(request.get("objective", problem)).strip()
        constraints = list(request.get("constraints") or [])
        capabilities = list(request.get("capabilities") or [])

        pattern_id = "P-" + hashlib.sha256(problem.encode("utf-8")).hexdigest()[:12]
        pattern = {
            "pattern_id": pattern_id,
            "version": "1.0.0",
            "status": "PROPOSAL",
            "pattern_family": "generated.reference",
            "intent": objective,
            "problem_class": "system-engineering",
            "assumptions": ["inputs are explicit and bounded"],
            "invariants": ["authority boundaries are preserved", "verification is required before promotion"],
            "architecture": {"mode": "governed-composition"},
            "components": [],
            "interfaces": [],
            "capability_contract": {
                "preconditions": constraints,
                "postconditions": ["requested objective is addressed"],
                "side_effects": ["execution is recorded"]
            },
            "agent_roles": ["ARCHITECT", "VERIFIER"],
            "tool_requirements": capabilities,
            "dependencies": [],
            "state_model": {"states": ["PROPOSAL", "TESTED", "VERIFIED"]},
            "behavior_model": {"steps": ["understand", "compose", "attack", "verify"]},
            "security_model": {"deny": ["self-authorize", "self-promote"]},
            "authority_model": {"promotion": "external-authority-required"},
            "failure_model": {
                "failure_modes": ["invalid-input", "contract-conflict", "verification-failure"],
                "anti_spec": ["MUST NOT self-promote"],
                "recovery": ["quarantine", "repair", "replay", "re-verify"]
            },
            "simulation": {"scenarios": ["NORMAL", "EDGE", "ADVERSARIAL"], "stop_conditions": ["critical-failure"]},
            "verification": {
                "required_checks": ["schema", "adversarial", "reproducibility"],
                "reproducibility": True
            },
            "evidence_requirements": {
                "minimum_refs": ["execution-record"],
                "counterevidence_required": True
            },
            "evolution_rules": {
                "mutation_axes": ["architecture", "capabilities", "recovery"],
                "recombination_allowed": True,
                "novelty_required": True
            },
            "provenance": {
                "creator": "reference-generator",
                "created_at": utc_now(),
                "parent_patterns": [],
                "source_refs": [],
                "genome_hash": ""
            },
            "commercial": {
                "license_class": "RESTRICTED_BY_DEFAULT",
                "exclusivity": "NONE",
                "customer_scope": ""
            }
        }
        pattern["provenance"]["genome_hash"] = sha256_hex(pattern)
        return pattern


def validate_pattern(pattern: Mapping[str, Any]) -> ValidationResult:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(pattern))
    if missing:
        errors.append("missing_required:" + ",".join(missing))

    status = pattern.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append("invalid_status")

    invariants = pattern.get("invariants")
    if not isinstance(invariants, list) or not invariants:
        errors.append("invariants_required")

    contract = pattern.get("capability_contract")
    if not isinstance(contract, Mapping):
        errors.append("capability_contract_required")
    else:
        for field in ("preconditions", "postconditions", "side_effects"):
            if not isinstance(contract.get(field), list):
                errors.append(f"capability_contract.{field}_must_be_list")

    failure = pattern.get("failure_model")
    if not isinstance(failure, Mapping):
        errors.append("failure_model_required")
    else:
        if not isinstance(failure.get("failure_modes"), list) or not failure.get("failure_modes"):
            errors.append("failure_modes_required")
        if not isinstance(failure.get("anti_spec"), list) or not failure.get("anti_spec"):
            errors.append("anti_spec_required")
        if not isinstance(failure.get("recovery"), list) or not failure.get("recovery"):
            errors.append("recovery_required")

    verification = pattern.get("verification")
    if not isinstance(verification, Mapping) or not verification.get("reproducibility", False):
        errors.append("reproducibility_required")

    evidence = pattern.get("evidence_requirements")
    if not isinstance(evidence, Mapping):
        errors.append("evidence_requirements_required")

    provenance = pattern.get("provenance")
    if not isinstance(provenance, Mapping):
        errors.append("provenance_required")

    lineage = provenance.get("parent_patterns", []) if isinstance(provenance, Mapping) else []
    version = str(pattern.get("version", ""))
    if ("." in version and version != "1.0.0") and not lineage:
        errors.append("lineage_required_for_evolved_pattern")

    if status in {"VERIFIED", "CANONICAL"}:
        if not evidence or not evidence.get("minimum_refs"):
            errors.append("evidence_required_for_verified_state")
        if not pattern.get("provenance", {}).get("genome_hash"):
            errors.append("genome_hash_required_for_verified_state")

    return ValidationResult(valid=not errors, errors=tuple(errors))


def adversarial_attack(pattern: Mapping[str, Any]) -> list[AttackFinding]:
    pid = str(pattern.get("pattern_id", "UNKNOWN"))
    findings: list[AttackFinding] = []

    def add(kind: str, severity: str, result: str, finding: str, counterexample: str = "", mutation: str = "") -> None:
        suffix = len(findings) + 1
        attack_id = f"ATK-{hashlib.sha256((pid + kind + str(suffix)).encode()).hexdigest()[:10]}"
        findings.append(AttackFinding(attack_id, kind, result, severity, finding, counterexample, mutation))

    if not pattern.get("intent"):
        add("OBJECTIVE", "CRITICAL", "BLOCK", "Pattern has no explicit intent.")
    else:
        add("OBJECTIVE", "INFO", "PASS", "Intent is present.")

    contract = pattern.get("capability_contract", {})
    if not isinstance(contract, Mapping) or not contract.get("postconditions"):
        add("CONTRACT", "CRITICAL", "BLOCK", "No measurable postcondition is declared.",
            "A candidate can appear successful without a defined outcome.", "Add measurable postconditions.")
    else:
        add("CONTRACT", "INFO", "PASS", "Postconditions exist.")

    authority = pattern.get("authority_model", {})
    serialized_authority = json.dumps(authority, sort_keys=True).lower()
    if any(token in serialized_authority for token in ("self-promote", "unrestricted", "root", "admin:*")):
        add("AUTHORITY", "CRITICAL", "BLOCK", "Authority model permits excessive or self-granting authority.",
            "A generated pattern could promote or execute beyond its delegated scope.",
            "Restrict authority and require an external promotion gate.")
    else:
        add("AUTHORITY", "INFO", "PASS", "Authority is not obviously self-granting.")

    failure = pattern.get("failure_model", {})
    if not isinstance(failure, Mapping) or not failure.get("failure_modes"):
        add("FAILURE", "HIGH", "BLOCK", "Failure modes are absent.")
    if not isinstance(failure, Mapping) or not failure.get("recovery"):
        add("FAILURE", "HIGH", "BLOCK", "Recovery strategy is absent.")

    verification = pattern.get("verification", {})
    evidence = pattern.get("evidence_requirements", {})
    if not isinstance(verification, Mapping) or not verification.get("reproducibility", False):
        add("VERIFICATION", "CRITICAL", "BLOCK", "Pattern cannot be reproduced deterministically.")
    else:
        add("VERIFICATION", "INFO", "PASS", "Reproducibility is explicitly required.")

    if not isinstance(evidence, Mapping) or not evidence.get("counterevidence_required", False):
        add("EVIDENCE", "HIGH", "BLOCK", "Counterevidence is not required.",
            "One-sided evidence can create false promotion confidence.",
            "Require counterevidence and independent attack results.")

    provenance = pattern.get("provenance", {})
    if not isinstance(provenance, Mapping) or not provenance.get("genome_hash"):
        add("LINEAGE", "HIGH", "BLOCK", "Pattern genome hash is missing.")
    else:
        add("LINEAGE", "INFO", "PASS", "Genome hash is present.")

    tools = pattern.get("tool_requirements", [])
    if isinstance(tools, list) and len(tools) > 1000:
        add("COMPOSITION", "MEDIUM", "FINDING", "Candidate requests an unusually large tool surface.",
            "Large capability surfaces increase attack and governance complexity.",
            "Reduce to the minimum compatible capability set.")

    return findings


def gate(pattern: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_pattern(pattern)
    attacks = adversarial_attack(pattern)
    critical = sum(1 for finding in attacks if finding.severity in CRITICAL_ATTACKS or finding.result == "BLOCK")
    promoted = validation.valid and critical == 0
    return {
        "pattern_id": pattern.get("pattern_id"),
        "valid": validation.valid,
        "validation_errors": list(validation.errors),
        "attack_count": len(attacks),
        "blocking_findings": critical,
        "promotion_candidate": promoted,
        "attacks": [finding.__dict__ for finding in attacks],
    }


def build_candidate(request: Mapping[str, Any], backend: GeneratorBackend | None = None) -> dict[str, Any]:
    generator = backend or ReferenceGenerator()
    candidate = dict(generator.generate(request))
    candidate.setdefault("provenance", {})["genome_hash"] = sha256_hex(candidate)
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Ω-Pattern Foundry reference engine")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate")
    gen.add_argument("--problem", required=True)
    gen.add_argument("--objective", default="")
    gen.add_argument("--constraints", nargs="*", default=[])
    gen.add_argument("--capabilities", nargs="*", default=[])

    check = sub.add_parser("check")
    check.add_argument("pattern_file")

    attack = sub.add_parser("attack")
    attack.add_argument("pattern_file")

    args = parser.parse_args()

    if args.command == "generate":
        candidate = build_candidate({
            "problem": args.problem,
            "objective": args.objective or args.problem,
            "constraints": args.constraints,
            "capabilities": args.capabilities,
        })
        print(json.dumps(candidate, indent=2, ensure_ascii=False))
        return 0

    with open(args.pattern_file, "r", encoding="utf-8") as handle:
        pattern = json.load(handle)

    if args.command == "check":
        print(json.dumps(validate_pattern(pattern).__dict__, indent=2))
        return 0 if validate_pattern(pattern).valid else 1

    result = gate(pattern)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["blocking_findings"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
