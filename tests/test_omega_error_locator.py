"""Regression tests for evidence-first Ω Error Locator."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.omega_error_locator import locate, sha256_text


class OmegaErrorLocatorTests(unittest.TestCase):
    def make_root(self, root: Path):
        (root / "scripts").mkdir()
        (root / "scripts" / "module.py").write_text(
            "def run(value):\n    return value + 1\n", encoding="utf-8"
        )
        (root / "tests").mkdir()
        (root / "tests" / "test_module.py").write_text(
            "def test_run():\n    assert run(1) == 3\n", encoding="utf-8"
        )

    def test_python_traceback_resolves_exact_path_and_line(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_root(root)
            report = locate(root, 'Traceback (most recent call last):\n  File "scripts/module.py", line 2, in run\nTypeError: bad input\n')
            self.assertEqual(report["state"], "LOCATION_FOUND_FROM_EXPLICIT_EVIDENCE")
            self.assertEqual(report["locations"][0]["path"], "scripts/module.py")
            self.assertEqual(report["locations"][0]["line"], 2)
            self.assertIn("TYPE_OR_SCHEMA", {s["signal"] for s in report["signals"]})

    def test_failed_pytest_node_is_candidate_without_exact_line(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_root(root)
            report = locate(root, "FAILED tests/test_module.py::test_run - AssertionError: mismatch\n")
            self.assertEqual(report["state"], "CANDIDATE_LOCATION_FOUND")
            self.assertEqual(report["locations"][0]["path"], "tests/test_module.py")
            self.assertIsNone(report["locations"][0]["line"])

    def test_unresolved_symbol_search_finds_candidate_occurrences(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_root(root)
            (root / "scripts" / "broken.py").write_text(
                "def entry():\n    ghost_call()\n", encoding="utf-8"
            )
            report = locate(root, "NameError: name 'ghost_call' is not defined\n")
            self.assertEqual(report["state"], "CANDIDATE_LOCATION_FOUND")
            matches = [
                item for item in report["locations"]
                if item["path"] == "scripts/broken.py"
                and item["symbol"] == "ghost_call"
            ]
            self.assertTrue(matches)
            self.assertEqual(matches[0]["line"], 2)
            self.assertIn("SYMBOL_REFERENCE_MATCH", matches[0]["evidence_methods"])

    def test_missing_location_is_reported_as_insufficient_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_root(root)
            report = locate(root, "error: something went wrong without a path\n")
            self.assertEqual(report["state"], "LOCALIZATION_INSUFFICIENT_EVIDENCE")
            self.assertEqual(report["confidence"], "INSUFFICIENT")
            self.assertTrue(report["next_steps"])

    def test_secrets_are_redacted_from_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_root(root)
            report = locate(root, "error: api_key=super-secret-value\n")
            self.assertNotIn("super-secret-value", str(report))
            self.assertIn("[REDACTED]", str(report))

    def test_report_hash_is_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_root(root)
            text = "ModuleNotFoundError: No module named 'unknown_pkg'\n"
            self.assertEqual(locate(root, text), locate(root, text))
            self.assertEqual(len(sha256_text(text)), 64)


if __name__ == "__main__":
    unittest.main()
