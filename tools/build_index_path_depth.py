"""Build a deterministic, reference-derived depth map for the VAIXLNS index.

Depth is semantic link distance from docs/indexes/README.md, not filesystem
nesting. Unknown historical Master Index identifiers are never guessed.
"""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from collections import deque
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT_INDEX = "docs/indexes/README.md"
OUTPUT = "registry/index_path_depth.v1.json"
SCHEMA_ID = "VAIXLNS.IndexPathDepth.v1"
INDEXABLE_SUFFIXES = {
    ".md", ".rst", ".txt", ".json", ".yaml", ".yml", ".py", ".toml", ".sh"
}
SKIP_DIRS = {
    ".git", ".pytest_cache", ".mypy_cache", "__pycache__", "node_modules",
    ".venv", "venv", "dist", "build", "target", ".next", ".cache"
}
MARKDOWN_LINK_RE = re.compile(
    r"!?\[[^\]]*\]\(\s*<?([^\s)>]+)>?(?:\s+[\"'][^)]*[\"'])?\s*\)"
)
PATH_REFERENCE_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])"
    r"((?:[\w.@+-]+/)*[\w.@+-]+\."
    r"(?:md|rst|txt|json|ya?ml|py|toml|sh))"
    r"(?:#[\w.-]+)?",
    re.IGNORECASE,
)


