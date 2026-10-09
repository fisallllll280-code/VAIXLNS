"""R2 external evidence evaluation primitives."""

from .contradiction_engine import (
    ARCXContradictionEngine,
    ARCXDecisionGateAdapter,
    ContradictionAnalysisResult,
    ContradictionSeverity,
    ContradictionType,
)

__all__ = [
    "ARCXContradictionEngine",
    "ARCXDecisionGateAdapter",
    "ContradictionAnalysisResult",
    "ContradictionSeverity",
    "ContradictionType",
]
