"""Conservative, evidence-producing test selection for VAIXLNS.

Unknown impact maps to the complete unit-test suite. This tool is an accelerator,
not an authority to waive repository-required CI, integration, security, or release gates.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
ALL_TEST_PATTERN = "test_*.py"

# Only known source-to-test dependency boundaries are allowed to use focused routing.
ROUTES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("vcre/**", ("test_vcre_predictive.py", "test_vcre_runtime.py")),
    ("scripts/vcre_probe.py", ("test_vcre_predictive.py", "test_vcre_runtime.py")),
    ("scripts/arcx_vx_bridge.py", ("test_arcx_vx_bridge.py",)),
    ("schemas/arcx-vx-engineering-task.schema.json", ("test_arcx_vx_bridge.py",)),
    ("schemas/arcx-vx-engineering-receipt.schema.json", ("test_arcx_vx_bridge.py",)),
    ("scripts/vx_federation_gate.py", ("test_vx_federation_gate.py",)),
    ("schemas/vx-federation-instance.schema.yaml", ("test_vx_federation_gate.py",)),
    ("scripts/vx_stage_runtime.py", ("test_vx_stage_runtime.py",)),
    ("schemas/vx-stage-evidence.schema.json", ("test_vx_stage_runtime.py",)),
    ("scripts/discovery_router.py", ("test_discovery_router.py", "test_server_discovery_probe.py")),
    ("tools/server_discovery_probe.py", ("test_server_discovery_probe.py",)),
    ("scripts/admission_evaluator.py", ("test_admission_evaluator.py", "test_canonical_control_plane.py")),
    ("scripts/admission_gate.py", ("test_admission_evaluator.py", "test_canonical_control_plane.py")),
    ("scripts/omega_pattern_foundry.py", ("test_omega_pattern_foundry.py",)),
    ("scripts/measure_innovations.py", ("test_innovation_measurement.py", "test_innovation_operation_index.py")),
    ("scripts/build_zero_loss_index.py", ("test_zero_loss_index.py",)),
    ("scripts/treasury_admission_probe.py", ("test_paper_treasury.py",)),
)

ROUTED_TEST_STEMS = {
    "test_vcre_predictive", "test_vcre_runtime",
    "test_arcx_vx_bridge", "test_vx_federation_gate", "test_vx_stage_runtime",
    "test_discovery_router", "test_server_discovery_probe",
    "test_admission_evaluator", "test_canonical_control_plane",
    "test_omega_pattern_foundry", "test_innovation_measurement",
    "test_innovation_operation_index", "test_zero_loss_index", "test_paper_treasury",
}


def _matches(path: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(path, pattern)


def plan_tests(changed_paths: Sequence[str] | None, diff_error: str | None = None) -> dict[str, Any]:
    """Return a conservative plan; unknown or unavailable impact means full suite."""
    normalized = sorted({
        str(path).replace("\\", "/").lstrip("./")
        for path in (changed_paths or []) if str(path).strip()
    })
    if diff_error:
        return {
            "selection_mode": "FULL_SUITE", "test_files": [],
            "changed_files": normalized, "fallback_reason": diff_error,
        }
    if not normalized:
        return {
            "selection_mode": "FULL_SUITE", "test_files": [],
            "changed_files": [], "fallback_reason": "EMPTY_OR_UNAVAILABLE_CHANGE_SET",
        }

    selected: set[str] = set()
    unknown: list[str] = []
    for path in normalized:
        if path.startswith("tests/test_") and path.endswith(".py"):
            stem = path[len("tests/"):-len(".py")]
            if stem not in ROUTED_TEST_STEMS:
                unknown.append(path)
                continue
            selected.add(stem + ".py")
            if stem.startswith("test_vcre_"):
                selected.update(("test_vcre_predictive.py", "test_vcre_runtime.py"))
            continue

        matched = False
        for pattern, targets in ROUTES:
            if _matches(path, pattern):
                selected.update(targets)
                matched = True
        if matched:
            continue
        # Documentation, workflows, schemas, registries and unknown paths are
        # cross-cutting by default. Do not infer that they are low risk.
        unknown.append(path)

    if unknown:
        return {
            "selection_mode": "FULL_SUITE", "test_files": [],
            "changed_files": normalized, "fallback_reason": "UNKNOWN_OR_CROSS_CUTTING_IMPACT",
            "unknown_or_cross_cutting_files": sorted(set(unknown)),
        }
    if not selected:
        return {
            "selection_mode": "FULL_SUITE", "test_files": [],
            "changed_files": normalized, "fallback_reason": "NO_SAFE_TARGET_TEST_MAPPING",
        }
    return {
        "selection_mode": "FOCUSED", "test_files": sorted(selected),
        "changed_files": normalized, "fallback_reason": None,
    }


def changed_files_from_git(base: str | None, head: str | None) -> tuple[list[str] | None, str | None]:
    """Collect names from a three-dot diff; return a reason rather than guess."""
    if not base or not head or set(base) == {"0"} or set(head) == {"0"}:
        return None, "BASE_OR_HEAD_UNAVAILABLE"
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", f"{base}...{head}"],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except OSError as exc:
        return None, f"GIT_DIFF_EXECUTION_FAILED:{type(exc).__name__}"
    if result.returncode != 0:
        return None, f"GIT_DIFF_FAILED:{result.stderr.strip()[:500]}"
    return [line.strip() for line in result.stdout.splitlines() if line.strip()], None


def _run_tests(plan: dict[str, Any]) -> tuple[int, str, float]:
    if plan["selection_mode"] == "FULL_SUITE":
        commands = [[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", ALL_TEST_PATTERN, "-v"]]
    else:
        commands = [
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", filename, "-v"]
            for filename in plan["test_files"]
        ]
    outputs: list[str] = []
    started = time.monotonic()
    code = 0
    for command in commands:
        try:
            result = subprocess.run(
                command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, check=False,
                env={**os.environ, "PYTHONPATH": str(ROOT)},
            )
            outputs.append("$ " + " ".join(command) + "\n" + result.stdout)
            if result.returncode:
                code = result.returncode
                break
        except OSError as exc:
            outputs.append(f"execution_error:{type(exc).__name__}:{exc}")
            code = 127
            break
    return code, "\n".join(outputs), time.monotonic() - started


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="base Git ref/SHA")
    parser.add_argument("--head", help="head Git ref/SHA")
    parser.add_argument("--changed-file", action="append", default=[], help="explicit changed path; repeat as needed")
    parser.add_argument("--output", default=".engineering-test-receipt.json")
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args(argv)

    changed, diff_error = (
        (args.changed_file, None) if args.changed_file
        else changed_files_from_git(args.base, args.head)
    )
    plan = plan_tests(changed, diff_error)
    receipt: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "PLANNED" if args.plan_only else "PENDING",
        "selection": plan,
        "test_command_family": "PYTHON_UNITTEST",
        "measurement": {"wall_time_seconds": None, "test_execution_exit_code": None},
        "assurance_boundary": {
            "focused_selection_is_not_release_approval": True,
            "unknown_impact_falls_back_to_full_suite": True,
            "required_independent_ci_gates_are_not_waived": True,
        },
    }
    if not args.plan_only:
        exit_code, output, elapsed = _run_tests(plan)
        receipt["status"] = "PASS" if exit_code == 0 else "FAIL"
        receipt["measurement"] = {
            "wall_time_seconds": round(elapsed, 6),
            "test_execution_exit_code": exit_code,
        }
        receipt["output_sha256"] = hashlib.sha256(output.encode("utf-8")).hexdigest()
        print(output, end="" if output.endswith("\n") else "\n")

    serialized = json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if args.plan_only or receipt["status"] == "PASS" else int(receipt["measurement"]["test_execution_exit_code"] or 1)


if __name__ == "__main__":
    raise SystemExit(main())
