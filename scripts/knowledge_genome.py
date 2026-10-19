#!/usr/bin/env python3
"""Deterministic, provenance-preserving file-level Knowledge Genome probe.

This tool inventories a local repository snapshot. It does not infer semantic
truth, authorize changes, or promote source files to VERIFIED. Run it against a
pinned checkout when reproducibility matters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "1.0.0"
MAX_FILE_BYTES_DEFAULT = 5 * 1024 * 1024
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".venv", "venv", "env", "node_modules",
    "vendor", "dist", "build", "target", "coverage", ".next", ".cache",
}
SENSITIVE_NAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
    "credentials.json", "service-account.json", "secrets.json",
}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore"}
SENSITIVE_NAME_PARTS = ("credential", "secret", "private-key", "private_key")
MARKDOWN_LINK_RE = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


def sha256_bytes(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def stable_artifact_id(repository_id: str, relative_path: str) -> str:
    key = f"{repository_id}\0{relative_path}".encode("utf-8")
    return "KG.FILE." + hashlib.sha256(key).hexdigest()[:20].upper()


def is_sensitive(relative_path: str) -> bool:
    p = PurePosixPath(relative_path)
    name = p.name.lower()
    if name in SENSITIVE_NAMES:
        return True
    if name.startswith(".env.") and name not in {".env.example", ".env.sample", ".env.template"}:
        return True
    if p.suffix.lower() in SENSITIVE_SUFFIXES:
        return True
    return any(part in name for part in SENSITIVE_NAME_PARTS)


def classify_file(relative_path: str) -> tuple[str, list[str]]:
    """Return transparent filename/path heuristics, not semantic conclusions."""
    p = PurePosixPath(relative_path)
    suffix = p.suffix.lower()
    name_parts = [part.lower() for part in p.parts]
    hints: set[str] = set()
    if "tests" in name_parts or p.name.startswith(("test_", "test-")) or p.name.endswith(("_test.py", ".test.ts", ".spec.ts")):
        hints.add("test-or-verification")
    if "schemas" in name_parts or suffix in {".schema", ".jsonschema"} or ".schema." in p.name:
        hints.add("schema-or-contract")
    if "docs" in name_parts or suffix in {".md", ".rst", ".adoc"}:
        hints.add("documentation-or-specification")
    if ".github" in name_parts or p.name in {"Dockerfile", "Makefile", "pyproject.toml", "Cargo.toml", "package.json"}:
        hints.add("build-or-operations")
    if "scripts" in name_parts or "tools" in name_parts:
        hints.add("tooling")
    if suffix in {".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".cs"}:
        hints.add("source-code")
    if suffix in {".json", ".yaml", ".yml", ".toml", ".ini"}:
        hints.add("structured-data-or-configuration")
    if not hints:
        hints.add("unclassified-file")
    return (suffix.lstrip(".") or "no-extension", sorted(hints))


def read_git_metadata(root: Path) -> tuple[str | None, str]:
    """Return the HEAD revision and explicit working-tree state when Git is available."""
    if not (root / ".git").exists():
        return None, "NOT_A_GIT_CHECKOUT"
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        revision_result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
            text=True, timeout=3, env=env,
        )
        revision = revision_result.stdout.strip()
        if revision_result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", revision):
            revision = None
        status_result = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
            text=True, timeout=5, env=env,
        )
        state = "CLEAN" if status_result.returncode == 0 and not status_result.stdout.strip() else "DIRTY_OR_UNKNOWN"
        return revision, state
    except (OSError, subprocess.SubprocessError):
        return None, "DIRTY_OR_UNKNOWN"


def walk_files(root: Path, counts: dict[str, int], excluded_paths: set[str]):
    """Yield sorted regular files and update exclusion counters without following symlinks."""
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_dirs = []
        for dirname in sorted(dirs):
            candidate = current_path / dirname
            if dirname in EXCLUDED_DIRS:
                counts["excluded_directories_skipped"] += 1
                continue
            if candidate.is_symlink():
                counts["symlinks_skipped"] += 1
                continue
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs
        for filename in sorted(files):
            candidate = current_path / filename
            relative = candidate.relative_to(root).as_posix()
            if candidate.is_symlink():
                counts["symlinks_skipped"] += 1
                continue
            if relative in excluded_paths:
                counts["control_files_excluded"] += 1
                continue
            if is_sensitive(relative):
                counts["sensitive_files_excluded"] += 1
                continue
            try:
                if not candidate.is_file():
                    continue
                size = candidate.stat().st_size
            except OSError:
                continue
            yield candidate, relative, size, counts


def read_baseline(path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != SCHEMA_VERSION or not isinstance(raw.get("artifacts"), list):
        raise ValueError("baseline_schema_or_shape_invalid")
    result: dict[str, dict[str, Any]] = {}
    for item in raw["artifacts"]:
        artifact_id = item.get("artifact_id")
        if not isinstance(artifact_id, str) or artifact_id in result:
            raise ValueError("baseline_duplicate_or_missing_artifact_id")
        result[artifact_id] = item
    return result


def local_markdown_relations(
    root: Path, artifacts: list[dict[str, Any]], by_path: dict[str, str]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Return resolvable local reference edges and explicit unresolved-link records."""
    relations: set[tuple[str, str, str]] = set()
    unresolved: set[tuple[str, str, str]] = set()
    for artifact in artifacts:
        if artifact["file_kind"] not in {"md", "markdown", "rst", "adoc"}:
            continue
        source_path = artifact["source"]["path"]
        full_path = root / source_path
        try:
            text = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            target = raw_target.strip().split("#", 1)[0].split("?", 1)[0]
            if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith(("/", "//", "mailto:")):
                continue
            parts = list(PurePosixPath(source_path).parent.parts)
            escaped = False
            for part in PurePosixPath(target).parts:
                if part in {"", "."}:
                    continue
                if part == "..":
                    if parts:
                        parts.pop()
                    else:
                        escaped = True
                        break
                else:
                    parts.append(part)
            normalized = PurePosixPath(*parts).as_posix() if parts else "."
            if escaped:
                unresolved.add((artifact["artifact_id"], "", "LINK_ESCAPES_REPOSITORY"))
                continue
            target_id = by_path.get(normalized)
            if target_id and target_id != artifact["artifact_id"]:
                relations.add((artifact["artifact_id"], "REFERENCES", target_id))
            elif is_sensitive(normalized):
                unresolved.add((artifact["artifact_id"], normalized, "EXCLUDED_SENSITIVE_TARGET"))
            else:
                unresolved.add((artifact["artifact_id"], normalized, "UNRESOLVED_LOCAL_TARGET"))
    return (
        [
            {"from_artifact_id": a, "relation": rel, "to_artifact_id": b}
            for a, rel, b in sorted(relations)
        ],
        [
            {"from_artifact_id": a, "target_path": path, "status": status}
            for a, path, status in sorted(unresolved)
        ],
    )


