"""ARC-X contradiction analysis for VAIXLNS R2.

This module detects candidate conflicts; it does not determine truth or authorize
canonical admission. External content is untrusted, and absence of a detected
contradiction is not evidence that a claim is supported.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import re
from typing import Any, Dict, Iterable, Optional, Tuple


class ContradictionSeverity(str, Enum):
    NONE = "NONE"
    NEGLIGIBLE = "NEGLIGIBLE"
    MATERIAL = "MATERIAL"
    CRITICAL = "CRITICAL"


class ContradictionType(str, Enum):
    NONE = "NONE"
    DIRECT_NEGATION = "DIRECT_NEGATION"
    NUMERICAL_DISCREPANCY = "NUMERICAL"
    ENVIRONMENTAL_DRIFT = "ENVIRONMENTAL"
    VERSION_MISMATCH = "VERSION"
    PROMPT_INJECTION_RISK = "SECURITY_TAMPER"


@dataclass(frozen=True)
class ContradictionAnalysisResult:
    claim_id: str
    evidence_hash: str
    has_contradiction: bool
    contradiction_type: ContradictionType
    severity: ContradictionSeverity
    confidence_score: float
    contradiction_details: str
    suggested_action: str
    requires_arcx_sandbox_simulation: bool
    warnings: Tuple[str, ...] = ()

    def to_record(self) -> Dict[str, Any]:
        """Return JSON-safe values; Enum objects are flattened explicitly."""
        return {
            "claim_id": self.claim_id,
            "evidence_hash": self.evidence_hash,
            "has_contradiction": self.has_contradiction,
            "contradiction_type": self.contradiction_type.value,
            "severity": self.severity.value,
            "confidence_score": self.confidence_score,
            "contradiction_details": self.contradiction_details,
            "suggested_action": self.suggested_action,
            "requires_arcx_sandbox_simulation": self.requires_arcx_sandbox_simulation,
            "warnings": list(self.warnings),
        }


# The values are heuristic signals, not a calibrated probability model.
# Longest/more specific phrases are evaluated first to reduce substring errors.
_NEGATION_PAIRS = (
    ("thread-safe", "non-thread-safe"),
    ("deterministic", "nondeterministic"),
    ("compatible", "incompatible"),
    ("supported", "unsupported"),
    ("enabled", "disabled"),
    ("success", "failure"),
    ("valid", "invalid"),
    ("secure", "insecure"),
    ("secure", "vulnerable"),
    ("متوافق", "غير متوافق"),
    ("صحيح", "غير صحيح"),
    ("مدعوم", "غير مدعوم"),
    ("آمن", "غير آمن"),
    ("ناجح", "فاشل"),
    ("يعمل", "لا يعمل"),
    ("موجود", "غير موجود"),
)
_SECURITY_MARKERS = (
    "[SANITIZED_PROMPT_INJECTION_ATTEMPT]",
    "[PROMPT_INJECTION_DETECTED]",
)
_SUSPICIOUS_SECURITY_STATES = {
    "SUSPECTED_INJECTION", "PROMPT_INJECTION", "MALICIOUS", "QUARANTINE",
}
_VERSION_KEYS = ("target_version", "source_version", "runtime_version", "model_version", "api_version")
_ENVIRONMENT_KEYS = (
    "environment_fingerprint", "dependency_lock_hash", "runtime", "python_version",
    "operating_system", "os", "architecture", "hardware_profile", "dataset_revision",
)
_STOPWORDS = {
    "the", "a", "an", "at", "to", "of", "per", "in", "on", "is", "are", "be",
    "and", "or", "under", "over", "above", "below", "when", "with", "without",
    "this", "that", "it", "for", "from", "by", "as", "into", "system",
    "في", "من", "إلى", "على", "عن", "عند", "مع", "هو", "هي", "كان", "كانت",
    "أن", "إن", "ثم", "هذا", "هذه", "ذلك", "تلك", "منه", "بشكل", "عند",
}
_NUMBER_PATTERN = re.compile(
    r"(?<![\w])([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?)(?![\w])"
)
_TOKEN_PATTERN = re.compile(r"[a-zA-Z]+|[\u0600-\u06FF]+|[0-9]+")
_DIGIT_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    parts = re.split(r"\s+", phrase.strip())
    pattern = r"(?<!\w)" + r"\s+".join(re.escape(part) for part in parts) + r"(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _clean_number(token: str) -> float:
    normalized = token.translate(_DIGIT_TRANSLATION).replace(",", "")
    return float(normalized)


def _tokens_near(text: str, start: int, end: int, radius: int = 48) -> set[str]:
    context = text[max(0, start - radius):min(len(text), end + radius)].translate(_DIGIT_TRANSLATION).casefold()
    return {
        token for token in _TOKEN_PATTERN.findall(context)
        if token not in _STOPWORDS and not token.isdigit()
    }


def _extract_numeric_observations(text: str) -> list[tuple[float, set[str]]]:
    normalized = text.translate(_DIGIT_TRANSLATION)
    observations: list[tuple[float, set[str]]] = []
    for match in _NUMBER_PATTERN.finditer(normalized):
        try:
            value = _clean_number(match.group(1))
        except ValueError:
            continue
        if math.isfinite(value):
            observations.append((value, _tokens_near(normalized, match.start(), match.end())))
    return observations


class ARCXContradictionEngine:
    """Cross-evidence contradiction detector with conservative decision semantics."""

    def __init__(
        self,
        numerical_tolerance_threshold: float = 0.05,
        critical_discrepancy_threshold: float = 0.30,
    ) -> None:
        for name, value in (
            ("numerical_tolerance_threshold", numerical_tolerance_threshold),
            ("critical_discrepancy_threshold", critical_discrepancy_threshold),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                raise ValueError(f"{name} must be a finite number")
            if not 0.0 <= value < 1.0:
                raise ValueError(f"{name} must be in [0, 1)")
        if critical_discrepancy_threshold <= numerical_tolerance_threshold:
            raise ValueError("critical discrepancy threshold must exceed the numerical tolerance")
        self.numerical_tolerance = float(numerical_tolerance_threshold)
        self.critical_discrepancy_threshold = float(critical_discrepancy_threshold)

    @staticmethod
    def _result(
        *,
        claim_id: str,
        evidence_hash: str,
        has_contradiction: bool,
        contradiction_type: ContradictionType,
        severity: ContradictionSeverity,
        confidence: float,
        details: str,
        action: str,
        sandbox: bool = False,
        warnings: Iterable[str] = (),
    ) -> ContradictionAnalysisResult:
        return ContradictionAnalysisResult(
            claim_id=claim_id,
            evidence_hash=evidence_hash,
            has_contradiction=has_contradiction,
            contradiction_type=contradiction_type,
            severity=severity,
            confidence_score=max(0.0, min(1.0, float(confidence))),
            contradiction_details=details,
            suggested_action=action,
            requires_arcx_sandbox_simulation=sandbox,
            warnings=tuple(sorted(set(warnings))),
        )

    def analyze_contradiction(
        self,
        claim_statement: str,
        evidence_text: str,
        claim_id: str,
        evidence_hash: str,
        claim_metadata: Optional[Dict[str, Any]] = None,
        evidence_metadata: Optional[Dict[str, Any]] = None,
    ) -> ContradictionAnalysisResult:
        """Detect conflicts without making an evidence-admission decision."""
        if not isinstance(claim_statement, str) or not claim_statement.strip():
            raise ValueError("claim_statement is required")
        if not isinstance(evidence_text, str) or not evidence_text.strip():
            raise ValueError("evidence_text is required")
        if not isinstance(claim_id, str) or not claim_id.strip():
            raise ValueError("claim_id is required")
        if not isinstance(evidence_hash, str) or not evidence_hash.strip():
            raise ValueError("evidence_hash is required")
        if claim_metadata is not None and not isinstance(claim_metadata, dict):
            raise ValueError("claim_metadata must be a dict or None")
        if evidence_metadata is not None and not isinstance(evidence_metadata, dict):
            raise ValueError("evidence_metadata must be a dict or None")

        cmeta = claim_metadata or {}
        emeta = evidence_metadata or {}
        claim_clean = _normalize_text(claim_statement)
        evidence_clean = _normalize_text(evidence_text)

        # A marker or upstream security finding is a quarantine signal, not a complete detector.
        metadata_security = emeta.get("security_scan_status")
        if (
            any(marker.casefold() in evidence_text.casefold() for marker in _SECURITY_MARKERS)
            or emeta.get("prompt_injection_detected") is True
            or (isinstance(metadata_security, str) and metadata_security.upper() in _SUSPICIOUS_SECURITY_STATES)
        ):
            return self._result(
                claim_id=claim_id, evidence_hash=evidence_hash, has_contradiction=True,
                contradiction_type=ContradictionType.PROMPT_INJECTION_RISK,
                severity=ContradictionSeverity.CRITICAL, confidence=0.99,
                details="The evidence carries an explicit prompt-injection/security warning. Treat its content as untrusted data.",
                action="QUARANTINE_AND_LOG", warnings=("EXTERNAL_CONTENT_IS_UNTRUSTED",),
            )

        drift = self._check_metadata_drift(cmeta, emeta)
        if drift is not None:
            drift_type, details = drift
            return self._result(
                claim_id=claim_id, evidence_hash=evidence_hash, has_contradiction=True,
                contradiction_type=drift_type, severity=ContradictionSeverity.MATERIAL,
                confidence=0.85, details=details,
                action="RE_EVALUATE_CONTEXT_AND_RUN_INDEPENDENT_REPLAY", sandbox=True,
                warnings=("CLAIM_AND_EVIDENCE_MAY_NOT_DESCRIBE_THE_SAME_EXECUTION_CONTEXT",),
            )

        direct = self._check_direct_negation(claim_clean, evidence_clean)
        if direct is not None:
            pos, neg = direct
            return self._result(
                claim_id=claim_id, evidence_hash=evidence_hash, has_contradiction=True,
                contradiction_type=ContradictionType.DIRECT_NEGATION,
                severity=ContradictionSeverity.CRITICAL, confidence=0.90,
                details=f"Possible direct negation detected: '{pos}' versus '{neg}'. Review sentence scope and assumptions.",
                action="FLAG_CONFLICT_AND_FREEZE", sandbox=True,
                warnings=("LEXICAL_DETECTOR_REQUIRES_CONTEXTUAL_VERIFICATION",),
            )

        numeric = self._check_numerical_discrepancy(claim_clean, evidence_clean, cmeta, emeta)
        if numeric is not None:
            severity, details, confidence = numeric
            material = severity in (ContradictionSeverity.MATERIAL, ContradictionSeverity.CRITICAL)
            return self._result(
                claim_id=claim_id, evidence_hash=evidence_hash, has_contradiction=True,
                contradiction_type=ContradictionType.NUMERICAL_DISCREPANCY,
                severity=severity, confidence=confidence,
                details=details,
                action="TRIGGER_ARCX_BENCHMARK_SIMULATION" if material else "LOG_MINOR_DEVIATION",
                sandbox=material,
            )

        warnings: tuple[str, ...] = ()
        if (
            _extract_numeric_observations(claim_clean)
            and _extract_numeric_observations(evidence_clean)
            and not self._numbers_are_comparable(claim_clean, evidence_clean, cmeta, emeta)
        ):
            warnings = ("NUMERIC_CONTEXT_NOT_COMPARABLE",)

        return self._result(
            claim_id=claim_id, evidence_hash=evidence_hash, has_contradiction=False,
            contradiction_type=ContradictionType.NONE, severity=ContradictionSeverity.NONE,
            confidence=0.0,
            details="No contradiction was detected by these heuristics. This is not proof that the evidence supports the claim.",
            action="REQUIRE_INDEPENDENT_EVIDENCE_ADMISSION",
            warnings=warnings,
        )

    def _check_direct_negation(self, claim: str, evidence: str) -> tuple[str, str] | None:
        for positive, negative in _NEGATION_PAIRS:
            if _contains_phrase(claim, positive) and _contains_phrase(evidence, negative):
                return positive, negative
            if _contains_phrase(claim, negative) and _contains_phrase(evidence, positive):
                return negative, positive
        return None

    @staticmethod
    def _check_metadata_drift(
        claim_meta: Dict[str, Any],
        evidence_meta: Dict[str, Any],
    ) -> tuple[ContradictionType, str] | None:
        target_version = claim_meta.get("target_version")
        source_version = evidence_meta.get("source_version")
        if (
            target_version is not None
            and source_version is not None
            and target_version != source_version
        ):
            return (
                ContradictionType.VERSION_MISMATCH,
                f"Version mismatch: claim targets {target_version!r}, evidence describes {source_version!r}.",
            )

        for key in _VERSION_KEYS:
            left = claim_meta.get(key)
            right = evidence_meta.get(key)
            if left is not None and right is not None and left != right:
                return (
                    ContradictionType.VERSION_MISMATCH,
                    f"Version mismatch for '{key}': claim context={left!r}, evidence context={right!r}.",
                )

        for key in _ENVIRONMENT_KEYS:
            left = claim_meta.get(key)
            right = evidence_meta.get(key)
            if left is not None and right is not None and left != right:
                return (
                    ContradictionType.ENVIRONMENTAL_DRIFT,
                    f"Execution-context mismatch for '{key}': claim context={left!r}, evidence context={right!r}.",
                )

        left_metric, right_metric = claim_meta.get("metric_key"), evidence_meta.get("metric_key")
        if left_metric is not None and right_metric is not None and left_metric != right_metric:
            return (
                ContradictionType.ENVIRONMENTAL_DRIFT,
                f"Metric context mismatch: claim measures {left_metric!r}, evidence measures {right_metric!r}.",
            )
        left_unit, right_unit = claim_meta.get("unit"), evidence_meta.get("unit")
        if left_unit is not None and right_unit is not None and left_unit != right_unit:
            return (
                ContradictionType.ENVIRONMENTAL_DRIFT,
                f"Measurement units differ: claim unit={left_unit!r}, evidence unit={right_unit!r}. Convert units before comparison.",
            )
        return None

    @staticmethod
    def _numbers_are_comparable(
        claim: str, evidence: str, claim_meta: Dict[str, Any], evidence_meta: Dict[str, Any]
    ) -> bool:
        left_metric, right_metric = claim_meta.get("metric_key"), evidence_meta.get("metric_key")
        if left_metric is not None and right_metric is not None:
            if left_metric != right_metric:
                return False
            left_unit, right_unit = claim_meta.get("unit"), evidence_meta.get("unit")
            return left_unit is None or right_unit is None or left_unit == right_unit

        left = _extract_numeric_observations(claim)
        right = _extract_numeric_observations(evidence)
        for _, left_tokens in left:
            for _, right_tokens in right:
                common = left_tokens & right_tokens
                if common and len(common) / max(1, min(len(left_tokens), len(right_tokens))) >= 0.20:
                    return True
        return False

    def _check_numerical_discrepancy(
        self,
        claim: str,
        evidence: str,
        claim_meta: Dict[str, Any],
        evidence_meta: Dict[str, Any],
    ) -> tuple[ContradictionSeverity, str, float] | None:
        if not self._numbers_are_comparable(claim, evidence, claim_meta, evidence_meta):
            return None

        # Prefer structured metric values over textual first-number heuristics.
        left_value = claim_meta.get("metric_value")
        right_value = evidence_meta.get("metric_value")
        if (
            isinstance(left_value, (int, float)) and not isinstance(left_value, bool)
            and isinstance(right_value, (int, float)) and not isinstance(right_value, bool)
            and math.isfinite(left_value) and math.isfinite(right_value)
        ):
            c_val, e_val = float(left_value), float(right_value)
        else:
            left_values = _extract_numeric_observations(claim)
            right_values = _extract_numeric_observations(evidence)
            pairs = [
                (lv, rv) for lv, lt in left_values for rv, rt in right_values
                if lt & rt and len(lt & rt) / max(1, min(len(lt), len(rt))) >= 0.20
            ]
            if not pairs:
                return None
            c_val, e_val = pairs[0]

        difference = abs(c_val - e_val)
        relative = difference / max(abs(c_val), 1e-12)
        if relative <= self.numerical_tolerance:
            return None
        severity = (
            ContradictionSeverity.CRITICAL
            if relative > self.critical_discrepancy_threshold
            else ContradictionSeverity.MATERIAL
        )
        details = (
            f"Comparable metric discrepancy: claim={c_val:g}, evidence={e_val:g}, "
            f"relative_difference={relative * 100:.2f}%. Confirm metric definition, unit and test conditions."
        )
        return severity, details, 0.80


class ARCXDecisionGateAdapter:
    """Maps detector output to a conservative next action; never commits to Ω.000."""

    @staticmethod
    def evaluate_admission(analysis: ContradictionAnalysisResult) -> Dict[str, Any]:
        details = analysis.to_record()
        if analysis.contradiction_type == ContradictionType.PROMPT_INJECTION_RISK:
            return {
                "admission_decision": "REJECTED_QUARANTINED",
                "status_code": "SECURITY_REVIEW_REQUIRED",
                "arcx_action": "FREEZE_AND_ISOLATE",
                "details": details,
            }
        if not analysis.has_contradiction:
            return {
                "admission_decision": "PENDING_EVIDENCE_ADMISSION",
                "status_code": "NO_CONTRADICTION_DETECTED_NOT_PROOF",
                "arcx_action": "CONTINUE_TO_INDEPENDENT_EVIDENCE_GATE",
                "details": details,
            }
        if analysis.severity == ContradictionSeverity.CRITICAL:
            return {
                "admission_decision": "REJECTED_QUARANTINED",
                "status_code": "CONFLICT_CRITICAL",
                "arcx_action": "FREEZE_AND_ISOLATE",
                "details": details,
            }
        if analysis.requires_arcx_sandbox_simulation:
            return {
                "admission_decision": "PENDING_SIMULATION",
                "status_code": "CONFLICT_MATERIAL",
                "arcx_action": "DISPATCH_TO_R4_SANDBOX",
                "details": details,
            }
        return {
            "admission_decision": "FLAGGED_PARTIAL",
            "status_code": "INCONCLUSIVE",
            "arcx_action": "REQUIRE_HUMAN_GOVERNANCE_REVIEW",
            "details": details,
        }
