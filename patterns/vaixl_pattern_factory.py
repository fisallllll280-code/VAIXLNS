"""VAIXLNS Pattern Factory v1."""
from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Mapping

DIRECTIONS = ("semantic", "structural", "operational", "evolutionary")

@dataclass(frozen=True)
class PatternLanguage:
    language_id: str
    binding_fingerprint: str
    directions: tuple[str, ...] = DIRECTIONS

@dataclass
class PatternCandidate:
    candidate_id: str
    architecture: str
    language: PatternLanguage
    metadata: dict[str, Any] = field(default_factory=dict)

class PrivatePatternDomain:
    @staticmethod
    def validate(context: Mapping[str, Any] | None) -> dict[str, Any]:
        # FIX 1: guard against None before .get().
        if context is None:
            return {"state": "MISSING", "reason": "private_pattern_context_missing"}
        language = context.get("language")
        if language is None:
            return {"state": "MISSING", "reason": "private_language_missing"}
        if not isinstance(language, Mapping):
            return {"state": "CONFLICT", "reason": "private_language_not_mapping"}
        fingerprint = language.get("binding_fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint:
            return {"state": "CONFLICT", "reason": "binding_fingerprint_missing"}
        return {"state": "VALID", "binding_fingerprint": fingerprint}

class PatternFactory:
    def __init__(self, *, architectures: tuple[str, ...] = ()) -> None:
        self.architectures = architectures
        self.replay: dict[str, Any] = {}

    def build(self, context: Mapping[str, Any] | None) -> list[dict[str, Any]]:
        # FIX 2: replay is optional and safely initialized.
        self.replay = dict(context.get("replay") or {}) if context else {}
        validation = PrivatePatternDomain.validate(context)
        if validation["state"] != "VALID":
            return []
        language = PatternLanguage(
            language_id=str(context["language"]["language_id"]),
            binding_fingerprint=validation["binding_fingerprint"],
        )
        routes = []
        for architecture in self.architectures:
            candidate_id = sha256(f"{architecture}:{language.language_id}".encode()).hexdigest()[:16]
            for direction in DIRECTIONS:
                routes.append({
                    "candidate_id": candidate_id,
                    "architecture": architecture,
                    "language_id": language.language_id,
                    "direction": direction,
                    "binding_fingerprint": language.binding_fingerprint,
                    "replay": self.replay.copy(),
                })
        return routes

def diagnose_route(route: Mapping[str, Any] | None) -> dict[str, str]:
    if route is None:
        return {"state": "MISSING", "reason": "route_missing"}
    required = ("candidate_id", "architecture", "language_id", "direction")
    missing = [key for key in required if not route.get(key)]
    if missing:
        return {"state": "REFERENCE_DEFICIENCY", "reason": ",".join(missing)}
    if route.get("direction") not in DIRECTIONS:
        return {"state": "INVARIANT_BREACH", "reason": "invalid_direction"}
    if not route.get("binding_fingerprint"):
        return {"state": "SECURITY_REJECTION", "reason": "language_binding_missing"}
    return {"state": "VALID", "reason": "route_passes_invariants"}
