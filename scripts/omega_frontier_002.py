"""Ω-FRONTIER-002 reference engines for bounded assurance analysis.

These functions analyze supplied models. They do not inspect repositories, execute tools,
grant authority, or prove properties outside the explicitly supplied finite model.
"""
from __future__ import annotations

from collections import defaultdict, deque
from itertools import combinations
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                     allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def uncertainty_to_action(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Compile unresolved epistemic conditions into fail-closed action constraints."""
    blocked: dict[str, set[str]] = defaultdict(set)
    findings = []
    for item in items:
        condition = str(item.get("condition", "UNKNOWN"))
        state = str(item.get("state", "UNKNOWN"))
        actions = item.get("affected_actions", [])
        if not isinstance(actions, list) or any(not isinstance(a, str) for a in actions):
            findings.append({"condition": condition, "status": "INVALID_INPUT"})
            continue
        if state not in {"RESOLVED", "VERIFIED"}:
            for action in actions:
                blocked[action].add(condition)
            findings.append({"condition": condition, "status": "RESTRICTION_COMPILED",
                             "affected_actions": sorted(set(actions))})
        else:
            findings.append({"condition": condition, "status": "RESOLVED"})
    return {"blocked_actions": {k: sorted(v) for k, v in sorted(blocked.items())},
            "findings": findings, "decision": "RESTRICTED" if blocked else
            ("INCOMPLETE" if any(f["status"] == "INVALID_INPUT" for f in findings) else "CLEAR"),
            "digest": canonical_digest({"blocked_actions": {k: sorted(v) for k, v in sorted(blocked.items())},
                                        "findings": findings})}


def assurance_singularity(dependencies: Mapping[str, Sequence[str]],
                          criticality: Mapping[str, int] | None = None) -> dict[str, Any]:
    """Rank shared dependency nodes; this is a bounded cut-set candidate analysis."""
    criticality = criticality or {}
    reverse: dict[str, set[str]] = defaultdict(set)
    for assurance, deps in dependencies.items():
        for dep in set(deps):
            reverse[dep].add(assurance)
    rows = []
    for dep, assurances in reverse.items():
        impact = sum(max(1, int(criticality.get(a, 1))) for a in assurances)
        rows.append({"dependency": dep, "affected_assurances": sorted(assurances),
                     "affected_count": len(assurances), "weighted_impact": impact,
                     "cut_set_candidate": len(assurances) > 1})
    rows.sort(key=lambda x: (-x["weighted_impact"], -x["affected_count"], x["dependency"]))
    return {"candidates": rows, "analysis": "SHARED_DEPENDENCY_HEURISTIC_NOT_GLOBAL_MIN_CUT",
            "digest": canonical_digest(rows)}


def compete_hypotheses(hypotheses: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Keep support/refutation explicit; never force a winner on ties or missing evidence."""
    rows = []
    for h in hypotheses:
        hid = str(h.get("id", ""))
        supports = h.get("supporting_evidence", [])
        refutes = h.get("refuting_evidence", [])
        if not hid or not isinstance(supports, list) or not isinstance(refutes, list):
            rows.append({"id": hid, "status": "INVALID_INPUT"})
            continue
        s, r = len(set(map(str, supports))), len(set(map(str, refutes)))
        status = "UNRESOLVED" if s == r else ("LEADING_NOT_PROVEN" if s > r else "WEAKENED_NOT_DISPROVEN")
        rows.append({"id": hid, "support_count": s, "refutation_count": r,
                     "status": status, "discriminating_tests": list(h.get("discriminating_tests", []))})
    valid = [x for x in rows if x.get("status") != "INVALID_INPUT"]
    scores = [x["support_count"] - x["refutation_count"] for x in valid]
    unique_leader = bool(valid) and scores.count(max(scores)) == 1 and max(scores) > 0
    return {"hypotheses": rows, "result": "LEADING_HYPOTHESIS_ONLY" if unique_leader else "UNRESOLVED",
            "digest": canonical_digest(rows)}


def synthesize_forbidden_states(initial_state: str, transitions: Mapping[str, Sequence[str]],
                                forbidden_states: Iterable[str], max_depth: int = 32) -> dict[str, Any]:
    """Bounded BFS counterexample search over a supplied finite transition graph."""
    forbidden = set(forbidden_states)
    queue = deque([(initial_state, [initial_state])])
    best_depth = {initial_state: 0}
    while queue:
        state, path = queue.popleft()
        if state in forbidden:
            return {"result": "COUNTEREXAMPLE_FOUND", "path": path,
                    "depth": len(path) - 1, "bounded": True}
        if len(path) - 1 >= max_depth:
            continue
        for nxt in sorted(set(transitions.get(state, []))):
            depth = len(path)
            if depth < best_depth.get(nxt, max_depth + 2):
                best_depth[nxt] = depth
                queue.append((nxt, path + [nxt]))
    truncated = any(len(p) >= max_depth + 1 for p in [])
    return {"result": "NO_COUNTEREXAMPLE_WITHIN_SEARCH_BOUND", "bounded": True,
            "max_depth": max_depth, "exhaustive_over_reachable_graph": not truncated,
            "warning": "No counterexample found is not a universal proof unless the supplied state graph is complete."}


def reconcile_histories(histories: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Reconcile event identity and explicit causal edges without inventing a total order."""
    definitions: dict[str, str] = {}
    origins: dict[str, set[str]] = defaultdict(set)
    edges: set[tuple[str, str]] = set()
    conflicts = []
    unobservable = []
    for h in histories:
        source = str(h.get("source", ""))
        events = h.get("events", [])
        if not source or not isinstance(events, list):
            unobservable.append({"source": source, "reason": "INVALID_HISTORY"})
            continue
        for e in events:
            eid = str(e.get("id", ""))
            if not eid:
                unobservable.append({"source": source, "reason": "EVENT_WITHOUT_ID"})
                continue
            fingerprint = canonical_digest({k: v for k, v in e.items() if k != "source"})
            if eid in definitions and definitions[eid] != fingerprint:
                conflicts.append({"event_id": eid, "reason": "SAME_ID_DIFFERENT_CONTENT"})
            else:
                definitions[eid] = fingerprint
            origins[eid].add(source)
            for parent in e.get("caused_by", []):
                edges.add((str(parent), eid))
    graph = defaultdict(list)
    indegree = {eid: 0 for eid in definitions}
    for parent, child in edges:
        if parent in indegree and child in indegree:
            graph[parent].append(child)
            indegree[child] += 1
        else:
            unobservable.append({"edge": [parent, child], "reason": "MISSING_CAUSAL_ENDPOINT"})
    queue = deque(sorted(k for k, v in indegree.items() if v == 0))
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for child in graph[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if visited < len(indegree):
        conflicts.append({"reason": "CAUSAL_CYCLE"})
    result = "CONFLICTED" if conflicts else ("UNOBSERVABLE" if unobservable else "CONSISTENT")
    return {"result": result, "event_count": len(definitions),
            "causal_edges": [list(x) for x in sorted(edges)],
            "shared_events": sorted(e for e, srcs in origins.items() if len(srcs) > 1),
            "conflicts": conflicts, "unobservable": unobservable,
            "note": "Concurrent events without a causal edge are not ordered by this model."}


def compare_refactor(old_contract: Mapping[str, Any], new_contract: Mapping[str, Any],
                     required_properties: Sequence[str]) -> dict[str, Any]:
    """Compare declared contract observations; missing coverage yields INCONCLUSIVE."""
    old_props = old_contract.get("properties", {})
    new_props = new_contract.get("properties", {})
    missing = sorted(p for p in required_properties if p not in old_props or p not in new_props)
    changed = sorted(p for p in required_properties if p in old_props and p in new_props
                     and old_props[p] != new_props[p])
    old_caps = set(old_contract.get("capabilities", []))
    new_caps = set(new_contract.get("capabilities", []))
    widened = sorted(new_caps - old_caps)
    if missing:
        result = "INCONCLUSIVE"
    elif changed or widened:
        result = "CONTRACT_REGRESSION"
    else:
        result = "DECLARED_CONTRACT_PRESERVED"
    return {"result": result, "missing_properties": missing, "changed_properties": changed,
            "added_capabilities": widened,
            "warning": "Declared observations are not semantic equivalence proof."}


def minimal_proof_surface(required_obligations: Iterable[str],
                          evidence_items: Sequence[Mapping[str, Any]],
                          max_items: int = 20) -> dict[str, Any]:
    """Exact bounded set-cover search while preserving mandatory obligations."""
    required = set(required_obligations)
    if len(evidence_items) > max_items:
        return {"result": "INCOMPLETE", "reason": "SEARCH_BOUND_EXCEEDED",
                "item_count": len(evidence_items), "max_items": max_items}
    eligible = []
    for item in evidence_items:
        if item.get("verified") is not True:
            continue
        covered = set(item.get("covers", []))
        eligible.append((str(item.get("id", "")), covered, bool(item.get("mandatory", False))))
    if any(not eid for eid, _, _ in eligible):
        return {"result": "INCOMPLETE", "reason": "EVIDENCE_ID_MISSING"}
    mandatory = [x for x in eligible if x[2]]
    optional = [x for x in eligible if not x[2]]
    base_cover = set().union(*(x[1] for x in mandatory)) if mandatory else set()
    if not required.issubset(base_cover | set().union(*(x[1] for x in optional)) if optional else base_cover):
        return {"result": "INCOMPLETE", "reason": "OBLIGATION_UNCOVERED",
                "uncovered": sorted(required - base_cover - (set().union(*(x[1] for x in optional)) if optional else set()))}
    for size in range(len(optional) + 1):
        for chosen in combinations(optional, size):
            cover = base_cover | (set().union(*(x[1] for x in chosen)) if chosen else set())
            if required.issubset(cover):
                ids = sorted(x[0] for x in mandatory + list(chosen))
                return {"result": "MINIMAL_WITHIN_BOUNDED_CANDIDATES", "selected_evidence": ids,
                        "covered_obligations": sorted(cover), "required_obligations": sorted(required),
                        "mandatory_preserved": True, "search_bound": max_items}
    return {"result": "INCOMPLETE", "reason": "NO_COVER_FOUND"}


def assurance_causality_map(invariants: Sequence[Mapping[str, Any]],
                            dependencies: Mapping[str, Sequence[str]],
                            evidence_states: Mapping[str, str]) -> dict[str, Any]:
    """Propagate unresolved/failed evidence to dependent invariants without collapsing states."""
    rows = []
    for inv in invariants:
        iid = str(inv.get("id", ""))
        deps = list(dependencies.get(iid, []))
        states = {d: evidence_states.get(d, "UNKNOWN") for d in deps}
        if any(s in {"FAILED", "REJECTED", "CONTRADICTED"} for s in states.values()):
            status = "REJECTED"
        elif any(s not in {"VERIFIED", "SUPPORTED"} for s in states.values()):
            status = "UNRESOLVED"
        else:
            status = "ELIGIBLE_FOR_NEXT_GATE"
        rows.append({"invariant": iid, "dependencies": states, "status": status})
    return {"invariants": rows, "digest": canonical_digest(rows),
            "authority_granted": False, "execution_performed": False}
