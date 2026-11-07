import copy
import json
from pathlib import Path
import unittest

from vcre.synthesis import (
    CandidateSynthesisError,
    assess_candidate,
    canonical_fingerprint,
    compile_verification_plan,
    pareto_frontier,
)


ROLES = (
    "SYSTEM_ARCHITECT",
    "MATHEMATICAL_FORMALIST",
    "COMPUTATIONAL_SCIENTIST",
    "PHYSICS_MODEL_SPECIALIST",
    "SOFTWARE_ENGINEER",
    "INTEGRATION_ENGINEER",
    "ADVERSARIAL_REVIEWER",
    "INDEPENDENT_VERIFIER",
    "EVOLUTION_JUDGE",
)


def candidate(candidate_id="CAND-A", latency=100.0, accuracy=0.95, cost=2.0):
    return {
        "schema_version": "1.0.0",
        "candidate_id": candidate_id,
        "intent": "Synthetic reference system for testing governed cross-domain composition.",
        "required_domains": ["mathematics", "computation", "software", "physics"],
        "domain_contracts": {
            "mathematics": {
                "model_id": "math.synthetic-oscillator.v1",
                "formalism": "ordinary differential equation",
                "assumptions": ["constant angular frequency"],
                "constraints": ["finite state", "declared units"],
                "proof_obligations": ["dimensional consistency", "invariant preservation"],
            },
            "computation": {
                "model_id": "compute.rk4-reference.v1",
                "algorithm": "RK4 with step-refinement diagnostics",
                "determinism_policy": "REPEATABLE",
                "resource_budget": {"max_steps": 10000, "max_memory_mb": 256, "max_wall_time_ms": 5000},
                "numerical_tolerances": {"absolute": 1e-7, "relative": 1e-6},
            },
            "software": {
                "model_id": "software.reference-package.v1",
                "implementation_language": "Python",
                "build_recipe": "python -m unittest discover -s tests",
                "dependency_lock_ref": "fixture:dependency-lock",
                "test_targets": ["fixture:test-suite"],
                "static_security_checks": ["fixture:static-check"],
                "rollback_plan": "retain prior immutable revision and revert candidate branch",
            },
            "physics": {
                "model_id": "physics.synthetic-oscillator.v1",
                "validity_domain": "synthetic undamped oscillator only",
                "units": {"x": "m", "v": "m/s", "omega": "1/s"},
                "invariants": ["bounded-energy-reference"],
                "initial_conditions": {"x": 1.0, "v": 0.0},
                "boundary_conditions": {"time": "0 <= t <= 2*pi"},
                "numerical_tolerances": {"state_abs": 1e-6},
                "validation_basis": "ANALYTIC_REFERENCE",
                "actuation_mode": "OBSERVE_SIMULATE",
            },
        },
        "constraints": [{
            "constraint_id": "HARD-RESOURCE-001",
            "kind": "HARD",
            "status": "PASS",
            "evidence_refs": ["fixture:resource-budget-check"],
        }],
        "objectives": [
            {"metric": "latency", "direction": "MINIMIZE", "unit": "ms", "value": latency, "evidence_state": "SIMULATED"},
            {"metric": "accuracy", "direction": "MAXIMIZE", "unit": "ratio", "value": accuracy, "evidence_state": "SIMULATED"},
            {"metric": "cost", "direction": "MINIMIZE", "unit": "credits", "value": cost, "evidence_state": "SIMULATED"},
        ],
        "integrations": [{
            "adapter_id": "adapter.local-contract.v1",
            "version": "1.0.0",
            "input_schema_ref": "fixture:input-schema",
            "output_schema_ref": "fixture:output-schema",
            "permission_scope": "local-read-only",
            "failure_policy": "fail-closed",
            "timeout_ms": 1000,
            "idempotency_supported": True,
        }],
        "agent_assignments": [
            {"role": role, "agent_id": "agent-" + role.lower(), "capabilities": ["contracted-test-capability"]}
            for role in ROLES
        ],
        "verification_plan": {
            "required_checks": ["schema", "dimensions", "invariants", "convergence", "software-tests", "integration", "adversarial", "independent-replay"],
            "independent_replay_required": True,
            "security_review_required": True,
        },
        "evidence": {"source_refs": ["fixture:source"], "test_refs": [], "measurement_refs": [], "validation_refs": []},
        "evolution": {
            "mutation_scope": "CANDIDATE_BRANCH_ONLY",
            "self_promotion": False,
            "rollback_plan": "revert to immutable known-good revision",
            "regression_suite_ref": "fixture:regression-suite",
            "max_generations": 2,
        },
    }


