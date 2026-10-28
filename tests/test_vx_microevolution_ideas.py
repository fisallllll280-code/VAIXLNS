import unittest
from scripts.vx_microevolution_ideas import evaluate_catalog


def idea(iid="A", deps=None):
    return {
        "id": iid, "title": iid, "hypothesis": "test hypothesis",
        "minimal_experiment": "test experiment", "success_metric": "measurable",
        "kill_criteria": "stop if invalid", "dependencies": deps or [],
        "horizon_years": 1, "impact": 4, "confidence": 3,
        "reversibility": 5, "leverage": 4, "cost": 2, "risk": 1,
        "evidence_gap": 2, "novelty": "UNASSESSED", "state": "PROPOSED",
    }


class IdeaEvaluatorTests(unittest.TestCase):
    def test_valid_catalog_is_screened_not_admitted(self):
        result = evaluate_catalog({"schema_version": "vx.microevolution.idea-catalog.v1", "catalog_id": "test", "ideas": [idea()]})
        self.assertEqual(result["status"], "SCREENED_NOT_ADMITTED")
        self.assertFalse(result["limits"]["authority_granted"])
        self.assertFalse(result["limits"]["automatic_promotion"])

    def test_duplicate_ids_block(self):
        result = evaluate_catalog({"schema_version": "vx.microevolution.idea-catalog.v1", "ideas": [idea(), idea()]})
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("DUPLICATE_ID" in e["error"] for e in result["errors"]))

    def test_missing_dependency_blocks(self):
        result = evaluate_catalog({"schema_version": "vx.microevolution.idea-catalog.v1", "ideas": [idea("A", ["NOPE"])]})
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("MISSING_DEPENDENCY" in e["error"] for e in result["errors"]))

    def test_dependency_cycle_blocks_and_clears_topological_order(self):
        a, b = idea("A", ["B"]), idea("B", ["A"])
        result = evaluate_catalog({"schema_version": "vx.microevolution.idea-catalog.v1", "ideas": [a, b]})
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["topological_order"], [])
        self.assertTrue(result["dependency_cycles"])

    def test_novelty_cannot_be_claimed_without_research(self):
        candidate = idea()
        candidate["novelty"] = "NOVEL"
        result = evaluate_catalog({"schema_version": "vx.microevolution.idea-catalog.v1", "ideas": [candidate]})
        self.assertEqual(result["status"], "BLOCKED")

    def test_invalid_score_blocks(self):
        candidate = idea()
        candidate["impact"] = 99
        result = evaluate_catalog({"schema_version": "vx.microevolution.idea-catalog.v1", "ideas": [candidate]})
        self.assertEqual(result["status"], "BLOCKED")

    def test_wrong_schema_fails_closed(self):
        with self.assertRaises(ValueError):
            evaluate_catalog({"schema_version": "unknown", "ideas": []})


if __name__ == "__main__":
    unittest.main()
