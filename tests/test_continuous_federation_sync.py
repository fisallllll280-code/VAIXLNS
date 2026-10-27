"""Offline conformance tests; no GitHub token or network required."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.continuous_federation_sync import (
    CONFIG_SCHEMA, FixtureReadOnly, SyncError, build, canonical_bytes,
    create_outputs, sha256, validate_sources, classify_path,
)

A = "a" * 40
B = "b" * 40
C = "c" * 40
D = "d" * 40
REPO = "example/sandbox"

def source_config(baseline=A):
    return {"schema": CONFIG_SCHEMA, "repositories": [{
        "repository": REPO, "branch": "main", "baseline_commit": baseline,
        "scope": "PUBLIC_METADATA_ONLY", "system_hint": "VX",
    }]}

def fixture(*, head=B, private=False, truncated=False, diff=True):
    paths = [
        {"path": "README.md", "type": "blob"},
        {"path": "docs/innovation/new-engine.md", "type": "blob"},
        {"path": "tests/test_engine.py", "type": "blob"},
        {"path": ".github/workflows/main.yml", "type": "blob"},
        {"path": "registry/omega/omega-000-master-index.json", "type": "blob"},
    ]
    responses = {
        f"/repos/{REPO}": {"full_name": REPO, "private": private},
        f"/repos/{REPO}/commits/main": {"sha": head, "commit": {"tree": {"sha": C}}},
        f"/repos/{REPO}/git/trees/{C}?recursive=1": {"tree": paths, "truncated": truncated},
    }
    if diff and head != A:
        responses[f"/repos/{REPO}/compare/{A}...{head}"] = {
            "status": "ahead", "files_changed": 3,
            "files": [
                {"filename": "docs/innovation/new-engine.md", "status": "added", "sha": D},
                {"filename": "tests/test_engine.py", "status": "modified", "sha": D},
                {"filename": "registry/omega/omega-000-master-index.json", "status": "modified", "sha": D},
            ],
        }
    return FixtureReadOnly(responses)


class ContinuousFederationSyncTests(unittest.TestCase):
    def test_validates_repositories_and_rejects_unknown_scope(self):
        self.assertEqual(validate_sources(source_config())[0]["repository"], REPO)
        data = source_config()
        data["repositories"][0]["scope"] = "PRIVATE_FULL_COPY"
        with self.assertRaisesRegex(SyncError, "ONLY_PUBLIC_METADATA"):
            validate_sources(data)

    def test_invalid_sha_rejected(self):
        data = source_config("main")
        with self.assertRaisesRegex(SyncError, "FULL_BASELINE"):
            validate_sources(data)

    def test_duplicate_repository_rejected(self):
        data = source_config()
        data["repositories"].append(dict(data["repositories"][0]))
        with self.assertRaisesRegex(SyncError, "INVALID_OR_DUPLICATE"):
            validate_sources(data)

    def test_accepts_baseline_identical_without_fabricating_changes(self):
        result = build(source_config(), fixture(head=A, diff=False), captured_at="TEST")
        self.assertEqual(result["decision"], "REVIEW_READY")
        self.assertEqual(result["changes"], [])
        self.assertEqual(result["repositories"][0]["comparison"], "BASELINE_EQUALS_HEAD")

    def test_pinned_changes_flow_to_review_queue_but_not_canonical(self):
        result = build(source_config(), fixture(), captured_at="TEST")
        self.assertEqual(result["decision"], "REVIEW_READY")
        self.assertEqual(len(result["changes"]), 3)
        self.assertTrue(all(e["implementation"] == "UNKNOWN" for e in result["changes"]))
        self.assertTrue(all(e["source_bytes_sha256"] is None for e in result["changes"]))
        self.assertEqual(result["canonical_promotion_count"], 0)
        self.assertEqual(result["repositories"][0]["workflow_file_count"], 1)
        with tempfile.TemporaryDirectory() as tmp:
            receipt = create_outputs(result, Path(tmp))
            self.assertEqual(receipt["status"], "REVIEW_READY")
            self.assertTrue((Path(tmp) / "federation-sync.v1.json").exists())
            queue = json.loads((Path(tmp) / "innovation-intake-queue.v1.json").read_text())
            self.assertEqual(len(queue["items"]), 2)
            self.assertFalse(queue["authority_granted"])

    def test_failure_isolation_makes_whole_snapshot_partial(self):
        response = fixture().responses
        response[f"/repos/{REPO}"] = {"_error": "GITHUB_HTTP_STATUS_404"}
        result = build(source_config(), FixtureReadOnly(response), captured_at="TEST")
        self.assertEqual(result["decision"], "PARTIAL_BLOCKED")
        self.assertEqual(result["source_repositories_unavailable"], 1)
        self.assertEqual(result["repositories"], [])

    def test_private_repository_never_inspected(self):
        result = build(source_config(), fixture(private=True), captured_at="TEST")
        self.assertEqual(result["decision"], "PARTIAL_BLOCKED")
        self.assertIn("PRIVATE_OR_UNVERIFIED", result["failures"][0]["reason_code"])

    def test_truncated_git_tree_is_blocking(self):
        result = build(source_config(), fixture(truncated=True), captured_at="TEST")
        self.assertEqual(result["decision"], "PARTIAL_BLOCKED")
        self.assertIn("TRUNCATED", result["failures"][0]["reason_code"])

    def test_incomplete_compare_is_blocking(self):
        responses = fixture().responses
        responses[f"/repos/{REPO}/compare/{A}...{B}"]["files_changed"] = 10
        result = build(source_config(), FixtureReadOnly(responses), captured_at="TEST")
        self.assertEqual(result["decision"], "PARTIAL_BLOCKED")


    def test_300_file_compare_limit_is_explicit_blocker(self):
        responses = fixture().responses
        responses[f"/repos/{REPO}/compare/{A}...{B}"]["files"] = [
            {"filename": f"docs/innovation/candidate-{i:03d}.md", "status": "added", "sha": D}
            for i in range(300)
        ]
        responses[f"/repos/{REPO}/compare/{A}...{B}"]["files_changed"] = 300
        result = build(source_config(), FixtureReadOnly(responses), captured_at="TEST")
        self.assertEqual(result["decision"], "PARTIAL_BLOCKED")
        self.assertIn("COMPARE_FILE_LIMIT_REACHED", result["failures"][0]["reason_code"])

    def test_rejects_directory_traversal_from_remote(self):
        responses = fixture().responses
        responses[f"/repos/{REPO}/compare/{A}...{B}"]["files"][0]["filename"] = "../evil.md"
        result = build(source_config(), FixtureReadOnly(responses), captured_at="TEST")
        self.assertEqual(result["decision"], "PARTIAL_BLOCKED")
        self.assertEqual(result["changes"], [])

    def test_source_hash_is_stable_for_exact_same_fixture(self):
        x = build(source_config(), fixture(), captured_at="TEST")
        y = build(source_config(), fixture(), captured_at="TEST")
        self.assertEqual(x["manifest_sha256"], y["manifest_sha256"])
        self.assertEqual(sha256(canonical_bytes({k: v for k, v in x.items() if k != "manifest_sha256"})), x["manifest_sha256"])

    def test_critical_changes_never_auto_promote(self):
        self.assertEqual(classify_path("project.genome"), "CANONICAL_GUARD_REVIEW")
        self.assertEqual(classify_path("registry/omega/omega-000-master-index.json"), "CANONICAL_GUARD_REVIEW")

    def test_external_connector_cannot_be_injected_into_config(self):
        data = source_config()
        data["repositories"].append({"repository": "https://evil.invalid", "branch": "main",
                                     "baseline_commit": A, "scope": "PUBLIC_METADATA_ONLY"})
        with self.assertRaises(SyncError):
            validate_sources(data)

if __name__ == "__main__":
    unittest.main()
