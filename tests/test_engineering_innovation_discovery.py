import json
import unittest
from unittest.mock import patch

from tools.engineering_innovation_discovery import (
    candidate_terms,
    classify,
    collect,
    render_markdown,
    request_json,
    validate_manifest,
)


def source_manifest():
    return {
        "schema_id": "TEST.SOURCES",
        "schema_version": "1",
        "sources": [{
            "id": "ENG-TEST",
            "provider": "github",
            "repository": "sample/solver",
            "domain": "MESH_FEA",
            "official_url": "https://example.org",
            "repository_url": "https://github.com/sample/solver",
            "focus": ["mesh", "finite element", "optimization"],
            "integration_role": "test role",
            "priority": "P1",
        }],
    }


def snapshot(release="v1.0.0", sha="abc123", license_id="MIT"):
    return {
        "provider": "github",
        "slug": "sample/solver",
        "repository_url": "https://github.com/sample/solver",
        "description": "Finite element mesh solver",
        "homepage": "https://example.org",
        "default_branch": "main",
        "pushed_at": "2026-10-01T00:00:00Z",
        "updated_at": "2026-10-01T00:00:00Z",
        "stars": 20,
        "forks": 3,
        "archived": False,
        "license_spdx": license_id,
        "topics": ["engineering"],
        "latest_release_tag": release,
        "latest_release_published_at": "2026-10-01T00:00:00Z",
        "head_sha": sha,
        "recent_releases": [{
            "tag": release,
            "name": "Mesh solver release",
            "published_at": "2026-10-01T00:00:00Z",
            "url": "https://github.com/sample/solver/releases/tag/" + release,
            "body": "Improved mesh quality and optimization performance.",
            "prerelease": False,
        }],
        "recent_commits": [{
            "sha": sha, "title": "Improve finite element solver",
            "committed_at": "2026-10-01T00:00:00Z",
            "url": "https://github.com/sample/solver/commit/" + sha,
        }],
    }


class FakeResponse:
    def __init__(self, obj):
        self.body = json.dumps(obj).encode()
    def read(self, size=-1):
        return self.body[:size]
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        return False


class FakeOpener:
    def __init__(self, obj):
        self.obj = obj
        self.request = None
        self.timeout = None
    def __call__(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return FakeResponse(self.obj)


class EngineeringDiscoveryTests(unittest.TestCase):
    def test_manifest_rejects_duplicate_ids_and_untrusted_gitlab_host(self):
        manifest = source_manifest()
        manifest["sources"].append(dict(manifest["sources"][0]))
        with self.assertRaises(ValueError):
            validate_manifest(manifest)

        manifest = source_manifest()
        manifest["sources"][0] = {
            "id": "BAD", "provider": "gitlab", "host": "attacker.invalid",
            "project_path": "group/project",
        }
        with self.assertRaises(ValueError):
            validate_manifest(manifest)

    def test_delta_classifier_detects_release_commit_license_and_no_change(self):
        prior = snapshot()
        self.assertEqual(classify(snapshot("v1.0.0", "abc123"), prior)[0], "NO_CHANGE_OBSERVED")
        changed_release = classify(snapshot("v1.1.0", "def456"), prior)
        self.assertEqual(changed_release[0], "NEW_RELEASE_SIGNAL")
        self.assertIn("HEAD_COMMIT_CHANGED", changed_release[2])
        self.assertEqual(classify(snapshot("v1.0.0", "def456"), prior)[0], "SOURCE_ACTIVITY_CHANGED")
        self.assertEqual(classify(snapshot("v1.0.0", "abc123", "Apache-2.0"), prior)[0],
                         "SOURCE_POLICY_OR_BRANCH_CHANGE")

    def test_collect_builds_evidence_linked_report_and_delta(self):
        manifest = source_manifest()
        baseline = {
            "source_snapshots": [{
                **snapshot("v1.0.0", "abc123"),
                "source_id": "ENG-TEST",
                "fetch_status": "SUCCESS",
            }]
        }
        def fetch(_source, _timeout):
            return snapshot("v1.1.0", "def456")
        report = collect(manifest, baseline=baseline, fetchers={"github": fetch})
        self.assertEqual(report["source_count"], 1)
        self.assertEqual(report["successful_source_count"], 1)
        item = report["findings"][0]
        self.assertEqual(item["state"], "NEW_RELEASE_SIGNAL")
        self.assertTrue(item["review_required"])
        self.assertEqual(item["repository_url"], "https://github.com/sample/solver")
        self.assertIn("mesh", item["engineering_terms"])
        rendered = render_markdown(report)
        self.assertIn("NEW_RELEASE_SIGNAL", rendered)
        self.assertIn("https://github.com/sample/solver/releases/tag/v1.1.0", rendered)

    def test_collect_records_source_failure_without_aborting_other_sources(self):
        manifest = source_manifest()
        manifest["sources"].append({
            "id": "ENG-TEST-2", "provider": "gitlab", "host": "gitlab.com",
            "project_path": "group/project", "domain": "CFD_MULTIPHYSICS",
            "official_url": "https://example.org", "repository_url": "https://gitlab.com/group/project",
            "focus": [], "priority": "P2",
        })
        def fetch_github(_source, _timeout):
            return snapshot()
        def fetch_gitlab(_source, _timeout):
            raise RuntimeError("HTTP_503")
        report = collect(manifest, fetchers={"github": fetch_github, "gitlab": fetch_gitlab})
        self.assertEqual(report["successful_source_count"], 1)
        self.assertEqual(report["failed_source_count"], 1)
        failed = [x for x in report["findings"] if x["source_id"] == "ENG-TEST-2"][0]
        self.assertEqual(failed["state"], "SOURCE_FETCH_FAILED")

    def test_gitlab_token_is_not_sent_to_external_gitlab_instance(self):
        opener = FakeOpener({"ok": True})
        request_json(
            "https://gitlab.onelab.info/api/v4/projects/gmsh%2Fgmsh",
            "gitlab", 2.0, opener=opener,
            environ={"GITLAB_TOKEN": "gitlab-com-secret"},
        )
        self.assertIsNone(opener.request.get_header("Private-token"))
        self.assertEqual(opener.request.get_method(), "GET")
        self.assertLessEqual(opener.timeout, 20.0)

    def test_candidate_terms_are_triage_terms_not_claims(self):
        found = candidate_terms(
            {"focus": ["mesh", "geometry"]},
            {"description": "parallel finite element solver", "recent_releases": [], "recent_commits": []},
        )
        self.assertIn("mesh", found)
        self.assertIn("geometry", found)
        self.assertIn("solver", found)


if __name__ == "__main__":
    unittest.main()
