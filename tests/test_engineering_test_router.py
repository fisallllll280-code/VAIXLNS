import unittest

from tools.engineering_test_router import _parse_test_summary, plan_tests


class EngineeringTestRouterTests(unittest.TestCase):
    def test_vcre_change_routes_to_predictive_and_legacy_vcre_tests(self):
        plan = plan_tests(["vcre/predictive.py"])
        self.assertEqual(plan["selection_mode"], "FOCUSED")
        self.assertEqual(plan["test_files"], ["test_vcre_predictive.py", "test_vcre_runtime.py"])

    def test_multiple_known_changes_union_the_targets(self):
        plan = plan_tests(["scripts/vcre_probe.py", "scripts/vx_federation_gate.py"])
        self.assertEqual(plan["selection_mode"], "FOCUSED")
        self.assertEqual(
            plan["test_files"],
            ["test_vcre_predictive.py", "test_vcre_runtime.py", "test_vx_federation_gate.py"],
        )

    def test_unknown_change_falls_back_to_complete_suite(self):
        plan = plan_tests(["experiments/new_solver.py"])
        self.assertEqual(plan["selection_mode"], "FULL_SUITE")
        self.assertEqual(plan["fallback_reason"], "UNKNOWN_OR_CROSS_CUTTING_IMPACT")

    def test_registry_schema_or_document_changes_fall_back_to_complete_suite(self):
        for path in ("schemas/new-model.schema.json", "registry/new-registry.json", "docs/new-engine.md"):
            with self.subTest(path=path):
                plan = plan_tests([path])
                self.assertEqual(plan["selection_mode"], "FULL_SUITE")

    def test_unavailable_diff_falls_back_to_complete_suite(self):
        plan = plan_tests(None, diff_error="BASE_OR_HEAD_UNAVAILABLE")
        self.assertEqual(plan["selection_mode"], "FULL_SUITE")
        self.assertEqual(plan["fallback_reason"], "BASE_OR_HEAD_UNAVAILABLE")

    def test_mixed_known_and_unknown_paths_fall_back_to_complete_suite(self):
        plan = plan_tests(["vcre/predictive.py", "random/mystery.py"])
        self.assertEqual(plan["selection_mode"], "FULL_SUITE")
        self.assertTrue(plan["unknown_or_cross_cutting_files"])

    def test_hidden_github_path_is_preserved_exactly(self):
        path = ".github/workflows/fast.yml"
        plan = plan_tests([path])
        self.assertEqual(plan["selection_mode"], "FULL_SUITE")
        self.assertIn(path, plan["unknown_or_cross_cutting_files"])

    def test_test_summary_parser_reports_count_and_runtime(self):
        self.assertEqual(_parse_test_summary("Ran 12 tests in 0.456s"), (12, 0.456))
        self.assertEqual(_parse_test_summary("Ran 1 test in 0.010s"), (1, 0.01))

    def test_zero_or_missing_test_summary_is_not_a_valid_test_run(self):
        self.assertEqual(_parse_test_summary("Ran 0 tests in 0.000s"), (0, 0.0))
        self.assertIsNone(_parse_test_summary("setup finished; no unittest summary"))


if __name__ == "__main__":
    unittest.main()
