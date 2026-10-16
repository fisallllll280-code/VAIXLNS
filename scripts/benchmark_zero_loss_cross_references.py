#!/usr/bin/env python3
"""Reproducible microbenchmark for the zero-loss index cross-reference stage.

This compares the previous all-path scan against the optimized candidate lookup
on the same synthetic corpus and verifies identical reference edges. It measures
only this index stage, not end-to-end VX runtime performance.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from scripts.build_zero_loss_index import _build_cross_references, _path_reference_line


def old_all_paths_scan(sources: list[dict[str, str]], text_by_path: dict[str, str]) -> list[tuple[str, str]]:
    known_paths = {source["path"] for source in sources}
    edges: list[tuple[str, str]] = []
    for source_path in sorted(text_by_path):
        content = text_by_path[source_path]
        for target_path in sorted(known_paths):
            if target_path == source_path:
                continue
            if _path_reference_line(content, target_path) is not None:
                edges.append((source_path, target_path))
    return sorted(set(edges))


def optimized_scan(sources: list[dict[str, str]], text_by_path: dict[str, str]) -> list[tuple[str, str]]:
    refs = _build_cross_references(sources, text_by_path)
    return sorted({(item["from_path"], item["to_path"]) for item in refs})


def run(paths_count: int, documents_count: int, repeats: int) -> dict[str, object]:
    sources = [{"path": f"pkg/module_{i:05d}.py", "source_id": f"SRC-{i:05d}"} for i in range(paths_count)]
    sources += [{"path": f"docs/doc_{i:05d}.md", "source_id": f"DOC-{i:05d}"} for i in range(documents_count)]
    texts: dict[str, str] = {}
    for i in range(documents_count):
        target_a = f"pkg/module_{(i * 37) % paths_count:05d}.py"
        target_b = f"pkg/module_{(i * 71 + 3) % paths_count:05d}.py"
        texts[f"docs/doc_{i:05d}.md"] = (
            f"Uses {target_a} and {target_b}. "
            f"Repeated prose for realistic scanning. {'engineering design notes ' * 12}\n"
        )
    baseline_edges = old_all_paths_scan(sources, texts)
    candidate_edges = optimized_scan(sources, texts)
    if baseline_edges != candidate_edges:
        raise RuntimeError("REFERENCE_EDGE_PARITY_FAILURE")
    baseline_times: list[float] = []
    candidate_times: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        old_all_paths_scan(sources, texts)
        baseline_times.append(time.perf_counter() - start)
        start = time.perf_counter()
        optimized_scan(sources, texts)
        candidate_times.append(time.perf_counter() - start)
    baseline = statistics.median(baseline_times)
    candidate = statistics.median(candidate_times)
    return {
        "schema_version": "vx-index-cross-reference-benchmark.v1",
        "state": "PASS",
        "scope": "zero-loss index cross-reference stage only; not end-to-end VX runtime",
        "paths": paths_count,
        "text_documents": documents_count,
        "repeats": repeats,
        "reference_edge_count": len(baseline_edges),
        "edge_parity": True,
        "baseline_median_seconds": round(baseline, 6),
        "optimized_median_seconds": round(candidate, 6),
        "speedup_x": round(baseline / candidate, 3) if candidate else None,
        "performance_target_10x_met": bool(candidate and baseline / candidate >= 10),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", type=int, default=1200)
    parser.add_argument("--documents", type=int, default=300)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.paths < 10 or args.documents < 1 or args.repeats < 1:
        parser.error("paths must be >=10; documents and repeats must be >=1")
    report = run(args.paths, args.documents, args.repeats)
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
