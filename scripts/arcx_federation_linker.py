"""ARC-X federation link planner. Pure local analysis; no network or execution."""
from __future__ import annotations
import hashlib
import json
from typing import Any

LINK_TYPES = {"DATA", "API", "EVENT", "BUILD", "VERIFICATION", "EXECUTION_REQUEST", "HUMAN_WORKFLOW"}
ALLOWED_STATES = {"DISCOVERED", "CONTRACT_PENDING", "COMPATIBLE_PENDING_TEST", "TESTED_PENDING_REVIEW", "AUTHORIZED", "ACTIVE", "BLOCKED", "PENDING_VERIFICATION"}
UNRESOLVED_IDENTITIES = {frozenset(("VLNS", "NAXLNS")), frozenset(("NEXNET", "NEXENT"))}

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

def plan_links(systems: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate candidate link declarations and produce a deterministic, non-authoritative plan."""
    ids = {}
    errors = []
    for system in systems:
        if not isinstance(system, dict) or not isinstance(system.get("system_id"), str) or not system["system_id"].strip():
            errors.append({"code":"INVALID_SYSTEM_IDENTITY_RECORD"})
            continue
        sid = system["system_id"]
        if sid in ids:
            errors.append({"code":"DUPLICATE_SYSTEM_ID","system_id":sid})
        ids[sid] = system
    links = []
    for item in candidates:
        if not isinstance(item, dict):
            errors.append({"code":"INVALID_LINK_RECORD"})
            continue
        src, dst = item.get("source_system"), item.get("target_system")
        kind = item.get("link_type")
        source_revision = item.get("source_revision")
        contract_digest = item.get("contract_sha256")
        direction = item.get("direction", "SOURCE_TO_TARGET")
        blockers = []
        if not isinstance(src, str) or not isinstance(dst, str) or src not in ids or dst not in ids:
            blockers.append("UNKNOWN_OR_INVALID_SYSTEM_ID")
        if isinstance(src, str) and isinstance(dst, str) and src == dst:
            blockers.append("SELF_LINK_REQUIRES_EXPLICIT_JUSTIFICATION")
        if not isinstance(kind, str) or kind not in LINK_TYPES:
            blockers.append("UNKNOWN_LINK_TYPE")
        if not isinstance(source_revision, str) or len(source_revision) != 40 or any(c not in "0123456789abcdefABCDEF" for c in source_revision):
            blockers.append("INVALID_SOURCE_REVISION")
        if not isinstance(contract_digest, str) or len(contract_digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in contract_digest):
            blockers.append("INVALID_CONTRACT_DIGEST")
        if direction not in {"SOURCE_TO_TARGET", "BIDIRECTIONAL"}:
            blockers.append("INVALID_LINK_DIRECTION")
        if isinstance(src, str) and isinstance(dst, str) and frozenset((src, dst)) in UNRESOLVED_IDENTITIES:
            blockers.append("IDENTITY_EQUIVALENCE_UNRESOLVED")
        state = "BLOCKED" if blockers else "PENDING_VERIFICATION"
        link_id = item.get("link_id")
        if not isinstance(link_id, str) or not link_id.strip():
            link_id = "link:"+digest(item)[:16]
        normalized = {
            "link_id": link_id,
            "source_system": src, "target_system": dst, "link_type": kind,
            "source_revision": source_revision,
            "contract_sha256": contract_digest,
            "direction": direction,
            "state": state, "blockers": sorted(set(blockers)),
            "execution_performed": False, "authority_granted": False,
        }
        links.append(normalized)
    links.sort(key=lambda x: (str(x["link_id"]), str(x["source_system"]), str(x["target_system"])))
    plan = {
        "schema_version":"arcx-federation-plan-v1",
        "state":"BLOCKED" if errors or any(x["state"]=="BLOCKED" for x in links) else "PENDING_VERIFICATION",
        "systems":sorted(ids),
        "links":links,
        "errors":errors,
        "authority_decision":"PENDING",
        "execution_performed":False,
        "canonical_write_performed":False,
    }
    plan["plan_sha256"] = digest(plan)
    return plan
