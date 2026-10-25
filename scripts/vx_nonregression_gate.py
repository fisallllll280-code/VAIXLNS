"""Fail-closed VX capability non-regression gate.

Compares a candidate benchmark against a pinned known-good baseline.
This tool evaluates supplied measurements only; it does not run workloads,
approve releases, or deploy candidates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

_REVISION = re.compile(r"^[0-9a-f]{40}$")
_DIRECTIONS = {"higher", "lower"}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _load_benchmark(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("BENCHMARK_MUST_BE_OBJECT")
    return value


def evaluate_nonregression(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic decision; missing/invalid evidence fails closed."""
    blockers: list[str] = []
    base_revision = baseline.get("revision") if isinstance(baseline, dict) else None
    candidate_revision = candidate.get("revision") if isinstance(candidate, dict) else None
    if not isinstance(base_revision, str) or not _REVISION.fullmatch(base_revision):
        blockers.append("INVALID_BASELINE_REVISION")
    if not isinstance(candidate_revision, str) or not _REVISION.fullmatch(candidate_revision):
        blockers.append("INVALID_CANDIDATE_REVISION")
    if base_revision == candidate_revision and base_revision is not None:
        blockers.append("BASELINE_AND_CANDIDATE_REVISION_IDENTICAL")

    base_metrics = baseline.get("metrics") if isinstance(baseline, dict) else None
    candidate_metrics = candidate.get("metrics") if isinstance(candidate, dict) else None
    if not isinstance(base_metrics, dict) or not base_metrics:
        blockers.append("BASELINE_METRICS_REQUIRED")
        base_metrics = {}
    if not isinstance(candidate_metrics, dict) or not candidate_metrics:
        blockers.append("CANDIDATE_METRICS_REQUIRED")
        candidate_metrics = {}

    base_names, candidate_names = set(base_metrics), set(candidate_metrics)
    if base_names != candidate_names:
        blockers.append("METRIC_SET_MISMATCH")

    comparisons: list[dict[str, Any]] = []
    any_improvement = False
    any_regression = False
    for name in sorted(base_names | candidate_names):
        old = base_metrics.get(name)
        new = candidate_metrics.get(name)
        if not isinstance(name, str) or not name.strip():
            blockers.append("INVALID_METRIC_NAME")
            continue
        if not isinstance(old, dict) or not isinstance(new, dict):
            blockers.append(f"INVALID_METRIC_RECORD:{name}")
            continue
        direction = old.get("direction")
        if direction not in _DIRECTIONS or new.get("direction") != direction:
            blockers.append(f"INVALID_OR_CHANGED_METRIC_DIRECTION:{name}")
            continue
        before, after = old.get("value"), new.get("value")
        if not _valid_number(before) or not _valid_number(after):
            blockers.append(f"INVALID_METRIC_VALUE:{name}")
            continue
        delta = float(after) - float(before)
        improved = delta > 0 if direction == "higher" else delta < 0
        regressed = delta < 0 if direction == "higher" else delta > 0
        any_improvement = any_improvement or improved
        any_regression = any_regression or regressed
        comparisons.append({
            "metric": name,
            "direction": direction,
            "baseline": before,
            "candidate": after,
            "delta": round(delta, 12),
            "result": "IMPROVED" if improved else "REGRESSED" if regressed else "UNCHANGED",
        })

    if blockers:
        state = "BLOCKED"
    elif any_regression:
        state = "REJECTED_REGRESSION"
    elif any_improvement:
        state = "ELIGIBLE_FOR_REVIEW"
    else:
        state = "NO_MEASURED_IMPROVEMENT"

    report: dict[str, Any] = {
        "schema_version": "vx-capability-nonregression-report-v1",
        "state": state,
        "baseline_revision": base_revision,
        "candidate_revision": candidate_revision,
        "comparisons": comparisons,
        "blockers": sorted(set(blockers)),
        "promotion_authorized": False,
        "deployment_performed": False,
        "measurements_executed_by_this_tool": False,
        "policy": "NO_REGRESSION; STRICT_IMPROVEMENT_REQUIRED_FOR_REVIEW",
    }
    report["report_sha256"] = _digest(report)
    return report


def _valid_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", help="Known-good benchmark JSON")
    parser.add_argument("candidate", help="Candidate benchmark JSON")
    parser.add_argument("--output", help="Write the report to this JSON path")
    args = parser.parse_args(argv)
    try:
        report = evaluate_nonregression(_load_benchmark(args.baseline), _load_benchmark(args.candidate))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"state": "BLOCKED", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["state"] in {"ELIGIBLE_FOR_REVIEW", "NO_MEASURED_IMPROVEMENT"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
