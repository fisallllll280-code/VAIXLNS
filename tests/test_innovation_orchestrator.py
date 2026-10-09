import json
import unittest

from agents.innovation_orchestrator import (
    MissionRequest, build_mission_plan, validate_mission_plan,
)


class InnovationOrchestratorTests(unittest.TestCase):
    def test_builds_thirteen_role_plan_with_valid_contracts(self):
        plan = build_mission_plan(MissionRequest(
            intent="Analyze and improve the computational agent system",
            required_capabilities=("test_generation", "source_coverage"),
            constraints=("preserve history", "no production changes"),
            source_refs=("docs/agents/AGENT_FABRIC_V1.md",),
        ))
        self.assertEqual(plan["status"], "PLANNED")
        self.assertEqual(len(plan["tasks"]), 13)
        self.assertEqual(validate_mission_plan(plan), ())
        self.assertFalse(plan["governance"]["self_authority"])
        self.assertFalse(plan["governance"]["canonical_write_permitted"])
        self.assertEqual(plan["evidence"]["provider_calls"], 0)

    def test_json_round_trip_plan_remains_valid(self):
        plan = build_mission_plan(MissionRequest(
            intent="serialize the governed agent plan",
            required_capabilities=("test_generation", "source_coverage"),
        ))
        decoded = json.loads(json.dumps(plan))
        self.assertEqual(validate_mission_plan(decoded), ())

    def test_plan_is_deterministic_for_same_request(self):
        request = MissionRequest(intent="reconstruct architecture", source_refs=("project.genome",))
        self.assertEqual(build_mission_plan(request), build_mission_plan(request))

    def test_unsupported_capability_blocks_plan(self):
        plan = build_mission_plan(MissionRequest(
            intent="execute unknown capability", required_capabilities=("quantum_time_travel",)
        ))
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertIn("quantum_time_travel", plan["coverage"]["unsupported_capabilities"])

    def test_prohibited_autonomous_actions_are_rejected(self):
        for action in ("canonical-write", "production-deploy", "self-promote", "financial-transfer"):
            with self.subTest(action=action):
                with self.assertRaisesRegex(PermissionError, "PROHIBITED_AUTONOMOUS_ACTION"):
                    build_mission_plan(MissionRequest(intent="do work", requested_actions=(action,)))

    def test_path_traversal_source_ref_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_REF_MUST_NOT_ESCAPE_WORKSPACE"):
            build_mission_plan(MissionRequest(intent="inspect files", source_refs=("../../secrets.txt",)))

    def test_mutated_task_authority_is_detected(self):
        plan = build_mission_plan(MissionRequest(intent="audit governance"))
        plan["tasks"][0]["execution_permitted"] = True
        self.assertIn("TASK_AUTHORITY_ESCALATION:TASK-" + plan["tasks"][0]["task_id"][5:],
                      validate_mission_plan(plan))

    def test_unknown_mission_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "MISSION_ID_INVALID"):
            build_mission_plan(MissionRequest(intent="test", mission_id="../bad"))


if __name__ == "__main__":
    unittest.main()
