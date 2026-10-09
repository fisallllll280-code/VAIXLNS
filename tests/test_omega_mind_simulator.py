import copy
import json
import unittest
from pathlib import Path
from scripts.omega_mind_simulator import ScenarioError, simulate, verify_event_chain

FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "omega-mind-simulation.example.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class OmegaMindSimulatorTests(unittest.TestCase):
    def test_fixture_is_deterministic_and_simulation_only(self):
        fixture = load_fixture()
        first = simulate(copy.deepcopy(fixture))
        second = simulate(copy.deepcopy(fixture))
        self.assertEqual(first, second)
        self.assertEqual(first["mode"], "SIMULATION_ONLY")
        self.assertFalse(first["production_execution_performed"])
        self.assertFalse(first["model_provider_invoked"])
        self.assertFalse(first["repository_modified"])
        self.assertFalse(first["canonical_status_changed"])

    def test_hash_chain_verifies_and_detects_tampering(self):
        result = simulate(load_fixture())
        self.assertTrue(verify_event_chain(result["events"]))
        events = copy.deepcopy(result["events"])
        events[1]["details"]["topology"] = "FAKE_SUCCESS"
        self.assertFalse(verify_event_chain(events))

    def test_canonical_path_is_blocked(self):
        result = simulate(load_fixture())
        outcome = next(x for x in result["outcomes"] if x["task_id"] == "t05_canonical_mutation_probe")
        self.assertEqual(outcome["status"], "BLOCKED")
        self.assertTrue(any("canonical authority path" in reason for reason in outcome["reasons"]))

    def test_role_cannot_request_ungranted_tool(self):
        fixture = load_fixture()
        task = fixture["tasks"][0]
        task["requested_tools"] = ["repo.read", "production.deploy"]
        task["allowed_tools"] = ["repo.read", "production.deploy"]
        result = simulate(fixture)
        outcome = next(x for x in result["outcomes"] if x["task_id"] == task["task_id"])
        self.assertEqual(outcome["status"], "BLOCKED")
        self.assertTrue(any("role does not grant" in reason for reason in outcome["reasons"]))

    def test_scope_escape_is_blocked(self):
        fixture = load_fixture()
        task = fixture["tasks"][0]
        task["write_paths"] = ["secrets/prod.env"]
        task["authorized_paths"] = ["docs"]
        result = simulate(fixture)
        outcome = next(x for x in result["outcomes"] if x["task_id"] == task["task_id"])
        self.assertEqual(outcome["status"], "BLOCKED")
        self.assertTrue(any("outside task grant" in reason for reason in outcome["reasons"]))

    def test_traversal_is_rejected_before_simulation(self):
        fixture = load_fixture()
        fixture["tasks"][0]["write_paths"] = ["docs/../../project.genome"]
        with self.assertRaisesRegex(ScenarioError, "traversal"):
            simulate(fixture)

    def test_failed_check_does_not_pass(self):
        fixture = load_fixture()
        fixture["tasks"][0]["verification"]["tests"] = "FAIL"
        result = simulate(fixture)
        outcome = next(x for x in result["outcomes"] if x["task_id"] == fixture["tasks"][0]["task_id"])
        self.assertEqual(outcome["status"], "SIMULATION_FAIL")

    def test_missing_evidence_is_inconclusive(self):
        fixture = load_fixture()
        fixture["tasks"][0]["verification"]["evidence_refs"] = []
        result = simulate(fixture)
        outcome = next(x for x in result["outcomes"] if x["task_id"] == fixture["tasks"][0]["task_id"])
        self.assertEqual(outcome["status"], "INCONCLUSIVE")

    def test_cycle_is_rejected(self):
        fixture = load_fixture()
        fixture["tasks"][0]["depends_on"] = [fixture["tasks"][1]["task_id"]]
        fixture["tasks"][1]["depends_on"] = [fixture["tasks"][0]["task_id"]]
        with self.assertRaisesRegex(ScenarioError, "cycle"):
            simulate(fixture)

    def test_failed_dependency_blocks_downstream(self):
        fixture = load_fixture()
        fixture["tasks"][0]["verification"]["tests"] = "FAIL"
        result = simulate(fixture)
        outcome = next(x for x in result["outcomes"] if x["task_id"] == "t03_contract_design")
        self.assertEqual(outcome["status"], "BLOCKED")
        self.assertTrue(any("dependency not simulation-passed" in reason for reason in outcome["reasons"]))

    def test_cost_budget_fails_closed(self):
        fixture = load_fixture()
        fixture["budgets"]["max_estimated_cost"] = 1
        result = simulate(fixture)
        self.assertTrue(all(x["status"] == "BLOCKED" for x in result["outcomes"]))

    def test_high_impact_task_cannot_self_approve(self):
        fixture = load_fixture()
        task = fixture["tasks"][0]
        task["risk"] = "HIGH"
        task["requires_human_approval"] = True
        result = simulate(fixture)
        outcome = next(x for x in result["outcomes"] if x["task_id"] == task["task_id"])
        self.assertEqual(outcome["status"], "BLOCKED")
        self.assertTrue(any("human approval" in reason for reason in outcome["reasons"]))


if __name__ == "__main__":
    unittest.main()
