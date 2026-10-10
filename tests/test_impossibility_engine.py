import unittest

from tools.impossibility_engine import assess


class ImpossibilityEngineTests(unittest.TestCase):
    def test_detects_explicit_range_contradiction(self):
        result = assess({
            "title": "Latency target",
            "goal": "Keep latency in an allowed range",
            "constraints": [{"kind": "range", "variable": "latency_ms", "min": 50, "max": 20}],
            "evidence": [{"state": "OBSERVED", "ref": "test-run-1"}],
        })
        self.assertEqual(result["classification"], "CONTRADICTION_DETECTED")
        self.assertEqual(result["findings"][0]["code"], "RANGE_CONTRADICTION")

    def test_does_not_call_unspecified_goal_impossible(self):
        result = assess({"title": "Make teleportation real", "goal": "Move matter instantly"})
        self.assertEqual(result["classification"], "INSUFFICIENT_SPECIFICATION")
        self.assertIn("Evidence for key assumptions and any claimed impossibility.", result["missing_information"])

    def test_well_specified_problem_remains_unproven_not_verified(self):
        result = assess({
            "title": "Prototype a low-power sensor",
            "goal": "Read temperature within 1 degree C",
            "constraints": [{"kind": "range", "variable": "power_mw", "min": 0.1, "max": 5}],
            "resources": ["bench supply", "reference thermometer"],
            "evidence": [{"state": "OBSERVED", "ref": "baseline-test"}],
        })
        self.assertEqual(result["classification"], "ENGINEERING_CHALLENGE")
        self.assertNotEqual(result["state"], "VERIFIED")
        self.assertTrue(result["safety_boundary"]["no_external_calls"])

    def test_rejects_bad_constraint_schema(self):
        with self.assertRaises(ValueError):
            assess({"goal": "x", "constraints": "not-a-list"})

    def test_result_has_stable_hash(self):
        problem = {
            "title": "Repeatability",
            "goal": "Same assessment for same input",
            "constraints": [{"kind": "range", "variable": "x", "min": 1, "max": 2}],
            "evidence": [{"state": "UNKNOWN", "ref": "none"}],
        }
        self.assertEqual(assess(problem)["assessment_sha256"], assess(problem)["assessment_sha256"])


if __name__ == "__main__":
    unittest.main()
