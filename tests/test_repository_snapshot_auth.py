"""Tests for safe Git HTTP authentication in federation snapshot capture."""
from __future__ import annotations

import base64
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.capture_repository_snapshots import clone_repository


class RepositorySnapshotAuthTests(unittest.TestCase):
    @patch("scripts.capture_repository_snapshots.run")
    def test_clone_uses_basic_auth_header_without_secret_in_process_arguments(self, mock_run):
        with patch.dict(
            os.environ,
            {
                "VAIXLNS_FEDERATION_TOKEN": "federation-test-token",
                "GITHUB_TOKEN": "fallback-token",
            },
            clear=False,
        ):
            clone_repository("owner/repo", Path("/tmp/source-repo"))

        args, kwargs = mock_run.call_args
        self.assertEqual(
            args,
            (
                "git", "clone", "--depth", "1",
                "https://github.com/owner/repo.git", "/tmp/source-repo",
            ),
        )
        self.assertNotIn("federation-test-token", " ".join(args))
        env = kwargs["extra_env"]
        self.assertEqual(env["GIT_CONFIG_COUNT"], "1")
        self.assertEqual(env["GIT_CONFIG_KEY_0"], "http.https://github.com/.extraheader")
        value = env["GIT_CONFIG_VALUE_0"]
        self.assertTrue(value.startswith("AUTHORIZATION: basic "))
        encoded = value.removeprefix("AUTHORIZATION: basic ")
        decoded = base64.b64decode(encoded).decode("utf-8")
        self.assertEqual(decoded, "x-access-token:federation-test-token")

    @patch("scripts.capture_repository_snapshots.run")
    def test_clone_without_token_uses_anonymous_git_request(self, mock_run):
        with patch.dict(
            os.environ,
            {"VAIXLNS_FEDERATION_TOKEN": "", "GITHUB_TOKEN": ""},
            clear=False,
        ):
            clone_repository("owner/public-repo", Path("/tmp/public-repo"))

        args, kwargs = mock_run.call_args
        self.assertEqual(
            args,
            (
                "git", "clone", "--depth", "1",
                "https://github.com/owner/public-repo.git", "/tmp/public-repo",
            ),
        )
        self.assertNotIn("extra_env", kwargs)


if __name__ == "__main__":
    unittest.main()
