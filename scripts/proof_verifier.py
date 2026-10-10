#!/usr/bin/env python3
"""Verify VAIXLNS proof records against repository bytes."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def proof_id(proof: dict) -> str:
    core = {
        "claim_id": proof["claim_id"],
        "statement": proof["statement"],
        "subject": proof["subject"],
        "evidence": proof["evidence"],
    }
    return hashlib.sha256(canonical_json(core)).hexdigest()

def verify(proof: dict) -> list[str]:
    errors: list[str] = []
    expected_id = proof_id(proof)
    if proof.get("proof_id") != expected_id:
        errors.append(f"PROOF_ID_MISMATCH:expected={expected_id}:actual={proof.get('proof_id')}")
    evidence = proof.get("evidence", [])
    if proof.get("epistemic_state") in {"VERIFIED", "CANONICAL"} and not evidence:
        errors.append("VERIFIED_PROOF_WITHOUT_EVIDENCE")
    for item in evidence:
        ref = item.get("ref", "")
        path = (ROOT / ref).resolve()
        if ROOT != path and ROOT not in path.parents:
            errors.append(f"EVIDENCE_OUTSIDE_REPOSITORY:{ref}")
            continue
        if not path.is_file():
            errors.append(f"EVIDENCE_FILE_MISSING:{ref}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item.get("digest"):
            errors.append(f"EVIDENCE_DIGEST_MISMATCH:{ref}:expected={item.get('digest')}:actual={actual}")
    verification = proof.get("verification", {})
    if verification.get("result") != "PASS":
        errors.append("PROOF_VERIFICATION_RESULT_NOT_PASS")
    return errors

def main() -> int:
    rel = sys.argv[1] if len(sys.argv) > 1 else "registry/evidence/control-plane-proof.json"
    path = ROOT / rel
    try:
        proof = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PROOF_FAIL: {exc}")
        return 1
    errors = verify(proof)
    if errors:
        print("PROOF_FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PROOF_PASS")
    print(f"proof_id={proof['proof_id']}")
    print(f"claim_id={proof['claim_id']}")
    print("evidence_count=" + str(len(proof.get("evidence", []))))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
