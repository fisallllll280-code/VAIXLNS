import json
import unittest
from pathlib import Path

from scripts.indexed_workflow import (
    DEFAULT_REGISTRY,
    WorkflowError,
    build_plan,
    file_digest,
    read_json,
    validate_plan,
    validate_registry,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "research-request.v1.json"


class IndexedWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = read_json(DEFAULT_REGISTRY)
        cls.registry_digest = file_digest(DEFAULT_REGISTRY)

    def test_registry_has_all_systems_and_thirteen_assigned_agents(self):
        validate_registry(self.registry)
        system_ids = {system["system_id"] for system in self.registry["system_registry"]}
        self.assertEqual(system_ids, {"VAIXLNS", "NEXENT", "VX", "XV", "VV"})
        self.assertEqual(len(self.registry["agents"]), 13)
        self.assertEqual(self.registry["agents"][10]["primary_system_id"], "VX")

    def test_non_mutating_request_produces_plan_but_does_not_execute(self):
        request = read_json(FIXTURE)
        plan = build_plan(request, self.registry, self.registry_digest)
        validate_plan(plan, self.registry)
        self.assertEqual(plan["plan_status"], "PLAN_READY_NOT_EXECUTED")
        self.assertFalse(plan["execution"]["external_agent_calls_performed"])
        self.assertFalse(plan["execution"]["repository_mutations_performed"])
        self.assertFalse(plan["execution"]["vx_runtime_calls_performed"])
        self.assertEqual(plan["master_index_id"], "Ω.000")
        self.assertIn("UNMAPPED", plan["master_index_item_mapping"])

    def test_repository_mutation_is_held_and_execution_agent_is_blocked(self):
        request = {
            "request_id": "WF-MUTATION-001",
            "intent": "Implement the approved integration change in a repository.",
            "work_type": "engineering",
            "target_system_id": "VX",
            "requested_capabilities": ["architecture_design"],
            "mutation_scope": "REPOSITORY",
            "risk_level": "MEDIUM",
            "source_refs": ["docs/agents/VAIXLNS_AGENT_OPERATING_MODEL_V1.md"],
            "constraints": ["require independent verification", "preserve previous state"],
        }
        plan = build_plan(request, self.registry, self.registry_digest)
        self.assertEqual(plan["plan_status"], "HOLD_FOR_AUTHORITY_AND_ADAPTER")
        self.assertTrue(plan["authority_required"])
        executor = [step for step in plan["steps"] if step["agent_id"] == "AG-011"]
        self.assertEqual(len(executor), 1)
        self.assertEqual(executor[0]["status"], "BLOCKED_REFERENCE_PLANNER_ONLY")
        self.assertTrue(any(reason.startswith("MUTATION_SCOPE_REQUIRES_AUTHORIZATION") for reason in plan["blocked_reasons"]))
        validate_plan(plan, self.registry)

    def test_high_risk_read_only_request_is_held(self):
        request = read_json(FIXTURE)
        request["risk_level"] = "HIGH"
        plan = build_plan(request, self.registry, self.registry_digest)
        self.assertEqual(plan["plan_status"], "HOLD_FOR_AUTHORITY_AND_ADAPTER")
        self.assertTrue(plan["authority_required"])

    def test_missing_capability_fails_closed(self):
        request = read_json(FIXTURE)
        request["requested_capabilities"] = ["unregistered_magic_capability"]
        with self.assertRaisesRegex(WorkflowError, "not covered"):
            build_plan(request, self.registry, self.registry_digest)

    def test_unknown_target_system_fails_closed(self):
        request = read_json(FIXTURE)
        request["target_system_id"] = "UNKNOWN-SYSTEM"
        with self.assertRaisesRegex(WorkflowError, "unknown target_system_id"):
            build_plan(request, self.registry, self.registry_digest)

    def test_caller_supplied_approval_reference_does_not_bypass_authority_gate(self):
        request = read_json(FIXTURE)
        request["mutation_scope"] = "CANONICAL"
        request["approval_ref"] = "APPROVED-BY-CALLER"
        plan = build_plan(request, self.registry, self.registry_digest)
        self.assertEqual(plan["plan_status"], "HOLD_FOR_AUTHORITY_AND_ADAPTER")
        self.assertFalse(plan["execution"]["approval_ref_is_verified"])
        self.assertEqual(plan["approval_reference_not_verified"], "APPROVED-BY-CALLER")

    def test_unknown_request_field_fails_closed(self):
        request = read_json(FIXTURE)
        request["grant_runtime_authority"] = True
        with self.assertRaisesRegex(WorkflowError, "unsupported request fields"):
            build_plan(request, self.registry, self.registry_digest)

    def test_target_system_may_be_omitted_without_inventing_owner(self):
        request = read_json(FIXTURE)
        request.pop("target_system_id")
        plan = build_plan(request, self.registry, self.registry_digest)
        self.assertIsNone(plan["target_system_id"])
        self.assertEqual(plan["plan_status"], "PLAN_READY_NOT_EXECUTED")

    def test_pipeline_cannot_move_execution_before_verification(self):
        registry = json.loads(json.dumps(self.registry))
        registry["pipelines"]["engineering"].remove("AG-010")
        registry["pipelines"]["engineering"].insert(0, "AG-011")
        with self.assertRaises(WorkflowError):
            validate_registry(registry)

    def test_plan_is_deterministic_for_same_request_and_registry(self):
        request = read_json(FIXTURE)
        first = build_plan(request, self.registry, self.registry_digest)
        second = build_plan(request, self.registry, self.registry_digest)
        self.assertEqual(first["plan_id"], second["plan_id"])
        self.assertEqual(first["plan_sha256"], second["plan_sha256"])
        self.assertEqual(first["trace_events"], second["trace_events"])

    def test_trace_hash_tampering_is_detected(self):
        plan = build_plan(read_json(FIXTURE), self.registry, self.registry_digest)
        plan["trace_events"][0]["payload"]["plan_status"] = "VERIFIED"
        with self.assertRaisesRegex(WorkflowError, "trace event hash"):
            validate_plan(plan, self.registry)

    def test_registry_rejects_authority_drift(self):
        registry = json.loads(json.dumps(self.registry))
        registry["system_registry"][1]["may_grant_runtime_authority"] = True
        with self.assertRaisesRegex(WorkflowError, "must not self-grant"):
            validate_registry(registry)


if __name__ == "__main__":
    unittest.main()
