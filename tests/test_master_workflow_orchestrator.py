import unittest

from scripts.master_workflow_orchestrator import build_plan


INDEX = {
    "index_id": "Ω.000",
    "records": [
        {"id": "VAIXLNS", "type": "SYSTEM", "epistemic_state": "IMPLEMENTED", "lifecycle_state": "ACTIVE"},
        {"id": "VX", "type": "SYSTEM", "epistemic_state": "PARTIAL", "lifecycle_state": "EVOLVING"},
    ],
}
AGENTS = {
    "agents": [
        {"agent_id": "AG-ARCHIVE", "capabilities": ["archive", "index", "repository"]},
        {"agent_id": "AG-ENGINEERING", "capabilities": ["engineering", "implementation", "build"]},
        {"agent_id": "AG-VERIFY", "capabilities": ["test", "verification", "proof"]},
        {"agent_id": "AG-GOVERN", "capabilities": ["governance", "authority", "admission"]},
        {"agent_id": "AG-SELF-PROMOTER", "capabilities": ["proof", "verification"], "may_promote": True},
    ]
}
FACTORY = {
    "repositories": [
        {"name": "VAIXLNS-lab", "auto_create": True},
        {"name": "unrelated", "auto_create": False},
    ]
}


class MasterWorkflowOrchestratorTests(unittest.TestCase):
    def test_plan_is_deterministic_and_never_authorizes_execution(self):
        first = build_plan(INDEX, AGENTS, FACTORY, {"mission": "reconcile"})
        second = build_plan(INDEX, AGENTS, FACTORY, {"mission": "reconcile"})
        self.assertEqual(first, second)
        self.assertEqual(first["task_count"], 12)
        self.assertFalse(first["execution_authorization"])
        self.assertTrue(all(not task["execution_authorization"] for task in first["tasks"]))

    def test_plan_preserves_index_ids_and_record_count(self):
        plan = build_plan(INDEX, AGENTS, FACTORY)
        self.assertEqual(plan["source_record_count"], 2)
        self.assertEqual(plan["source_record_ids"], ["VAIXLNS", "VX"])

    def test_conflicting_or_unverified_record_holds_reconciliation(self):
        index = {
            "index_id": "Ω.000",
            "records": [{"id": "VX-OLD", "epistemic_state": "CONFLICT", "lifecycle_state": "QUARANTINED"}],
        }
        plan = build_plan(index, AGENTS, FACTORY)
        self.assertEqual(plan["status"], "HOLD_FOR_RECONCILIATION")
        self.assertIn("UNRESOLVED_INDEX_RECORDS_REQUIRE_RECONCILIATION", plan["tasks"][1]["blockers"])

    def test_duplicate_index_ids_are_rejected(self):
        index = {"index_id": "Ω.000", "records": [{"id": "VX"}, {"id": "VX"}]}
        with self.assertRaisesRegex(ValueError, "DUPLICATE_MASTER_INDEX_ID"):
            build_plan(index, AGENTS, FACTORY)

    def test_missing_index_records_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "MASTER_INDEX_RECORDS_MUST_BE_A_LIST"):
            build_plan({"index_id": "Ω.000"}, AGENTS, FACTORY)

    def test_self_promoting_agent_is_never_selected(self):
        plan = build_plan(INDEX, AGENTS, FACTORY)
        selected = {agent for task in plan["tasks"] for agent in task["eligible_agent_ids"]}
        self.assertNotIn("AG-SELF-PROMOTER", selected)

    def test_only_manifest_authorized_factory_entries_are_counted(self):
        plan = build_plan(INDEX, AGENTS, FACTORY)
        self.assertTrue(all(task["factory_candidate_count"] == 1 for task in plan["tasks"]))

    def test_task_dependencies_form_a_sequential_reviewable_chain(self):
        plan = build_plan(INDEX, AGENTS, FACTORY)
        self.assertEqual(plan["tasks"][0]["depends_on"], [])
        for previous, current in zip(plan["tasks"], plan["tasks"][1:]):
            self.assertEqual(current["depends_on"], [previous["task_id"]])


if __name__ == "__main__":
    unittest.main()
