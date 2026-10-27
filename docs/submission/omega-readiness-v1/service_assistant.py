"""Offline, advisory-only government service journey checker.

Synthetic fixtures only. Never books, submits, authenticates, or stores credentials.
"""
from dataclasses import dataclass
from typing import Mapping
from datetime import date
import re

OFFICIAL_ABSHER = "https://www.absher.sa/"
ALLOWED_SERVICES = {"passport_guidance", "appointment_guidance", "data_correction"}
SENSITIVE_KEYS = {"national_id", "passport_number", "password", "otp", "access_token", "iqama", "document_image"}

@dataclass(frozen=True)
class AdvisoryResult:
    status: str
    warnings: tuple[str, ...]
    next_step: str
    source_url: str
    action_mode: str = "GUIDANCE_ONLY"

def preflight(service: str, answers: Mapping[str, str], *, source_verified_on: str | None = None, today: date | None = None) -> AdvisoryResult:
    """Check selections without copying user-provided values to output.

    This is NOT an authoritative eligibility evaluator.
    """
    if service not in ALLOWED_SERVICES:
        return AdvisoryResult("BLOCKED", ("UNKNOWN_SERVICE",), "Confirm service directly through official portal.", OFFICIAL_ABSHER)
    if not isinstance(answers, Mapping):
        return AdvisoryResult("BLOCKED", ("INVALID_INPUT",), "Use the official portal.", OFFICIAL_ABSHER)
    if any(str(k).lower() in SENSITIVE_KEYS for k in answers):
        return AdvisoryResult("BLOCKED", ("SENSITIVE_INPUT_NOT_ACCEPTED",), "Enter credentials and identity data only in the official portal.", OFFICIAL_ABSHER)
    if any(re.search(r"(?i)(password|otp|token|secret)", str(k)) for k in answers):
        return AdvisoryResult("BLOCKED", ("CREDENTIAL_FIELD_NOT_ACCEPTED",), "Use the official portal.", OFFICIAL_ABSHER)

    warnings = []
    if not source_verified_on:
        warnings.append("OFFICIAL_REQUIREMENTS_NOT_CURRENTLY_VERIFIED")
    else:
        try:
            checked = date.fromisoformat(source_verified_on)
            now = today or date.today()
            if checked > now or (now - checked).days > 30:
                warnings.append("REQUIREMENTS_STALE_OR_FUTURE")
        except ValueError:
            warnings.append("INVALID_SOURCE_DATE")

    if service == "passport_guidance":
        if answers.get("operation") not in {"issue", "renew"}:
            warnings.append("SELECT_ISSUE_OR_RENEW")
        if answers.get("arabic_latin_name_review") != "confirmed":
            warnings.append("REVIEW_NAME_TRANSLITERATION_IN_OFFICIAL_PORTAL")
    elif service == "appointment_guidance":
        warnings.append("APPOINTMENT_NEED_MUST_BE_VERIFIED_OFFICIALLY")
    elif service == "data_correction":
        warnings.append("OFFICIAL_CORRECTION_ROUTE_REQUIRED")
    return AdvisoryResult("REVIEW_REQUIRED" if warnings else "GUIDANCE_READY",
                          tuple(warnings),
                          "Review the current official steps and authenticate directly with the responsible authority.",
                          OFFICIAL_ABSHER)
