#!/usr/bin/env python3
"""Evidence gate for the VAIXLNS revenue opportunity register.

This tool validates record completeness and truth/safety guardrails. It does NOT
verify customer demand, contact prospects, call AI providers, or claim revenue.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REGISTER = Path("docs/strategy/REVENUE_OPPORTUNITY_REGISTER_001.md")
REQUIRED_GUARDRAILS = (
    "Do not contact anyone or publish outreach without human approval.",
    "No spending, money movement, external contact, or public posting without explicit authorization.",
    "Preserve project.genome, Ω.000, and all historical artifacts.",
)
REQUIRED_TABLE_HEADERS = ("Candidate", "Public evidence", "Testable commercial hypothesis", "Qualification question", "Public source")


def parse_candidate_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    in_table = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            if in_table and rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not in_table:
            if tuple(cells) == REQUIRED_TABLE_HEADERS:
                in_table = True
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        if len(cells) != len(REQUIRED_TABLE_HEADERS):
            raise ValueError(f"Candidate table row has {len(cells)} cells; expected {len(REQUIRED_TABLE_HEADERS)}: {line}")
        rows.append(dict(zip(REQUIRED_TABLE_HEADERS, cells)))
    if not in_table:
        raise ValueError("Required candidate table/header not found")
    return rows


def validate(text: str, source_path: str) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        candidates = parse_candidate_rows(text)
    except ValueError as exc:
        candidates = []
        errors.append(str(exc))

    status_line = next((line for line in text.splitlines() if line.lower().startswith("status:")), "")
    if "NOT QUALIFIED" not in status_line.upper():
        errors.append("Register status must explicitly remain NOT QUALIFIED until direct buyer evidence exists.")
    if not candidates:
        errors.append("No candidate records found.")

    for i, row in enumerate(candidates, start=1):
        name = row["Candidate"]
        for field in ("Public evidence", "Testable commercial hypothesis", "Qualification question"):
            if not row[field] or row[field].lower() in {"tbd", "unknown", "n/a"}:
                errors.append(f"Candidate row {i} ({name}) missing usable field: {field}.")
        if not re.search(r"https://[^\s|]+", row["Public source"]):
            errors.append(f"Candidate row {i} ({name}) has no HTTPS source URL.")
        if "may " in row["Testable commercial hypothesis"].lower() or "possible " in row["Testable commercial hypothesis"].lower() or "potential " in row["Testable commercial hypothesis"].lower():
            warnings.append(f"{name}: hypothesis is explicitly unverified; do not treat it as buyer-demand evidence.")

    for phrase in REQUIRED_GUARDRAILS:
        if phrase not in text:
            errors.append(f"Required safety guardrail missing: {phrase}")

    if re.search(r"(?im)^\s*Status:\s*(?:VERIFIED|QUALIFIED|CUSTOMER_CONFIRMED)\b", text):
        errors.append("Unsafe status promotion detected; status requires direct evidence and independent review.")
    if "no customer need or purchase intent verified" not in text.lower():
        errors.append("Register must state that customer need/purchase intent has not been verified.")

    return {
        "schema": "vaixlns.revenue-opportunity-gate.v1",
        "status": "PASS" if not errors else "FAIL",
        "scope": "document_completeness_and_guardrails_only",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_path": source_path,
        "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "candidate_count": len(candidates),
        "candidate_names": [row["Candidate"] for row in candidates],
        "errors": errors,
        "warnings": warnings,
        "limitations": [
            "A passing gate is not proof of customer demand, buying authority, budget, qualification, or revenue.",
            "No prospect contact, external API calls, spending, publishing, or customer-data access occurred.",
            "AI/model providers and specialist agents are not invoked by this script."
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, default=DEFAULT_REGISTER)
    parser.add_argument("--report", type=Path, help="Optional path to write the JSON evidence report.")
    args = parser.parse_args()
    try:
        text = args.register.read_text(encoding="utf-8")
    except OSError as exc:
        print(json.dumps({"status": "FAIL", "errors": [str(exc)]}, indent=2), file=sys.stderr)
        return 2
    report = validate(text, str(args.register))
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(rendered, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
