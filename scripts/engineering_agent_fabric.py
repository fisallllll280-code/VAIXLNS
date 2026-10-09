#!/usr/bin/env python3
"""Inspect a project and build an evidence-gated engineering-agent execution plan.

This tool inventories and classifies artifacts, proposes specialist work packets,
and discovers conservative build/test recipes. It never executes project code
unless an explicit approval manifest is supplied; even then, only built-in
allowlisted recipes can run, without shell=True, with a timeout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SCHEMA = "vaixlns.engineering-agent-fabric.v1"
IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build", "target", ".next", ".vaixl_ns"}
IGNORE_FILES = {"omega-research-results.json", "engineering-execution-plan.json", "engineering-execution-receipt.json", "innovation-network.json", "conformance-evidence.txt"}
AGENTS = (
    ("PROJECT_ARCHAEOLOGY", "Reconstruct the project structure, entry points, and historical boundaries.", ("repository_inventory.json", "entrypoints.json")),
    ("REQUIREMENTS_RECOVERY", "Extract explicit requirements, implicit assumptions, constraints, and acceptance criteria.", ("requirements.json", "unknowns.json")),
    ("CANON_AND_PROVENANCE", "Preserve source identity, immutable references, hashes, and canonical-versus-projection boundaries.", ("provenance.json", "lineage.json")),
    ("SEMANTIC_MODELING", "Extract domain concepts, entities, interfaces, state machines, and invariants.", ("domain_model.json", "interface_map.json")),
    ("REVERSE_ENGINEERING", "Infer behavior only from inspectable evidence; separate observation from inference.", ("behavior_map.json", "inference_register.json")),
    ("DEPENDENCY_AND_BUILD", "Identify languages, dependencies, build tools, test runners, and reproducible setup requirements.", ("dependency_map.json", "build_recipes.json")),
    ("IMPLEMENTATION_ENGINEER", "Turn accepted requirements into the smallest reviewable implementation change.", ("patch_plan.json", "implementation_diff")),
    ("TEST_AND_REPLAY", "Create regression, boundary, negative, determinism, and replay tests.", ("test_plan.json", "replay_instructions.json")),
    ("SECURITY_ADVERSARY", "Inspect trust boundaries, secrets exposure, unsafe execution, permissions, and misuse paths.", ("threat_model.json", "security_findings.json")),
    ("PERFORMANCE_AND_COST", "Identify measurable latency, memory, throughput, reliability, and cost constraints.", ("benchmark_plan.json", "cost_model.json")),
    ("INDEPENDENT_VERIFIER", "Try to falsify claims and independently reproduce the result using pinned inputs.", ("verification_report.json", "counterevidence.json")),
    ("RELEASE_AND_RECOVERY", "Prepare rollback, migration, release evidence, and recovery steps.", ("release_plan.json", "rollback_plan.json")),
    ("FEDERATED_RESEARCH_AND_INDEX", "Retrieve evidence from configured public sources and approved server adapters; preserve citations, source identities, normalized hashes, confidence boundaries, and unanswered research gaps.", ("source_evidence.json", "omega_index_delta.json")),
)
# Exact argument vectors only. No arbitrary shell strings or discovered scripts are executed.
RECIPES = {
    "python-unittest": ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
    "python-pytest": ["python", "-m", "pytest", "-q"],
    "cargo-workspace-test": ["cargo", "test", "--workspace"],
    "go-test-all": ["go", "test", "./..."],
}
RECIPE_DETECTION = (
    ("python-unittest", lambda names: "tests" in names and any(p.endswith(".py") for p in names)),
    ("python-pytest", lambda names: "pytest.ini" in names or "pyproject.toml" in names or "conftest.py" in names),
    ("cargo-workspace-test", lambda names: "Cargo.toml" in names),
    ("go-test-all", lambda names: "go.mod" in names),
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def git_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def inventory(root: Path) -> list[dict[str, Any]]:
    rows = []
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS and not (Path(current) / d).is_symlink())
        for filename in sorted(files):
            path = Path(current) / filename
            if path.is_symlink() or not path.is_file() or filename in IGNORE_FILES:
                continue
            relative = path.relative_to(root).as_posix()
            try:
                raw = path.read_bytes()
            except OSError:
                continue
            suffix = path.suffix.lower()
            category = (
                "TEST" if "test" in path.parts or filename.startswith("test_") or ".test." in filename
                else "CONFIG" if filename.lower() in {"pyproject.toml", "package.json", "cargo.toml", "go.mod", "makefile", "dockerfile", "justfile"}
                else "DOCUMENTATION" if suffix in {".md", ".rst", ".adoc"}
                else "SOURCE" if suffix in {".py", ".rs", ".go", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift", ".kt"}
                else "SCHEMA_OR_DATA" if suffix in {".json", ".yaml", ".yml", ".toml", ".xml", ".sql"}
                else "OTHER"
            )
            rows.append({"path": relative, "bytes": len(raw), "sha256": sha256_bytes(raw), "category": category})
    return sorted(rows, key=lambda row: row["path"])



def load_research_context(root: Path) -> dict[str, Any]:
    """Bind a prior Ω Research Fabric result to this execution plan without treating it as proof."""
    artifact = root / "omega-research-results.json"
    if not artifact.is_file():
        return {"state": "NOT_AVAILABLE", "artifact": artifact.name, "verified": False}
    try:
        payload = json.loads(artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"state": "UNREADABLE", "artifact": artifact.name, "verified": False}
    if not isinstance(payload, dict) or payload.get("schema") != "vaixlns.omega-research-fabric.v1":
        return {"state": "SCHEMA_MISMATCH", "artifact": artifact.name, "verified": False}
    claimed = payload.get("result_sha256")
    core = {key: value for key, value in payload.items() if key != "result_sha256"}
    integrity_ok = bool(claimed) and claimed == sha256_value(core)
    return {
        "state": "PRESENT_HASH_VALID" if integrity_ok else "HASH_MISMATCH",
        "artifact": artifact.name,
        "result_sha256": claimed,
        "inventory_sha256": (payload.get("index") or {}).get("inventory_sha256"),
        "query": payload.get("query", ""),
        "local_result_count": len(payload.get("local_results", [])),
        "remote_discovery_count": len(payload.get("remote_discoveries", [])),
        "provider_status": [
            {"provider": item.get("provider"), "state": item.get("state"), "count": item.get("count", 0)}
            for item in payload.get("provider_status", []) if isinstance(item, dict)
        ],
        "server_status": [
            {"server_id": item.get("server_id"), "state": item.get("state"), "result_count": len(item.get("results", []))}
            for item in payload.get("server_status", []) if isinstance(item, dict)
        ],
        "remote_discoveries_remain_unverified": True,
        "verified": integrity_ok,
    }


def build_plan(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files = inventory(root)
    names = {Path(row["path"]).name for row in files}
    candidates = []
    for recipe_id, detector in RECIPE_DETECTION:
        if detector(names):
            candidates.append({
                "recipe_id": recipe_id,
                "argv": RECIPES[recipe_id],
                "detected_by": "FILE_PRESENCE_HEURISTIC",
                "state": "CANDIDATE_NOT_EXECUTED",
                "approval_required": True,
                "timeout_seconds": 600,
            })
    if not candidates:
        candidates.append({
            "recipe_id": "manual-build-discovery",
            "argv": [],
            "detected_by": "NO_KNOWN_RECIPE_MATCHED",
            "state": "MANUAL_DISCOVERY_REQUIRED",
            "approval_required": True,
            "timeout_seconds": 0,
        })
    agents = []
    for sequence, (agent_id, mission, outputs) in enumerate(AGENTS, start=1):
        agents.append({
            "agent_id": agent_id,
            "task_id": "ENG-" + hashlib.sha256((agent_id + sha256_value(files)).encode()).hexdigest()[:16].upper(),
            "sequence": sequence,
            "mission": mission,
            "required_outputs": list(outputs),
            "input_scope": "REPOSITORY_INVENTORY_AND_PINNED_REFERENCES",
            "state": "PLANNED_NOT_DISPATCHED",
            "authority": "ANALYZE_AND_RECOMMEND_ONLY",
            "acceptance": "Cite file paths and hashes; distinguish observed facts, inference, unknowns, and proposals.",
        })
    core = {
        "schema": SCHEMA,
        "project_root_name": root.name,
        "repository_revision": git_revision(root),
        "inventory_sha256": sha256_value(files),
        "summary": {
            "file_count": len(files),
            "source_count": sum(row["category"] == "SOURCE" for row in files),
            "test_count": sum(row["category"] == "TEST" for row in files),
            "agent_specialist_count": len(agents),
            "build_recipe_candidates": len(candidates),
            "agents_dispatched": 0,
            "commands_executed": 0,
            "runtime_verified": False,
        },
        "agents": agents,
        "artifacts": files,
        "research_context": load_research_context(root),
        "execution_candidates": candidates,
        "execution_gate": {
            "default": "BLOCKED_UNTIL_EXPLICIT_APPROVAL",
            "requires": ["pinned_repository_revision", "exact_allowlisted_recipe_id", "approval_record", "timeout", "captured_exit_code_and_logs"],
            "shell_execution": "PROHIBITED",
            "arbitrary_generated_code_execution": "PROHIBITED",
            "production_effects": "PROHIBITED",
            "claim_rule": "Only a captured successful run can support a runtime-verified claim, and only for that exact revision and command.",
        },
    }
    return {**core, "plan_sha256": sha256_value(core)}


def execute_approved(root: Path, plan: dict[str, Any], approval_path: Path) -> dict[str, Any]:
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    expected_revision = plan.get("repository_revision")
    if not expected_revision or approval.get("repository_revision") != expected_revision:
        raise ValueError("approval repository_revision must exactly match the inspected git HEAD")
    approver = str(approval.get("authorized_by") or "").strip()
    approval_ref = str(approval.get("approval_ref") or "").strip()
    if not approver or not approval_ref:
        raise ValueError("approval requires non-empty authorized_by and approval_ref")
    requested = approval.get("recipe_ids")
    if not isinstance(requested, list) or not requested:
        raise ValueError("approval recipe_ids must be a non-empty array")
    known = {candidate["recipe_id"]: candidate for candidate in plan["execution_candidates"]}
    results = []
    for recipe_id in requested:
        if recipe_id not in RECIPES or recipe_id not in known or not known[recipe_id]["argv"]:
            raise ValueError(f"recipe is not a detected built-in allowlisted candidate: {recipe_id}")
        argv = RECIPES[recipe_id]
        started = time.monotonic()
        try:
            proc = subprocess.run(
                argv, cwd=root, capture_output=True, text=True, timeout=600,
                shell=False, check=False,
                env={"PATH": os.environ.get("PATH", ""), "HOME": str(Path.home()), "CI": "1", "PYTHONNOUSERSITE": "1"},
            )
            result = {
                "recipe_id": recipe_id, "argv": argv, "exit_code": proc.returncode,
                "stdout": proc.stdout[-20000:], "stderr": proc.stderr[-20000:],
                "duration_seconds": round(time.monotonic() - started, 3),
                "state": "EXECUTION_PASSED" if proc.returncode == 0 else "EXECUTION_FAILED",
            }
        except subprocess.TimeoutExpired as exc:
            result = {
                "recipe_id": recipe_id, "argv": argv, "exit_code": None,
                "stdout": str(exc.stdout or "")[-20000:], "stderr": str(exc.stderr or "")[-20000:],
                "duration_seconds": round(time.monotonic() - started, 3), "state": "EXECUTION_TIMED_OUT",
            }
        results.append(result)
        if result["state"] != "EXECUTION_PASSED":
            break
    core = {
        "schema": "vaixlns.engineering-execution-receipt.v1",
        "repository_revision": expected_revision,
        "plan_sha256": plan["plan_sha256"],
        "approval": {"authorized_by": approver, "approval_ref": approval_ref, "approval_sha256": sha256_bytes(approval_path.read_bytes())},
        "results": results,
        "summary": {
            "commands_requested": len(requested),
            "commands_run": len(results),
            "all_passed": bool(results) and all(item["state"] == "EXECUTION_PASSED" for item in results) and len(results) == len(requested),
            "runtime_verified": bool(results) and all(item["state"] == "EXECUTION_PASSED" for item in results) and len(results) == len(requested),
        },
    }
    return {**core, "receipt_sha256": sha256_value(core)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root to inspect")
    parser.add_argument("--output", default="engineering-execution-plan.json")
    parser.add_argument("--execute-approved", help="Run detected built-in recipes listed in an explicit approval JSON")
    parser.add_argument("--receipt", default="engineering-execution-receipt.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"project root is not a directory: {root}")
    try:
        plan = build_plan(root)
        Path(args.output).write_text(json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"plan": args.output, "plan_sha256": plan["plan_sha256"], "files": plan["summary"]["file_count"], "agents": plan["summary"]["agent_specialist_count"], "candidate_recipes": plan["summary"]["build_recipe_candidates"], "execution": "NOT_EXECUTED"}, sort_keys=True))
        if args.execute_approved:
            receipt = execute_approved(root, plan, Path(args.execute_approved))
            Path(args.receipt).write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"receipt": args.receipt, **receipt["summary"]}, sort_keys=True))
            return 0 if receipt["summary"]["all_passed"] else 2
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
