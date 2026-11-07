#!/usr/bin/env python3
"""PCS-001 reference admission validator. Standard library only."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from typing import Any

PROTECTED = {"LEGAL", "VALIDATED", "RELEASED", "ACTIVE", "PROMOTED"}

def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

def validate(candidate: dict[str, Any], now: int | None = None) -> dict[str, Any]:
    reasons: list[str] = []
    required = ("state_id", "state_type", "schema_version", "content_digest",
                "evidence", "replay", "verification", "provenance", "promotion", "validity")
    for key in required:
        if key not in candidate:
            reasons.append("DENY_SCHEMA_MISSING:" + key)
    if reasons:
        return {"decision":"DENY", "reasons":reasons}
    content = candidate.get("content")
    if content is None or candidate["content_digest"] != digest(content):
        reasons.append("DENY_INTEGRITY_MISMATCH")
    ev = candidate["evidence"]
    if not isinstance(ev, list) or not ev:
        reasons.append("DENY_EVIDENCE_MISSING")
    elif any(not isinstance(x, dict) or not all(x.get(k) for k in ("evidence_id","content_digest","issuer","created_at","scope")) or x.get("verified") is not True for x in ev):
        reasons.append("DENY_EVIDENCE_INSUFFICIENT")
    replay = candidate["replay"]
    if not isinstance(replay, dict) or not all(replay.get(k) for k in ("input_refs","input_digests","runtime_version","configuration_digest","command")):
        reasons.append("DENY_NOT_REPLAYABLE")
    ver = candidate["verification"]
    if not isinstance(ver, list) or not ver or any(not isinstance(x, dict) or x.get("result") != "PASS" or not all(x.get(k) for k in ("verifier","verifier_version","timestamp","evidence_digest")) for x in ver):
        reasons.append("DENY_VERIFICATION")
    prov = candidate["provenance"]
    if not isinstance(prov, dict) or not all(prov.get(k) for k in ("source_digest","producer","derivation")) or "parents" not in prov:
        reasons.append("DENY_PROVENANCE")
    promo = candidate["promotion"]
    if not isinstance(promo, dict) or not all(promo.get(k) for k in ("from_state","to_state","policy_id","policy_digest","authorized_principal","approval_evidence","timestamp","transition_digest")) or promo.get("authorized") is not True:
        reasons.append("DENY_PROMOTION_AUTHORITY")
    validity = candidate["validity"]
    if not isinstance(validity, dict) or validity.get("revoked") is not False:
        reasons.append("DENY_STALE_OR_REVOKED")
    elif validity.get("expires_at") is not None and now is not None and int(validity["expires_at"]) <= now:
        reasons.append("DENY_STALE_OR_REVOKED")
    requested = str(candidate.get("requested_status", "")).upper()
    if requested in PROTECTED and reasons:
        decision = "DENY"
    else:
        decision = "ADMIT" if not reasons else "DENY"
    return {"decision":decision,"state_id":candidate.get("state_id"),"requested_status":requested,"reasons":sorted(set(reasons)),"contract":"PCS-001","contract_version":"1.0.0"}

def main() -> int:
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidate", help="JSON candidate file")
    p.add_argument("--now",type=int,default=None,help="Unix timestamp for expiry validation")
    args=p.parse_args()
    try:
        result=validate(json.loads(Path(args.candidate).read_text(encoding="utf-8")),args.now)
    except (OSError,json.JSONDecodeError,TypeError,ValueError) as exc:
        print(json.dumps({"decision":"DENY","reasons":["DENY_INPUT_INVALID"],"detail":str(exc)},ensure_ascii=False))
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["decision"]=="ADMIT" else 1

if __name__=="__main__":
    raise SystemExit(main())
