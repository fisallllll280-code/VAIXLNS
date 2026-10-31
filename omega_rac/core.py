"""Deterministic, dependency-aware Ω-RAC reference engine.

The engine computes assurance state only. It never mutates runtime state and never
issues governance decisions. Governance consumes the resulting report.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Any, Iterable

BOUNDARY_ZONES = (
    "OBSERVED", "INFERRED", "VERIFIED", "PROVEN",
    "VALID", "STALE", "UNKNOWN", "UNOBSERVABLE",
)
TERMINAL_BLOCKING = {"STALE", "UNKNOWN", "UNOBSERVABLE"}

@dataclass(frozen=True)
class AssuranceReport:
    claim_id: str
    status: str
    boundary_zone: str
    unknown_vector: dict[str, float]
    obligations: tuple[str, ...]
    satisfied_obligations: tuple[str, ...]
    dependency_closure: tuple[str, ...]
    revalidation_frontier: tuple[str, ...]
    cycles: tuple[tuple[str, ...], ...]
    canonical_input_hash: str
    engine_version: str
    policy_version: str
    environment_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _canon(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _canon(value[k]) for k in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canon(v) for v in value]
    return value

def canonical_input(obj: dict[str, Any]) -> str:
    """Stable canonical JSON representation used as the determinism boundary."""
    return json.dumps(_canon(obj), ensure_ascii=False, separators=(",", ":"), sort_keys=True)

def _hash(obj: dict[str, Any]) -> str:
    return sha256(canonical_input(obj).encode("utf-8")).hexdigest()

def detect_cycles(edges: dict[str, Iterable[str]]) -> tuple[tuple[str, ...], ...]:
    graph={k:tuple(v) for k,v in edges.items()}
    for v in tuple(graph):
        graph.setdefault(v, ())
    found=[]
    visiting=set()
    stack=[]
    emitted=set()
    def dfs(node):
        if node in visiting:
            i=stack.index(node)
            cyc=tuple(stack[i:]+[node])
            key=min(tuple(cyc[j:]+cyc[:j]) for j in range(len(cyc)-1))
            if key not in emitted:
                emitted.add(key); found.append(tuple(key))
            return
        visiting.add(node); stack.append(node)
        for nxt in graph[node]: dfs(nxt)
        stack.pop(); visiting.remove(node)
    for n in sorted(graph): dfs(n)
    return tuple(sorted(found))

def dependency_closure(root: str, edges: dict[str, Iterable[str]]) -> tuple[str, ...]:
    reverse={}
    for src,deps in edges.items():
        for dep in deps:
            reverse.setdefault(dep,set()).add(src)
    seen={root}; todo=[root]
    while todo:
        cur=todo.pop()
        for parent in sorted(reverse.get(cur,())):
            if parent not in seen:
                seen.add(parent); todo.append(parent)
    return tuple(sorted(seen))

def _frontier(closure: set[str], edges: dict[str, Iterable[str]]) -> tuple[str, ...]:
    # Minimal boundary: affected nodes whose dependents are not themselves affected.
    reverse={}
    for src,deps in edges.items():
        for dep in deps: reverse.setdefault(dep,set()).add(src)
    return tuple(sorted(n for n in closure if not (reverse.get(n,set()) & closure)))

def assess(
    claim: dict[str, Any],
    *,
    evidence: dict[str, Any] | None = None,
    edges: dict[str, Iterable[str]] | None = None,
    unknown_vector: dict[str, float] | None = None,
    tolerance: dict[str, float] | None = None,
    engine_version: str = "omega-rac-1.1.0",
    policy_version: str = "default-1",
    environment_fingerprint: str = "unspecified",
) -> AssuranceReport:
    evidence=evidence or {}
    edges=edges or {}
    unknown_vector=unknown_vector or {}
    tolerance=tolerance or {}
    claim_id=str(claim["claim_id"])
    obligations=tuple(sorted(map(str,claim.get("obligations",()))))
    satisfied=tuple(sorted(map(str,evidence.get("satisfied_obligations",()))))
    cycles=detect_cycles(edges)
    closure=set(dependency_closure(claim_id,edges))
    frontier=_frontier(closure,edges)
    exceeded=any(float(unknown_vector.get(k,0)) > float(tolerance.get(k,0)) for k in unknown_vector)
    missing=tuple(o for o in obligations if o not in satisfied)
    if cycles:
        status="INSUFFICIENT_RECURSIVE_ASSURANCE"; zone="UNKNOWN"
    elif exceeded:
        status="QUARANTINE_INSUFFICIENT_ASSURANCE"; zone="UNKNOWN"
    elif missing:
        status="REQUIRES_OBSERVATION"; zone="UNOBSERVABLE"
    else:
        status="PROVEN"; zone="PROVEN"
    inp={
        "claim":claim,"evidence":evidence,"edges":edges,
        "unknown_vector":unknown_vector,"tolerance":tolerance,
        "engine_version":engine_version,"policy_version":policy_version,
        "environment_fingerprint":environment_fingerprint,
    }
    return AssuranceReport(
        claim_id=claim_id,status=status,boundary_zone=zone,
        unknown_vector=dict(sorted((str(k),float(v)) for k,v in unknown_vector.items())),
        obligations=obligations,satisfied_obligations=satisfied,
        dependency_closure=tuple(sorted(closure)),revalidation_frontier=frontier,
        cycles=cycles,canonical_input_hash=_hash(inp),
        engine_version=engine_version,policy_version=policy_version,
        environment_fingerprint=environment_fingerprint,
    )
