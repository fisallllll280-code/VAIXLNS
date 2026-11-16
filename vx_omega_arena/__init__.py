"""VX Ω-Arena offline-first runtime primitives."""
from .core import (
    CandidateResult, EvidenceEvent, EvidenceLedger, ProviderDescriptor,
    candidate_receipt, promotion_gate, score_candidate,
)

__all__ = [
    "CandidateResult", "EvidenceEvent", "EvidenceLedger", "ProviderDescriptor",
    "candidate_receipt", "promotion_gate", "score_candidate",
]
