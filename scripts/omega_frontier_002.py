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
    """Compile unresolved epistemic conditions into proposed action restrictions."""
    blocked: dict[str, set[str]] = defaultdict(set)
    findings = []
    invalid = False
    for item in items:
        if not isinstance(item, Mapping):
            findings.append({"condition": "", "status": "INVALID_INPUT"})
            invalid = True
            continue
        condition = item.get("condition", "UNKNOWN")
        state = item.get("state", "UNKNOWN")
        actions = item.get("affected_actions", [])
        if (not isinstance(condition, str) or not condition.strip()
                or not isinstance(state, str)
                or not isinstance(actions, list)
                or any(not isinstance(a, str) or not a.strip() for a in actions)):
            findings.append({"condition": str(condition), "status": "INVALID_INPUT"})
            invalid = True
            continue
        if state not in {"RESOLVED", "VERIFIED"}:
            if not actions:
                findings.append({"condition": condition, "status": "INVALID_INPUT",
                                 "reason": "UNRESOLVED_CONDITION_HAS_NO_AFFECTED_ACTIONS"})
                invalid = True
                continue
            for action in actions:
                blocked[action].add(condition)
            findings.append({"condition": condition, "status": "RESTRICTION_COMPILED",
                             "affected_actions": sorted(set(actions))})
        else:
            findings.append({"condition": condition, "status": "RESOLVED"})
    restrictions = {k: sorted(v) for k, v in sorted(blocked.items())}
    decision = "INCOMPLETE" if invalid else ("RESTRICTED" if restrictions else "CLEAR")
    return {"blocked_actions": restrictions, "findings": findings, "decision": decision,
            "digest": canonical_digest({"blocked_actions": restrictions, "findings": findings})}

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
    """Compare declared evidence IDs; invalid candidates prevent choosing a leader."""
    rows = []
    seen_ids: set[str] = set()
    invalid = False
    for h in hypotheses:
        if not isinstance(h, Mapping):
            rows.append({"id": "", "status": "INVALID_INPUT"})
            invalid = True
            continue
        hid = h.get("id", "")
        supports = h.get("supporting_evidence", [])
        refutes = h.get("refuting_evidence", [])
        tests = h.get("discriminating_tests", [])
        valid = (
            isinstance(hid, str) and bool(hid.strip()) and hid not in seen_ids
            and isinstance(supports, list)
            and all(isinstance(x, str) and x.strip() for x in supports)
            and isinstance(refutes, list)
            and all(isinstance(x, str) and x.strip() for x in refutes)
            and isinstance(tests, list)
            and all(isinstance(x, str) and x.strip() for x in tests)
        )
        if not valid:
            rows.append({"id": str(hid), "status": "INVALID_INPUT"})
            invalid = True
            continue
        seen_ids.add(hid)
        support_ids, refute_ids = set(supports), set(refutes)
        score = len(support_ids) - len(refute_ids)
        status = "UNRESOLVED" if score == 0 else (
            "LEADING_NOT_PROVEN" if score > 0 else "WEAKENED_NOT_DISPROVEN")
        rows.append({"id": hid, "support_count": len(support_ids),
                     "refutation_count": len(refute_ids), "net_count": score,
                     "overlapping_evidence_ids": sorted(support_ids & refute_ids),
                     "status": status, "discriminating_tests": sorted(set(tests))})
    if invalid or not rows:
        result = "INCOMPLETE"
    else:
        scores = [x["net_count"] for x in rows]
        result = ("LEADING_HYPOTHESIS_ONLY"
                  if scores.count(max(scores)) == 1 and max(scores) > 0
                  else "UNRESOLVED")
    return {"hypotheses": rows, "result": result,
            "digest": canonical_digest(rows),
            "limitation": "Evidence counts are not quality, independence, or probability."}

