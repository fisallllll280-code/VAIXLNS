"""VAIXLNS Ω-Impossibility Engine and bounded execution fabric."""
from .engine import ENGINE_VERSION, assess
from .fabric import RemoteWorker, run_batch

__all__ = ["ENGINE_VERSION", "RemoteWorker", "assess", "run_batch"]
