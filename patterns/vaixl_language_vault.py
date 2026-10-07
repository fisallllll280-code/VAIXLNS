"""Pattern-local language vault binding. No secret source or raw identity is stored."""
from __future__ import annotations
import hmac
import hashlib

def binding_fingerprint(secret: bytes, pattern_id: str) -> str:
    if not secret:
        raise ValueError("secret must not be empty")
    if not pattern_id:
        raise ValueError("pattern_id must not be empty")
    return hmac.new(secret, pattern_id.encode("utf-8"), hashlib.sha256).hexdigest()

def verify_binding(secret: bytes, pattern_id: str, expected: str) -> bool:
    return hmac.compare_digest(binding_fingerprint(secret, pattern_id), expected)