def synthesize_forbidden_states(initial_state: str, transitions: Mapping[str, Sequence[str]],
                                forbidden_states: Iterable[str], max_depth: int = 32,
                                model_complete: bool = False) -> dict[str, Any]:
    """Bounded BFS over a declared graph; universal closure needs a complete model."""
    if not isinstance(max_depth, int) or isinstance(max_depth, bool) or max_depth < 0:
        return {"result": "INCOMPLETE", "reason": "INVALID_MAX_DEPTH"}
    if not isinstance(initial_state, str) or not initial_state:
        return {"result": "INCOMPLETE", "reason": "INVALID_INITIAL_STATE"}
    try:
        forbidden = set(forbidden_states)
        if not all(isinstance(x, str) and x for x in forbidden):
            return {"result": "INCOMPLETE", "reason": "INVALID_FORBIDDEN_STATE"}
    except TypeError:
        return {"result": "INCOMPLETE", "reason": "INVALID_FORBIDDEN_STATE"}
    if not isinstance(transitions, Mapping):
        return {"result": "INCOMPLETE", "reason": "INVALID_TRANSITION_GRAPH"}
    normalized: dict[str, list[str]] = {}
    for state, successors in transitions.items():
        if not isinstance(state, str) or not state or not isinstance(successors, (list, tuple)):
            return {"result": "INCOMPLETE", "reason": "INVALID_TRANSITION_GRAPH"}
        if any(not isinstance(nxt, str) or not nxt for nxt in successors):
            return {"result": "INCOMPLETE", "reason": "INVALID_TRANSITION_TARGET"}
        normalized[state] = sorted(set(successors))
    queue = deque([(initial_state, [initial_state])])
    best_depth = {initial_state: 0}
    bound_reached = False
    while queue:
        state, path = queue.popleft()
        if state in forbidden:
            return {"result": "COUNTEREXAMPLE_FOUND", "path": path,
                    "depth": len(path) - 1, "bounded": True,
                    "model_complete_assumed": model_complete}
        if len(path) - 1 >= max_depth:
            if normalized.get(state, []):
                bound_reached = True
            continue
        for nxt in normalized.get(state, []):
            depth = len(path)
            if depth < best_depth.get(nxt, max_depth + 2):
                best_depth[nxt] = depth
                queue.append((nxt, path + [nxt]))
    exhausted = bool(model_complete and not bound_reached)
    return {"result": "NO_COUNTEREXAMPLE_WITHIN_SEARCH_BOUND", "bounded": True,
            "max_depth": max_depth, "model_complete_assumed": model_complete,
            "bound_truncated": bound_reached, "exhaustive_over_reachable_graph": exhausted,
            "warning": "No counterexample found is not a universal proof unless the supplied state graph is complete and search was exhaustive."}

