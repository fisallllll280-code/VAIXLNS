"""Validation of innovation publication from a trusted CI review receipt."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.continuous_federation_sync import CONFIG_SCHEMA, FixtureReadOnly, build, create_outputs
from scripts.publish_federation_sync_review import ReviewError, render_review

SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40
SHA_D = "d" * 40
REPO = "example/public"

class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "registry/federation").mkdir(parents=True)
        self.config = {"schema": CONFIG_SCHEMA, "repositories": [
            {"repository": REPO, "branch": "main",
             "baseline_commit": SHA_A, "scope": "PUBLIC_METADATA_ONLY", "system_hint": "VX"}
        ]}
        (self.root / "registry/federation/continuous-sync-sources.v1.json").write_text(json.dumps(self.config))
        self.out = self.root / "build"
        responses = {
            f"/repos/{REPO}": {"full_name": REPO, "private": False},
            f"/repos/{REPO}/commits/main": {"sha": SHA_B, "commit": {"tree": {"sha": SHA_C}}},
            f"/repos/{REPO}/git/trees/{SHA_C}?recursive=1":
                {"tree": [{"type": "blob", "path": "docs/innovation/new.md"}], "truncated": False},
            f"/repos/{REPO}/compare/{SHA_A}...{SHA_B}":
                {"status": "ahead", "files_changed": 1, "files": [
                    {"filename": "docs/innovation/new.md", "status": "added", "sha": SHA_D}]},
        }
        manifest = build(self.config, FixtureReadOnly(responses), captured_at="2026-10-27T20:00:00+00:00")
        create_outputs(manifest, self.out)

    def tearDown(self):
        self.temp.cleanup()

    def read(self, name):
        return json.loads((self.out / name).read_text(encoding="utf-8"))

    def write(self, name, value):
        (self.out / name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")

    def test_generates_noncanonical_evidence_and_innovation(self):
        evidence, innovation = render_review(self.root, self.out)
        e, i = json.loads(evidence.read_text()), json.loads(innovation.read_text())
        self.assertEqual(e["state"], "OBSERVED_NEEDS_HUMAN_REVIEW")
        self.assertEqual(e["innovation_review_count"], 1)
        self.assertEqual(i["state"], "PROPOSED_NOT_ADMITTED")
        self.assertEqual(i["review_items"][0]["verified"], "UNKNOWN")

    def test_rejects_manifest_tampering(self):
        m = self.read("federation-sync.v1.json")
        m["changes"][0]["verified"] = "VERIFIED"
        self.write("federation-sync.v1.json", m)
        with self.assertRaisesRegex(ReviewError, "MANIFEST_DIGEST_MISMATCH"):
            render_review(self.root, self.out)

    def test_rejects_receipt_tampering(self):
        r = self.read("sync-receipt.v1.json")
        r["innovation_queue_sha256"] = "0"*64
        self.write("sync-receipt.v1.json", r)
        with self.assertRaisesRegex(ReviewError, "RECEIPT_CONTENT_DIGEST_MISMATCH"):
            render_review(self.root, self.out)

    def test_rejects_private_scope_mismatch(self):
        m = self.read("federation-sync.v1.json")
        m["repositories"][0]["repository_visibility"] = "PRIVATE"
        from scripts.continuous_federation_sync import canonical_bytes, sha256
        m["manifest_sha256"] = sha256(canonical_bytes({k: v for k, v in m.items() if k != "manifest_sha256"}))
        self.write("federation-sync.v1.json", m)
        with self.assertRaisesRegex(ReviewError, "PRIVATE_OR_UNVERIFIED_SOURCE"):
            render_review(self.root, self.out)

    def test_rejects_partial_capture(self):
        m = self.read("federation-sync.v1.json")
        m["decision"] = "PARTIAL_BLOCKED"
        self.write("federation-sync.v1.json", m)
        with self.assertRaisesRegex(ReviewError, "SOURCE_NOT_READY"):
            render_review(self.root, self.out)

    def test_rejects_fixture_stamped_source(self):
        m = self.read("federation-sync.v1.json")
        m["captured_at_utc"] = "FIXTURE_ONLY_NOT_LIVE"
        self.write("federation-sync.v1.json", m)
        with self.assertRaisesRegex(ReviewError, "NONLIVE_SOURCE_TIMESTAMP"):
            render_review(self.root, self.out)

if __name__ == "__main__":
    unittest.main()
