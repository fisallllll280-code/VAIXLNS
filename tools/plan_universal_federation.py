#!/usr/bin/env python3
"""Plan a non-destructive VAIXLNS federation of explicitly declared accounts.

Offline, standard-library-only. This script never authenticates, fetches remote
content, writes to source systems, activates models, or promotes canonical state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

CATALOG = Path("registry/federation/universal-account-system-source-classes.v1.json")
STATES = {"DECLARED", "AUTHORIZED", "SUSPENDED", "REVOKED"}
CLASSIFICATIONS = {"PUBLIC", "INTERNAL", "RESTRICTED"}
ALIAS = re.compile(r"^[a-z][a-z0-9_-]{2,63}$")
SENSITIVE_NAMES = ("password", "secret", "token", "private_key", "access_key", "credential", "refresh", "authorization_header")
GATES = (
    "DECLARE_SOURCE",
    "AUTHORIZE_ACCOUNT",
    "INVENTORY_READ_ONLY",
    "CAPTURE_DELTA_OR_SNAPSHOT",
    "CONTENT_HASH_AND_LINEAGE",
    "CLASSIFY_AND_ROUTE",
    "RECONCILE_WITH_Ω.000_AND_ZERO_LOSS",
    "DEPENDENCY_AND_IDENTITY_AUDIT",
    "CONTRACT_AND_SECURITY_GATE",
    "SANDBOX_AND_TEST",
    "INDEPENDENT_EVIDENCE_REVIEW",
    "AUTHORIZED_COMMIT_OR_HOLD",
    "CONTINUOUS_MONITOR_AND_REVALIDATE",
)
ROUTES = {
    "CHAT": "PRIVATE_LIBRARY/CHAT",
    "REPOSITORY": "VAIXLNS/registry/federation/repository-projection",
    "DOCUMENTS": "PRIVATE_LIBRARY/DOCUMENTS",
    "COMMUNICATION": "PRIVATE_LIBRARY/COMMUNICATION",
    "FILES": "PRIVATE_LIBRARY/FILES",
    "MODEL": "VAIXLNS/registry/models/review",
    "SYSTEM": "VAIXLNS/registry/federation/runtime-review",
}

class FederationError(ValueError):
    pass


def stable_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def reject_secrets(value: Any, path: str = "manifest") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).casefold()
            if any(part in normalized for part in SENSITIVE_NAMES):
                raise FederationError(f"Sensitive property forbidden: {path}.{key}")
            reject_secrets(item, f"{path}.{key}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            reject_secrets(item, f"{path}[{i}]")
    elif isinstance(value, str):
        if ("-----BEGIN" in value and "PRIVATE KEY" in value) or "sk-proj-" in value or "ghp_" in value:
            raise FederationError(f"Credential-like value forbidden at {path}")


def load_catalog(root: Path) -> dict:
    catalog = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    if catalog.get("schema") != "VAIXLNS.UniversalAccountSystemSources.v1":
        raise FederationError("Invalid federation catalog")
    return {item["class"]: item for item in catalog["source_classes"]}


def validate(manifest: dict, catalog: dict) -> list[dict]:
    reject_secrets(manifest)
    if manifest.get("schema") != "VAIXLNS.AccountSourceManifest.v1":
        raise FederationError("Unexpected manifest schema")
    accounts = manifest.get("accounts")
    if not isinstance(accounts, list):
        raise FederationError("accounts must be a list")
    seen, result = set(), []
    for item in accounts:
        if not isinstance(item, dict):
            raise FederationError("account entry must be object")
        allowed = {"alias", "source_class", "authorization", "classification", "permission_evidence", "scope_summary", "source_owner_approved", "purpose"}
        extras = set(item) - allowed
        if extras:
            raise FederationError(f"Unsupported fields: {sorted(extras)}")
        alias = item.get("alias")
        if not isinstance(alias, str) or not ALIAS.fullmatch(alias):
            raise FederationError("Every account needs a non-identifying local alias (no email, address, or login)")
        if alias in seen:
            raise FederationError(f"Duplicate account alias: {alias}")
        seen.add(alias)
        cls = item.get("source_class")
        if cls not in catalog:
            raise FederationError(f"Unknown source class: {cls}")
        state = item.get("authorization")
        if state not in STATES:
            raise FederationError(f"Invalid authorization state for {alias}")
        privacy = item.get("classification")
        if privacy not in CLASSIFICATIONS:
            raise FederationError(f"Invalid data classification for {alias}")
        evidence = item.get("permission_evidence", [])
        if not isinstance(evidence, list) or any(not isinstance(e, str) or not e.strip() for e in evidence):
            raise FederationError(f"Invalid permission evidence for {alias}")
        if state == "AUTHORIZED" and (not evidence or item.get("source_owner_approved") is not True):
            raise FederationError(f"AUTHORIZED source {alias} requires owner approval and evidence refs")
        if state in {"SUSPENDED", "REVOKED"} and item.get("source_owner_approved") is True:
            raise FederationError(f"Non-active source {alias} must not claim active approval")
        if not isinstance(item.get("purpose", ""), str) or len(item.get("purpose", "")) > 250:
            raise FederationError(f"Invalid purpose for {alias}")
        result.append(item)
    return sorted(result, key=lambda item: item["alias"])


def compose_plan(manifest: dict, catalog: dict) -> dict:
    accounts = validate(manifest, catalog)
    result = []
    for account in accounts:
        alias = account["alias"]
        cls = catalog[account["source_class"]]
        family = cls["family"]
        authorized = account["authorization"] == "AUTHORIZED" and account.get("source_owner_approved") is True
        # This tool cannot verify the validity or freshness of submitted evidence.
        admission = "ELIGIBLE_FOR_SEPARATE_AUTHORIZATION_REVIEW" if authorized else "BLOCKED"
        destination = ROUTES[family]
        blocked = account["authorization"] in {"DECLARED", "SUSPENDED", "REVOKED"}
        tasks = []
        for number, stage in enumerate(GATES):
            if number == 0:
                state = "DOCUMENTED_NOT_EXECUTED"
            elif number == 1:
                state = "EVIDENCE_CLAIM_REVIEW_REQUIRED" if authorized else "BLOCKED"
            elif blocked:
                state = "BLOCKED"
            else:
                state = "PLANNED_NOT_EXECUTED"
            if stage in {"AUTHORIZED_COMMIT_OR_HOLD", "CONTINUOUS_MONITOR_AND_REVALIDATE"}:
                state = "BLOCKED_PENDING_INDEPENDENT_ADMISSION"
            tasks.append({"stage": stage, "state": state, "depends_on": GATES[number-1] if number else None})
        result.append({
            "account_alias": alias,
            "class": account["source_class"],
            "family": family,
            "authorization_claim": account["authorization"],
            "source_owner_approved_claim": bool(account.get("source_owner_approved", False)),
            "classification": account["classification"],
            "data_policy": "NO_PUBLIC_RAW_CONTENT" if account["classification"] != "PUBLIC" else "SOURCE_POLICY_REQUIRED",
            "capture_mode": cls["sync"],
            "destination_proposal": destination,
            "admission": admission,
            "execution": "NOT_RUN",
            "connector_live_status": "NOT_TESTED",
            "human_review_required": True,
            "stages": tasks,
        })
    snapshot = {
        "schema": "VAIXLNS.UniversalAccountFederationPlan.v1",
        "source_manifest_digest_sha256": hashlib.sha256(stable_bytes(manifest)).hexdigest(),
        "authority": "VAIXLNS",
        "source_system_count": len(result),
        "admitted": 0,
        "connected_and_live_verified": 0,
        "mode": "OFFLINE_PLAN_ONLY",
        "systems": result,
        "constraints": ["NO_NETWORK_CALLS", "NO_RAW_DATA_COPIES", "NO_SECRET_EXPORTS",
                        "NO_CROSS_ACCOUNT_IMPERSONATION", "NO_PRODUCTION_ACTIVATION",
                        "NO_AUTOMATIC_CANONICAL_PROMOTION"],
    }
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a privately held account inventory; produce a safe federation plan")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, required=True, help="Private JSON with non-identifying account aliases; never commit it")
    parser.add_argument("--out", type=Path, default=Path("build/universal-federation-plan.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = args.manifest.resolve()
    # Avoid accidentally publishing the user's account inventory to Git.
    if manifest_path.is_relative_to(root) and not manifest_path.is_relative_to(root / "build"):
        parser.error("Store your private account manifest outside the repo or under ignored build/")
    out = (args.out if args.out.is_absolute() else root / args.out).resolve()
    if not out.is_relative_to(root / "build"):
        parser.error("Output must stay inside ignored build/; do not publish account inventory")
    catalog = load_catalog(root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = compose_plan(manifest, catalog)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(stable_bytes(report))
    print(json.dumps({"accounts": report["source_system_count"], "mode": report["mode"],
                      "admitted": 0, "output": str(out)}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
