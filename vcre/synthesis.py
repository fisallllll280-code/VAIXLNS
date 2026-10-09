"""Governed cross-domain system-candidate synthesis.

Validates engineering contracts and compiles a deterministic verification plan.
It does not execute models, authorize deployment, or certify physical truth.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any


CORE_DOMAINS = frozenset({"mathematics", "computation", "software", "physics"})
ALLOWED_DOMAINS = CORE_DOMAINS | frozenset({"integration", "agents", "operations", "security"})
REQUIRED_AGENT_ROLES = frozenset({
    "SYSTEM_ARCHITECT",
    "MATHEMATICAL_FORMALIST",
    "COMPUTATIONAL_SCIENTIST",
    "PHYSICS_MODEL_SPECIALIST",
    "SOFTWARE_ENGINEER",
    "INTEGRATION_ENGINEER",
    "ADVERSARIAL_REVIEWER",
    "INDEPENDENT_VERIFIER",
    "EVOLUTION_JUDGE",
})
ALLOWED_PHYSICS_BASES = frozenset({
    "ANALYTIC_REFERENCE", "BENCHMARK", "EXPERIMENT",
    "INDEPENDENT_SOLVER", "TEST_FIXTURE", "NONE",
})
ALLOWED_ACTUATION_MODES = frozenset({"OBSERVE_SIMULATE", "HARDWARE_IN_LOOP", "REAL_ACTUATION"})
ALLOWED_OBJECTIVE_DIRECTIONS = frozenset({"MINIMIZE", "MAXIMIZE"})
ALLOWED_OBJECTIVE_EVIDENCE = frozenset({"TARGET", "ESTIMATED", "SIMULATED", "MEASURED"})


class CandidateSynthesisError(ValueError):
    """Raised when a candidate cannot be fingerprinted or compiled."""


@dataclass(frozen=True)
class CandidateAssessment:
    candidate_id: str
    status: str
    candidate_fingerprint: str | None
    errors: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_fingerprint(value: Mapping[str, Any]) -> str:
    """Return deterministic SHA-256 over canonical JSON; reject NaN and Infinity."""
    try:
        canonical = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CandidateSynthesisError(f"input is not canonical JSON: {exc}") from exc
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _positive_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0
    )


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def assess_candidate(candidate: Mapping[str, Any]) -> CandidateAssessment:
    """Check structure and fail closed on unknown mandatory obligations.

    READY_FOR_REVIEW means only that the candidate is structurally eligible for
    review. It never means implemented, verified, admitted, or physically valid.
    """
    candidate_id = str(candidate.get("candidate_id", "UNKNOWN")) if isinstance(candidate, Mapping) else "UNKNOWN"
    errors: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    rejection_reasons: list[str] = []

    if not isinstance(candidate, Mapping):
        return CandidateAssessment("UNKNOWN", "INVALID", None, ("candidate_must_be_object",), (), ())

    try:
        fingerprint = canonical_fingerprint(candidate)
    except CandidateSynthesisError as exc:
        fingerprint = None
        errors.append(f"canonicalization_failed:{exc}")

    required_top = {
        "schema_version", "candidate_id", "intent", "required_domains",
        "domain_contracts", "constraints", "objectives", "integrations",
        "agent_assignments", "verification_plan", "evidence", "evolution",
    }
    missing_top = sorted(required_top - set(candidate))
    if missing_top:
        errors.append("missing_required_fields:" + ",".join(missing_top))

    if not _text(candidate.get("schema_version")):
        errors.append("schema_version_required")
    if not _text(candidate.get("candidate_id")):
        errors.append("candidate_id_required")
    if not _text(candidate.get("intent")):
        errors.append("intent_required")

    required_domains = candidate.get("required_domains")
    if not isinstance(required_domains, list) or any(not _text(d) for d in required_domains):
        errors.append("required_domains_must_be_nonempty_string_list")
        required_domains = []
    else:
        if len(set(required_domains)) != len(required_domains):
            errors.append("required_domains_must_be_unique")
        missing_core = sorted(CORE_DOMAINS - set(required_domains))
        if missing_core:
            errors.append("core_domains_missing:" + ",".join(missing_core))
        unsupported = sorted(set(required_domains) - ALLOWED_DOMAINS)
        if unsupported:
            errors.append("unsupported_domains:" + ",".join(unsupported))

    domains = candidate.get("domain_contracts")
    if not isinstance(domains, Mapping):
        errors.append("domain_contracts_must_be_object")
        domains = {}
    for domain in required_domains:
        if domain not in domains:
            errors.append(f"domain_contract_missing:{domain}")
    for domain in sorted(set(domains) - ALLOWED_DOMAINS):
        errors.append(f"unsupported_domain_contract:{domain}")

    math_contract = domains.get("mathematics", {})
    if not isinstance(math_contract, Mapping):
        errors.append("mathematics_contract_must_be_object")
        math_contract = {}
    for field in ("model_id", "formalism"):
        if not _text(math_contract.get(field)):
            errors.append(f"mathematics.{field}_required")
    for field in ("assumptions", "constraints", "proof_obligations"):
        if not _nonempty_list(math_contract.get(field)):
            errors.append(f"mathematics.{field}_must_be_nonempty_list")

    comp_contract = domains.get("computation", {})
    if not isinstance(comp_contract, Mapping):
        errors.append("computation_contract_must_be_object")
        comp_contract = {}
    for field in ("model_id", "algorithm", "determinism_policy"):
        if not _text(comp_contract.get(field)):
            errors.append(f"computation.{field}_required")
    budget = comp_contract.get("resource_budget")
    if not isinstance(budget, Mapping):
        errors.append("computation.resource_budget_required")
    else:
        for field in ("max_steps", "max_memory_mb", "max_wall_time_ms"):
            value = budget.get(field)
            if not _positive_number(value) or (field == "max_steps" and int(value) != value):
                errors.append(f"computation.resource_budget.{field}_must_be_positive")
    tolerances = comp_contract.get("numerical_tolerances")
    if not isinstance(tolerances, Mapping) or not tolerances:
        errors.append("computation.numerical_tolerances_required")
    elif any(not _positive_number(v) for v in tolerances.values()):
        errors.append("computation.numerical_tolerances_must_be_positive_finite")

    software_contract = domains.get("software", {})
    if not isinstance(software_contract, Mapping):
        errors.append("software_contract_must_be_object")
        software_contract = {}
    for field in ("model_id", "implementation_language", "build_recipe", "dependency_lock_ref", "rollback_plan"):
        if not _text(software_contract.get(field)):
            errors.append(f"software.{field}_required")
    for field in ("test_targets", "static_security_checks"):
        if not _nonempty_list(software_contract.get(field)):
            errors.append(f"software.{field}_must_be_nonempty_list")

    physics = domains.get("physics", {})
    if not isinstance(physics, Mapping):
        errors.append("physics_contract_must_be_object")
        physics = {}
    for field in ("model_id", "validity_domain"):
        if not _text(physics.get(field)):
            errors.append(f"physics.{field}_required")
    for field in ("units", "initial_conditions", "boundary_conditions"):
        value = physics.get(field)
        if not isinstance(value, Mapping) or not value:
            errors.append(f"physics.{field}_must_be_nonempty_object")
    units = physics.get("units", {})
    if isinstance(units, Mapping) and any(not _text(k) or not _text(v) for k, v in units.items()):
        errors.append("physics.units_require_named_variables_and_unit_labels")
    if not _nonempty_list(physics.get("invariants")):
        errors.append("physics.invariants_must_be_nonempty_list")
    physics_tolerances = physics.get("numerical_tolerances")
    if not isinstance(physics_tolerances, Mapping) or not physics_tolerances:
        errors.append("physics.numerical_tolerances_required")
    elif any(not _positive_number(v) for v in physics_tolerances.values()):
        errors.append("physics.numerical_tolerances_must_be_positive_finite")
    validation_basis = physics.get("validation_basis")
    if validation_basis not in ALLOWED_PHYSICS_BASES:
        errors.append("physics.validation_basis_invalid")
    elif validation_basis == "NONE":
        blockers.append("PHYSICS_VALIDATION_BASIS_MISSING")
    actuation_mode = physics.get("actuation_mode", "OBSERVE_SIMULATE")
    if actuation_mode not in ALLOWED_ACTUATION_MODES:
        errors.append("physics.actuation_mode_invalid")
    if actuation_mode == "HARDWARE_IN_LOOP":
        if not _text(physics.get("hil_plan_ref")) or not _text(physics.get("safety_contract_ref")):
            blockers.append("HARDWARE_IN_LOOP_REQUIRES_PLAN_AND_SAFETY_CONTRACT")
    if actuation_mode == "REAL_ACTUATION":
        if not _text(physics.get("authority_ref")) or not _text(physics.get("safety_contract_ref")):
            blockers.append("REAL_ACTUATION_REQUIRES_SEPARATE_AUTHORITY_AND_SAFETY_CONTRACT")

    constraints = candidate.get("constraints")
    if not _nonempty_list(constraints):
        errors.append("constraints_must_be_nonempty_list")
    else:
        for index, item in enumerate(constraints):
            prefix = f"constraints[{index}]"
            if not isinstance(item, Mapping):
                errors.append(f"{prefix}_must_be_object")
                continue
            if not _text(item.get("constraint_id")):
                errors.append(f"{prefix}.constraint_id_required")
            kind, status = item.get("kind"), item.get("status")
            if kind not in {"HARD", "SOFT"}:
                errors.append(f"{prefix}.kind_invalid")
            if status not in {"PASS", "FAIL", "UNKNOWN"}:
                errors.append(f"{prefix}.status_invalid")
            refs = item.get("evidence_refs", [])
            if not isinstance(refs, list):
                errors.append(f"{prefix}.evidence_refs_must_be_list")
                refs = []
            if status == "FAIL" and kind == "HARD":
                rejection_reasons.append(f"HARD_CONSTRAINT_FAILED:{item.get('constraint_id', index)}")
            elif status == "FAIL" and kind == "SOFT":
                warnings.append(f"SOFT_CONSTRAINT_FAILED:{item.get('constraint_id', index)}")
            elif status == "UNKNOWN" and kind == "HARD":
                blockers.append(f"HARD_CONSTRAINT_UNKNOWN:{item.get('constraint_id', index)}")
            if status == "PASS" and not refs:
                blockers.append(f"CONSTRAINT_PASS_WITHOUT_EVIDENCE:{item.get('constraint_id', index)}")

    integrations = candidate.get("integrations")
    if not _nonempty_list(integrations):
        errors.append("integrations_must_be_nonempty_list")
    else:
        for index, adapter in enumerate(integrations):
            prefix = f"integrations[{index}]"
            if not isinstance(adapter, Mapping):
                errors.append(f"{prefix}_must_be_object")
                continue
            for field in ("adapter_id", "version", "input_schema_ref", "output_schema_ref", "permission_scope", "failure_policy"):
                if not _text(adapter.get(field)):
                    errors.append(f"{prefix}.{field}_required")
            if not _positive_number(adapter.get("timeout_ms")):
                errors.append(f"{prefix}.timeout_ms_must_be_positive")
            if not isinstance(adapter.get("idempotency_supported"), bool):
                errors.append(f"{prefix}.idempotency_supported_must_be_boolean")

    agents = candidate.get("agent_assignments")
    if not _nonempty_list(agents):
        errors.append("agent_assignments_must_be_nonempty_list")
        agents = []
    assigned_roles: set[str] = set()
    agent_by_role: dict[str, str] = {}
    for index, agent in enumerate(agents):
        prefix = f"agent_assignments[{index}]"
        if not isinstance(agent, Mapping):
            errors.append(f"{prefix}_must_be_object")
            continue
        role, agent_id = agent.get("role"), agent.get("agent_id")
        if not _text(role) or not _text(agent_id):
            errors.append(f"{prefix}.role_and_agent_id_required")
            continue
        assigned_roles.add(role)
        agent_by_role.setdefault(role, agent_id)
        if not _nonempty_list(agent.get("capabilities")):
            errors.append(f"{prefix}.capabilities_must_be_nonempty_list")
    missing_roles = sorted(REQUIRED_AGENT_ROLES - assigned_roles)
    if missing_roles:
        errors.append("required_agent_roles_missing:" + ",".join(missing_roles))
    verifier = agent_by_role.get("INDEPENDENT_VERIFIER")
    for producer_role in ("SOFTWARE_ENGINEER", "PHYSICS_MODEL_SPECIALIST"):
        if verifier and verifier == agent_by_role.get(producer_role):
            blockers.append(f"VERIFIER_NOT_INDEPENDENT_OF:{producer_role}")

    objectives = candidate.get("objectives")
    if not _nonempty_list(objectives):
        errors.append("objectives_must_be_nonempty_list")
    else:
        seen_metrics: set[str] = set()
        for index, objective in enumerate(objectives):
            prefix = f"objectives[{index}]"
            if not isinstance(objective, Mapping):
                errors.append(f"{prefix}_must_be_object")
                continue
            metric = objective.get("metric")
            if not _text(metric) or metric in seen_metrics:
                errors.append(f"{prefix}.metric_required_and_unique")
            else:
                seen_metrics.add(metric)
            if objective.get("direction") not in ALLOWED_OBJECTIVE_DIRECTIONS:
                errors.append(f"{prefix}.direction_invalid")
            if not _text(objective.get("unit")):
                errors.append(f"{prefix}.unit_required")
            if not _finite_number(objective.get("value")):
                errors.append(f"{prefix}.value_must_be_finite_number")
            if objective.get("evidence_state") not in ALLOWED_OBJECTIVE_EVIDENCE:
                errors.append(f"{prefix}.evidence_state_invalid")

    verification = candidate.get("verification_plan")
    if not isinstance(verification, Mapping):
        errors.append("verification_plan_must_be_object")
    else:
        if not _nonempty_list(verification.get("required_checks")):
            errors.append("verification_plan.required_checks_required")
        if verification.get("independent_replay_required") is not True:
            errors.append("independent_replay_must_be_required")
        if verification.get("security_review_required") is not True:
            errors.append("security_review_must_be_required")

    if not isinstance(candidate.get("evidence"), Mapping):
        errors.append("evidence_must_be_object")

    evolution = candidate.get("evolution")
    if not isinstance(evolution, Mapping):
        errors.append("evolution_must_be_object")
    else:
        if evolution.get("self_promotion") is True:
            rejection_reasons.append("SELF_PROMOTION_FORBIDDEN")
        if evolution.get("mutation_scope") not in {"SANDBOX_ONLY", "CANDIDATE_BRANCH_ONLY"}:
            rejection_reasons.append("UNSAFE_MUTATION_SCOPE")
        for field in ("rollback_plan", "regression_suite_ref"):
            if not _text(evolution.get(field)):
                errors.append(f"evolution.{field}_required")
        generations = evolution.get("max_generations")
        if not isinstance(generations, int) or isinstance(generations, bool) or generations < 1:
            errors.append("evolution.max_generations_must_be_positive_integer")

    secret_keys = {"api_key", "access_token", "password", "client_secret", "private_key"}
    def find_secret_keys(value: Any, path: str = "candidate") -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                key_text = str(key).lower()
                if key_text in secret_keys:
                    errors.append(f"raw_secret_field_forbidden:{path}.{key_text}")
                find_secret_keys(child, f"{path}.{key_text}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                find_secret_keys(child, f"{path}[{index}]")
    find_secret_keys(candidate)

    warnings.extend([
        "NOT_A_VERIFICATION_RESULT",
        "NO_RUNTIME_OR_PHYSICAL_ACTUATION_PERFORMED",
    ])

    if rejection_reasons:
        status = "REJECTED"
        errors.extend(rejection_reasons)
    elif errors:
        status = "INVALID"
    elif blockers:
        status = "HOLD"
    else:
        status = "READY_FOR_REVIEW"

    return CandidateAssessment(
        candidate_id=candidate_id,
        status=status,
        candidate_fingerprint=fingerprint,
        errors=tuple(sorted(set(errors))),
        blockers=tuple(sorted(set(blockers))),
        warnings=tuple(sorted(set(warnings))),
    )


def compile_verification_plan(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Compile a deterministic, non-executing dependency DAG of proof obligations."""
    assessment = assess_candidate(candidate)
    if assessment.status in {"INVALID", "REJECTED"}:
        raise CandidateSynthesisError(f"candidate cannot be planned: {assessment.status}")

    tasks = [
        {"task_id": "P00_CONTRACT_PREFLIGHT", "owner_role": "SYSTEM_ARCHITECT", "depends_on": []},
        {"task_id": "P10_MATH_AND_DIMENSION_CHECKS", "owner_role": "MATHEMATICAL_FORMALIST", "depends_on": ["P00_CONTRACT_PREFLIGHT"]},
        {"task_id": "P20_PHYSICS_INVARIANT_CHECKS", "owner_role": "PHYSICS_MODEL_SPECIALIST", "depends_on": ["P10_MATH_AND_DIMENSION_CHECKS"]},
        {"task_id": "P30_NUMERICAL_CONVERGENCE_AND_SENSITIVITY", "owner_role": "COMPUTATIONAL_SCIENTIST", "depends_on": ["P20_PHYSICS_INVARIANT_CHECKS"]},
        {"task_id": "P40_SOFTWARE_BUILD_TESTS_AND_SUPPLY_CHAIN", "owner_role": "SOFTWARE_ENGINEER", "depends_on": ["P00_CONTRACT_PREFLIGHT"]},
        {"task_id": "P50_INTEGRATION_CONFORMANCE", "owner_role": "INTEGRATION_ENGINEER", "depends_on": ["P00_CONTRACT_PREFLIGHT"]},
        {"task_id": "P60_ADVERSARIAL_AND_FAILURE_RECOVERY", "owner_role": "ADVERSARIAL_REVIEWER", "depends_on": ["P30_NUMERICAL_CONVERGENCE_AND_SENSITIVITY", "P40_SOFTWARE_BUILD_TESTS_AND_SUPPLY_CHAIN", "P50_INTEGRATION_CONFORMANCE"]},
        {"task_id": "P70_INDEPENDENT_REPLAY_AND_VERIFICATION", "owner_role": "INDEPENDENT_VERIFIER", "depends_on": ["P60_ADVERSARIAL_AND_FAILURE_RECOVERY"]},
        {"task_id": "P80_AUTHORITY_AND_EVOLUTION_REVIEW", "owner_role": "EVOLUTION_JUDGE", "depends_on": ["P70_INDEPENDENT_REPLAY_AND_VERIFICATION"]},
    ]
    plan_payload = {
        "plan_version": "vcre-synthesis-plan-1.0",
        "candidate_fingerprint": assessment.candidate_fingerprint,
        "status": "PLANNED_NOT_EXECUTED",
        "tasks": tasks,
    }
    plan_payload["plan_fingerprint"] = canonical_fingerprint(plan_payload)
    return plan_payload


