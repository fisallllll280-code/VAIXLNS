#!/usr/bin/env python3
"""Read-only VAIXLNS assembly manifest preflight. No network or deployment."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry/assemblies/assembly-federation.v1.json"
VALID_STATES = {"INVENTORIED", "IDENTITY_HOLD", "SPECIFICATION_OR_PARTIAL", "PROPOSED", "PARTIAL", "SPECIFIED", "ADAPTER_CANDIDATE", "QUARANTINED"}

def validate(data):
    errors = []
    if data.get("schema") != "vaixlns.assembly-federation.v1":
        errors.append("invalid schema")
    policy = data.get("policy", {})
    for key, expected in (("preserve_history", True), ("destructive_merge", False), ("auto_publish", False), ("proof_required", True), ("identity_conflicts_block_admission", True)):
        if policy.get(key) is not expected:
            errors.append(f"unsafe policy: {key}")
    groups = data.get("groups", [])
    if not isinstance(groups, list) or len(groups) != 8:
        errors.append("expected eight assembly groups")
        groups = groups if isinstance(groups, list) else []
    ids, repositories = set(), set()
    for group in groups:
        gid = group.get("id")
        if gid in ids:
            errors.append(f"duplicate group: {gid}")
        ids.add(gid)
        if group.get("state") not in VALID_STATES:
            errors.append(f"invalid state: {gid}")
        for repo in group.get("repositories", []):
            if not isinstance(repo, str) or repo.count("/") != 1:
                errors.append(f"invalid repository: {repo}")
            if repo in repositories:
                errors.append(f"duplicate repository assignment: {repo}")
            repositories.add(repo)
        if group.get("unresolved") and group.get("state") != "IDENTITY_HOLD":
            errors.append(f"identity conflict not on hold: {gid}")
    omega = data.get("omega_infinity", {})
    if omega.get("verification_state") != "NOT_REPRODUCED":
        errors.append("archive verification must not be asserted without attached evidence")
    if omega.get("archive_bundle") != "NOT_ATTACHED":
        errors.append("archive bundle absent from this change")
    return errors, {"groups": len(groups), "repository_assignments": len(repositories), "unresolved_groups": sum(bool(g.get("unresolved")) for g in groups)}

def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors, summary = validate(data)
    print(json.dumps({"status": "FAIL" if errors else "PASS", "summary": summary, "errors": errors}, ensure_ascii=False, indent=2))
    return int(bool(errors))

if __name__ == "__main__":
    sys.exit(main())
