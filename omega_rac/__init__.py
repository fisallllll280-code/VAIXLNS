"""Executable Ω-RAC assurance substrate (v1.1 canonical implementation)."""
from .core import assess, detect_cycles, dependency_closure, canonical_input, AssuranceReport
__all__=["assess","detect_cycles","dependency_closure","canonical_input","AssuranceReport"]
