"""Read-only VX autonomy preflight. This is not a deployed security enforcement boundary."""
import hashlib
import json

BUILD = {"INDEX_READ", "OPPORTUNITY_RESEARCH", "SANDBOX_BUILD", "SANDBOX_TEST", "BRANCH_BUILD"}
RELEASE = {"DEPLOY", "PUBLISH", "RELEASE_UPDATE", "MARKETPLACE_LIST", "PRODUCTION_MERGE"}
COSTLY = {"PAID_API", "PAYMENT", "PURCHASE", "PAID_AD", "TRANSFER"}
PROTECTED = {"project.genome", "registry/omega/omega-000-master-index.json"}

def evaluate(request, *, approval_registry=None):
    """Fail closed; approvals are trusted only after verification by a separate adapter."""
    approvals = approval_registry or {}
    if not isinstance(request, dict):
        request = {}
    reasons = []
    action, repo, branch = (request.get(k) for k in ("action", "repository", "branch"))
    revision, paths, cost = (request.get(k) for k in ("revision", "paths", "external_cost_sar"))
    if action not in BUILD | RELEASE | COSTLY:
        reasons.append("UNKNOWN_ACTION")
    if not isinstance(repo, str) or not repo.strip():
        reasons.append("REPOSITORY_REQUIRED")
    if not isinstance(branch, str) or not branch.strip() or branch in {"main", "master"}:
        reasons.append("ISOLATED_BRANCH_REQUIRED")
    if not isinstance(revision, str) or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        reasons.append("PINNED_SHA_REQUIRED")
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        reasons.append("PATHS_REQUIRED")
    elif any(p.lstrip("./") in PROTECTED or p.startswith("../") or "\\" in p for p in paths):
        reasons.append("PROTECTED_OR_UNSAFE_PATH")
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost != 0:
        reasons.append("NONZERO_OR_UNKNOWN_COST")
    if action in COSTLY:
        reasons.append("EXTERNAL_FINANCIAL_ACTION_BLOCKED")
    if action in RELEASE:
        aid = request.get("release_approval_id")
        approval = approvals.get(aid) if isinstance(aid, str) else None
        fields = {"repository": repo, "revision": revision, "action": action,
                  "target": request.get("target"), "status": "APPROVED"}
        if not isinstance(approval, dict) or any(approval.get(k) != v for k, v in fields.items()) or not approval.get("verified_by_trusted_adapter"):
            reasons.append("RELEASE_APPROVAL_REQUIRED")
    if action in BUILD and request.get("sandbox_verified") is not True:
        reasons.append("SANDBOX_NOT_VERIFIED")
    if request.get("tool_registered") is not True:
        reasons.append("UNREGISTERED_TOOL")
    if request.get("actor_authorized") is not True:
        reasons.append("ACTOR_NOT_AUTHORIZED")
    receipt = {"schema_version": "vx-autonomy-preflight-v1",
               "status": "HOLD" if reasons else "ELIGIBLE_FOR_ADAPTER_CHECK",
               "reasons": sorted(set(reasons)), "action": action, "repository": repo,
               "revision": revision, "note": "Preflight only; no operation was executed or released."}
    receipt["digest"] = hashlib.sha256(json.dumps(receipt, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return receipt
