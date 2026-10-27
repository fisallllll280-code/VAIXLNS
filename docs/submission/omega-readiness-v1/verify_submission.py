#!/usr/bin/env python3
"""Read-only submission artifact lint. Never marks runtime VERIFIED."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REQUIRED = (
    "README.md", "CABSOLUTE_PROMPT_AI.md", "EXECUTION_AND_TEST_MAP.md",
    "CLAIM_PROOF_REGISTER.csv", "COMPLIANCE_MATRIX.csv",
    "READINESS_DECISION.md", "SUBMISSION_DOSSIER_DRAFT.md",
    "VX_CHATGPT_GATEWAY_CONTRACT.md", "G0_EVIDENCE_INTAKE.md",
)
CLAIM_COLUMNS = {"claim_id", "claim", "source_repository", "source_commit",
                 "implementation_path", "test_id", "evidence_uri",
                 "independent_reviewer", "status", "blocker"}
COMPLIANCE_COLUMNS = {"control_id", "domain", "applicability",
                      "requirement_source", "control_evidence",
                      "owner", "state", "gap", "next_action"}

def check(root: Path = ROOT) -> dict:
    findings: list[str] = []
    for name in REQUIRED:
        if not (root / name).is_file():
            findings.append(f"MISSING_FILE:{name}")
    for name, cols, id_col in (
        ("CLAIM_PROOF_REGISTER.csv", CLAIM_COLUMNS, "claim_id"),
        ("COMPLIANCE_MATRIX.csv", COMPLIANCE_COLUMNS, "control_id"),
    ):
        f = root / name
        if not f.exists():
            continue
        with f.open(encoding="utf-8-sig", newline="") as inp:
            table = csv.DictReader(inp)
            missing = cols - set(table.fieldnames or [])
            if missing:
                findings.append(f"MISSING_COLUMNS:{name}:{','.join(sorted(missing))}")
                continue
            seen: set[str] = set()
            for rownum, row in enumerate(table, 2):
                rid = row[id_col].strip()
                if not rid or rid in seen:
                    findings.append(f"BAD_ID:{name}:{rownum}")
                seen.add(rid)
                if name.startswith("CLAIM"):
                    status = row["status"].strip().upper()
                    if status not in {"PROPOSED","IMPLEMENTED","VERIFIED","RECOVERED","CANONICAL"}:
                        findings.append(f"UNKNOWN_STATUS:{rid}")
                    if status == "VERIFIED":
                        missing_evidence = any(row[k].strip() in ("", "UNKNOWN", "UNAVAILABLE", "UNASSIGNED", "NOT_MAPPED")
                                               for k in ("source_commit", "test_id", "evidence_uri", "independent_reviewer"))
                        if missing_evidence:
                            findings.append(f"UNSUPPORTED_VERIFIED:{rid}")
    return {"document_validation": "PASS" if not findings else "FAIL",
            "runtime_verification": "NOT_ASSESSED",
            "submission_decision": "HOLD",
            "findings": findings,
            "required_file_count": len(REQUIRED)}

def main() -> int:
    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["document_validation"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
