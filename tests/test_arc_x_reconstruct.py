"""Conformance tests for the ARC-X deterministic reconstruction slice."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.arc_x_reconstruct import build_eir, canonical_json, reconstruct


class ArcXReconstructionTests(unittest.TestCase):
    def test_eir_is_deterministic_for_same_pinned_inputs(self):
        records = [{
            "artifact_id": "file:README.md", "path": "README.md",
            "size_bytes": 3, "sha256": "a" * 64, "media_kind": "text",
        }]
        first = build_eir("example/repo", "abc1234", records)
        second = build_eir("example/repo", "abc1234", records)
        self.assertEqual(first, second)
        self.assertEqual(first["eir_sha256"], __import__("hashlib").sha256(
            canonical_json({k: v for k, v in first.items() if k != "eir_sha256"})
        ).hexdigest())

    def test_reconstruction_emits_three_auditable_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / "repo"
            out = Path(temp) / "out"
            base.mkdir()
            (base / "README.md").write_text("preserve me", encoding="utf-8")
            result = reconstruct(base, out, "example/repo", "0123456789abcdef")
            self.assertEqual(result["artifact_count"], 1)
            for name in ("repository.model.json", "eir.json", "source.receipt.json"):
                self.assertTrue((out / name).is_file())
            eir = json.loads((out / "eir.json").read_text(encoding="utf-8"))
            self.assertEqual(eir["claims"][0]["authority_state"], "NOT_AUTHORIZED")
            receipt = json.loads((out / "source.receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["authority_decision"], "BLOCKED")

    def test_moving_branch_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            with self.assertRaises(ValueError):
                reconstruct(base, base / "out", "example/repo", "main")


if __name__ == "__main__":
    unittest.main()