def reconcile_histories(histories: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Reconcile event identity and explicit causal edges without inventing total order."""
    definitions: dict[str, str] = {}
    origins: dict[str, set[str]] = defaultdict(set)
    edges: set[tuple[str, str]] = set()
    conflicts, unobservable = [], []
    sources_with_events: set[str] = set()
    for h in histories:
        if not isinstance(h, Mapping):
            unobservable.append({"source": "", "reason": "INVALID_HISTORY"})
            continue
        source, events = h.get("source", ""), h.get("events", [])
        if not isinstance(source, str) or not source or not isinstance(events, list):
            unobservable.append({"source": str(source), "reason": "INVALID_HISTORY"})
            continue
        for e in events:
            if not isinstance(e, Mapping):
                unobservable.append({"source": source, "reason": "INVALID_EVENT_RECORD"})
                continue
            eid = e.get("id", "")
            if not isinstance(eid, str) or not eid:
                unobservable.append({"source": source, "reason": "EVENT_WITHOUT_VALID_ID"})
                continue
            if "caused_by" not in e:
                unobservable.append({"source": source, "event_id": eid,
                                     "reason": "CAUSAL_RELATIONS_UNSPECIFIED"})
                continue
            parents = e.get("caused_by")
            if not isinstance(parents, list) or any(not isinstance(p, str) or not p for p in parents):
                unobservable.append({"source": source, "event_id": eid,
                                     "reason": "INVALID_CAUSAL_RELATIONS"})
                continue
            sources_with_events.add(source)
            fingerprint = canonical_digest({k: v for k, v in e.items() if k != "source"})
            if eid in definitions and definitions[eid] != fingerprint:
                conflicts.append({"event_id": eid, "reason": "SAME_ID_DIFFERENT_CONTENT"})
            else:
                definitions[eid] = fingerprint
            origins[eid].add(source)
            for parent in parents:
                edges.add((parent, eid))
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
    if conflicts:
        result = "CONFLICTED"
    elif unobservable:
        result = "UNOBSERVABLE"
    elif len(sources_with_events) > 1:
        result = "RECONCILABLE"
    else:
        result = "CONSISTENT"
    return {"result": result, "event_count": len(definitions),
            "causal_edges": [list(x) for x in sorted(edges)],
            "shared_events": sorted(e for e, srcs in origins.items() if len(srcs) > 1),
            "sources": sorted(sources_with_events),
            "conflicts": conflicts, "unobservable": unobservable,
            "note": "Concurrent events without explicit causal edges are not ordered by this model."}

def compare_refactor(old_contract: Mapping[str, Any], new_contract: Mapping[str, Any],
                     required_properties: Sequence[str]) -> dict[str, Any]:
    """Compare declared contract observations; missing coverage is inconclusive."""
    if not isinstance(old_contract, Mapping) or not isinstance(new_contract, Mapping):
        return {"result": "INCONCLUSIVE", "reason": "INVALID_CONTRACT"}
    old_props, new_props = old_contract.get("properties", {}), new_contract.get("properties", {})
    old_caps, new_caps = old_contract.get("capabilities", []), new_contract.get("capabilities", [])
    if (not isinstance(old_props, Mapping) or not isinstance(new_props, Mapping)
            or not isinstance(old_caps, (list, tuple)) or not isinstance(new_caps, (list, tuple))
            or any(not isinstance(x, str) or not x for x in list(old_caps) + list(new_caps))):
        return {"result": "INCONCLUSIVE", "reason": "INVALID_CONTRACT_SHAPE"}
    widened = sorted(set(new_caps) - set(old_caps))
    missing = sorted(p for p in required_properties if p not in old_props or p not in new_props)
    changed = sorted(p for p in required_properties if p in old_props and p in new_props
                     and old_props[p] != new_props[p])
    if widened or changed:
        result = "CONTRACT_REGRESSION"
    elif missing:
        result = "INCONCLUSIVE"
    else:
        result = "DECLARED_CONTRACT_PRESERVED"
    return {"result": result, "missing_properties": missing, "changed_properties": changed,
            "added_capabilities": widened,
            "warning": "Declared observations are not semantic equivalence proof."}

def minimal_proof_surface(required_obligations: Iterable[str],
                          evidence_items: Sequence[Mapping[str, Any]],
                          max_items: int = 20) -> dict[str, Any]:
    """Find a minimum optional evidence subset while preserving all mandatory items."""
    if not isinstance(max_items, int) or isinstance(max_items, bool) or max_items < 1:
        return {"result": "INCOMPLETE", "reason": "INVALID_SEARCH_BOUND"}
    try:
        required_list = list(required_obligations)
    except TypeError:
        return {"result": "INCOMPLETE", "reason": "INVALID_REQUIRED_OBLIGATIONS"}
    if not required_list or any(not isinstance(x, str) or not x for x in required_list):
        return {"result": "INCOMPLETE", "reason": "INVALID_OR_EMPTY_REQUIRED_OBLIGATIONS"}
    required = set(required_list)
    if not isinstance(evidence_items, Sequence) or len(evidence_items) > max_items:
        return {"result": "INCOMPLETE", "reason": "SEARCH_BOUND_EXCEEDED",
                "item_count": len(evidence_items) if isinstance(evidence_items, Sequence) else None,
                "max_items": max_items}
    parsed = []
    seen_ids: set[str] = set()
    for item in evidence_items:
        if not isinstance(item, Mapping):
            return {"result": "INCOMPLETE", "reason": "INVALID_EVIDENCE_RECORD"}
        eid, mandatory, verified, covers = item.get("id"), item.get("mandatory", False), item.get("verified"), item.get("covers")
        if not isinstance(eid, str) or not eid.strip():
            return {"result": "INCOMPLETE", "reason": "EVIDENCE_ID_MISSING"}
        if eid in seen_ids:
            return {"result": "INCOMPLETE", "reason": "DUPLICATE_EVIDENCE_ID", "evidence_id": eid}
        seen_ids.add(eid)
        if not isinstance(mandatory, bool):
            return {"result": "INCOMPLETE", "reason": "INVALID_MANDATORY_FLAG", "evidence_id": eid}
        if not isinstance(covers, (list, tuple)) or any(not isinstance(x, str) or not x for x in covers):
            return {"result": "INCOMPLETE", "reason": "INVALID_COVERAGE", "evidence_id": eid}
        if mandatory and verified is not True:
            return {"result": "INCOMPLETE", "reason": "MANDATORY_EVIDENCE_NOT_VERIFIED", "evidence_id": eid}
        parsed.append((eid, set(covers), mandatory, verified is True))
    eligible = sorted((item for item in parsed if item[3]), key=lambda x: x[0])
    mandatory_items = [x for x in eligible if x[2]]
    optional = [x for x in eligible if not x[2]]
    base_cover = set().union(*(x[1] for x in mandatory_items)) if mandatory_items else set()
    all_cover = base_cover | (set().union(*(x[1] for x in optional)) if optional else set())
    if not required.issubset(all_cover):
        return {"result": "INCOMPLETE", "reason": "OBLIGATION_UNCOVERED",
                "uncovered": sorted(required - all_cover)}
    for size in range(len(optional) + 1):
        for chosen in combinations(optional, size):
            cover = base_cover | (set().union(*(x[1] for x in chosen)) if chosen else set())
            if required.issubset(cover):
                selected = sorted(x[0] for x in mandatory_items + list(chosen))
                return {"result": "MINIMAL_WITHIN_BOUNDED_CANDIDATES", "selected_evidence": selected,
                        "covered_obligations": sorted(cover), "required_obligations": sorted(required),
                        "mandatory_preserved": True, "search_bound": max_items}
    return {"result": "INCOMPLETE", "reason": "NO_COVER_FOUND"}

def assurance_causality_map(invariants: Sequence[Mapping[str, Any]],
                            dependencies: Mapping[str, Sequence[str]],
                            evidence_states: Mapping[str, str]) -> dict[str, Any]:
    """Propagate evidence states; eligibility requires explicit dependencies all VERIFIED."""
    rows = []
    seen = set()
    for inv in invariants:
        iid = inv.get("id") if isinstance(inv, Mapping) else None
        if not isinstance(iid, str) or not iid:
            rows.append({"invariant": str(iid), "status": "INCOMPLETE",
                         "reason": "INVARIANT_ID_MISSING"})
            continue
        if iid in seen:
            rows.append({"invariant": iid, "status": "INCOMPLETE",
                         "reason": "DUPLICATE_INVARIANT_ID"})
            continue
        seen.add(iid)
        if iid not in dependencies:
            rows.append({"invariant": iid, "dependencies": {},
                         "status": "UNRESOLVED", "reason": "DEPENDENCIES_NOT_DECLARED"})
            continue
        deps = dependencies[iid]
        if not isinstance(deps, (list, tuple)) or any(not isinstance(d, str) or not d for d in deps):
            rows.append({"invariant": iid, "status": "INCOMPLETE",
                         "reason": "INVALID_DEPENDENCY_DECLARATION"})
            continue
        if not deps and inv.get("evidence_not_required") is not True:
            rows.append({"invariant": iid, "dependencies": {},
                         "status": "UNRESOLVED", "reason": "NO_ASSURANCE_DEPENDENCIES_DECLARED"})
            continue
        states = {d: evidence_states.get(d, "UNKNOWN") for d in deps}
        if any(s in {"FAILED", "REJECTED", "CONTRADICTED"} for s in states.values()):
            status = "REJECTED"
        elif any(s != "VERIFIED" for s in states.values()):
            status = "UNRESOLVED"
        else:
            status = "ELIGIBLE_FOR_NEXT_GATE"
        rows.append({"invariant": iid, "dependencies": states, "status": status})
    return {"invariants": rows, "digest": canonical_digest(rows),
            "authority_granted": False, "execution_performed": False}