def pareto_frontier(candidates: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return nondominated READY_FOR_REVIEW candidates with comparable objectives.

    This ranking is an exploration aid, not a verification or admission decision.
    Objective sets must match in metric names, units, directions, and evidence state.
    """
    eligible = [
        candidate for candidate in candidates
        if assess_candidate(candidate).status == "READY_FOR_REVIEW"
    ]
    if not eligible:
        return []

    def vector(candidate: Mapping[str, Any]) -> dict[str, tuple[str, str, str, float]]:
        result: dict[str, tuple[str, str, str, float]] = {}
        for item in candidate["objectives"]:
            result[str(item["metric"])] = (
                str(item["unit"]),
                str(item["direction"]),
                str(item["evidence_state"]),
                float(item["value"]),
            )
        return result

    vectors = {str(candidate["candidate_id"]): vector(candidate) for candidate in eligible}
    reference_id = next(iter(vectors))
    reference = vectors[reference_id]
    reference_shape = tuple((name, *reference[name][:3]) for name in sorted(reference))
    for candidate_id, vec in vectors.items():
        shape = tuple((name, *vec[name][:3]) for name in sorted(vec))
        if shape != reference_shape:
            raise CandidateSynthesisError(f"incomparable objective contracts: {candidate_id}")

    def dominates(left: Mapping[str, tuple[str, str, str, float]],
                  right: Mapping[str, tuple[str, str, str, float]]) -> bool:
        no_worse = True
        strictly_better = False
        for name in left:
            direction = left[name][1]
            lval, rval = left[name][3], right[name][3]
            if direction == "MINIMIZE":
                no_worse &= lval <= rval
                strictly_better |= lval < rval
            else:
                no_worse &= lval >= rval
                strictly_better |= lval > rval
        return no_worse and strictly_better

    frontier = []
    for candidate_id, candidate_vector in vectors.items():
        if not any(
            other_id != candidate_id and dominates(other_vector, candidate_vector)
            for other_id, other_vector in vectors.items()
        ):
            frontier.append(candidate_id)
    return sorted(frontier)
