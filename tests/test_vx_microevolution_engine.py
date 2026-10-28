import tempfile
import unittest
from pathlib import Path

from scripts.vx_microevolution_engine import build_report


class MicroEvolutionEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "module.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        (self.root / "README.md").write_text("# Example\nA small project.\n", encoding="utf-8")
        (self.root / "tests" / "test_module.py").write_text("def test_add():\n    assert 1 + 1 == 2\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_report_has_inventory_and_candidates(self):
        report = build_report(self.root, 5)
        self.assertEqual(report["schema_version"], "vx.microevolution.report.v1")
        self.assertEqual(report["summary"]["files_scanned"], 3)
        self.assertGreaterEqual(report["summary"]["candidate_count"], 1)
        self.assertFalse(report["limits"]["source_modified"])
        self.assertFalse(report["limits"]["automatic_approval"])

    def test_scan_does_not_modify_source(self):
        target = self.root / "src" / "module.py"
        before = target.read_bytes()
        build_report(self.root, 3)
        self.assertEqual(target.read_bytes(), before)

    def test_longitudinal_comparison_detects_changes(self):
        baseline = build_report(self.root, 5)
        (self.root / "src" / "module.py").write_text("def add(a, b):\\n    return a + b + 1\\n", encoding="utf-8")
        (self.root / "src" / "new_module.py").write_text("VALUE = 1\\n", encoding="utf-8")
        current = build_report(self.root, 5, baseline_report=baseline)
        comparison = current["longitudinal_comparison"]
        self.assertEqual(comparison["status"], "COMPARED")
        self.assertIn("src/module.py", comparison["changed_paths"])
        self.assertIn("src/new_module.py", comparison["added_paths"])
        self.assertEqual(comparison["removed_paths"], [])

    def test_invalid_baseline_fails_closed(self):
        with self.assertRaises(ValueError):
            build_report(self.root, 5, baseline_report={"inventory": "invalid"})

    def test_horizon_validation(self):
        with self.assertRaises(ValueError):
            build_report(self.root, 7)

    def test_missing_root_fails_closed(self):
        with self.assertRaises(ValueError):
            build_report(self.root / "missing", 5)

    def test_secret_and_build_directories_are_excluded(self):
        (self.root / ".env").write_text("NOT_A_SECRET_VALUE", encoding="utf-8")
        (self.root / "build").mkdir()
        (self.root / "build" / "hidden.py").write_text("bad = True", encoding="utf-8")
        report = build_report(self.root)
        paths = {item["path"] for item in report["inventory"]}
        self.assertNotIn(".env", paths)
        self.assertNotIn("build/hidden.py", paths)


if __name__ == "__main__":
    unittest.main()
