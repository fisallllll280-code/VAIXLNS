#!/usr/bin/env python3
"""Analyze innovation-to-index, repository, system and evidence relationships.

All inferred links are explicitly labeled as candidates. This tool does not
rewrite canonical records or promote the state of an innovation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

SCHEMA = "vaixlns.omega-innovation-integration-graph.v1"
EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build", "target", ".next", ".cache"}
SOURCE_SUFFIXES = {".md", ".rst", ".py", ".rs", ".go", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift", ".kt", ".json", ".yaml", ".yml", ".toml", ".sql"}
SYSTEMS = ("VAIXLNS", "VLNS", "VX", "NEXNET", "VV", "XV", "NEXENT")

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

def tokens(value: Any) -> set[str]:
    return {part for part in normalize(value).split() if len(part) >= 3}

def stable_id(prefix: str, *parts: str) -> str:
    joined = "\x1f".join(normalize(part) for part in parts)
    return prefix + "-" + hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16].upper()

def list_of_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, (str, int)) and str(item).strip()]

def inventory(root: Path, max_files: int = 10000, max_file_bytes: int = 1_000_000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDED_DIRS and not (Path(current) / name).is_symlink())
        for name in sorted(files):
            path = Path(current) / name
            if path.is_symlink() or path.suffix.lower() not in SOURCE_SUFFIXES or not path.is_file():
                continue
            try:
                size = path.stat().st_size
                raw = path.read_bytes() if size <= max_file_bytes else None
            except OSError:
                continue
            rel = path.relative_to(root).as_posix()
            rows.append({
                "path": rel,
                "bytes": size,
                "sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
                "content_scanned": raw is not None,
                "raw_text": raw.decode("utf-8", errors="replace") if raw is not None else "",
            })
            if len(rows) >= max_files:
                return rows
    return rows

def build_graph(source: dict[str, Any], root: Path) -> dict[str, Any]:
    raw_items = source.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("source items must be a non-empty list")
    root = root.resolve()
    files = inventory(root)
    path_map = {row["path"]: row for row in files}
    nodes: list[dict[str, Any]] = []
    node_id_by_name: dict[str, str] = {}
    source_rows = []
    for ordinal, item in enumerate(raw_items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"source item #{ordinal} must be an object")
        name = str(item.get("name") or item.get("title") or "").strip()
        if not name:
            raise ValueError(f"source item #{ordinal} needs name or title")
        family = str(item.get("family") or "")
        owner = str(item.get("owner") or item.get("canonical_owner") or "UNASSIGNED")
        source_state = str(item.get("state") or item.get("status") or "UNSPECIFIED")
        canonical_id = str(item.get("canonical_id") or item.get("id") or stable_id("INNOV", name, family, owner))
        node_id = "innovation:" + canonical_id
        aliases = list_of_strings(item.get("aliases"))
        explicit_repos = list_of_strings(item.get("source_repositories")) + list_of_strings(item.get("implementation_repositories"))
        evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
        explicit_paths = list_of_strings(item.get("evidence_paths")) + list_of_strings(evidence.get("paths"))
        derived_from = list_of_strings(item.get("derived_from"))
        relations = list_of_strings(item.get("relations")) + list_of_strings(item.get("related_to"))
        referenced_path_states = []
        for path_ref in sorted(set(explicit_paths)):
            relative = path_ref.replace("\\", "/")
            local = (root / relative).resolve()
            try:
                local.relative_to(root)
                in_root = True
            except ValueError:
                in_root = False
            exists = in_root and local.is_file()
            referenced_path_states.append({"path": relative, "exists": bool(exists)})
        content = json.dumps(item, ensure_ascii=False, sort_keys=True)
        nodes.append({
            "node_id": node_id,
            "node_type": "INNOVATION",
            "canonical_id": canonical_id,
            "name": name,
            "family": family,
            "owner": owner,
            "source_state": source_state,
            "source_item_sha256": digest(item),
            "aliases": aliases,
            "declared_repository_refs": sorted(set(explicit_repos)),
            "declared_path_refs": referenced_path_states,
            "declared_derived_from": derived_from,
            "declared_relations": relations,
            "authority_effect": "NONE_ANALYSIS_DOES_NOT_MUTATE_SOURCE_STATE",
        })
        node_id_by_name.setdefault(normalize(canonical_id), node_id)
        node_id_by_name.setdefault(normalize(name), node_id)
        for alias in aliases:
            node_id_by_name.setdefault(normalize(alias), node_id)
        source_rows.append({
            "node_id": node_id, "item": item, "name": name, "family": family,
            "owner": owner, "source_state": source_state, "explicit_repos": explicit_repos,
            "explicit_paths": explicit_paths, "derived_from": derived_from, "relations": relations,
        })

    for system in SYSTEMS:
        nodes.append({
            "node_id": "system:" + system, "node_type": "SYSTEM_BOUNDARY",
            "canonical_id": system, "name": system,
            "authority_effect": "BOUNDARY_LABEL_ONLY_CONNECTIVITY_NOT_ASSERTED",
        })

    edges: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    edge_keys: set[tuple[str, str, str, str]] = set()

    def add_edge(source_id: str, target_id: str, relation: str, state: str, evidence: Any, confidence: str = "EXPLICIT"):
        key = (source_id, target_id, relation, state)
        if key in edge_keys:
            return
        edge_keys.add(key)
        edges.append({
            "edge_id": stable_id("EDGE", source_id, target_id, relation, state),
            "from": source_id, "to": target_id, "relation": relation,
            "state": state, "confidence": confidence, "evidence": evidence,
        })

    for row in source_rows:
        nid = row["node_id"]
        owner_tokens = tokens(row["owner"])
        for system in SYSTEMS:
            if system in row["owner"].upper().replace("NEXENT RESEARCH", "NEXENT RESEARCH"):
                add_edge(nid, "system:" + system, "OWNED_OR_DECLARED_BY", "SOURCE_DECLARED", {"owner": row["owner"]})
        for ref in row["explicit_repos"]:
            add_edge(nid, "repository:" + ref, "IMPLEMENTED_OR_SOURCED_IN", "DECLARED_NOT_RUNTIME_VERIFIED", {"repository_ref": ref})
        for path_ref in sorted(set(row["explicit_paths"])):
            local = (root / path_ref).resolve()
            try:
                local.relative_to(root)
                inside = True
            except ValueError:
                inside = False
            exists = inside and local.is_file()
            path_node = "repository_path:" + path_ref.replace("\\", "/")
            add_edge(nid, path_node, "EVIDENCE_PATH", "PATH_EXISTS" if exists else "PATH_MISSING_OR_OUTSIDE_ROOT", {"declared_path": path_ref})
            if not exists:
                gaps.append({"gap_type": "DECLARED_EVIDENCE_PATH_UNRESOLVED", "node_id": nid, "innovation": row["name"], "reference": path_ref, "severity": "REVIEW"})
        for ref in row["derived_from"]:
            target = node_id_by_name.get(normalize(ref))
            if target:
                add_edge(nid, target, "DERIVED_FROM", "SOURCE_DECLARED", {"reference": ref})
            else:
                gaps.append({"gap_type": "UNRESOLVED_DERIVATION_REFERENCE", "node_id": nid, "innovation": row["name"], "reference": ref, "severity": "REVIEW"})
        for ref in row["relations"]:
            target = node_id_by_name.get(normalize(ref))
            if target and target != nid:
                add_edge(nid, target, "RELATED_TO", "SOURCE_DECLARED", {"reference": ref})
            elif not target:
                gaps.append({"gap_type": "UNRESOLVED_RELATION_REFERENCE", "node_id": nid, "innovation": row["name"], "reference": ref, "severity": "REVIEW"})

        if not row["explicit_paths"] and not row["explicit_repos"]:
            gaps.append({
                "gap_type": "NO_EXPLICIT_IMPLEMENTATION_OR_EVIDENCE_PATH",
                "node_id": nid, "innovation": row["name"], "source_state": row["source_state"],
                "severity": "REVIEW_NOT_AUTOMATICALLY_MISSING",
            })

        # Text/path matches are only candidate links: they do not establish implementation or correctness.
        search_terms = [row["name"], *list_of_strings(row["item"].get("aliases"))]
        family_tokens = tokens(row["family"])
        for file_row in files:
            relative = file_row["path"]
            if relative.startswith((".git/", "node_modules/")):
                continue
            searchable = normalize(relative)
            path_match = any(normalize(term) and normalize(term) in searchable for term in search_terms)
            if not path_match and file_row["content_scanned"]:
                normalized_name = normalize(row["name"])
                if len(normalized_name) >= 6 and normalized_name in normalize(file_row["raw_text"][:160_000]):
                    path_match = True
            if path_match:
                add_edge(nid, "repository_path:" + relative, "POSSIBLE_IMPLEMENTATION_OR_REFERENCE", "CANDIDATE_MATCH_NOT_PROOF",
                         {"file_sha256": file_row["sha256"], "file_bytes": file_row["bytes"]}, "HEURISTIC")

    # Conservative pairwise similarity candidates; never merge or delete automatically.
    for i, left in enumerate(source_rows):
        left_tokens = tokens(left["name"] + " " + left["family"])
        if not left_tokens:
            continue
        for right in source_rows[i + 1:]:
            right_tokens = tokens(right["name"] + " " + right["family"])
            if not right_tokens:
                continue
            union = left_tokens | right_tokens
            score = len(left_tokens & right_tokens) / len(union) if union else 0.0
            if normalize(left["name"]) == normalize(right["name"]):
                add_edge(left["node_id"], right["node_id"], "POSSIBLE_DUPLICATE_NAME", "REVIEW_REQUIRED",
                         {"normalized_name": normalize(left["name"])}, "HIGH_LEXICAL_SIMILARITY")
                gaps.append({"gap_type": "POSSIBLE_DUPLICATE_INNOVATION", "node_id": left["node_id"], "related_node_id": right["node_id"], "score": 1.0, "severity": "REVIEW"})
            elif score >= 0.72:
                add_edge(left["node_id"], right["node_id"], "SIMILAR_NAME_OR_FAMILY", "REVIEW_REQUIRED",
                         {"jaccard_token_similarity": round(score, 4)}, "HEURISTIC")
                gaps.append({"gap_type": "POSSIBLE_OVERLAPPING_FAMILY", "node_id": left["node_id"], "related_node_id": right["node_id"], "score": round(score, 4), "severity": "REVIEW"})

    # Deterministic dependency-cycle report over explicit DERIVED_FROM links.
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        if edge["relation"] == "DERIVED_FROM" and edge["state"] == "SOURCE_DECLARED":
            adjacency.setdefault(edge["from"], []).append(edge["to"])
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: list[list[str]] = []

    def visit(node: str, stack: list[str]):
        if node in visiting:
            start = stack.index(node) if node in stack else 0
            cycle = stack[start:] + [node]
            canonical = min("->".join(cycle[i:] + cycle[:i] + [cycle[i]]) for i in range(len(cycle) - 1))
            if not any("->".join(existing) == canonical for existing in cycles):
                cycles.append(cycle)
            return
        if node in visited:
            return
        visiting.add(node)
        for nxt in sorted(adjacency.get(node, [])):
            visit(nxt, stack + [node])
        visiting.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        visit(node, [])

    node_by_id = {node["node_id"]: node for node in nodes}
    for cycle in cycles:
        gaps.append({"gap_type": "DECLARED_DERIVATION_CYCLE", "cycle_node_ids": cycle, "severity": "BLOCK_REVIEW"})

    file_summary = [{
        "path": f["path"], "bytes": f["bytes"], "sha256": f["sha256"],
        "content_scanned": f["content_scanned"],
    } for f in files]
    core = {
        "schema": SCHEMA,
        "state": "ANALYZED_CANDIDATES_NOT_CANONICAL",
        "input_schema": source.get("schema"),
        "input_snapshot": source.get("snapshot"),
        "input_sha256": digest(source),
        "repository_inventory_sha256": digest(file_summary),
        "nodes": sorted(nodes, key=lambda item: item["node_id"]),
        "edges": sorted(edges, key=lambda item: (item["from"], item["relation"], item["to"], item["state"])),
        "integration_gaps": sorted(gaps, key=lambda item: (item.get("severity", ""), item.get("gap_type", ""), item.get("node_id", ""), item.get("reference", ""))),
        "cycles": cycles,
        "summary": {
            "innovation_count": len(source_rows),
            "system_boundary_count": len(SYSTEMS),
            "repository_files_indexed": len(files),
            "edges_count": len(edges),
            "candidate_edges_count": sum(edge["confidence"] == "HEURISTIC" for edge in edges),
            "explicit_relation_edges_count": sum(edge["confidence"] == "EXPLICIT" for edge in edges),
            "integration_gap_count": len(gaps),
            "dependency_cycle_count": len(cycles),
            "canonical_records_mutated": 0,
            "innovations_promoted": 0,
            "connectivity_verified": False,
        },
        "limitations": [
            "Filename/content matches and token similarity are candidate links, not proof of implementation or semantic equivalence.",
            "The input federation may have been assembled from historical/source-asserted records; statuses are preserved without reinterpretation.",
            "Only the provided repository root is scanned. Other repositories require explicit source snapshots and their own inventory hashes.",
            "The report does not modify the Master Index or any source innovation record.",
        ],
    }
    return {**core, "graph_sha256": digest(core)}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Innovation federation JSON")
    parser.add_argument("--root", default=".", help="Repository root to index")
    parser.add_argument("--output", default="omega-innovation-integration-graph.json")
    args = parser.parse_args()
    try:
        source = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(source, dict):
            raise ValueError("input root must be a JSON object")
        graph = build_graph(source, Path(args.root))
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(graph, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"output": str(output), **graph["summary"], "graph_sha256": graph["graph_sha256"]}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
