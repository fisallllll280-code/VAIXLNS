#!/usr/bin/env python3
"""VAIXLNS perpetual repository pulse.

Creates only repositories explicitly listed with auto_create=true in the
repository factory manifest. Requires VAIXLNS_REPO_ADMIN_TOKEN for repository
creation. With no admin token, the pulse remains a read-only audit.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"

def api(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "VAIXLNS-repository-pulse/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}

def load_manifest() -> dict:
    path = (
        Path(__file__).resolve().parents[1]
        / 'registry'
        / 'repository-orchestration'
        / 'REPOSITORY_FACTORY_MANIFEST_V1.json'
    )
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    token = os.getenv("VAIXLNS_REPO_ADMIN_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print("READ_ONLY: no GitHub admin token configured")
        return 0

    manifest = load_manifest()
    owner = manifest["owner"]

    try:
        existing = api("GET", "/user/repos?per_page=100&type=owner", token)
    except urllib.error.HTTPError as exc:
        print(f"ERROR: unable to inventory repositories: HTTP {exc.code}")
        return 2

    existing_names = {item["name"] for item in existing if item.get("owner", {}).get("login") == owner}

    created = []
    present = []

    for spec in manifest["repositories"]:
        name = spec["name"]
        if name in existing_names:
            present.append(name)
            continue
        if not spec.get("auto_create", False):
            print(f"SKIP: {name} is not approved for automatic creation")
            continue

        payload = {
            "name": name,
            "description": spec.get("description", ""),
            "private": manifest["policy"].get("default_visibility") == "private",
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False,
            "auto_init": True,
        }
        try:
            api("POST", "/user/repos", token, payload)
            created.append(name)
            print(f"CREATED: {owner}/{name}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"ERROR: create {name}: HTTP {exc.code}: {body[:400]}")
            return 3

    print(json.dumps({"present": present, "created": created}, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())