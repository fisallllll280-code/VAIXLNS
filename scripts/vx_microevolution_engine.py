#!/usr/bin/env python3
"""Read-only, deterministic micro-evolution opportunity scanner for VAIXLNS.

This tool inventories source files and emits evidence-backed candidate improvements.
It does not edit source files, install dependencies, execute project code, or approve changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone
from typing import Any

VERSION = "0.1.0"
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".next", ".cache", "target"}
SKIP_NAMES = {".env", ".env.local", ".env.production", "credentials.json", "id_rsa", "id_ed25519"}
SKIP_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
TEXT_SUFFIXES = {".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml", ".toml", ".md", ".sh", ".sql"}
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_FILES = 20000


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=3, check=False,
        )
        value = result.stdout.strip()
        return value if result.returncode == 0 and value else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def discover_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(names):
            path = Path(current) / name
            if name in SKIP_NAMES or path.suffix.lower() in SKIP_SUFFIXES:
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                if path.is_symlink() or path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            found.append(path)
            if len(found) >= MAX_FILES:
                return found
    return found


def classify_file(path: Path, root: Path, data: bytes) -> dict[str, Any]:
    rel = path.relative_to(root).as_posix()
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    suffix = path.suffix.lower()
    role = (
        "test" if "/test" in "/" + rel.lower() or rel.lower().startswith("test") or "test_" in path.name.lower()
        else "documentation" if suffix == ".md"
        else "manifest" if path.name.lower() in {"pyproject.toml", "cargo.toml", "package.json", "requirements.txt", "go.mod"}
        else "source" if suffix in {".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".sh", ".sql"}
        else "configuration"
    )
    return {
        "path": rel,
        "role": role,
        "bytes": len(data),
        "lines": len(lines),
        "sha256": sha256_bytes(data),
        "has_todo_marker": any(token in text.lower() for token in ("todo", "fixme", "not implemented")),
        "has_test_like_name": "test" in path.name.lower() or "/tests/" in "/" + rel.lower(),
    }


def build_report(root: str | Path, horizon_years: int = 5) -> dict[str, Any]:
    base = Path(root).expanduser().resolve()
    if not base.is_dir():
        raise ValueError(f"root is not a directory: {base}")
    if horizon_years not in (1, 3, 5):
        raise ValueError("horizon_years must be 1, 3, or 5")

    files = discover_files(base)
    inventory: list[dict[str, Any]] = []
    for path in files:
        try:
            data = path.read_bytes()
        except OSError:
            continue
        inventory.append(classify_file(path, base, data))

    tests = [item for item in inventory if item["role"] == "test"]
    source = [item for item in inventory if item["role"] == "source"]
    docs = [item for item in inventory if item["role"] == "documentation"]
    manifests = [item for item in inventory if item["role"] == "manifest"]
    findings: list[dict[str, Any]] = []

    def add(candidate_id: str, title: str, category: str, impact: int, effort: int,
            confidence: str, rationale: str, evidence: list[dict[str, str]],
            horizon: int, next_step: str) -> None:
        score = round((impact * 2 + (6 - effort) + (2 if confidence == "high" else 1)) / 3, 2)
        findings.append({
            "id": candidate_id, "title": title, "category": category,
            "impact_1_to_5": impact, "effort_1_to_5": effort,
            "priority_score_1_to_5": min(5.0, score), "confidence": confidence,
            "rationale": rationale, "evidence": evidence,
            "horizon_years": horizon, "next_step": next_step,
            "status": "PROPOSAL_NOT_IMPLEMENTED",
        })

    if source and not tests:
        add("MX-TEST-001", "Introduce a minimal regression test seam",
            "testability", 5, 2, "medium",
            "Source files were found but no test-role files were detected by the scanner; validate the inventory before adding tests.",
            [{"kind": "inventory", "value": f"{len(source)} source files; 0 test-role files detected"}],
            1, "Identify the smallest deterministic, side-effect-free function and add a focused test.")
    todo_files = [x for x in inventory if x["has_todo_marker"]]
    if todo_files:
        sample = todo_files[:10]
        add("MX-TODO-001", "Triage unfinished-work markers",
            "reliability", 3, 1, "medium",
            "Markers can indicate unfinished work but can also be historical examples; each match requires human triage.",
            [{"kind": "file", "value": f"{x['path']} (sha256={x['sha256']})"} for x in sample],
            1, "Review each cited line and classify as active defect, accepted limitation, or historical text.")
    if manifests:
        unpinned = [x for x in manifests if x["path"].endswith(("requirements.txt", "package.json", "pyproject.toml", "Cargo.toml".lower(), "go.mod"))]
        if unpinned:
            add("MX-DEP-001", "Verify dependency reproducibility and lifecycle",
                "dependency-health", 4, 2, "low",
                "Manifest presence is not evidence of unsafe or outdated dependencies; establish lockfile, version, license, and support-policy status before recommending upgrades.",
                [{"kind": "manifest", "value": f"{x['path']} (sha256={x['sha256']})"} for x in unpinned[:10]],
                min(horizon_years, 3), "Check lockfiles and supported-version policies in a controlled, network-enabled dependency audit.")
    if docs and source:
        add("MX-TRACE-001", "Bind key implementation claims to executable evidence",
            "traceability", 4, 2, "medium",
            "Both documentation and source are present; a file inventory alone cannot determine whether claims map to tests or runtime evidence.",
            [{"kind": "inventory", "value": f"{len(docs)} documentation files; {len(source)} source files"}],
            3, "Select one high-value documented capability and map claim → entry point → test → reproducible evidence.")
    if horizon_years >= 3:
        add("MX-COMPAT-001", "Establish a compatibility baseline for long-lived interfaces",
            "future-compatibility", 4, 2, "low",
            "Long-horizon resilience is best tracked through explicit interface versions and compatibility tests; no future failure is predicted by this scan.",
            [{"kind": "scope", "value": f"requested planning horizon: {horizon_years} years"}],
            horizon_years, "Inventory public schemas and API contracts, then add backward-compatibility fixtures for one critical interface.")

    findings.sort(key=lambda item: (-item["priority_score_1_to_5"], item["effort_1_to_5"], item["id"]))
    return {
        "schema_version": "vx.microevolution.report.v1",
        "engine_version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(base),
        "git_revision": git_revision(base),
        "mode": "READ_ONLY_INVENTORY_AND_HEURISTIC_PROPOSALS",
        "planning_horizon_years": horizon_years,
        "limits": {
            "max_files": MAX_FILES,
            "max_file_bytes": MAX_FILE_BYTES,
            "inventory_count": len(inventory),
            "inventory_truncated": len(inventory) >= MAX_FILES,
            "runtime_tests_executed": False,
            "network_accessed": False,
            "source_modified": False,
            "automatic_approval": False,
        },
        "summary": {
            "files_scanned": len(inventory),
            "source_files": len(source),
            "test_files": len(tests),
            "documentation_files": len(docs),
            "manifest_files": len(manifests),
            "candidate_count": len(findings),
        },
        "inventory": inventory,
        "candidates": findings,
        "decision_rule": "Candidates are hypotheses, not verified defects. No patch is applied and no candidate is promoted automatically.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root to inspect (default: current directory)")
    parser.add_argument("--horizon-years", type=int, choices=(1, 3, 5), default=5)
    parser.add_argument("--output", help="write JSON report to this path; stdout if omitted")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.root, args.horizon_years)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
