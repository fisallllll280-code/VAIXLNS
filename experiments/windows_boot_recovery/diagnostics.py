"""Plan-only Windows boot/recovery diagnostics for VAIXLNS.

No Windows APIs, shell commands, disk access, repair, or external effects are used.
The module scores hypotheses from caller-supplied symptoms and returns safe proposals.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable


class DiagnosticContractError(ValueError):
    """Input or action violates the experiment's safety contract."""


ALLOWED_SYMPTOMS = {
    "boot_loop",
    "boot_device_missing",
    "recent_driver_change",
    "system_file_integrity_warning",
    "update_failed",
    "disk_health_warning",
    "recovery_environment_unavailable",
    "device_not_recognized",
}

# These are transparent heuristic weights, not a trained medical/diagnostic model.
HYPOTHESIS_WEIGHTS = {
    "boot_configuration_or_startup_path": {
        "boot_loop": 3,
        "boot_device_missing": 4,
        "recovery_environment_unavailable": 1,
    },
    "driver_or_device_compatibility": {
        "recent_driver_change": 4,
        "device_not_recognized": 3,
        "boot_device_missing": 1,
    },
    "system_file_or_component_corruption": {
        "system_file_integrity_warning": 4,
        "boot_loop": 1,
        "update_failed": 2,
    },
    "update_or_pending_servicing": {
        "update_failed": 4,
        "boot_loop": 2,
        "system_file_integrity_warning": 1,
    },
    "storage_health_or_connectivity": {
        "disk_health_warning": 5,
        "boot_device_missing": 3,
    },
    "recovery_environment_configuration": {
        "recovery_environment_unavailable": 5,
    },
}

SAFE_PROPOSALS = {
    "boot_configuration_or_startup_path": (
        "Collect startup error code and boot mode; inspect recovery options before proposing changes."
    ),
    "driver_or_device_compatibility": (
        "Record device identifiers and driver provider/version; verify trusted signature and vendor provenance."
    ),
    "system_file_or_component_corruption": (
        "Capture integrity-check results; propose supported offline/online repair only after backup and approval."
    ),
    "update_or_pending_servicing": (
        "Record update history and pending servicing indicators; review supported recovery options."
    ),
    "storage_health_or_connectivity": (
        "Stop write operations; capture storage health evidence and confirm backups before further action."
    ),
    "recovery_environment_configuration": (
        "Check recovery-environment availability and trusted recovery media; do not alter boot settings automatically."
    ),
}


@dataclass(frozen=True)
class RemediationRequest:
    action_id: str
    effect_class: str
    requires_approval: bool = True
    approval_receipt: str | None = None


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def rank_hypotheses(symptoms: Iterable[str]) -> dict[str, object]:
    """Return deterministic, normalized hypothesis scores without claiming certainty."""
    supplied = tuple(symptoms)
    if not supplied:
        raise DiagnosticContractError("AT_LEAST_ONE_SYMPTOM_REQUIRED")
    unknown = set(supplied) - ALLOWED_SYMPTOMS
    if unknown:
        raise DiagnosticContractError("UNKNOWN_SYMPTOM:" + ",".join(sorted(unknown)))
    if len(set(supplied)) != len(supplied):
        raise DiagnosticContractError("DUPLICATE_SYMPTOM")

    raw = {
        hypothesis: sum(weights.get(symptom, 0) for symptom in supplied)
        for hypothesis, weights in HYPOTHESIS_WEIGHTS.items()
    }
    raw = {key: score for key, score in raw.items() if score > 0}
    total = sum(raw.values())
    ranked = sorted(raw.items(), key=lambda pair: (-pair[1], pair[0]))
    candidates = [
        {
            "hypothesis": name,
            "raw_score": score,
            "relative_weight": round(score / total, 6),
            "confidence_semantics": "heuristic_relative_weight_not_probability",
            "proposal": SAFE_PROPOSALS[name],
        }
        for name, score in ranked
    ]
    body = {
        "schema_version": "1.0.0",
        "mode": "READ_ONLY_TRIAGE",
        "symptoms": sorted(supplied),
        "candidates": candidates,
        "no_automatic_repair": True,
    }
    return {**body, "evidence_hash": _sha256(body)}


def authorize_remediation(request: RemediationRequest) -> dict[str, object]:
    """Fail closed: require an explicit approval receipt for reversible writes;
    always block destructive, boot-security-bypass, and canonical mutations.
    """
    if not request.action_id.strip():
        raise DiagnosticContractError("ACTION_ID_REQUIRED")
    if request.effect_class not in {
        "read_only",
        "reversible_system_change",
        "destructive_change",
        "security_bypass",
        "canonical_write",
    }:
        raise DiagnosticContractError("UNKNOWN_EFFECT_CLASS")

    if request.effect_class in {"destructive_change", "security_bypass", "canonical_write"}:
        return {
            "action_id": request.action_id,
            "decision": "BLOCKED",
            "reason": "FORBIDDEN_EFFECT_CLASS",
            "execution_performed": False,
        }
    if request.effect_class == "read_only":
        return {
            "action_id": request.action_id,
            "decision": "PROPOSED_READ_ONLY",
            "reason": "NO_SYSTEM_MUTATION",
            "execution_performed": False,
        }
    if not request.requires_approval or not request.approval_receipt:
        return {
            "action_id": request.action_id,
            "decision": "AWAITING_APPROVAL",
            "reason": "VALID_APPROVAL_RECEIPT_REQUIRED",
            "execution_performed": False,
        }
    return {
        "action_id": request.action_id,
        "decision": "APPROVAL_RECEIPT_PRESENT_REVIEW_REQUIRED",
        "reason": "PROTOTYPE_DOES_NOT_EXECUTE_REMEDIATION",
        "execution_performed": False,
    }
