from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_index_path_depth import build_report, validate_report  # noqa: E402


class IndexPathDepthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs/indexes").mkdir(parents=True)
        (self.root / "docs/architecture").mkdir(parents=True)
        (self.root / "tools").mkdir()
        (self.root / "docs/indexes/README.md").write_text(
            "# Root\n[A](A.md)\n[A duplicate](A.md)\n"
            "tools/probe.py\n"
            "[External](https://example.test/ref.md)\n"
            "[Broken](missing.md)\n[Escape](../../../outside.md)\n",
            encoding="utf-8",
        )
        (self.root / "docs/indexes/A.md").write_text(
            "# A\n[C](../architecture/C.md)\n[Back](README.md)\n",
            encoding="utf-8",
        )
        (self.root / "docs/architecture/C.md").write_text(
            "# C\n[Root](../indexes/README.md)\n",
            encoding="utf-8",
        )
        (self.root / "tools/probe.py").write_text("# small fixture\n", encoding="utf-8")
        (self.root / "docs/unreachable.md").write_text("# not referenced\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_discovers_shortest_reference_depth_and_cycles(self) -> None:
        report = build_report(self.root)
        nodes = {node["path"]: node for node in report["nodes"]}
        self.assertEqual(nodes["docs/indexes/README.md"]["depth"], 0)
        self.assertEqual(nodes["docs/indexes/A.md"]["depth"], 1)
        self.assertEqual(nodes["tools/probe.py"]["depth"], 1)
        self.assertEqual(nodes["docs/architecture/C.md"]["depth"], 2)
        self.assertEqual(
            nodes["docs/architecture/C.md"]["path_chain"],
            ["docs/indexes/README.md", "docs/indexes/A.md", "docs/architecture/C.md"],
        )
        self.assertIsNone(nodes["docs/unreachable.md"]["depth"])
        self.assertEqual(report["unreachable_file_count"], 1)
        validate_report(report)

    def test_reports_broken_and_blocks_path_escape(self) -> None:
        report = build_report(self.root)
        self.assertEqual(report["broken_link_count"], 1)
        self.assertEqual(report["broken_links"][0]["target"], "missing.md")
        self.assertEqual(report["blocked_link_count"], 1)
        self.assertEqual(report["blocked_links"][0]["target"], "../../../outside.md")

    def test_output_is_deterministic(self) -> None:
        self.assertEqual(build_report(self.root), build_report(self.root))

    def test_validator_rejects_invalid_chain(self) -> None:
        report = build_report(self.root)
        target = next(n for n in report["nodes"] if n["path"] == "docs/indexes/A.md")
        target["path_chain"] = ["docs/indexes/A.md"]
        with self.assertRaises(ValueError):
            validate_report(report)


if __name__ == "__main__":
    unittest.main()
