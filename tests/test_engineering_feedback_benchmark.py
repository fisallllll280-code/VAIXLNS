import unittest

from tools.benchmark_engineering_feedback import summarize


class EngineeringFeedbackBenchmarkTests(unittest.TestCase):
    def test_summary_uses_median_and_preserves_range(self):
        result = summarize([
            {"harness_wall_time_seconds": 3.0},
            {"harness_wall_time_seconds": 1.0},
            {"harness_wall_time_seconds": 2.0},
        ])
        self.assertEqual(result["runs"], 3)
        self.assertEqual(result["median_wall_time_seconds"], 2.0)
        self.assertEqual(result["min_wall_time_seconds"], 1.0)
        self.assertEqual(result["max_wall_time_seconds"], 3.0)

    def test_empty_summary_is_explicitly_empty(self):
        self.assertEqual(
            summarize([]),
            {
                "runs": 0,
                "median_wall_time_seconds": None,
                "min_wall_time_seconds": None,
                "max_wall_time_seconds": None,
            },
        )


if __name__ == "__main__":
    unittest.main()