def exact_duplicate_relations(artifacts: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Link byte-identical files without implying semantic equivalence."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for artifact in artifacts:
        digest = artifact["source"]["content_sha256"]
        groups.setdefault(digest, []).append(artifact)
    edges: list[dict[str, str]] = []
    for group in groups.values():
        if len(group) < 2:
            continue
        ordered = sorted(group, key=lambda item: (item["source"]["path"], item["artifact_id"]))
        anchor = ordered[0]["artifact_id"]
        for duplicate in ordered[1:]:
            edges.append({
                "from_artifact_id": duplicate["artifact_id"],
                "relation": "EXACT_BYTE_DUPLICATE_OF",
                "to_artifact_id": anchor,
            })
    return sorted(edges, key=lambda item: (item["from_artifact_id"], item["relation"], item["to_artifact_id"]))


def build_genome(root_arg: Path, repository_id: str, max_file_bytes: int, baseline_path: Path | None = None, exclude_paths: list[Path] | None = None) -> dict[str, Any]:
    root = root_arg.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("repository_root_must_be_existing_directory")
    if not repository_id.strip():
        raise ValueError("repository_id_must_not_be_empty")
    if max_file_bytes < 1:
        raise ValueError("max_file_bytes_must_be_positive")

    baseline = read_baseline(baseline_path) if baseline_path else {}
    artifacts: list[dict[str, Any]] = []
    by_path: dict[str, str] = {}
    excluded_counts = {"sensitive_files_excluded": 0, "oversize_files_skipped": 0, "symlinks_skipped": 0, "excluded_directories_skipped": 0, "control_files_excluded": 0}
    paths_to_exclude = list(exclude_paths or [])
    if baseline_path is not None:
        paths_to_exclude.append(baseline_path)
    excluded_relative_paths: set[str] = set()
    for excluded_path in paths_to_exclude:
        try:
            excluded_relative_paths.add(excluded_path.resolve().relative_to(root).as_posix())
        except ValueError:
            continue
    revision, working_tree_state = read_git_metadata(root)
    for path, relative, size, _counts in walk_files(root, excluded_counts, excluded_relative_paths):
        if size > max_file_bytes:
            excluded_counts["oversize_files_skipped"] += 1
            continue
        try:
            content = path.read_bytes()
        except OSError:
            continue
        artifact_id = stable_artifact_id(repository_id, relative)
        file_kind, hints = classify_file(relative)
        previous = baseline.get(artifact_id)
        digest = sha256_bytes(content)
        if previous is None:
            change_state = "NEW" if baseline_path else "SNAPSHOT"
        elif previous.get("source", {}).get("content_sha256") == digest:
            change_state = "UNCHANGED"
        else:
            change_state = "CHANGED"
        artifact = {
            "artifact_id": artifact_id,
            "record_type": "SOURCE_FILE_OBSERVATION",
            "file_kind": file_kind,
            "classification_hints": hints,
            "semantic_status": "NOT_EXTRACTED",
            "change_state": change_state,
            "source": {
                "repository_id": repository_id,
                "revision": revision,
                "working_tree_state": working_tree_state,
                "path": relative,
                "size_bytes": len(content),
                "content_sha256": digest,
            },
        }
        artifacts.append(artifact)
        by_path[relative] = artifact_id
    artifacts.sort(key=lambda item: (item["source"]["path"], item["artifact_id"]))
    reference_relations, unresolved_references = local_markdown_relations(root, artifacts, by_path)
    duplicate_relations = exact_duplicate_relations(artifacts)
    relations = sorted(reference_relations + duplicate_relations, key=lambda item: (item["from_artifact_id"], item["relation"], item["to_artifact_id"]))
    current_ids = {item["artifact_id"] for item in artifacts}
    missing = []
    for artifact_id, previous in sorted(baseline.items()):
        if artifact_id not in current_ids:
            missing.append({
                "artifact_id": artifact_id,
                "path": previous.get("source", {}).get("path"),
                "status": "MISSING_FROM_CURRENT_SNAPSHOT",
                "previous_content_sha256": previous.get("source", {}).get("content_sha256"),
                "action": "PRESERVE_RECORD_NO_DELETE_OR_ARCHIVE_AUTHORIZED",
            })
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "genome_type": "FILE_LEVEL_KNOWLEDGE_GENOME",
        "repository": {"repository_id": repository_id, "revision": revision, "working_tree_state": working_tree_state},
        "epistemic_state": "PARTIAL",
        "scope": "local file inventory, SHA-256 fingerprints, non-authoritative filename/path hints, Markdown reference resolution, exact byte-duplicate edges, and baseline diff",
        "limitations": [
            "No semantic meaning is asserted from filenames, paths, or hashes.",
            "External repositories and remote references are not fetched by this local probe.",
            "Exact byte duplicates do not imply semantic duplicates or interchangeable behavior.",
            "A matching hash establishes byte equality only, not correctness or authority.",
            "VERIFIED and CANONICAL promotion require independent tests, provenance, and an authority gate.",
        ],
        "policy": {
            "no_destructive_operations": True,
            "missing_items_are_preserved": True,
            "sensitive_files_excluded": True,
            "oversize_files_are_skipped_and_counted": True,
            "classification_hints_are_non_authoritative": True,
        },
        "coverage": {
            "captured_artifacts": len(artifacts),
            "reference_relations": len(reference_relations),
            "exact_byte_duplicate_relations": len(duplicate_relations),
            "unresolved_local_references": len(unresolved_references),
            "missing_from_current_snapshot": len(missing),
            "oversize_files_skipped": excluded_counts["oversize_files_skipped"],
            "sensitive_files_excluded": excluded_counts["sensitive_files_excluded"],
            "symlinks_skipped": excluded_counts["symlinks_skipped"],
            "excluded_directories_skipped": excluded_counts["excluded_directories_skipped"],
            "control_files_excluded": excluded_counts["control_files_excluded"],
        },
        "artifacts": artifacts,
        "relations": relations,
        "unresolved_references": unresolved_references,
        "missing_from_current_snapshot": missing,
    }
    body["snapshot_fingerprint"] = sha256_bytes(canonical_json(body))
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository checkout directory (default: current directory)")
    parser.add_argument("--repository-id", required=True, help="stable identity such as owner/repository")
    parser.add_argument("--output", help="write JSON report to this path; stdout when omitted")
    parser.add_argument("--baseline", help="prior genome JSON; missing artifacts are recorded, never deleted")
    parser.add_argument("--max-file-bytes", type=int, default=MAX_FILE_BYTES_DEFAULT)
    args = parser.parse_args(argv)
    try:
        output_path = Path(args.output) if args.output else None
        report = build_genome(Path(args.root), args.repository_id, args.max_file_bytes, Path(args.baseline) if args.baseline else None, [output_path] if output_path else None)
        encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(encoded, encoding="utf-8")
        else:
            sys.stdout.write(encoded)
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
