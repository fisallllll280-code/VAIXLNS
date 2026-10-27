#!/usr/bin/env python3
"""Read-only audit for the VAIXLNS Innovation Operation Index.

This script does not regenerate the index, modify source files, change status,
promote canonical authority, or perform Git operations. Optional checks invoke
the existing validator and unit-test suite as subprocesses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INDEX_REL = Path("registry/innovation-operation-index.v1.json")
SCHEMA_REL = Path("schemas/innovation-operation-index.schema.json")
PROFILE_REL = Path("registry/innovation-operation-profiles.v1.json")
VALIDATOR_REL = Path("tools/validate_innovation_operation_index.py")
TEST_REL = Path("tests/test_innovation_operation_index.py")
PROTECTED = ("project.genome", "Ω.000")
ALLOWED_STATES = {
    "CANONICAL", "VERIFIED", "IMPLEMENTED", "SPECIFIED", "PARTIAL",
    "MISSING", "CONFLICT", "PROPOSAL", "RECOVERED", "QUARANTINED",
    "SOURCE-ASSERTED", "UNKNOWN",
}
ALLOWED_QUALITIES = {
    "SOURCE_BACKED", "CURATED_DESIGN_DRAFT", "RULE_DERIVED_DRAFT",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, findings: list[dict[str, str]]) -> dict[str, Any] | None:
    if not path.is_file():
        findings.append({"severity": "ERROR", "code": "FILE_NOT_FOUND", "detail": str(path.relative_to(ROOT))})
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        findings.append({"severity": "ERROR", "code": "INVALID_JSON", "detail": f"{path.relative_to(ROOT)}: {exc}"})
        return None
    if not isinstance(value, dict):
        findings.append({"severity": "ERROR", "code": "JSON_ROOT_NOT_OBJECT", "detail": str(path.relative_to(ROOT))})
        return None
    return value


def finding(findings: list[dict[str, str]], severity: str, code: str, detail: str) -> None:
    findings.append({"severity": severity, "code": code, "detail": detail})


def run_check(label: str, command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True, check=False, timeout=300
        )
        return {
            "name": label,
            "command": command,
            "exit_code": completed.returncode,
            "passed": completed.returncode == 0,
            "stdout": completed.stdout[-12000:],
            "stderr": completed.stderr[-12000:],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"name": label, "command": command, "exit_code": None, "passed": False, "error": str(exc)}


def audit() -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    index_path = ROOT / INDEX_REL
    schema_path = ROOT / SCHEMA_REL
    profile_path = ROOT / PROFILE_REL
    data = load_json(index_path, findings)
    schema = load_json(schema_path, findings)
    profiles = load_json(profile_path, findings)

    report: dict[str, Any] = {
        "report_schema": "VAIXLNS.InnovationOperationAudit.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(ROOT),
        "git_revision_hint": os.environ.get("GITHUB_SHA") or os.environ.get("GIT_COMMIT") or None,
        "mode": "READ_ONLY",
        "checks_executed": [],
        "findings": findings,
        "summary": {},
        "file_digests": {},
    }

    for rel in (INDEX_REL, SCHEMA_REL, PROFILE_REL, VALIDATOR_REL, TEST_REL):
        path = ROOT / rel
        if path.is_file():
            report["file_digests"][str(rel)] = {
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        elif rel in (INDEX_REL, SCHEMA_REL, PROFILE_REL):
            # load_json already reports required input absence.
            pass
        else:
            finding(findings, "WARN", "OPTIONAL_CHECK_FILE_ABSENT", str(rel))

    for protected in PROTECTED:
        path = ROOT / protected
        report["file_digests"][protected] = (
            {"sha256": sha256_file(path), "bytes": path.stat().st_size, "modified": False}
            if path.is_file()
            else {"present": False, "modified": False}
        )

    counts: Counter[str] = Counter()
    quality_counts: Counter[str] = Counter()
    empty_evidence = 0
    empty_dependencies = 0
    review_required = 0
    item_count = 0

    if data is not None:
        if data.get("schema") != "VAIXLNS.InnovationOperationIndex.v1":
            finding(findings, "ERROR", "SCHEMA_ID_MISMATCH", repr(data.get("schema")))
        if data.get("canonical_source") != "project.genome::v1.0.0":
            finding(findings, "ERROR", "CANONICAL_SOURCE_MISMATCH", repr(data.get("canonical_source")))
        if data.get("authority_anchor") != "Ω0_GENESIS_CORE":
            finding(findings, "ERROR", "AUTHORITY_ANCHOR_MISMATCH", repr(data.get("authority_anchor")))
        if data.get("master_index") != "Ω.000":
            finding(findings, "ERROR", "MASTER_INDEX_MISMATCH", repr(data.get("master_index")))

        generation = data.get("generation")
        if not isinstance(generation, dict):
            finding(findings, "ERROR", "GENERATION_BLOCK_INVALID", "generation must be an object")
            generation = {}
        if generation.get("state_promotion") != "DISABLED":
            finding(findings, "ERROR", "STATE_PROMOTION_NOT_DISABLED", repr(generation.get("state_promotion")))
        if generation.get("mode") != "deterministic":
            finding(findings, "WARN", "GENERATION_NOT_DECLARED_DETERMINISTIC", repr(generation.get("mode")))

        source_files = generation.get("source_files", [])
        if not isinstance(source_files, list):
            finding(findings, "ERROR", "SOURCE_FILES_INVALID", "generation.source_files must be an array")
            source_files = []
        for source in source_files:
            if not isinstance(source, str) or not source.strip():
                finding(findings, "ERROR", "SOURCE_PATH_INVALID", repr(source))
                continue
            if not (ROOT / source).is_file() and not source.startswith(("http://", "https://")):
                finding(findings, "WARN", "DECLARED_SOURCE_NOT_FOUND", source)

        items = data.get("items")
        if not isinstance(items, list):
            finding(findings, "ERROR", "ITEMS_NOT_ARRAY", "items must be an array")
            items = []
        item_count = len(items)
        ids: set[str] = set()
        for pos, item in enumerate(items):
            prefix = f"items[{pos}]"
            if not isinstance(item, dict):
                finding(findings, "ERROR", "ITEM_NOT_OBJECT", prefix)
                continue
            canonical_id = item.get("canonical_id")
            name = item.get("name")
            label = str(name or canonical_id or prefix)
            if not isinstance(canonical_id, str) or not canonical_id.strip():
                finding(findings, "ERROR", "CANONICAL_ID_EMPTY", label)
            elif canonical_id in ids:
                finding(findings, "ERROR", "DUPLICATE_CANONICAL_ID", canonical_id)
            else:
                ids.add(canonical_id)

            for key in ("canonical_id", "name", "family", "owner", "status",
                        "description", "description_basis", "mechanism_basis", "profile_quality"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    finding(findings, "ERROR", "REQUIRED_FIELD_EMPTY", f"{label}: {key}")

            status = item.get("status")
            if isinstance(status, str):
                counts[status] += 1
                if status not in ALLOWED_STATES:
                    finding(findings, "ERROR", "UNKNOWN_STATUS_ENUM", f"{label}: {status}")
            quality = item.get("profile_quality")
            if isinstance(quality, str):
                quality_counts[quality] += 1
                if quality not in ALLOWED_QUALITIES:
                    finding(findings, "ERROR", "UNKNOWN_PROFILE_QUALITY", f"{label}: {quality}")

            if item.get("canonical_promotion_allowed") is not False:
                finding(findings, "ERROR", "PROMOTION_NOT_EXPLICITLY_DISABLED", label)

            mechanism = item.get("operating_mechanism")
            if not isinstance(mechanism, list) or not mechanism or any(
                not isinstance(step, str) or not step.strip() for step in mechanism
            ):
                finding(findings, "ERROR", "OPERATING_MECHANISM_INVALID", label)

            refs = item.get("source_refs", [])
            if not isinstance(refs, list):
                finding(findings, "ERROR", "SOURCE_REFS_INVALID", label)
                refs = []
            for ref in refs:
                if not isinstance(ref, str) or not ref.strip():
                    finding(findings, "ERROR", "SOURCE_REF_EMPTY", label)
                elif not ref.startswith(("http://", "https://")) and not (ROOT / ref).is_file():
                    finding(findings, "WARN", "ITEM_SOURCE_NOT_FOUND", f"{label}: {ref}")

            evidence = item.get("evidence_refs", [])
            if not isinstance(evidence, list):
                finding(findings, "ERROR", "EVIDENCE_REFS_INVALID", label)
                evidence = []
            if not evidence:
                empty_evidence += 1
                finding(findings, "WARN", "NO_EVIDENCE_REFS", label)

            dependencies = item.get("dependencies", [])
            if not isinstance(dependencies, list):
                finding(findings, "ERROR", "DEPENDENCIES_INVALID", label)
                dependencies = []
            if not dependencies:
                empty_dependencies += 1

            if item.get("review_required") is True:
                review_required += 1
                finding(findings, "WARN", "MANUAL_REVIEW_REQUIRED", label)
            if item.get("status_disagreement") is True or status == "CONFLICT":
                finding(findings, "WARN", "STATUS_DISAGREEMENT_OR_CONFLICT", label)

            observations = item.get("status_observations", [])
            if not isinstance(observations, list):
                finding(findings, "ERROR", "STATUS_OBSERVATIONS_INVALID", label)
                observations = []
            for obs in observations:
                if not isinstance(obs, dict):
                    finding(findings, "ERROR", "STATUS_OBSERVATION_NOT_OBJECT", label)
                    continue
                if obs.get("axis") not in {"readiness", "measurement"}:
                    finding(findings, "ERROR", "STATUS_OBSERVATION_AXIS_INVALID", label)
                if not isinstance(obs.get("source"), str) or not isinstance(obs.get("state"), str):
                    finding(findings, "ERROR", "STATUS_OBSERVATION_FIELDS_INVALID", label)

        summary = data.get("summary")
        if not isinstance(summary, dict):
            finding(findings, "ERROR", "SUMMARY_INVALID", "summary must be an object")
        else:
            if summary.get("record_count") != item_count:
                finding(findings, "ERROR", "RECORD_COUNT_MISMATCH",
                        f"declared={summary.get('record_count')} actual={item_count}")
            if summary.get("status_counts") != dict(counts):
                finding(findings, "WARN", "STATUS_SUMMARY_MISMATCH",
                        f"declared={summary.get('status_counts')} actual={dict(counts)}")
            if summary.get("profile_quality_counts") != dict(quality_counts):
                finding(findings, "WARN", "QUALITY_SUMMARY_MISMATCH",
                        f"declared={summary.get('profile_quality_counts')} actual={dict(quality_counts)}")

    if schema is not None:
        if schema.get("title") != "VAIXLNS Innovation Operation Index":
            finding(findings, "ERROR", "SCHEMA_TITLE_MISMATCH", repr(schema.get("title")))
        # Validate key structural agreement without requiring third-party jsonschema.
        required = schema.get("required", [])
        if not isinstance(required, list) or not {"schema", "items", "summary"}.issubset(set(required)):
            finding(findings, "ERROR", "SCHEMA_REQUIRED_FIELDS_INCOMPLETE", repr(required))

    profile_count = None
    if profiles is not None:
        profile_items = profiles.get("profiles")
        if not isinstance(profile_items, list):
            finding(findings, "ERROR", "PROFILES_NOT_ARRAY", "profiles.profiles must be an array")
        else:
            profile_count = len(profile_items)
            profile_names = [p.get("canonical_name") for p in profile_items if isinstance(p, dict)]
            if len(profile_names) != len(set(profile_names)):
                finding(findings, "WARN", "DUPLICATE_PROFILE_NAMES", "profile canonical_name values repeat")

    report["summary"] = {
        "record_count": item_count,
        "status_counts": dict(sorted(counts.items())),
        "profile_quality_counts": dict(sorted(quality_counts.items())),
        "manual_review_required": review_required,
        "records_without_evidence_refs": empty_evidence,
        "records_without_declared_dependencies": empty_dependencies,
        "profile_count": profile_count,
        "finding_counts": dict(sorted(Counter(f["severity"] for f in findings).items())),
        "interpretation": (
            "Inventory and metadata checks only. This report does not prove implementation, "
            "runtime behavior, canonical authority, or production readiness."
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, help="Write the audit report to this path; default is stdout only.")
    parser.add_argument("--run-checks", action="store_true",
                        help="Also run the existing validator and unit tests (subprocesses; no regeneration).")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero when any WARN or ERROR finding exists.")
    args = parser.parse_args()

    report = audit()
    if args.run_checks:
        checks = [
            run_check("innovation-index-validator",
                      [sys.executable, str(ROOT / VALIDATOR_REL)]),
            run_check("innovation-index-unit-tests",
                      [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                       "-p", "test_innovation_operation_index.py", "-v"]),
        ]
        report["checks_executed"] = checks
        for check in checks:
            if not check.get("passed"):
                report["findings"].append({
                    "severity": "ERROR",
                    "code": "CHECK_FAILED",
                    "detail": f"{check['name']}: exit_code={check.get('exit_code')} error={check.get('error', '')}",
                })
        report["summary"]["finding_counts"] = dict(sorted(
            Counter(f["severity"] for f in report["findings"]).items()
        ))

    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        destination = args.json_out if args.json_out.is_absolute() else (Path.cwd() / args.json_out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
        print(f"AUDIT_REPORT_WRITTEN: {destination}")
    else:
        sys.stdout.write(rendered)

    has_error = any(item["severity"] == "ERROR" for item in report["findings"])
    has_findings = bool(report["findings"])
    if has_error or (args.strict and has_findings):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
