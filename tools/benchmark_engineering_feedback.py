#!/usr/bin/env python3
"""Measure full-suite versus safely focused engineering feedback time.

This is an opt-in benchmark. It records raw runs and environment metadata; it
does not waive required CI gates or claim that focused tests establish release
readiness. Unknown-impact changes still require the full suite.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "tools" / "engineering_test_router.py"


def _revision() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except OSError:
        return "UNKNOWN"
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def _run_case(label: str, changed_file: str, output_path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    result = subprocess.run(
        [
            sys.executable, str(ROUTER),
            "--changed-file", changed_file,
            "--output", str(output_path),
        ],
        cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    wall_seconds = time.perf_counter() - started
    receipt: dict[str, Any] = {}
    if output_path.exists():
        try:
            receipt = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            receipt = {}
    measurement = receipt.get("measurement", {})
    return {
        "label": label,
        "changed_file_fixture": changed_file,
        "exit_code": result.returncode,
        "status": receipt.get("status", "MISSING_RECEIPT"),
        "selection_mode": receipt.get("selection", {}).get("selection_mode", "UNKNOWN"),
        "test_case_count": measurement.get("test_case_count"),
        "router_wall_time_seconds": measurement.get("wall_time_seconds"),
        "harness_wall_time_seconds": round(wall_seconds, 6),
        "receipt_path": str(output_path.relative_to(ROOT)) if output_path.is_relative_to(ROOT) else str(output_path),
        "output_tail": result.stdout[-2000:],
    }


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(run["harness_wall_time_seconds"]) for run in runs]
    return {
        "runs": len(values),
        "median_wall_time_seconds": round(statistics.median(values), 6) if values else None,
        "min_wall_time_seconds": round(min(values), 6) if values else None,
        "max_wall_time_seconds": round(max(values), 6) if values else None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3, help="runs per case (1-10; default: 3)")
    parser.add_argument("--output", default="engineering-acceleration-benchmark.json")
    args = parser.parse_args(argv)
    if not 1 <= args.repeats <= 10:
        parser.error("--repeats must be between 1 and 10")

    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)

    full_runs: list[dict[str, Any]] = []
    focused_runs: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="vaixlns-accel-") as temporary:
        temp_root = Path(temporary)
        for index in range(args.repeats):
            # A documentation path is intentionally unmapped and must select FULL_SUITE.
            full_runs.append(_run_case(
                "full_suite", "docs/benchmark/full-suite-baseline.md",
                temp_root / f"full-{index + 1}.json",
            ))
            # This path has an explicit, tested mapping in engineering_test_router.py.
            focused_runs.append(_run_case(
                "focused_vcre", "vcre/predictive.py",
                temp_root / f"focused-{index + 1}.json",
            ))

    full_summary = summarize(full_runs)
    focused_summary = summarize(focused_runs)
    full_median = full_summary["median_wall_time_seconds"]
    focused_median = focused_summary["median_wall_time_seconds"]
    speedup = (
        round(full_median / focused_median, 4)
        if full_median is not None and focused_median is not None and focused_median > 0
        else None
    )
    all_runs = full_runs + focused_runs
    passed = all(
        run["exit_code"] == 0 and run["status"] == "PASS"
        for run in all_runs
    ) and all(run["selection_mode"] == expected for run, expected in (
        [(run, "FULL_SUITE") for run in full_runs]
        + [(run, "FOCUSED") for run in focused_runs]
    ))
    report = {
        "schema": "vaixlns.engineering-acceleration-benchmark.v1",
        "status": "PASS" if passed else "FAIL",
        "claim_boundary": (
            "Measured only for this revision, environment and test suite. "
            "Focused feedback does not replace required CI, integration, security or release gates."
        ),
        "environment": {
            "repository": "fisallllll280-code/VAIXLNS",
            "revision": _revision(),
            "python": sys.version,
            "platform": platform.platform(),
            "repeats_per_case": args.repeats,
        },
        "cases": {
            "full_suite": {"summary": full_summary, "raw_runs": full_runs},
            "focused_vcre": {"summary": focused_summary, "raw_runs": focused_runs},
        },
        "comparison": {
            "median_speedup_ratio_full_over_focused": speedup,
            "median_seconds_saved": (
                round(full_median - focused_median, 6)
                if full_median is not None and focused_median is not None else None
            ),
            "interpretation": "OBSERVED_MEASUREMENT_NOT_GENERALIZED",
        },
        "assurance": {
            "unknown_impact_falls_back_to_full_suite": True,
            "focused_route_does_not_waive_other_ci_gates": True,
            "raw_runs_retained": True,
        },
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Benchmark report: {output}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
