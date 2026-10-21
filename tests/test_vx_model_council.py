import unittest
from intelligence_federation.adaptive_router import Candidate
from intelligence_federation.model_council import plan_council, CouncilPolicy, normalize_provider_registry

class CouncilTests(unittest.TestCase):
    def test_unconfigured_registry_is_not_active(self):
        models = normalize_provider_registry({"providers":[{"provider":"openai","model_id":"x","verified_capabilities":["reasoning"]}]})
        self.assertEqual(plan_council("job",models)["status"],"BLOCKED")

    def test_two_providers_assign_without_invoking(self):
        models=[Candidate("a","m1",frozenset({"reasoning","coding"}),"ACTIVE"),
                Candidate("b","m2",frozenset({"reasoning","coding"}),"ACTIVE")]
        result=plan_council("job",models)
        self.assertEqual(result["status"],"PROPOSED")
        self.assertFalse(result["api_called"])
        self.assertEqual(len(result["assignments"]),5)
        self.assertGreaterEqual(result["distinct_providers"],2)

    def test_one_provider_fails_independence(self):
        models=[Candidate("a","m1",frozenset({"reasoning","coding"}),"ACTIVE")]
        self.assertEqual(plan_council("job",models)["status"],"BLOCKED")

    def test_default_budget_denies_cost(self):
        models=[Candidate("a","m1",frozenset({"reasoning","coding"}),"ACTIVE",unit_cost=1),
                Candidate("b","m2",frozenset({"reasoning","coding"}),"ACTIVE",unit_cost=1)]
        self.assertEqual(plan_council("job",models)["status"],"BLOCKED")

    def test_invalid_policy(self):
        with self.assertRaises(ValueError):
            plan_council("job",[],policy=CouncilPolicy(max_models=6))

if __name__ == "__main__":
    unittest.main()
