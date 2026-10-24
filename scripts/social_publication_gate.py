"""Offline-only social publication decision gate: no external API calls."""
import hashlib
import json

CHANNELS = frozenset({"x", "linkedin", "youtube", "tiktok", "instagram", "facebook"})

def prepare_publication(program, channels, text, approvals=None):
    """Prepare a review-only record, never transmit."""
    blockers = []
    if not isinstance(program, str) or not program.strip():
        blockers.append("INVALID_PROGRAM")
    if not isinstance(text, str) or not text.strip() or len(text) > 2000:
        blockers.append("INVALID_TEXT")
    if not isinstance(channels, list) or not channels or any(
        not isinstance(c, str) or c not in CHANNELS for c in channels
    ):
        blockers.append("INVALID_CHANNELS")
        channels = []
    if approvals is not None and not isinstance(approvals, dict):
        blockers.append("INVALID_APPROVALS")
    record = {
        "schema_version": "vaixlns.social-publication.v1",
        "status": "BLOCKED" if blockers else "DRAFT_REVIEW_REQUIRED",
        "blockers": sorted(blockers),
        "program": program if isinstance(program, str) else None,
        "channels": sorted(set(channels)) if channels else [],
        "text": text if isinstance(text, str) else None,
        "oauth_connected": False,
        "owner_approved": False,
        "publish_executed": False,
        "external_spend_sar": 0,
    }
    record["receipt_sha256"] = hashlib.sha256(json.dumps(
        record, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return record
