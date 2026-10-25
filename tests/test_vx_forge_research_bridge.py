"""Offline VX research bridge tests."""
import copy
import unittest
from scripts.vx_forge_research_bridge import plan_research

class ResearchBridgeTests(unittest.TestCase):
    def setUp(self):
        self.problem = {"title": "Latency", "goal": "Reduce latency",
                        "capability": "mathematics",
                        "constraints": [{"kind": "range", "variable": "latency", "min": 0, "max": 100}],
                        "evidence": [{"state": "HYPOTHESIS"}]}
        self.models = [{"provider": "offline", "model": "solver", "version": "v1",
                        "capabilities": ["mathematics"]}]
    def test_no_external_execution(self):
        result = plan_research(self.problem, self.models)
        self.assertEqual(result["execution"], "DISABLED")
        self.assertEqual(result["provider_calls"], 0)
        self.assertEqual(result["admission"], "HOLD")
    def test_determinism(self):
        self.assertEqual(plan_research(self.problem, self.models)["plan_digest"],
                         plan_research(self.problem, self.models)["plan_digest"])
    def test_contradiction(self):
        problem = copy.deepcopy(self.problem)
        problem["constraints"][0]["min"] = 200
        result = plan_research(problem, self.models)
        self.assertEqual(result["feasibility_triage"]["status"], "CONTRADICTION_DETECTED")
    def test_empty_goal_rejected(self):
        problem = copy.deepcopy(self.problem)
        problem["goal"] = ""
        with self.assertRaises(ValueError):
            plan_research(problem, self.models)
    def test_unknown_capability_rejected(self):
        problem = copy.deepcopy(self.problem)
        problem["capability"] = "unsupported"
        with self.assertRaises(ValueError):
            plan_research(problem, self.models)
