"""Unit tests for ARC-X read-only MCP prototype."""
from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.arcx_mcp.server import ArcxError, _safe_source_path, classify_claim, fetch_source, inspect_repository


class ArcxMcpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / "docs").mkdir()
        (self.root / "docs" / "sample.md").write_text("ARC-X evidence sample\n", encoding="utf-8")
        (self.root / ".env").write_text("TOKEN=do-not-read\n", encoding="utf-8")
        self.env = patch.dict(os.environ, {"ARCX_REPOSITORY_ROOT": str(self.root)})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.temp.cleanup()

    def test_inspect_returns_scoped_inventory(self) -> None:
        result = inspect_repository()
        self.assertIn("docs/sample.md", result["files"])
        self.assertNotIn(".env", result["files"])
        self.assertIn(result["status"], {"SPECIFIED", "PARTIAL"})

    def test_fetch_returns_sha256_and_content(self) -> None:
        result = fetch_source("docs/sample.md")
        raw = b"ARC-X evidence sample\n"
        self.assertEqual(result["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["content"], raw.decode("utf-8"))

    def test_path_traversal_is_rejected(self) -> None:
        with self.assertRaises(ArcxError):
            _safe_source_path(self.root, "../outside.txt")

    def test_sensitive_file_is_rejected(self) -> None:
        with self.assertRaises(ArcxError):
            _safe_source_path(self.root, ".env")

    def test_symlink_escape_is_rejected(self) -> None:
        outside = self.root.parent / (self.root.name + "-outside.txt")
        outside.write_text("outside", encoding="utf-8")
        link = self.root / "outside-link.txt"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            outside.unlink(missing_ok=True)
            self.skipTest("Symlinks are unavailable in this environment")
        try:
            with self.assertRaises(ArcxError):
                _safe_source_path(self.root, "outside-link.txt")
        finally:
            outside.unlink(missing_ok=True)

    def test_claim_is_not_verified_from_references_alone(self) -> None:
        result = classify_claim("Example claim", ["sha256:abc"], "PASS")
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["authority_decision"], "NOT_REQUESTED")

    def test_missing_evidence_is_missing(self) -> None:
        result = classify_claim("Unsupported claim", [])
        self.assertEqual(result["status"], "MISSING")


if __name__ == "__main__":
    unittest.main()
