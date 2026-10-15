"""Tests for safe Git HTTP authentication in the federation snapshot capture."""
from __future__ import annotations

import base64
import os
from pathlib import Path
from unittest.mock import patch

from scripts.capture_repository_snapshots import clone_repository


@patch("scripts.capture_repository_snapshots.run")
def test_clone_uses_basic_auth_header_without_secret_in_process_arguments(mock_run):
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
    assert args == (
        "git", "clone", "--depth", "1",
        "https://github.com/owner/repo.git", "/tmp/source-repo",
    )
    assert "federation-test-token" not in " ".join(args)
    env = kwargs["extra_env"]
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GIT_CONFIG_COUNT"] == "1"
    assert env["GIT_CONFIG_KEY_0"] == "http.https://github.com/.extraheader"
    value = env["GIT_CONFIG_VALUE_0"]
    scheme, encoded = value.split(" ", 1)
    assert scheme == "AUTHORIZATION:"
    auth_scheme, payload = encoded.split(" ", 1)
    assert auth_scheme.lower() == "basic"
    decoded = base64.b64decode(payload).decode("utf-8")
    assert decoded == "x-access-token:federation-test-token"


@patch("scripts.capture_repository_snapshots.run")
def test_clone_without_token_uses_anonymous_git_request(mock_run):
    with patch.dict(os.environ, {"VAIXLNS_FEDERATION_TOKEN": "", "GITHUB_TOKEN": ""}, clear=False):
        clone_repository("owner/public-repo", Path("/tmp/public-repo"))

    args, kwargs = mock_run.call_args
    assert args == (
        "git", "clone", "--depth", "1",
        "https://github.com/owner/public-repo.git", "/tmp/public-repo",
    )
    assert "extra_env" not in kwargs
