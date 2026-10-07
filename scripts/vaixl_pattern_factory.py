#!/usr/bin/env python3
"""Deterministic VAIXLNS Pattern Factory.

Builds governed pattern candidates from one intent by exploring multiple
architectural directions and logical route variants. The factory is an
orchestration layer over existing Ω-Pattern Foundry, Ω-Language Guardian,
and VAIXLNS Code Corrector surfaces.

The factory deliberately uses logical parallelism: route generation is
deterministic and schedulable on bounded workers, but this reference
implementation does not introduce nondeterministic threads or random fuzzing.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from scripts.omega_pattern_foundry import adversarial_attack, gate
from scripts.vaixl_code_corrector import correct_source
from scripts.vaixl_private_pattern_domain import (
    attach_private_language,
    build_pattern_language_binding,
    validate_pattern_language_boundary,
)
from scripts.vaixl_language_guardian import analyze as guardian_analyze
from scripts.vaixl_language_guardian import parse_source as guardian_parse


FACTORY_ID = "VAIXLNS-PATTERN-FACTORY-001"
SCHEMA_VERSION = "vaixlns.pattern_factory.v1"
DIRECTIONS = (
    ("D01_EVENT_SOURCING", "event-sourced", "events"),
    ("D02_STATE_MACHINE", "state-machine", "state"),
    ("D03_FUNCTIONAL_CORE", "functional-core", "pure"),
    ("D04_DATAFLOW", "dataflow", "stream"),
    ("D05_ACTOR_MODEL", "actor-model", "actors"),
    ("D06_PIPELINE", "pipeline", "stages"),
    ("D07_CQRS", "cqrs", "read-write-separation"),
    ("D08_RULE_ENGINE", "rule-engine", "policy"),
    ("D09_GRAPH_ORIENTED", "graph-oriented", "relationships"),
    ("D10_HYBRID", "hybrid-composition", "adaptive"),
)
VARIANT_AXES = (
    "bounded",
    "low-latency",
    "high-auditability",
    "high-recovery",
    "low-state",
    "high-isolation",
    "replay-first",
    "evidence-first",
)
MUTATION_CLASSES = (
    "OBJECTIVE",
    "CONTRACT",
    "AUTHORITY",
    "EVIDENCE",
    "VERIFICATION",
    "FAILURE",
    "CAPABILITY",
)


@dataclass(frozen=True)
class FactoryInput:
    problem: str
    objective: str
    constraints: tuple[str, ...]
    capabilities: tuple[str, ...]
    routes_per_direction: int = 80

    def as_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "objective": self.objective,
            "constraints": list(self.constraints),
            "capabilities": list(self.capabilities),
            "routes_per_direction": self.routes_per_direction,
        }


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def unique_sorted(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted({str(v).strip() for v in values if str(v).strip()})


def normalize_input(request: Mapping[str, Any]) -> FactoryInput:
    problem = str(request.get("problem", "")).strip()
    if not problem:
        raise ValueError("problem is required")
    objective = str(request.get("objective", problem)).strip() or problem
    constraints = tuple(sorted({str(v).strip() for v in request.get("constraints", []) if str(v).strip()}))
    capabilities = tuple(sorted({str(v).strip() for v in request.get("capabilities", []) if str(v).strip()}))
    routes = int(request.get("routes_per_direction", 80))
    if routes < 1 or routes > 80:
        raise ValueError("routes_per_direction must be between 1 and 80")
    return FactoryInput(problem, objective, constraints, capabilities, routes)


def route_seed(factory_input: FactoryInput, direction_id: str, route_index: int) -> str:
    material = {
        "factory": FACTORY_ID,
        "schema": SCHEMA_VERSION,
        "input": factory_input.as_dict(),
        "direction": direction_id,
        "route_index": route_index,
    }
    return sha256_json(material)


def render_semantic_source(pattern: Mapping[str, Any]) -> str:
    def line_list(key: str, values: list[str]) -> str:
        rendered = [key]
        rendered.extend(f"    {value}" for value in values)
        return "\n".join(rendered)

    caps = unique_sorted(pattern.get("tool_requirements"))
    forbidden = unique_sorted(pattern.get("failure_model", {}).get("anti_spec", []))
    evidence = ["provenance", "replay", "independent-verification"]
    authority = ["bounded-scope", "external-promotion-required"]
    admission = ["verification-required", "authority-required"]

    return "\n".join(
        [
            f"SYSTEM {pattern['pattern_id']}",
            "PURPOSE",
            f"    {pattern['intent']}",
            line_list("CAPABILITY", caps or ["observe"]),
            line_list("AUTHORITY", authority),
            line_list("MUST_NOT", forbidden or ["self-authorize"]),
            "BEHAVIOR",
            "    preserve invariants",
            "    record execution evidence",
            line_list("EVIDENCE", evidence),
            line_list("VERIFY", ["schema", "adversarial", "replay"]),
            line_list("SIMULATE", ["NORMAL", "EDGE", "ADVERSARIAL"]),
            line_list("RECOVER", ["quarantine", "repair", "replay", "re-verify"]),
            line_list("ADMISSION", admission),
            "",
        ]
    )


def build_route_pattern(
    factory_input: FactoryInput,
    direction_id: str,
    mode: str,
    route_index: int,
) -> dict[str, Any]:
    seed = route_seed(factory_input, direction_id, route_index)
    variant = VARIANT_AXES[(route_index - 1) % len(VARIANT_AXES)]
    route_id = f"{direction_id}-R{route_index:02d}"
    pattern_id = f"PF-{seed[:12]}"
    invariant_set = sorted(
        {
            "authority boundaries are preserved",
            "verification is required before promotion",
            "route generation is deterministic",
            *factory_input.constraints,
        }
    )
    capability_contract = {
        "preconditions": list(factory_input.constraints) or ["inputs are explicit and bounded"],
        "postconditions": [
            "requested objective is addressed",
            "execution is recorded",
            "route identity is reproducible",
        ],
        "side_effects": ["execution is recorded"],
    }
    failure_model = {
        "failure_modes": [
            "invalid-input",
            "contract-conflict",
            "authority-conflict",
            "verification-failure",
            "route-collision",
        ],
        "anti_spec": [
            "MUST NOT self-promote",
            "MUST NOT widen authority",
            "MUST NOT mutate canonical intent",
        ],
        "recovery": ["quarantine", "repair", "replay", "re-verify"],
    }
    pattern = {
        "pattern_id": pattern_id,
        "version": "1.0.0",
        "status": "PROPOSAL",
        "pattern_family": "private.deterministic.factory",
        "visibility": "PRIVATE_INTERNAL_PATTERN",
        "intent": factory_input.objective,
        "problem_class": "system-engineering",
        "assumptions": ["inputs are explicit and bounded", "route evaluation is governed"],
        "invariants": invariant_set,
        "architecture": {
            "mode": mode,
            "direction_id": direction_id,
            "route_id": route_id,
            "variant": variant,
            "seed": seed,
        },
        "components": [],
        "interfaces": [],
        "capability_contract": capability_contract,
        "agent_roles": ["ARCHITECT", "ADVERSARIAL", "VERIFIER"],
        "tool_requirements": list(factory_input.capabilities),
        "dependencies": [],
        "state_model": {
            "states": ["PROPOSAL", "TESTED", "VERIFIED", "QUARANTINED"],
            "strategy": variant,
        },
        "behavior_model": {
            "steps": ["understand", "compose", "attack", "correct", "replay", "verify"],
            "execution_shape": variant,
        },
        "security_model": {
            "deny": ["self-authorize", "self-promote", "undeclared-capability"],
            "isolation": "route-local-quarantine",
        },
        "authority_model": {
            "scope": "bounded",
            "promotion": "external-authority-required",
        },
        "failure_model": failure_model,
        "simulation": {
            "scenarios": ["NORMAL", "EDGE", "ADVERSARIAL"],
            "stop_conditions": ["critical-failure", "authority-violation", "invariant-violation"],
        },
        "verification": {
            "required_checks": ["schema", "adversarial", "guardian", "replay", "provenance"],
            "reproducibility": True,
        },
        "evidence_requirements": {
            "minimum_refs": ["route-record", "execution-record", "replay-record"],
            "counterevidence_required": True,
        },
        "evolution_rules": {
            "mutation_axes": ["architecture", "capabilities", "recovery"],
            "recombination_allowed": True,
            "novelty_required": True,
        },
        "provenance": {
            "creator": FACTORY_ID,
            "created_at": "1970-01-01T00:00:00Z",
            "parent_patterns": [],
            "source_refs": ["pattern-factory-input"],
            "genome_hash": "",
        },
        "commercial": {
            "license_class": "RESTRICTED_BY_DEFAULT",
            "exclusivity": "PRIVATE",
            "customer_scope": "",
        },
    }
    language_hash = sha256_json(
        {
            "pattern_id": pattern_id,
            "binding_type": "PATTERN_BOUND_PRIVATE_LANGUAGE",
            "fabric": [
                "syntax",
                "semantics",
                "grammar",
                "transformation",
                "security",
                "verification",
            ],
        }
    )
    language_binding = build_pattern_language_binding(
        pattern_id=pattern_id,
        language_id=f"{pattern_id}-PRIVATE-LANGUAGE",
        language_genome_hash=language_hash,
    )
    pattern = attach_private_language(pattern, language_binding)
    return pattern


def candidate_score(report: Mapping[str, Any], route_index: int) -> tuple[int, int, int, int]:
    return (
        int(report.get("blocking_findings", 0)),
        len(report.get("validation_errors", [])),
        int(report.get("attack_count", 0)),
        route_index,
    )


def mutate_for_attack(pattern: Mapping[str, Any], mutation_class: str) -> dict[str, Any]:
    mutated = copy.deepcopy(pattern)
    if mutation_class == "OBJECTIVE":
        mutated["intent"] = ""
    elif mutation_class == "CONTRACT":
        mutated["capability_contract"]["postconditions"] = []
    elif mutation_class == "AUTHORITY":
        mutated["authority_model"] = {"permissions": ["admin:*"], "promotion": "self-promote"}
    elif mutation_class == "EVIDENCE":
        mutated["evidence_requirements"]["counterevidence_required"] = False
    elif mutation_class == "VERIFICATION":
        mutated["verification"]["reproducibility"] = False
    elif mutation_class == "FAILURE":
        mutated["failure_model"]["recovery"] = []
    elif mutation_class == "CAPABILITY":
        mutated["tool_requirements"] = unique_sorted(mutated.get("tool_requirements")) + ["UNDECLARED_SECRET_ACCESS"]
    else:
        raise ValueError(f"unknown mutation class: {mutation_class}")
    return mutated


def adversarial_mutation_engine(pattern: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for mutation_class in MUTATION_CLASSES:
        mutated = mutate_for_attack(pattern, mutation_class)
        report = gate(mutated)
        blocked = bool(report["blocking_findings"] > 0)
        guardian_findings = 0

        # Capability mutations are evaluated against the original declaration:
        # declaring a new capability inside the mutation does not make it authorized.
        if mutation_class == "CAPABILITY":
            original_source = guardian_parse(render_semantic_source(pattern))
            guardian = guardian_analyze(
                original_source,
                observed_capabilities=list(mutated.get("tool_requirements") or []),
            )
            guardian_findings = len(guardian["findings"])
            blocked = blocked or guardian["decision"] == "QUARANTINE"

        records.append(
            {
                "mutation_class": mutation_class,
                "mutation_hash": sha256_json(mutated),
                "blocked": blocked,
                "blocking_findings": report["blocking_findings"],
                "guardian_findings": guardian_findings,
                "attack_count": report["attack_count"],
            }
        )
    return records


def detect_internal_collisions(pattern: Mapping[str, Any]) -> list[dict[str, Any]]:
    collisions: list[dict[str, Any]] = []
    capabilities = set(unique_sorted(pattern.get("tool_requirements")))
    forbidden = set(unique_sorted(pattern.get("failure_model", {}).get("anti_spec", [])))
    if capabilities & {"READ_SECRETS", "SECRET_ACCESS", "UNDECLARED_SECRET_ACCESS"}:
        collisions.append(
            {
                "class": "CAPABILITY_CONSTRAINT_COLLISION",
                "severity": "CRITICAL",
                "details": "Sensitive access capability conflicts with the private pattern security boundary.",
            }
        )
    serialized_authority = canonical_json(pattern.get("authority_model", {})).upper()
    if any(token in serialized_authority for token in ("ADMIN:*", "UNRESTRICTED", "SELF-PROMOTE")):
        collisions.append(
            {
                "class": "AUTHORITY_COLLISION",
                "severity": "CRITICAL",
                "details": "Authority model contains a forbidden escalation token.",
            }
        )
    if "MUST NOT self-promote" not in forbidden:
        collisions.append(
            {
                "class": "INVARIANT_COLLISION",
                "severity": "HIGH",
                "details": "Required anti-self-promotion rule is missing.",
            }
        )
    return collisions


def safe_repair(pattern: Mapping[str, Any], collisions: list[Mapping[str, Any]]) -> dict[str, Any]:
    repaired = copy.deepcopy(pattern)
    if not collisions:
        return {"changed": False, "pattern": repaired, "repair_class": "NONE", "repair_hash": sha256_json(repaired)}

    # Only bounded structural normalization is permitted here. Security,
    # authority, invariants, and intent are immutable under auto-repair.
    repaired["tool_requirements"] = unique_sorted(repaired.get("tool_requirements"))
    repaired["invariants"] = unique_sorted(repaired.get("invariants"))
    repaired["dependencies"] = unique_sorted(repaired.get("dependencies"))
    changed = repaired != pattern
    return {
        "changed": changed,
        "pattern": repaired,
        "repair_class": "STRUCTURAL_NORMALIZATION" if changed else "NO_SAFE_REPAIR",
        "repair_hash": sha256_json(repaired),
    }


def evaluate_candidate(pattern: Mapping[str, Any]) -> dict[str, Any]:
    collisions = detect_internal_collisions(pattern)
    private_language_findings = validate_pattern_language_boundary(pattern)
    if collisions:
        repair = safe_repair(pattern, collisions)
        post_repair_collisions = detect_internal_collisions(repair["pattern"])
    else:
        repair = {"changed": False, "pattern": dict(pattern), "repair_class": "NONE", "repair_hash": sha256_json(pattern)}
        post_repair_collisions = []

    effective = repair["pattern"]
    foundry_report = gate(effective)
    source = render_semantic_source(effective)
    corrector = correct_source(source)
    guardian_source = guardian_parse(corrector["repaired_source"])
    guardian = guardian_analyze(
        guardian_source,
        observed_capabilities=list(effective.get("tool_requirements") or []),
    )
    attacks = adversarial_attack(effective)
    mutation_tests = adversarial_mutation_engine(effective)
    mutation_failures = [item for item in mutation_tests if not item["blocked"]]

    blocking = int(foundry_report["blocking_findings"])
    blocking += len(private_language_findings)
    blocking += 1 if post_repair_collisions else 0
    blocking += 1 if guardian["decision"] == "QUARANTINE" else 0
    blocking += sum(1 for f in attacks if f.severity == "CRITICAL" or f.result == "BLOCK")
    blocking += len(mutation_failures)

    return {
        "pattern": effective,
        "foundry": foundry_report,
        "collisions": collisions,
        "private_language_findings": private_language_findings,
        "post_repair_collisions": post_repair_collisions,
        "repair": {
            "changed": repair["changed"],
            "repair_class": repair["repair_class"],
            "repair_hash": repair["repair_hash"],
        },
        "corrector": {
            "changed": corrector["changed"],
            "input_hash": corrector["input_hash"],
            "output_hash": corrector["output_hash"],
            "authority_mutation": corrector["authority_mutation"],
            "constraint_mutation": corrector["constraint_mutation"],
            "semantic_escalation": corrector["semantic_escalation"],
        },
        "guardian": {
            "decision": guardian["decision"],
            "source_hash": guardian["subject"]["source_hash"],
            "finding_count": len(guardian["findings"]),
        },
        "attack_count": len(attacks),
        "mutation_tests": len(mutation_tests),
        "mutation_failures": len(mutation_failures),
        "blocking_findings": blocking,
        "status": "QUARANTINED" if blocking else "SURVIVING_CANDIDATE",
    }


def build_factory_run(request: Mapping[str, Any]) -> dict[str, Any]:
    factory_input = normalize_input(request)
    candidates: list[dict[str, Any]] = []
    candidate_patterns: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    scores: list[tuple[tuple[int, int, int, int], str]] = []

    for direction_id, mode, _semantic in DIRECTIONS:
        for route_index in range(1, factory_input.routes_per_direction + 1):
            pattern = build_route_pattern(factory_input, direction_id, mode, route_index)
            evaluation = evaluate_candidate(pattern)
            route_id = pattern["architecture"]["route_id"]
            summary = {
                "route_id": route_id,
                "direction_id": direction_id,
                "pattern_id": pattern["pattern_id"],
                "genome_hash": pattern["provenance"]["genome_hash"],
                "status": evaluation["status"],
                "blocking_findings": evaluation["blocking_findings"],
                "attack_count": evaluation["attack_count"],
                "mutation_tests": evaluation["mutation_tests"],
                "mutation_failures": evaluation["mutation_failures"],
                "guardian_decision": evaluation["guardian"]["decision"],
                "corrector_changed": evaluation["corrector"]["changed"],
                "repair_changed": evaluation["repair"]["changed"],
                "private_language_bound": not bool(evaluation["private_language_findings"]),
            }
            candidates.append(summary)
            candidate_patterns.append({"summary": summary, "pattern": pattern})
            if evaluation["status"] == "QUARANTINED":
                quarantined.append(summary)
            else:
                scores.append(
                    (
                        candidate_score(evaluation["foundry"], route_index),
                        pattern["pattern_id"],
                    )
                )

    if not scores:
        selected = None
    else:
        best_id = min(scores, key=lambda item: item[0])[1]
        selected = next(item["pattern"] for item in candidate_patterns if item["pattern"]["pattern_id"] == best_id)

    route_hashes = [item["genome_hash"] for item in sorted(candidates, key=lambda x: x["route_id"])]
    replay_hash = hashlib.sha256("".join(route_hashes).encode("utf-8")).hexdigest()
    evidence_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "factory_id": FACTORY_ID,
        "input": factory_input.as_dict(),
        "topology": {
            "direction_count": len(DIRECTIONS),
            "routes_per_direction": factory_input.routes_per_direction,
            "total_logical_routes": len(candidates),
            "parallelism_model": "logical-bounded-scheduling",
        },
        "candidates": candidates,
        "quarantined": quarantined,
        "selected_pattern": selected,
        "replay_hash": replay_hash,
        "deterministic": True,
    }
    evidence_hash = sha256_json(evidence_without_hash)
    return {**evidence_without_hash, "evidence_hash": evidence_hash}


def replay_factory_run(request: Mapping[str, Any], reference: Mapping[str, Any]) -> dict[str, Any]:
    replay = build_factory_run(request)
    return {
        "match": replay["evidence_hash"] == reference["evidence_hash"],
        "reference_evidence_hash": reference["evidence_hash"],
        "replay_evidence_hash": replay["evidence_hash"],
        "reference_replay_hash": reference["replay_hash"],
        "replay_replay_hash": replay["replay_hash"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="VAIXLNS deterministic pattern factory")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--problem", required=True)
    parser.add_argument("--objective", default="")
    parser.add_argument("--constraints", nargs="*", default=[])
    parser.add_argument("--capabilities", nargs="*", default=[])
    parser.add_argument("--routes-per-direction", type=int, default=80)
    parser.add_argument("--output", default="")

    args = parser.parse_args()
    request = {
        "problem": args.problem,
        "objective": args.objective or args.problem,
        "constraints": args.constraints,
        "capabilities": args.capabilities,
        "routes_per_direction": args.routes_per_direction,
    }
    result = build_factory_run(request)
    result["replay"] = replay_factory_run(request, result)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    print(rendered, end="")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered)
    return 0 if result["replay"]["match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
