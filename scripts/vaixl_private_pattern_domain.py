#!/usr/bin/env python3
"""Governed private-language boundary for pattern-bound private languages.

The language belongs to a Pattern Genome, but the language source remains outside
the VAIXLNS/VX runtime and repository. This module exposes only an opaque
capability interface, provenance, lifecycle, and governed transfer/deprovisioning.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping


DOMAIN_ID = "VAIXLNS-PRIVATE-PATTERN-DOMAIN-001"
SCHEMA_VERSION = "vaixlns.private_pattern_domain.v1"

ACTIVE = "ACTIVE"
SEALED = "SEALED"
TRANSFERRED = "TRANSFERRED"
LOCKED = "LOCKED"
REVOKED = "REVOKED"

ALLOWED_STATES = {ACTIVE, SEALED, TRANSFERRED, LOCKED, REVOKED}
REQUIRED_FABRIC = (
    "syntax",
    "semantics",
    "grammar",
    "transformation",
    "security",
    "verification",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def opaque_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:20]}"


def build_pattern_language_binding(
    *,
    pattern_id: str,
    language_id: str,
    language_genome_hash: str,
    interface_id: str = "PATTERN-LANGUAGE-CAPABILITY-V1",
) -> dict[str, Any]:
    if not pattern_id or not language_id or not language_genome_hash:
        raise ValueError("pattern_id, language_id, and language_genome_hash are required")
    if len(language_genome_hash) != 64:
        raise ValueError("language_genome_hash must be a SHA-256 hex digest")
    binding = {
        "schema_version": SCHEMA_VERSION,
        "domain_id": DOMAIN_ID,
        "binding_type": "PATTERN_BOUND_PRIVATE_LANGUAGE",
        "pattern_id": pattern_id,
        "language_ref": opaque_id("PL", language_id),
        "language_genome_hash": language_genome_hash,
        "source": {
            "location": "EXTERNAL_SECRET_VAULT",
            "repository_persistence": False,
            "runtime_source_exposure": False,
            "agent_source_exposure": False,
        },
        "fabric": {
            "preserved_dimensions": list(REQUIRED_FABRIC),
            "fabric_hash": sha256_json({"dimensions": list(REQUIRED_FABRIC), "genome": language_genome_hash}),
        },
        "interface": {
            "id": interface_id,
            "mode": "CAPABILITY_ONLY",
            "allows_source_export": False,
            "allows_source_reconstruction": False,
            "allows_self_authorization": False,
        },
        "lifecycle": {
            "state": SEALED,
            "transfer_policy": "REVOKE_LANGUAGE_SOURCE_FROM_DELIVERED_ARTIFACT",
            "history_preserved": True,
        },
        "provenance": {
            "authority": "EXTERNAL_PATTERN_AUTHORITY",
            "domain": DOMAIN_ID,
        },
    }
    binding["binding_hash"] = sha256_json(binding)
    return binding


def validate_pattern_language_boundary(pattern: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    private_language = pattern.get("private_language")
    if not isinstance(private_language, Mapping):
        return ["PRIVATE_LANGUAGE_BINDING_MISSING"]

    source = private_language.get("source", {})
    interface = private_language.get("interface", {})
    lifecycle = private_language.get("lifecycle", {})
    fabric = private_language.get("fabric", {})

    if source.get("location") != "EXTERNAL_SECRET_VAULT":
        findings.append("PRIVATE_LANGUAGE_SOURCE_NOT_EXTERNAL")
    if source.get("repository_persistence") is not False:
        findings.append("PRIVATE_LANGUAGE_REPOSITORY_PERSISTENCE_ENABLED")
    if source.get("runtime_source_exposure") is not False:
        findings.append("PRIVATE_LANGUAGE_RUNTIME_EXPOSURE_ENABLED")
    if source.get("agent_source_exposure") is not False:
        findings.append("PRIVATE_LANGUAGE_AGENT_EXPOSURE_ENABLED")
    if interface.get("mode") != "CAPABILITY_ONLY":
        findings.append("PRIVATE_LANGUAGE_INTERFACE_NOT_CAPABILITY_ONLY")
    if interface.get("allows_source_export") is not False:
        findings.append("PRIVATE_LANGUAGE_SOURCE_EXPORT_ENABLED")
    if interface.get("allows_source_reconstruction") is not False:
        findings.append("PRIVATE_LANGUAGE_RECONSTRUCTION_ENABLED")
    if interface.get("allows_self_authorization") is not False:
        findings.append("PRIVATE_LANGUAGE_SELF_AUTHORIZATION_ENABLED")
    if lifecycle.get("history_preserved") is not True:
        findings.append("PRIVATE_LANGUAGE_HISTORY_NOT_PRESERVED")
    if sorted(fabric.get("preserved_dimensions", [])) != sorted(REQUIRED_FABRIC):
        findings.append("PRIVATE_LANGUAGE_FABRIC_INCOMPLETE")
    return findings


def attach_private_language(pattern: Mapping[str, Any], binding: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(pattern))
    result["private_language"] = copy.deepcopy(dict(binding))
    result["provenance"] = copy.deepcopy(result.get("provenance", {}))
    result["provenance"]["genome_hash"] = sha256_json(result)
    return result


def build_transfer_artifact(
    pattern: Mapping[str, Any],
    *,
    recipient_scope: str,
    deprovision_event: Mapping[str, Any],
) -> dict[str, Any]:
    if not recipient_scope:
        raise ValueError("recipient_scope is required")
    errors = validate_pattern_language_boundary(pattern)
    if errors:
        raise ValueError("cannot transfer invalid private-language boundary: " + ",".join(errors))

    delivered = copy.deepcopy(dict(pattern))
    binding = delivered["private_language"]
    delivered["private_language"] = {
        "schema_version": binding["schema_version"],
        "domain_id": binding["domain_id"],
        "binding_type": binding["binding_type"],
        "language_ref": binding["language_ref"],
        "language_genome_hash": binding["language_genome_hash"],
        "source": {
            "location": "NOT_DELIVERED",
            "repository_persistence": False,
            "runtime_source_exposure": False,
            "agent_source_exposure": False,
        },
        "fabric": copy.deepcopy(binding["fabric"]),
        "interface": {
            "id": binding["interface"]["id"],
            "mode": "CAPABILITY_ONLY",
            "allows_source_export": False,
            "allows_source_reconstruction": False,
            "allows_self_authorization": False,
        },
        "lifecycle": {
            "state": REVOKED,
            "transfer_policy": "LANGUAGE_SOURCE_REVOKED_FROM_DELIVERY",
            "history_preserved": True,
        },
        "provenance": copy.deepcopy(binding["provenance"]),
        "delivery": {
            "recipient_scope": recipient_scope,
            "language_source_delivered": False,
            "deprovision_event_hash": sha256_json(deprovision_event),
        },
    }
    delivered["delivery_state"] = "TRANSFERRED_WITH_PRIVATE_LANGUAGE_REVOKED"
    delivered["delivery_provenance"] = {
        "deprovision_event": copy.deepcopy(dict(deprovision_event)),
        "original_pattern_hash": sha256_json(pattern),
    }
    delivered["provenance"] = copy.deepcopy(delivered.get("provenance", {}))
    delivered["provenance"]["genome_hash"] = sha256_json(delivered)
    return delivered


def deprovision_pattern(
    pattern: Mapping[str, Any],
    *,
    agent_id: str,
    authority_envelope: Mapping[str, Any],
    recipient_scope: str,
) -> dict[str, Any]:
    """Execute a governed agent-mediated language deprovisioning operation.

    The agent performs the operation, but cannot grant itself the authority.
    """
    if not agent_id:
        raise ValueError("agent_id is required")
    errors = validate_pattern_language_boundary(pattern)
    if errors:
        raise ValueError("pattern language boundary invalid: " + ",".join(errors))

    grants = authority_envelope.get("grants", [])
    operation = authority_envelope.get("operation")
    issuer = authority_envelope.get("issuer")
    if operation != "PATTERN_LANGUAGE_DEPROVISION":
        raise PermissionError("authority envelope does not grant deprovisioning")
    if "PATTERN_LANGUAGE_DEPROVISION" not in grants:
        raise PermissionError("deprovisioning grant missing")
    if not issuer or issuer == agent_id:
        raise PermissionError("agent cannot self-issue deprovision authority")

    event = {
        "event_type": "PATTERN_LANGUAGE_DEPROVISIONED",
        "domain_id": DOMAIN_ID,
        "agent_id": agent_id,
        "authority_issuer": issuer,
        "authority_operation": operation,
        "recipient_scope": recipient_scope,
        "source_state_before": pattern["private_language"]["lifecycle"]["state"],
        "source_state_after": TRANSFERRED,
        "delivery_state": REVOKED,
        "language_source_delivered": False,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    event["event_hash"] = sha256_json(event)

    return {
        "status": "DEPROVISIONED",
        "event": event,
        "delivered_pattern": build_transfer_artifact(
            pattern,
            recipient_scope=recipient_scope,
            deprovision_event=event,
        ),
    }


def main() -> int:
    raise SystemExit(
        "This module is a library boundary. Pattern language source is intentionally not exposed by a CLI."
    )


if __name__ == "__main__":
    main()
