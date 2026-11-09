"""Validate secret references without reading or materializing secret values.

This is a reference-format guard, not a secrets manager or a proof that the
referenced object exists or is authorized. Production resolution must be done by
a trusted workload identity against the selected secrets service.
"""
import re
from urllib.parse import urlsplit

_ALLOWED_SCHEMES = {"vault", "aws-sm", "azure-kv", "gcp-sm", "github-actions"}
_SAFE_PATH = re.compile(r"^[A-Za-z0-9._/-]+$")


def validate_secret_reference(reference):
    errors = []
    if not isinstance(reference, str) or not reference or len(reference) > 512:
        return {"valid": False, "errors": ["SECRET_REFERENCE_REQUIRED"]}
    if any(ch.isspace() for ch in reference):
        return {"valid": False, "errors": ["SECRET_REFERENCE_WHITESPACE"]}
    try:
        parsed = urlsplit(reference)
    except ValueError:
        return {"valid": False, "errors": ["SECRET_REFERENCE_MALFORMED"]}

    if parsed.scheme not in _ALLOWED_SCHEMES:
        errors.append("SECRET_REFERENCE_SCHEME_NOT_ALLOWED")
    if not parsed.netloc or parsed.username is not None or parsed.password is not None:
        errors.append("SECRET_REFERENCE_AUTHORITY_INVALID")
    if parsed.query or parsed.fragment:
        errors.append("SECRET_REFERENCE_QUERY_OR_FRAGMENT_FORBIDDEN")
    if not parsed.path or not _SAFE_PATH.fullmatch(parsed.path.lstrip("/")):
        errors.append("SECRET_REFERENCE_PATH_INVALID")
    segments = parsed.path.split("/")
    if any(segment in {".", ".."} for segment in segments):
        errors.append("SECRET_REFERENCE_PATH_TRAVERSAL")
    return {"valid": not errors, "errors": sorted(set(errors))}
