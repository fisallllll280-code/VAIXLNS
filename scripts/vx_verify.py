#!/usr/bin/env python3
"""Evidence-first readiness gate for VX / VAIXLNS.

The report distinguishes repository artifacts from live operational evidence.
Unknown or absent evidence is FAIL. This tool never activates connectors or
starts services; it probes only explicitly configured health endpoints.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ARTIFACTS = (
    "scripts/vx_federation_runtime.py",
    "scripts/pcs001_validator.py",
    "registry/federation/vx_model_connectors.v1.json",
    "docs/canonical/PCS-001-VX-CGF.md",
    "tests/test_pcs001_validator.py",
    "tests/test_vx_federation_runtime.py",
)
REQUIRED_SERVICES = ("VX", "VLNS", "LNS", "NEXENT")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def http_json(url: str, timeout: float = 4.0, headers: dict[str, str] | None = None) -> dict[str, Any] | None:
    """GET an operator-supplied health URL; return None on any failure."""
    if not url.startswith(("http://", "https://")):
        return None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status < 200 or response.status >= 300:
                return None
            value = json.loads(response.read(1_000_000).decode("utf-8"))
            return value if isinstance(value, dict) else None
    except (OSError, TimeoutError, ValueError, urllib.error.URLError):
        return None


def check_service_health_detailed() -> tuple[bool, dict[str, str], dict[str, str]]:
    """Return the unchanged PASS/FAIL gate plus actionable, non-secret diagnostics.

    Diagnostics never relax readiness. Missing configuration, invalid input,
    unreachable endpoints, malformed responses, and unhealthy responses remain
    failing states; the function does not start services or mutate configuration.
    """
    raw = os.environ.get("VX_SERVICE_HEALTH_URLS", "")
    if not raw.strip():
        return (
            False,
            {name: "FAIL" for name in REQUIRED_SERVICES},
            {name: "NOT_CONFIGURED" for name in REQUIRED_SERVICES},
        )
    try:
        urls = json.loads(raw)
    except json.JSONDecodeError:
        return (
            False,
            {name: "FAIL" for name in REQUIRED_SERVICES},
            {name: "INVALID_HEALTH_URLS_JSON" for name in REQUIRED_SERVICES},
        )
    if not isinstance(urls, dict):
        return (
            False,
            {name: "FAIL" for name in REQUIRED_SERVICES},
            {name: "INVALID_HEALTH_URLS_SHAPE" for name in REQUIRED_SERVICES},
        )

    outcomes: dict[str, str] = {}
    diagnostics: dict[str, str] = {}
    for name in REQUIRED_SERVICES:
        url = urls.get(name)
        if not isinstance(url, str) or not url.strip():
            outcomes[name] = "FAIL"
            diagnostics[name] = "URL_NOT_CONFIGURED"
            continue
        if not url.startswith(("http://", "https://")):
            outcomes[name] = "FAIL"
            diagnostics[name] = "INVALID_URL_SCHEME"
            continue

        payload = http_json(url)
        if payload is None:
            outcomes[name] = "FAIL"
            diagnostics[name] = "ENDPOINT_UNAVAILABLE_OR_INVALID_RESPONSE"
            continue
        healthy = (
            str(payload.get("status", "")).lower() in {"ok", "healthy"}
            or payload.get("ok") is True
        )
        outcomes[name] = "PASS" if healthy else "FAIL"
        diagnostics[name] = "HEALTHY" if healthy else "UNHEALTHY_RESPONSE"

    return all(value == "PASS" for value in outcomes.values()), outcomes, diagnostics


def check_service_health() -> tuple[bool, dict[str, str]]:
    """Backward-compatible PASS/FAIL service gate; diagnostics are reported separately."""
    ok, outcomes, _ = check_service_health_detailed()
    return ok, outcomes


def timestamp_is_fresh(value: Any, max_age: timedelta = timedelta(minutes=15)) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return False
        age = datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)
        return timedelta(seconds=-60) <= age <= max_age
    except ValueError:
        return False


def check_meeting_health() -> bool:
    url = os.environ.get("VX_MEETING_HEALTH_URL", "")
    if not url:
        return False
    challenge = str(uuid.uuid4())
    payload = http_json(
        url,
        headers={"X-VX-Probe-Challenge": challenge, "Cache-Control": "no-cache"},
    )
    if not payload:
        return False
    # The endpoint must bind its live observation to this fresh probe. A static
    # JSON fixture cannot know the unpredictable challenge value.
    return all((
        payload.get("probe_challenge") == challenge,
        timestamp_is_fresh(payload.get("observed_at"), timedelta(seconds=60)),
        payload.get("room_live") is True,
        payload.get("audio_test_passed") is True,
        payload.get("participant_presence_verified") is True,
        payload.get("names_persisted") is True,
        isinstance(payload.get("session_id"), str) and bool(payload["session_id"].strip()),
        isinstance(payload.get("participant_count"), int) and payload["participant_count"] >= 2,
    ))


def check_state_guard_coverage() -> bool:
    """Require a commit-bound coverage receipt, all declared paths, and passing bypass tests.

    This is an evidence gate, not a source-code proof. Review the receipt and its
    underlying test artifacts independently before treating coverage as verified.
    """
    raw = os.environ.get("VX_PCS001_COVERAGE_RECEIPT", "")
    if not raw:
        return False
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    try:
        receipt = read_json(path)
    except (OSError, json.JSONDecodeError):
        return False
    commit = os.environ.get("GITHUB_SHA", "")
    writers = receipt.get("writer_paths")
    if not isinstance(writers, list) or not writers or receipt.get("status") != "VERIFIED":
        return False
    if commit and receipt.get("commit_sha") != commit:
        return False
    for writer in writers:
        if not isinstance(writer, dict):
            return False
        if not all(writer.get(key) for key in ("path", "guard_call", "bypass_test")):
            return False
        if writer.get("bypass_test_result") != "PASS":
            return False
        if not (ROOT / str(writer["path"])).is_file():
            return False
    return True


def check_connectors() -> tuple[bool, int, dict[str, int]]:
    registry = ROOT / "registry/federation/vx_model_connectors.v1.json"
    try:
        data = read_json(registry)
        connectors = data.get("connectors", [])
        if not isinstance(connectors, list):
            return False, 0, {}
        counts: dict[str, int] = {}
        for item in connectors:
            status = str(item.get("status", "UNKNOWN")).upper()
            counts[status] = counts.get(status, 0) + 1
        active = counts.get("ACTIVE_VERIFIED", 0)
    except (OSError, json.JSONDecodeError, TypeError, AttributeError):
        return False, 0, {}
    # An ACTIVE_VERIFIED label alone is insufficient. Require a recent successful
    # smoke receipt supplied by the operator and tied to one of those connectors.
    receipt_path = os.environ.get("VX_CONNECTOR_SMOKE_EVIDENCE", "")
    if not receipt_path:
        return False, active, counts
    p = Path(receipt_path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        receipt = read_json(p)
    except (OSError, json.JSONDecodeError):
        return False, active, counts
    valid = (
        receipt.get("result") == "PASS"
        and receipt.get("connector_id")
        and receipt.get("request_id")
        and receipt.get("response_digest")
        and timestamp_is_fresh(receipt.get("timestamp"))
        and receipt.get("credential_redacted") is True
        and receipt.get("connector_id") in {
            item.get("connector_id") for item in connectors
            if str(item.get("status", "")).upper() == "ACTIVE_VERIFIED"
        }
    )
    return bool(active and valid), active, counts


def run_tests() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        check=False,
    )
    return result.returncode == 0


def build_report(local_tests_passed: bool | None = None) -> dict[str, Any]:
    artifact_results = {p: (ROOT / p).is_file() for p in REQUIRED_ARTIFACTS}
    artifacts_ok = all(artifact_results.values())
    connectors_ok, active_count, connector_statuses = check_connectors()
    state_ok = check_state_guard_coverage()
    runtime_ok, service_results, service_diagnostics = check_service_health_detailed()
    meeting_ok = check_meeting_health()
    ci_tests_ok = (
        os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("VX_TESTS_PASSED") == "true"
        and bool(os.environ.get("GITHUB_SHA"))
    )
    checks = {
        "REQUIRED_ARTIFACTS_PRESENT": artifacts_ok,
        "MODEL_CONNECTORS_ACTIVE": connectors_ok,
        "STATE_GUARD_WRITE_PATHS_COVERED": state_ok,
        "UNIFIED_RUNTIME_STARTED": runtime_ok,
        "MEETING_ROOM_LIVE": meeting_ok,
        "CI_TESTS_PASSED": ci_tests_ok,
    }
    ready = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": os.environ.get("GITHUB_SHA") or None,
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID") or None,
        "checks": checks,
        "details": {
            "artifact_results": artifact_results,
            "active_verified_connector_count": active_count,
            "connector_registry_status_counts": connector_statuses,
            "connector_smoke_evidence_required": True,
            "state_guard_coverage_receipt_required": True,
            "unified_service_health": service_results,
            "unified_service_health_diagnostics": service_diagnostics,
            "meeting_health_endpoint_requires": [
                "echoed per-request probe_challenge", "observed_at within 60 seconds",
                "room_live=true", "audio_test_passed=true",
                "participant_presence_verified=true", "names_persisted=true",
                "session_id", "participant_count>=2",
            ],
            "local_tests_passed": local_tests_passed,
        },
        "overall_status": "READY" if ready else "NOT_READY",
        "limitations": [
            "A passing report is only as trustworthy as its referenced endpoints and evidence receipts.",
            "This script does not deploy or start services, provision secrets, or activate connectors.",
            "CI_TESTS_PASSED records successful tests in this GitHub Actions job, not overall repository-wide CI status.",
        ],
    }


def print_report(report: dict[str, Any]) -> None:
    checks = report["checks"]
    for key, value in checks.items():
        print(f"{key}={'true' if value else 'false'} | {'PASS' if value else 'FAIL'}")
    print(f"ACTIVE_VERIFIED_CONNECTOR_COUNT={report['details']['active_verified_connector_count']}")
    for name, result in report["details"]["unified_service_health"].items():
        print(f"UNIFIED_SERVICE_{name}={result}")
    print(f"OVERALL_STATUS={report['overall_status']}")
    print("REPORT_JSON=" + json.dumps(report, ensure_ascii=False, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-tests", action="store_true", help="run Python unittest discovery first")
    parser.add_argument("--strict", action="store_true", help="return nonzero unless all readiness gates pass")
    parser.add_argument("--json-out", help="also write the full JSON report to this path")
    args = parser.parse_args()
    tests_passed = run_tests() if args.run_tests else None
    report = build_report(tests_passed)
    print_report(report)
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if tests_passed is False:
        return 2
    return 1 if args.strict and report["overall_status"] != "READY" else 0


if __name__ == "__main__":
    raise SystemExit(main())
