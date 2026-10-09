"""Tests for the read-only repository lifecycle posture audit."""
from __future__ import annotations

import unittest

from scripts.omega_repository_lifecycle_audit import (
    build_report, classify_access_error, flatten_repo_pages, security_features,
)


def repo(name, visibility="public", archived=False, branch="main", owner="fisallllll280-code"):
    return {
        "full_name": f"{owner}/{name}",
        "name": name,
        "owner": {"login": owner},
        "visibility": visibility,
        "private": visibility == "private",
        "archived": archived,
        "default_branch": branch,
        "permissions": {"admin": True, "push": True, "pull": True},
    }


class RepositoryLifecycleAuditTests(unittest.TestCase):
    def test_flatten_pages_deduplicates_by_full_name(self):
        one = repo("alpha")
        result = flatten_repo_pages([[one], [one, repo("beta", "private")]])
        self.assertEqual([item["full_name"] for item in result],
                         ["fisallllll280-code/alpha", "fisallllll280-code/beta"])

    def test_public_private_archive_counts_are_read_only(self):
        report = build_report([repo("public-a"), repo("private-a", "private"), repo("old", archived=True)], None, False)
        self.assertEqual(report["summary"]["repository_count"], 3)
        self.assertEqual(report["summary"]["public_count"], 1)
        self.assertEqual(report["summary"]["private_count"], 1)
        self.assertEqual(report["summary"]["archived_count"], 1)
        self.assertEqual(report["summary"]["repositories_modified"], 0)
        self.assertEqual(report["summary"]["repositories_archived_by_tool"], 0)
        self.assertEqual(report["mode"], "READ_ONLY_AUDIT")

    def test_owner_filter_does_not_mix_organizations(self):
        report = build_report([repo("one", owner="owner-a"), repo("two", owner="owner-b")], "owner-a", False)
        self.assertEqual(report["summary"]["repository_count"], 1)
        self.assertEqual(report["repositories"][0]["full_name"], "owner-a/one")

    def test_settings_are_unknown_when_not_requested(self):
        report = build_report([repo("alpha")], None, False)
        self.assertEqual(report["repositories"][0]["branch_protection"]["state"], "NOT_CHECKED")
        self.assertEqual(report["repositories"][0]["repository_rulesets"]["state"], "NOT_CHECKED")

    def test_permission_errors_remain_unknown_not_proven_unprotected(self):
        self.assertEqual(classify_access_error("HTTP 403 forbidden", 1), "UNKNOWN_INSUFFICIENT_PERMISSION")
        self.assertEqual(classify_access_error("HTTP 404 not found", 1), "NOT_FOUND_OR_NOT_CONFIGURED")
        self.assertEqual(classify_access_error(None, 0), "READABLE")

    def test_missing_security_fields_are_not_reported_as_enabled(self):
        self.assertEqual(security_features(repo("alpha")), {"state": "NOT_EXPOSED_BY_API", "features": {}})
        value = repo("beta")
        value["security_and_analysis"] = {"secret_scanning": {"status": "enabled"}}
        self.assertEqual(security_features(value)["features"]["secret_scanning"], "enabled")


if __name__ == "__main__":
    unittest.main()