class CrossDomainSynthesisTests(unittest.TestCase):
    def test_candidate_is_reviewable_but_never_claimed_verified(self):
        report = assess_candidate(candidate())
        self.assertEqual(report.status, "READY_FOR_REVIEW")
        self.assertEqual(len(report.candidate_fingerprint), 64)
        self.assertIn("NOT_A_VERIFICATION_RESULT", report.warnings)
        self.assertIn("NO_RUNTIME_OR_PHYSICAL_ACTUATION_PERFORMED", report.warnings)

    def test_candidate_schema_is_valid_json(self):
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "engineering-system-candidate.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("domain_contracts", schema["required"])

    def test_dictionary_key_order_does_not_change_fingerprint(self):
        first = {"b": 2, "a": {"y": 1, "x": 0}}
        second = {"a": {"x": 0, "y": 1}, "b": 2}
        self.assertEqual(canonical_fingerprint(first), canonical_fingerprint(second))

    def test_non_finite_numeric_input_is_rejected_for_fingerprinting(self):
        with self.assertRaises(CandidateSynthesisError):
            canonical_fingerprint({"value": float("nan")})

    def test_physical_contract_rejects_missing_units(self):
        item = candidate()
        item["domain_contracts"]["physics"]["units"] = {}
        report = assess_candidate(item)
        self.assertEqual(report.status, "INVALID")
        self.assertIn("physics.units_must_be_nonempty_object", report.errors)

    def test_unknown_hard_constraint_holds_candidate(self):
        item = candidate()
        item["constraints"][0]["status"] = "UNKNOWN"
        report = assess_candidate(item)
        self.assertEqual(report.status, "HOLD")
        self.assertTrue(any(x.startswith("HARD_CONSTRAINT_UNKNOWN") for x in report.blockers))

    def test_failed_hard_constraint_rejects_candidate(self):
        item = candidate()
        item["constraints"][0]["status"] = "FAIL"
        report = assess_candidate(item)
        self.assertEqual(report.status, "REJECTED")
        self.assertIn("HARD_CONSTRAINT_FAILED:HARD-RESOURCE-001", report.errors)

    def test_self_promotion_is_rejected(self):
        item = candidate()
        item["evolution"]["self_promotion"] = True
        self.assertEqual(assess_candidate(item).status, "REJECTED")

    def test_real_actuation_without_authority_stays_on_hold(self):
        item = candidate()
        item["domain_contracts"]["physics"]["actuation_mode"] = "REAL_ACTUATION"
        report = assess_candidate(item)
        self.assertEqual(report.status, "HOLD")
        self.assertIn("REAL_ACTUATION_REQUIRES_SEPARATE_AUTHORITY_AND_SAFETY_CONTRACT", report.blockers)

    def test_producer_cannot_be_its_own_independent_verifier(self):
        item = candidate()
        verifier = next(x for x in item["agent_assignments"] if x["role"] == "INDEPENDENT_VERIFIER")
        builder = next(x for x in item["agent_assignments"] if x["role"] == "SOFTWARE_ENGINEER")
        verifier["agent_id"] = builder["agent_id"]
        report = assess_candidate(item)
        self.assertEqual(report.status, "HOLD")
        self.assertIn("VERIFIER_NOT_INDEPENDENT_OF:SOFTWARE_ENGINEER", report.blockers)

    def test_verification_plan_is_stable_and_not_executed(self):
        item = candidate()
        first = compile_verification_plan(item)
        second = compile_verification_plan(copy.deepcopy(item))
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "PLANNED_NOT_EXECUTED")
        self.assertEqual(len(first["plan_fingerprint"]), 64)
        ids = [task["task_id"] for task in first["tasks"]]
        self.assertLess(ids.index("P00_CONTRACT_PREFLIGHT"), ids.index("P70_INDEPENDENT_REPLAY_AND_VERIFICATION"))
        self.assertLess(ids.index("P70_INDEPENDENT_REPLAY_AND_VERIFICATION"), ids.index("P80_AUTHORITY_AND_EVOLUTION_REVIEW"))

    def test_rejected_candidate_cannot_compile_plan(self):
        item = candidate()
        item["evolution"]["mutation_scope"] = "PRODUCTION_DIRECT"
        with self.assertRaisesRegex(CandidateSynthesisError, "REJECTED"):
            compile_verification_plan(item)

    def test_pareto_frontier_keeps_tradeoffs_and_drops_dominated_candidate(self):
        a = candidate("A", latency=100.0, accuracy=0.90, cost=2.0)
        b = candidate("B", latency=120.0, accuracy=0.98, cost=1.5)
        c = candidate("C", latency=150.0, accuracy=0.80, cost=3.0)
        self.assertEqual(pareto_frontier([a, b, c]), ["A", "B"])

    def test_pareto_comparison_rejects_duplicate_candidate_ids(self):
        with self.assertRaisesRegex(CandidateSynthesisError, "candidate_id values must be unique"):
            pareto_frontier([candidate("DUP"), candidate("DUP", latency=80.0)])

    def test_pareto_comparison_rejects_incomparable_evidence_states(self):
        a = candidate("A")
        b = candidate("B")
        b["objectives"][0]["evidence_state"] = "MEASURED"
        with self.assertRaisesRegex(CandidateSynthesisError, "incomparable objective contracts"):
            pareto_frontier([a, b])


if __name__ == "__main__":
    unittest.main()
