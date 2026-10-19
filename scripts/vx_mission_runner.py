"""Bounded VX mission runner MVP for allowlisted repository verification tasks.

No shell is used. Only Python compileall for repository scripts/tests and
unittest modules under tests.* are accepted. This is not a general-purpose
remote executor and does not deploy software.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_MODULE = re.compile(r"^tests\.[A-Za-z0-9_]+$")
_ALLOWED_ROOTS = ("scripts/", "tests/")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _validate_step(step: Any) -> tuple[list[str] | None, str | None]:
    if not isinstance(step, dict):
        return None, "INVALID_STEP_RECORD"
    step_id = step.get("step_id")
    argv = step.get("argv")
    timeout = step.get("timeout_seconds", 60)
    if not isinstance(step_id, str) or not step_id.strip():
        return None, "INVALID_STEP_ID"
    if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 300:
        return None, "INVALID_TIMEOUT"
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
        return None, "INVALID_ARGV"
    if len(argv) >= 4 and argv[0] in {"python", sys.executable} and argv[1:3] == ["-m", "unittest"]:
        if len(argv) not in (4, 5) or not _MODULE.fullmatch(argv[3]) or (len(argv) == 5 and argv[4] != "-v"):
            return None, "COMMAND_NOT_ALLOWLISTED"
        return argv, None
    if len(argv) >= 5 and argv[0] in {"python", sys.executable} and argv[1:4] == ["-m", "compileall", "-q"]:
        if any(not p.startswith(_ALLOWED_ROOTS) or ".." in Path(p).parts for p in argv[4:]):
            return None, "PATH_OUTSIDE_ALLOWLIST"
        return argv, None
    return None, "COMMAND_NOT_ALLOWLISTED"


def run_mission(mission: dict[str, Any], repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root).resolve()
    blockers: list[str] = []
    mission_id = mission.get("mission_id") if isinstance(mission, dict) else None
    steps = mission.get("steps") if isinstance(mission, dict) else None
    if not isinstance(mission_id, str) or not mission_id.strip():
        blockers.append("INVALID_MISSION_ID")
    if not isinstance(steps, list) or not steps:
        blockers.append("NONEMPTY_STEP_LIST_REQUIRED")
        steps = []
    if blockers:
        report = {"schema_version": "vx-mission-receipt-v1", "mission_id": mission_id, "state": "BLOCKED", "blockers": blockers, "steps": [], "execution_performed": False}
        report["receipt_sha256"] = _sha(report)
        return report

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for step in steps:
        argv, error = _validate_step(step)
        step_id = step.get("step_id") if isinstance(step, dict) else None
        if isinstance(step_id, str) and step_id in seen:
            error = "DUPLICATE_STEP_ID"
        if isinstance(step_id, str):
            seen.add(step_id)
        if error:
            results.append({"step_id": step_id, "state": "BLOCKED", "error": error, "return_code": None})
            break
        timeout = step.get("timeout_seconds", 60)
        started = time.monotonic()
        try:
            completed = subprocess.run(
                argv, cwd=root, shell=False, capture_output=True, text=True,
                timeout=timeout, check=False,
            )
            elapsed_ms = round((time.monotonic() - started) * 1000, 3)
            results.append({
                "step_id": step_id,
                "state": "PASSED" if completed.returncode == 0 else "FAILED",
                "argv": argv,
                "return_code": completed.returncode,
                "elapsed_ms": elapsed_ms,
                "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest(),
                "stderr_sha256": hashlib.sha256(completed.stderr.encode("utf-8")).hexdigest(),
                "stdout_tail": completed.stdout[-4000:],
                "stderr_tail": completed.stderr[-4000:],
            })
            if completed.returncode != 0:
                break
        except subprocess.TimeoutExpired as exc:
            results.append({"step_id": step_id, "state": "TIMED_OUT", "argv": argv, "timeout_seconds": timeout, "error": str(exc)})
            break
        except OSError as exc:
            results.append({"step_id": step_id, "state": "FAILED_TO_START", "argv": argv, "error": str(exc)})
            break

    failed = any(item["state"] != "PASSED" for item in results)
    all_steps_run = len(results) == len(steps)
    state = "BLOCKED" if any(item["state"] == "BLOCKED" for item in results) else "FAILED" if failed else "PASSED" if all_steps_run else "INCOMPLETE"
    report = {
        "schema_version": "vx-mission-receipt-v1",
        "mission_id": mission_id,
        "state": state,
        "steps": results,
        "execution_performed": any(item.get("return_code") is not None or item["state"] in {"TIMED_OUT", "FAILED_TO_START"} for item in results),
        "deployment_performed": False,
        "shell_used": False,
    }
    report["receipt_sha256"] = _sha(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mission_json")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        mission = json.loads(Path(args.mission_json).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"state": "BLOCKED", "error": str(exc)}), file=sys.stderr)
        return 2
    report = run_mission(mission, args.repo_root)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["state"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
