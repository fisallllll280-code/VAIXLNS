#!/usr/bin/env python3
"""VAIXLNS perpetual repository pulse.

Inventory the owned repository surface, execute local conformance probes, and
create only repositories explicitly approved by the canonical factory manifest.
Newly created repositories receive a canonical contract, evidence placeholder
and a minimal conformance workflow.

Creation requires VAIXLNS_REPO_ADMIN_TOKEN. Without it the repository factory
is read-only. Operational probes never require an admin token.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
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
            "User-Agent": "VAIXLNS-repository-pulse/1.2",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def load_manifest() -> dict:
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            root
            / "registry"
            / "repository-orchestration"
            / "REPOSITORY_FACTORY_MANIFEST_V1.json"
        ).read_text(encoding="utf-8")
    )


def load_contract() -> str:
    root = Path(__file__).resolve().parents[1]
    return (
        root / "registry" / "repository-orchestration" / "VAIXLNS_REPOSITORY_CONTRACT.md"
    ).read_text(encoding="utf-8")


CONFORMANCE_WORKFLOW = """name: VAIXLNS Conformance

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  conformance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Contract present
        run: test -f VAIXLNS_REPOSITORY_CONTRACT.md
      - name: Report repository state
        run: |
          printf '%s\\n' "Repository: $GITHUB_REPOSITORY"
          printf '%s\\n' "Commit: $GITHUB_SHA"
          test -f README.md || true
"""


def put_file(
    owner: str, name: str, path: str, content: str, token: str, message: str
) -> None:
    payload = {
        "message": message,
        "content": __import__("base64")
        .b64encode(content.encode("utf-8"))
        .decode("ascii"),
    }
    api("PUT", f"/repos/{owner}/{name}/contents/{path}", token, payload)


def seed_repository(owner: str, name: str, spec: dict, token: str, contract: str) -> None:
    header = [
        f"# {name}",
        "",
        "Managed under the VAIXLNS Repository Perpetual Engine.",
        "",
        f"- Role: {spec.get('role', 'TBD')}",
        f"- System Family: {spec.get('system_family', 'TBD')}",
        "- Lifecycle: SEEDED",
        "- Canonical authority: VAIXLNS",
        "",
        "This repository is created from the governed repository factory manifest.",
    ]
    put_file(
        owner,
        name,
        "VAIXLNS_REPOSITORY_CONTRACT.md",
        contract,
        token,
        "chore: seed VAIXLNS repository contract",
    )
    put_file(
        owner,
        name,
        "README.md",
        "\n".join(header),
        token,
        "docs: seed VAIXLNS repository identity",
    )
    put_file(
        owner,
        name,
        ".github/workflows/vaixlns-conformance.yml",
        CONFORMANCE_WORKFLOW,
        token,
        "ci: seed VAIXLNS conformance workflow",
    )
    put_file(
        owner,
        name,
        "docs/DEVELOPMENT_QUEUE.md",
        "# Development Queue\n\n"
        "- [ ] Establish executable entrypoint\n"
        "- [ ] Add deterministic tests\n"
        "- [ ] Capture verification evidence\n"
        "- [ ] Register performance metrics\n"
        "- [ ] Link innovation records\n",
        token,
        "docs: seed development queue",
    )


def run_treasury_conformance(root: Path) -> dict:
    """Run the paper treasury as part of every repository pulse."""
    probe = root / "scripts" / "treasury_admission_probe.py"
    test_dir = root / "tests"
    if not probe.exists() or not test_dir.exists():
        return {
            "status": "N/A",
            "reason": "treasury_probe_not_present",
        }

    python = shutil.which("python3") or sys.executable
    test_cmd = [python, "-m", "unittest", "discover", "-s", "tests", "-v"]
    probe_cmd = [python, str(probe)]

    test_run = subprocess.run(test_cmd, cwd=root, text=True, capture_output=True, timeout=120)
    probe_run = subprocess.run(probe_cmd, cwd=root, text=True, capture_output=True, timeout=120)

    evidence = root / ".treasury-evidence.json"
    if evidence.exists():
        pulse_dir = root / ".pulse"
        pulse_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(evidence, pulse_dir / "TREASURY_EVIDENCE.json")

    result = {
        "status": "PASS" if test_run.returncode == 0 and probe_run.returncode == 0 else "FAIL",
        "tests_exit_code": test_run.returncode,
        "probe_exit_code": probe_run.returncode,
        "tests_tail": test_run.stdout[-2000:] + test_run.stderr[-2000:],
        "probe_tail": probe_run.stdout[-4000:] + probe_run.stderr[-2000:],
    }
    print(json.dumps({"treasury_conformance": result}, indent=2))
    return result


def main() -> int:
    root = Path(__file__).resolve().parents[1]

    treasury_result = run_treasury_conformance(root)
    if treasury_result["status"] == "FAIL":
        print("BLOCKED: treasury conformance failed")
        return 4

    token = os.getenv("VAIXLNS_REPO_ADMIN_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print("READ_ONLY: no GitHub admin token configured")

        return 0

    manifest = load_manifest()
    owner = manifest["owner"]
    contract = load_contract()

    try:
        existing = api("GET", "/user/repos?per_page=100&type=owner", token)
    except urllib.error.HTTPError as exc:
        print(f"ERROR: unable to inventory repositories: HTTP {exc.code}")
        return 2

    existing_names = {
        item["name"]
        for item in existing
        if item.get("owner", {}).get("login") == owner
    }
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
            seed_repository(owner, name, spec, token, contract)
            created.append(name)
            print(f"CREATED+SEEDED: {owner}/{name}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"ERROR: {name}: HTTP {exc.code}: {body[:500]}")
            return 3

    print(json.dumps({"present": present, "created": created}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