def _indexable_files(repo_root: Path) -> set[str]:
    result: set[str] = set()
    for path in repo_root.rglob("*"):
        relative = path.relative_to(repo_root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in INDEXABLE_SUFFIXES:
            continue
        rel = relative.as_posix()
        # Exclude generated output as an input to prevent self-referential drift.
        if rel == OUTPUT:
            continue
        result.add(rel)
    return result


def _local_target(raw_target: str) -> tuple[str | None, bool]:
    target = unquote(raw_target.strip())
    if not target or target.startswith("#"):
        return None, False
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None, False
    target = parsed.path
    if not target:
        return None, False
    if target.startswith("/"):
        target = target.lstrip("/")
    return target, True


def _resolve_reference(source: str, raw_target: str, files: set[str]) -> tuple[str | None, str]:
    """Resolve a local reference safely; return (path, status)."""
    target, is_local = _local_target(raw_target)
    if not is_local or target is None:
        return None, "external"
    if "\\" in target:
        return None, "blocked"

    candidates: list[str] = []
    was_rooted = raw_target.strip().startswith("/")
    if not was_rooted:
        candidates.append(posixpath.normpath(posixpath.join(posixpath.dirname(source), target)))
    candidates.append(posixpath.normpath(target))

    expanded: list[str] = []
    for candidate in candidates:
        if candidate == ".." or candidate.startswith("../") or candidate.startswith("/"):
            continue
        expanded.append(candidate)
        if not Path(candidate).suffix:
            expanded.extend((
                candidate + ".md",
                posixpath.join(candidate, "README.md"),
                posixpath.join(candidate, "index.md"),
            ))
    for candidate in expanded:
        if candidate in files:
            return candidate, "resolved"

    basename = posixpath.basename(target)
    matches = sorted(path for path in files if posixpath.basename(path) == basename)
    if basename and len(matches) == 1:
        return matches[0], "resolved"

    normalized = posixpath.normpath(posixpath.join(posixpath.dirname(source), target))
    if normalized == ".." or normalized.startswith("../") or normalized.startswith("/"):
        return None, "blocked"
    return None, "unresolved"


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _collect_edges(repo_root: Path, files: set[str]):
    edge_map: dict[tuple[str, str], dict[str, object]] = {}
    broken: set[tuple[str, str, int]] = set()
    blocked: set[tuple[str, str, int]] = set()

    for source in sorted(files):
        try:
            text = (repo_root / source).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for match in MARKDOWN_LINK_RE.finditer(text):
            raw = match.group(1)
            resolved, status = _resolve_reference(source, raw, files)
            line = _line_number(text, match.start())
            if status == "resolved" and resolved:
                key = (source, resolved)
                edge_map[key] = {
                    "source": source, "target": resolved, "kind": "markdown_link",
                    "line": line, "reference": raw,
                }
            elif status == "unresolved":
                broken.add((source, raw, line))
            elif status == "blocked":
                blocked.add((source, raw, line))

        # Also index explicit file-path mentions, including plain filename bullets.
        for match in PATH_REFERENCE_RE.finditer(text):
            raw = match.group(1)
            resolved, status = _resolve_reference(source, raw, files)
            if status != "resolved" or not resolved:
                continue
            key = (source, resolved)
            edge_map.setdefault(key, {
                "source": source, "target": resolved, "kind": "explicit_path_reference",
                "line": _line_number(text, match.start()), "reference": raw,
            })

    edges = sorted(
        edge_map.values(),
        key=lambda e: (str(e["source"]), str(e["target"]), str(e["kind"]), int(e["line"])),
    )
    broken_links = [
        {"source": s, "target": t, "line": n} for s, t, n in sorted(broken)
    ]
    blocked_links = [
        {"source": s, "target": t, "line": n} for s, t, n in sorted(blocked)
    ]
    return edges, broken_links, blocked_links


def build_report(repo_root: Path, root_index: str = ROOT_INDEX) -> dict[str, object]:
    repo_root = repo_root.resolve()
    files = _indexable_files(repo_root)
    if root_index not in files:
        raise FileNotFoundError(f"Canonical root index is missing: {root_index}")

    edges, broken_links, blocked_links = _collect_edges(repo_root, files)
    adjacency: dict[str, list[dict[str, object]]] = {path: [] for path in files}
    for edge in edges:
        adjacency[str(edge["source"])].append(edge)
    for source in adjacency:
        adjacency[source].sort(
            key=lambda e: (str(e["target"]), str(e["kind"]), int(e["line"]))
        )

    depths: dict[str, int] = {root_index: 0}
    parents: dict[str, dict[str, object]] = {}
    queue: deque[str] = deque([root_index])
    while queue:
        source = queue.popleft()
        for edge in adjacency[source]:
            target = str(edge["target"])
            if target in depths:
                continue
            depths[target] = depths[source] + 1
            parents[target] = edge
            queue.append(target)

    def chain_for(path: str) -> list[str]:
        if path not in depths:
            return []
        chain = [path]
        while chain[-1] != root_index:
            chain.append(str(parents[chain[-1]]["source"]))
        chain.reverse()
        return chain

    nodes = []
    for path in sorted(files):
        parent = parents.get(path)
        nodes.append({
            "path": path,
            "depth": depths.get(path),
            "path_chain": chain_for(path),
            "predecessor": parent["source"] if parent else None,
            "reference_kind": parent["kind"] if parent else ("root" if path == root_index else None),
            "reference_line": parent["line"] if parent else None,
        })

    report: dict[str, object] = {
        "schema": SCHEMA_ID,
        "root": root_index,
        "depth_semantics": (
            "Shortest directed chain of explicit same-repository references from root; "
            "root depth is 0; null means unreachable and is not inferred from directory nesting."
        ),
        "file_count": len(files),
        "reachable_file_count": len(depths),
        "unreachable_file_count": len(files) - len(depths),
        "max_depth": max(depths.values(), default=0),
        "edge_count": len(edges),
        "broken_link_count": len(broken_links),
        "blocked_link_count": len(blocked_links),
        "nodes": nodes,
        "edges": edges,
        "broken_links": broken_links,
        "blocked_links": blocked_links,
    }
    validate_report(report)
    return report


def validate_report(report: dict[str, object]) -> None:
    if report.get("schema") != SCHEMA_ID:
        raise ValueError("Unexpected index path-depth schema")
    root, nodes = report.get("root"), report.get("nodes")
    if not isinstance(root, str) or not isinstance(nodes, list):
        raise ValueError("Report must contain root and nodes")
    by_path: dict[str, dict[str, object]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("path"), str):
            raise ValueError("Malformed node")
        path = str(node["path"])
        if path in by_path:
            raise ValueError(f"Duplicate node path: {path}")
        by_path[path] = node
        depth, chain = node.get("depth"), node.get("path_chain")
        if depth is None:
            if chain != []:
                raise ValueError(f"Unreachable node must have an empty path_chain: {path}")
        else:
            if not isinstance(depth, int) or depth < 0:
                raise ValueError(f"Invalid depth for {path}")
            if not isinstance(chain, list) or len(chain) != depth + 1:
                raise ValueError(f"Invalid path_chain for {path}")
            if not chain or chain[0] != root or chain[-1] != path:
                raise ValueError(f"Path chain endpoints are invalid for {path}")
    if root not in by_path or by_path[root].get("depth") != 0:
        raise ValueError("Root must exist with depth 0")
    reachable = sum(node.get("depth") is not None for node in nodes)
    if report.get("file_count") != len(nodes):
        raise ValueError("file_count does not match node inventory")
    if report.get("reachable_file_count") != reachable:
        raise ValueError("reachable_file_count does not match nodes")
    if report.get("unreachable_file_count") != len(nodes) - reachable:
        raise ValueError("unreachable_file_count does not match nodes")
    for count_key, list_key in (
        ("edge_count", "edges"), ("broken_link_count", "broken_links"),
        ("blocked_link_count", "blocked_links"),
    ):
        if report.get(count_key) != len(report.get(list_key, [])):
            raise ValueError(f"{count_key} does not match {list_key}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--root-index", default=ROOT_INDEX, help="Canonical root index path")
    parser.add_argument("--output", default=OUTPUT, help="Output path relative to repository root")
    parser.add_argument("--check", action="store_true", help="Fail if the output is stale")
    args = parser.parse_args()

    repo_root = args.root.resolve()
    output_path = (repo_root / args.output).resolve()
    try:
        report = build_report(repo_root, args.root_index)
        rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not output_path.exists():
                raise SystemExit(f"Generated report is missing: {args.output}")
            if output_path.read_text(encoding="utf-8") != rendered:
                raise SystemExit("Stale generated report: run python tools/build_index_path_depth.py")
            print(
                f"VALID index path depth: {report['reachable_file_count']}/{report['file_count']} "
                f"reachable; max depth={report['max_depth']}; "
                f"broken links={report['broken_link_count']}"
            )
            return 0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(
            f"BUILT index path depth: {report['reachable_file_count']}/{report['file_count']} "
            f"reachable; max depth={report['max_depth']}; "
            f"broken links={report['broken_link_count']}; "
            f"blocked links={report['blocked_link_count']}"
        )
        return 0
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"INDEX PATH-DEPTH ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
