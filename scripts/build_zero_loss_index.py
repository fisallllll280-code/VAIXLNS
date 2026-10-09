#!/usr/bin/env python3
"""Build the VAIXLNS ZERO-LOSS INDEX from the checked-out repository.

The builder is deterministic for a fixed source tree. It never deletes or
rewrites source files and never promotes records to CANONICAL, IMPLEMENTED,
or VERIFIED. Run it against an immutable checkout and retain the output hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import posixpath
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TAXONOMY_RELATIVE_PATH = Path("registry/indexes/zero-loss-index-taxonomy.v1.json")
DEFAULT_OUTPUT_RELATIVE_PATH = Path("build/zero-loss-index")
ARTIFACT_NAMES = {
    "index": "zero-loss-index.v1.json",
    "sources": "zero-loss-source-index.v1.json",
    "records": "zero-loss-atomic-records.v1.jsonl",
    "coverage": "zero-loss-coverage.v1.json",
    "cross_references": "zero-loss-cross-reference.v1.json",
}
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "site-packages", "build", "dist", "target",
}
BINARY_SUFFIXES = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".eot", ".zip", ".gz", ".7z",
    ".tar", ".xz", ".sqlite", ".db", ".mp4", ".mov", ".mp3", ".wav",
    ".p12", ".pfx", ".pem", ".key",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".drawio"}
LEGACY_KEY_PATTERN = re.compile(
    r"""(?i)(?:["']?legacy[_ -]?id["']?|legacy\s+(?:master\s+)?(?:entry|item|record|identifier)|historical\s+id)\s*["']?\s*[:=|#-]\s*["']?(\d{1,6})\b"""
)
HEADING_PATTERN = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
LIST_ITEM_PATTERN = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$")
ACRONYM_PATTERN = re.compile(r"\b[A-Z][A-Z0-9]{1,11}(?:-[A-Z0-9]{1,8})*\b")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HEX_256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ARCHITECTURE_PATTERN = re.compile(r"(?<![A-Za-z0-9_])(?:VAIXLNS|NEXENT|AURX|VV|VX|XV|LNS|VA)(?![A-Za-z0-9_])", re.I)


class IndexBuildError(RuntimeError):
    """Raised when an index invariant cannot be established."""


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _jsonl_bytes(records: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in records
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_hash(value: Any) -> str:
    return _sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _as_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, (list, tuple, set)) else [value]
    result: list[str] = []
    for item in values:
        text = _as_text(item)
        if text is not None:
            result.append(text)
    return result


def _relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _git_revision(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=3,
        )
        revision = result.stdout.strip()
        return revision if re.fullmatch(r"[0-9a-f]{40,64}", revision) else "UNPINNED_LOCAL_CHECKOUT"
    except (OSError, subprocess.SubprocessError):
        return "UNPINNED_LOCAL_CHECKOUT"


def _source_kind(path: Path) -> str:
    lower = path.as_posix().lower()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "PDF"
    if suffix in IMAGE_SUFFIXES and any(token in lower for token in ("diagram", "drawing", "figure", "visual", "architecture", "assets/")):
        return "DIAGRAM"
    if suffix in IMAGE_SUFFIXES:
        return "IMAGE_ARTIFACT"
    if lower.startswith(".github/workflows/"):
        return "WORKFLOW"
    if path.parts and path.parts[0].lower() == "tests":
        return "TEST"
    if lower.startswith("schemas/"):
        return "SCHEMA"
    if lower.startswith(("archive/", "recovery/")):
        return "ARCHIVE"
    if lower.startswith(("scripts/", "tools/")):
        return "ENGINEERING_TOOL"
    if lower.startswith("docs/"):
        return "DOCUMENT"
    if suffix in {".py", ".rs", ".go", ".js", ".jsx", ".ts", ".tsx", ".sh", ".bash", ".sql", ".tf"}:
        return "IMPLEMENTATION_SOURCE"
    return "REPOSITORY_FILE"


def _read_source(path: Path) -> tuple[bytes, str | None, str, str]:
    if path.is_symlink():
        target = os.readlink(path)
        return target.encode("utf-8"), None, "SYMLINK_TARGET_TEXT_SHA256", "SYMLINK"
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise IndexBuildError(f"SOURCE_READ_FAILED:{path}:{exc}") from exc
    if path.suffix.lower() in BINARY_SUFFIXES:
        return raw, None, "SOURCE_BYTES_SHA256", "OPAQUE_BINARY"
    try:
        return raw, raw.decode("utf-8-sig"), "SOURCE_BYTES_SHA256", "UTF-8"
    except UnicodeDecodeError:
        return raw, None, "SOURCE_BYTES_SHA256", "OPAQUE_BINARY"


def _discover_sources(root: Path, output_dir: Path) -> list[Path]:
    discovered: list[Path] = []
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_dirs: list[str] = []
        linked_dirs: list[Path] = []
        for dirname in sorted(dirnames):
            child = current_path / dirname
            if dirname in EXCLUDED_DIRS or _is_within(child, output_dir):
                continue
            if child.is_symlink():
                linked_dirs.append(child)
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs
        for path in linked_dirs:
            discovered.append(path)
        for filename in sorted(filenames):
            path = current_path / filename
            if _is_within(path, output_dir):
                continue
            if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
                continue
            discovered.append(path)
    return sorted(set(discovered), key=lambda item: item.relative_to(root).as_posix())


def _record_uid(source_id: str, location: dict[str, Any], record_kind: str, name: str, fragment_sha256: str | None) -> str:
    identity = {
        "source_id": source_id,
        "location": location,
        "record_kind": record_kind,
        "name": name,
        "fragment_sha256": fragment_sha256,
    }
    return "ATOM-" + _canonical_hash(identity)[:24]


def _record_base(
    source: dict[str, Any],
    record_kind: str,
    name: str,
    location: dict[str, Any],
    *,
    ingestion_state: str,
    fragment_sha256: str | None = None,
    fragment_hash_kind: str | None = None,
    source_excerpt: str | None = None,
    parent: str | None = None,
    source_fields: list[str] | None = None,
    explicit: dict[str, Any] | None = None,
    classification_status: str = "UNRESOLVED",
) -> dict[str, Any]:
    explicit = explicit or {}
    uid = _record_uid(source["source_id"], location, record_kind, name, fragment_sha256)
    source_status = _as_text(explicit.get("status"))
    source_type = _as_text(explicit.get("type"))
    state_value = explicit.get("state_model", explicit.get("state"))
    if not isinstance(state_value, dict):
        state_value = {"source_state": state_value, "source_claim_only": True} if state_value is not None else None
    explicit_origin = _as_text(explicit.get("origin"))
    source_lineage = [source["source_id"]]
    if parent:
        source_lineage.append(parent)
    record = {
        "uid": uid,
        "source_id": source["source_id"],
        "source_location": location,
        "source_sha256": source["sha256"],
        "fragment_sha256": fragment_sha256,
        "fragment_hash_kind": fragment_hash_kind,
        "legacy_id": _as_text(explicit.get("legacy_id", explicit.get("legacyId"))),
        "canonical_id": _as_text(explicit.get("canonical_id")),
        "name": name or "(unnamed source item)",
        "aliases": _string_list(explicit.get("aliases")),
        "type": source_type or record_kind,
        "family": _as_text(explicit.get("family")),
        "domain": _as_text(explicit.get("domain")),
        "origin": explicit_origin or source["source_kind"],
        "meaning": _as_text(explicit.get("meaning", explicit.get("description"))),
        "status": "RECOVERED",
        "classification_status": classification_status,
        "semantic_status": "UNRESOLVED",
        "ingestion_state": ingestion_state,
        "parent": parent,
        "children": [],
        "lineage": source_lineage,
        "supersedes": _string_list(explicit.get("supersedes")),
        "superseded_by": _string_list(explicit.get("superseded_by")),
        "dependencies": _string_list(explicit.get("dependencies")),
        "capabilities": _string_list(explicit.get("capabilities")),
        "contracts": _string_list(explicit.get("contracts")),
        "authority": _string_list(explicit.get("authority")),
        "relations": _string_list(explicit.get("relations", explicit.get("relationships"))),
        "state": state_value if state_value is not None else {"ingestion_state": ingestion_state},
        "events": _string_list(explicit.get("events")),
        "execution": _string_list(explicit.get("execution")) or ["NOT_EXECUTED_BY_INDEXER"],
        "evidence": [f"SOURCE_SHA256:{source['sha256']}"],
        "proof": _string_list(explicit.get("proof")),
        "implementation": _string_list(explicit.get("implementation")),
        "tests": _string_list(explicit.get("tests")),
        "failure": _string_list(explicit.get("failure", explicit.get("failure_modes"))),
        "recovery": _string_list(explicit.get("recovery")),
        "version": _as_text(explicit.get("version", explicit.get("schema_version"))),
        "lifecycle": _as_text(explicit.get("lifecycle", explicit.get("lifecycle_state"))),
        "evolution": _string_list(explicit.get("evolution", explicit.get("evolution_eligibility"))),
        "source_claimed_status": source_status,
        "source_fields": sorted(source_fields or []),
        "source_excerpt": source_excerpt,
        "_record_kind": record_kind,
        "_search_text": source_excerpt or name,
    }
    return record


def _line_location(path: str, start: int | None, end: int | None) -> dict[str, Any]:
    return {"path": path, "line_start": start, "line_end": end, "json_pointer": None}


def _explicit_legacy_ids(text: str) -> set[int]:
    found: set[int] = set()
    for match in LEGACY_KEY_PATTERN.finditer(text):
        try:
            found.add(int(match.group(1)))
        except ValueError:
            continue
    return found


def _walk_json(value: Any, pointer: str = ""):
    if isinstance(value, dict):
        yield pointer or "", value
        for key in sorted(value):
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from _walk_json(value[key], f"{pointer}/{escaped}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_json(child, f"{pointer}/{index}")


def _meaning_from_term_line(term: str, line: str) -> str | None:
    pattern = re.compile(r"\b" + re.escape(term) + r"\s*(?:—|–|::|:|=)\s*(.+)$")
    match = pattern.search(line.strip())
    if not match:
        return None
    value = match.group(1).strip(" \t*_")
    return value[:400] if len(value) >= 4 else None


def _extract_markdown_records(source: dict[str, Any], source_record_uid: str, text: str) -> list[dict[str, Any]]:
    path = source["path"]
    lines = text.splitlines(keepends=True)
    if not lines:
        return []
    records: list[dict[str, Any]] = []
    headings: list[tuple[int, str]] = []
    for number, line in enumerate(lines, start=1):
        match = HEADING_PATTERN.match(line.rstrip("\r\n"))
        if match:
            headings.append((number, match.group(2).strip()))
    section_ranges: list[tuple[int, int, str]] = []
    if headings:
        if headings[0][0] > 1 and any(line.strip() for line in lines[: headings[0][0] - 1]):
            section_ranges.append((1, headings[0][0] - 1, "Document preamble"))
        for index, (start, name) in enumerate(headings):
            end = headings[index + 1][0] - 1 if index + 1 < len(headings) else len(lines)
            section_ranges.append((start, end, name))
    elif text.strip():
        section_ranges.append((1, len(lines), Path(path).name))
    parent_by_line: dict[int, str] = {}
    for start, end, name in section_ranges:
        excerpt = "".join(lines[start - 1 : end])
        record = _record_base(
            source, "SOURCE_SECTION", name, _line_location(path, start, end),
            ingestion_state="ATOMIC", fragment_sha256=_sha256(excerpt.encode("utf-8")),
            fragment_hash_kind="NORMALIZED_UTF8_SPAN_SHA256", source_excerpt=excerpt,
            parent=source_record_uid, classification_status="CLASSIFIED" if name != "Document preamble" else "UNRESOLVED",
        )
        record["_search_text"] = excerpt
        records.append(record)
        for line_number in range(start, end + 1):
            parent_by_line[line_number] = record["uid"]
    for number, line in enumerate(lines, start=1):
        match = LIST_ITEM_PATTERN.match(line.rstrip("\r\n"))
        if not match or HEADING_PATTERN.match(line.rstrip("\r\n")):
            continue
        item_name = match.group(1).strip()
        if not item_name:
            continue
        parent = parent_by_line.get(number, source_record_uid)
        record = _record_base(
            source, "SOURCE_LIST_ITEM", item_name, _line_location(path, number, number),
            ingestion_state="ATOMIC", fragment_sha256=_sha256(line.encode("utf-8")),
            fragment_hash_kind="NORMALIZED_UTF8_LINE_SHA256", source_excerpt=line,
            parent=parent, classification_status="CLASSIFIED",
        )
        record["_search_text"] = line.rstrip("\r\n")
        records.append(record)
    return records


def _extract_text_block_records(source: dict[str, Any], source_record_uid: str, text: str) -> list[dict[str, Any]]:
    if not text.strip():
        return []
    path = source["path"]
    lines = text.splitlines(keepends=True)
    records: list[dict[str, Any]] = []
    start: int | None = None
    for number, line in enumerate(lines + ["\n"], start=1):
        if line.strip():
            if start is None:
                start = number
            continue
        if start is None:
            continue
        end = number - 1
        excerpt = "".join(lines[start - 1 : end])
        name = next((item.strip() for item in excerpt.splitlines() if item.strip()), Path(path).name)[:180]
        record = _record_base(
            source, "SOURCE_BLOCK", name, _line_location(path, start, end),
            ingestion_state="ATOMIC", fragment_sha256=_sha256(excerpt.encode("utf-8")),
            fragment_hash_kind="NORMALIZED_UTF8_BLOCK_SHA256", source_excerpt=excerpt,
            parent=source_record_uid, classification_status="UNRESOLVED",
        )
        record["_search_text"] = excerpt
        records.append(record)
        start = None
    return records


def _extract_json_records(source: dict[str, Any], source_record_uid: str, text: str) -> tuple[list[dict[str, Any]], set[int]]:
    try:
        document = json.loads(text)
    except (json.JSONDecodeError, RecursionError):
        return [], set()
    records: list[dict[str, Any]] = []
    observed_legacy: set[int] = set()
    for pointer, node in _walk_json(document):
        if not isinstance(node, dict):
            continue
        if "legacy_id" in node or "legacyId" in node:
            raw_legacy = _as_text(node.get("legacy_id", node.get("legacyId")))
            if raw_legacy and raw_legacy.isdigit():
                observed_legacy.add(int(raw_legacy))
        meaningful_identity = any(key in node for key in ("canonical_id", "legacy_id", "legacyId", "name", "title", "label"))
        structured_context = any(key in node for key in ("id", "type", "role", "meaning", "description", "canonical_id", "legacy_id", "legacyId"))
        if not (meaningful_identity and structured_context):
            continue
        name = next(
            (_as_text(node.get(key)) for key in ("name", "title", "label", "canonical_id", "id", "legacy_id", "legacyId") if _as_text(node.get(key))),
            None,
        )
        if not name:
            continue
        serialized = json.dumps(node, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        excerpt = serialized if len(serialized) <= 12000 else serialized[:4000] + " ... [SOURCE OBJECT EXCERPT TRUNCATED; FULL FILE HASH RETAINED]"
        location = {"path": source["path"], "line_start": None, "line_end": None, "json_pointer": pointer or "/"}
        record = _record_base(
            source, "JSON_ENTITY", name, location,
            ingestion_state="ATOMIC", fragment_sha256=_sha256(serialized.encode("utf-8")),
            fragment_hash_kind="CANONICAL_JSON_VALUE_SHA256", source_excerpt=excerpt,
            parent=source_record_uid, source_fields=list(node.keys()), explicit=node,
            classification_status="CLASSIFIED",
        )
        record["_search_text"] = serialized
        records.append(record)
    return records, observed_legacy


def _extract_term_records(source: dict[str, Any], source_record_uid: str, text: str) -> list[dict[str, Any]]:
    if Path(source["path"]).suffix.lower() not in {".md", ".markdown", ".txt", ".rst", ".json", ".yaml", ".yml", ".toml"}:
        return []
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for number, line in enumerate(text.splitlines(keepends=True), start=1):
        for match in ACRONYM_PATTERN.finditer(line):
            term = match.group(0).strip("-")
            if term in seen:
                continue
            seen.add(term)
            meaning = _meaning_from_term_line(term, line)
            excerpt = line.rstrip("\r\n")
            explicit = {"meaning": meaning} if meaning else {}
            record = _record_base(
                source, "TERMINOLOGY_CANDIDATE", term, _line_location(source["path"], number, number),
                ingestion_state="ATOMIC", fragment_sha256=_sha256(line.encode("utf-8")),
                fragment_hash_kind="NORMALIZED_UTF8_LINE_SHA256", source_excerpt=excerpt[:2000],
                parent=source_record_uid, classification_status="CLASSIFIED" if meaning else "UNRESOLVED",
                explicit=explicit,
            )
            record["_search_text"] = excerpt
            records.append(record)
    return records


def _format_legacy(number: int) -> str:
    return str(number).zfill(4)


def _compress_ranges(numbers: set[int], start: int, end: int) -> list[dict[str, Any]]:
    missing = sorted(set(range(start, end + 1)) - numbers)
    if not missing:
        return []
    ranges: list[dict[str, Any]] = []
    first = previous = missing[0]
    for number in missing[1:]:
        if number == previous + 1:
            previous = number
            continue
        ranges.append({"start": _format_legacy(first), "end": _format_legacy(previous)})
        first = previous = number
    ranges.append({"start": _format_legacy(first), "end": _format_legacy(previous)})
    return ranges


def _path_reference_line(text: str, token: str) -> int | None:
    escaped = re.escape(token)
    pattern = re.compile(r"(?<![A-Za-z0-9_./-])" + escaped + r"(?![A-Za-z0-9_./-])")
    match = pattern.search(text)
    return text.count("\n", 0, match.start()) + 1 if match else None


def _resolve_markdown_target(source_path: str, raw_target: str, known_paths: set[str]) -> str | None:
    target = raw_target.strip().strip("<>")
    if not target or target.startswith(("http://", "https://", "mailto:", "#", "data:")):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return None
    if target in known_paths:
        return target
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), target))
    return resolved if resolved in known_paths else None


def _build_cross_references(sources: list[dict[str, Any]], text_by_path: dict[str, str]) -> list[dict[str, Any]]:
    known_paths = {source["path"] for source in sources}
    source_by_path = {source["path"]: source for source in sources}
    results: list[dict[str, Any]] = []
    for source_path in sorted(text_by_path):
        content = text_by_path[source_path]
        matches: dict[str, tuple[int | None, str]] = {}
        for raw_target in MARKDOWN_LINK_PATTERN.findall(content):
            resolved = _resolve_markdown_target(source_path, raw_target, known_paths)
            if resolved and resolved != source_path:
                position = content.find(raw_target)
                line = content.count("\n", 0, max(position, 0)) + 1 if position >= 0 else None
                matches.setdefault(resolved, (line, raw_target))
        for target_path in sorted(known_paths):
            if target_path == source_path or target_path in matches:
                continue
            line = _path_reference_line(content, target_path)
            if line is not None:
                matches[target_path] = (line, target_path)
        for target_path, (line, token) in sorted(matches.items()):
            results.append({
                "from_source_id": source_by_path[source_path]["source_id"],
                "from_path": source_path,
                "to_source_id": source_by_path[target_path]["source_id"],
                "to_path": target_path,
                "relationship": "SOURCE_PATH_REFERENCE",
                "classification_status": "DIRECT_TEXT_REFERENCE_NOT_DEPENDENCY",
                "evidence": {"source_path": source_path, "line": line, "matched_token": token},
            })
    return results


def _view_match(spec: dict[str, Any], record: dict[str, Any], search_text: str, referenced_source_ids: set[str]) -> bool:
    key = spec["key"]
    kind = record["_record_kind"]
    path = record["source_location"]["path"].casefold()
    text = (path + "\n" + record["name"] + "\n" + search_text).casefold()
    if key in {"source_index", "artifact_index"}:
        return kind == "SOURCE_FILE"
    if key == "legacy_master_index":
        return record["legacy_id"] is not None
    if key == "entity_index":
        return kind in {"JSON_ENTITY", "SOURCE_SECTION", "SOURCE_LIST_ITEM", "SOURCE_BLOCK"}
    if key == "terminology_index":
        return kind == "TERMINOLOGY_CANDIDATE"
    if key == "cross_reference_index":
        return record["source_id"] in referenced_source_ids or kind in {"SOURCE_FILE", "JSON_ENTITY", "SOURCE_SECTION", "SOURCE_LIST_ITEM", "TERMINOLOGY_CANDIDATE"}
    if key == "architecture_index" and ARCHITECTURE_PATTERN.search(text):
        return True
    path_match = any(token.casefold() in path for token in spec.get("path_tokens", []))
    content_match = any(token.casefold() in text for token in spec.get("path_tokens", []))
    source_fields = set(record.get("source_fields", []))
    explicit_field_match = any(field in source_fields for field in spec.get("explicit_fields", []))
    populated_field_match = any(bool(record.get(field)) for field in spec.get("explicit_fields", []))
    if key == "repository_index" and ("github.com/" in text or "repo:" in text):
        return True
    return path_match or content_match or explicit_field_match or populated_field_match


def validate_transition(record: dict[str, Any], target_state: str, authority_evidence: str | None = None) -> None:
    """Validate a requested state transition without performing it."""
    source_id = record.get("source_id")
    source_digest = record.get("source_sha256")
    location = record.get("source_location")
    lineage = record.get("lineage")
    if target_state == "ATOMIC":
        if not source_id or not isinstance(source_digest, str) or not HEX_256_PATTERN.fullmatch(source_digest):
            raise ValueError("ATOMIC_REQUIRES_SOURCE_ID_AND_SHA256")
        if not isinstance(location, dict) or not location.get("path"):
            raise ValueError("ATOMIC_REQUIRES_TRACEABLE_SOURCE_LOCATION")
        if not isinstance(lineage, list) or source_id not in lineage:
            raise ValueError("ATOMIC_REQUIRES_SOURCE_LINEAGE")
        return
    if target_state == "CANONICAL":
        if not record.get("canonical_id"):
            raise ValueError("CANONICAL_REQUIRES_SOURCE_GROUNDED_CANONICAL_ID")
        if not authority_evidence:
            raise ValueError("CANONICAL_REQUIRES_EXPLICIT_AUTHORITY_EVIDENCE")
        raise ValueError("CANONICAL_ADMISSION_REQUIRES_SEPARATE_AUTHORIZED_GATE")
    if target_state == "IMPLEMENTED":
        if not record.get("implementation") or not record.get("tests") or not record.get("evidence"):
            raise ValueError("IMPLEMENTED_REQUIRES_IMPLEMENTATION_TEST_AND_EVIDENCE")
        if not authority_evidence:
            raise ValueError("IMPLEMENTED_REQUIRES_AUTHORIZED_TRANSITION")
        raise ValueError("IMPLEMENTATION_ADMISSION_REQUIRES_SEPARATE_AUTHORIZED_GATE")
    if target_state == "VERIFIED":
        if not record.get("proof") or not record.get("tests") or not record.get("evidence"):
            raise ValueError("VERIFIED_REQUIRES_REPRODUCIBLE_TEST_AND_PROOF_EVIDENCE")
        raise ValueError("VERIFICATION_REQUIRES_INDEPENDENT_VERIFICATION_RECORD")
    if target_state == "UNRESOLVED":
        return
    raise ValueError(f"UNKNOWN_OR_UNSUPPORTED_TRANSITION:{target_state}")


def _validate_bundle(index: dict[str, Any], sources: list[dict[str, Any]], records: list[dict[str, Any]], cross_refs: list[dict[str, Any]], taxonomy: dict[str, Any]) -> None:
    if len(taxonomy.get("indexes", [])) != 28:
        raise IndexBuildError("TAXONOMY_MUST_DEFINE_EXACTLY_28_INDEXES")
    source_ids = [item.get("source_id") for item in sources]
    if len(source_ids) != len(set(source_ids)):
        raise IndexBuildError("DUPLICATE_SOURCE_ID")
    source_id_set = set(source_ids)
    for source in sources:
        if not HEX_256_PATTERN.fullmatch(source.get("sha256", "")):
            raise IndexBuildError(f"SOURCE_SHA256_INVALID:{source.get('path')}")
        if not source.get("path") or not source.get("source_id"):
            raise IndexBuildError("SOURCE_ID_OR_PATH_MISSING")
    record_ids = [record.get("uid") for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise IndexBuildError("DUPLICATE_ATOMIC_UID")
    record_id_set = set(record_ids)
    for record in records:
        if record["source_id"] not in source_id_set:
            raise IndexBuildError(f"ORPHAN_RECORD_SOURCE:{record['uid']}")
        if record["source_id"] not in record.get("lineage", []):
            raise IndexBuildError(f"RECORD_LINEAGE_MISSING_SOURCE:{record['uid']}")
        if not HEX_256_PATTERN.fullmatch(record.get("source_sha256", "")):
            raise IndexBuildError(f"RECORD_SOURCE_HASH_INVALID:{record['uid']}")
        if record.get("ingestion_state") == "ATOMIC":
            validate_transition(record, "ATOMIC")
        elif record.get("ingestion_state") == "UNRESOLVED":
            validate_transition(record, "UNRESOLVED")
        elif record.get("ingestion_state") != "SOURCE":
            raise IndexBuildError(f"UNKNOWN_INGESTION_STATE:{record['uid']}")
        if record["status"] in {"CANONICAL", "IMPLEMENTED", "VERIFIED"}:
            raise IndexBuildError(f"AUTOMATIC_PROMOTION_FORBIDDEN:{record['uid']}")
    for item in cross_refs:
        if item["from_source_id"] not in source_id_set or item["to_source_id"] not in source_id_set:
            raise IndexBuildError("CROSS_REFERENCE_ENDPOINT_MISSING")
    for view in index["indexes"]:
        if not set(view["record_refs"]).issubset(record_id_set):
            raise IndexBuildError(f"VIEW_HAS_UNKNOWN_RECORD:{view['index_id']}")
        if not set(view["source_refs"]).issubset(source_id_set):
            raise IndexBuildError(f"VIEW_HAS_UNKNOWN_SOURCE:{view['index_id']}")


def build_payloads(root: Path, output_dir: Path, legacy_start: int | None = None, legacy_end: int | None = None) -> dict[str, bytes]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    taxonomy_path = root / TAXONOMY_RELATIVE_PATH
    if not taxonomy_path.is_file():
        raise IndexBuildError(f"TAXONOMY_MISSING:{TAXONOMY_RELATIVE_PATH}")
    try:
        taxonomy_bytes = taxonomy_path.read_bytes()
        taxonomy = json.loads(taxonomy_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IndexBuildError(f"TAXONOMY_UNREADABLE:{exc}") from exc
    taxonomy_indexes = taxonomy.get("indexes")
    if not isinstance(taxonomy_indexes, list) or len(taxonomy_indexes) != 28:
        raise IndexBuildError("TAXONOMY_MUST_DEFINE_EXACTLY_28_INDEXES")
    keys = [item.get("key") for item in taxonomy_indexes]
    if len(keys) != len(set(keys)) or any(not key for key in keys):
        raise IndexBuildError("TAXONOMY_INDEX_KEYS_MUST_BE_UNIQUE_AND_NONEMPTY")

    revision = _git_revision(root)
    paths = _discover_sources(root, output_dir)
    if not paths:
        raise IndexBuildError("NO_SOURCE_FILES_DISCOVERED")
    source_rows: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    text_by_path: dict[str, str] = {}
    observed_legacy_ids: set[int] = set()
    opaque_sources: list[dict[str, str]] = []
    pdf_paths: list[str] = []
    diagram_paths: list[str] = []
    duplicate_digest_paths: dict[str, list[str]] = defaultdict(list)

    for path in paths:
        relative = _relative_path(path, root)
        raw, text, digest_kind, encoding = _read_source(path)
        digest = _sha256(raw)
        source_id = "SRC-" + _sha256((relative + "\0" + digest).encode("utf-8"))[:24]
        source_kind = _source_kind(path)
        media_type = mimetypes.guess_type(relative)[0] or "application/octet-stream"
        if path.name.lower() == "dockerfile" or path.name.lower().startswith("dockerfile."):
            media_type = "text/plain"
        source = {
            "source_id": source_id,
            "path": relative,
            "source_uri": f"repo://{os.environ.get('GITHUB_REPOSITORY', 'LOCAL_REPOSITORY')}@{revision}/{relative}",
            "source_kind": source_kind,
            "media_type": media_type,
            "byte_size": len(raw),
            "sha256": digest,
            "digest_kind": digest_kind,
            "text_encoding": encoding,
            "source_revision": revision,
            "original_retained": True,
            "ingestion_state": "SOURCE",
            "extracted_record_count": 0,
        }
        source_rows.append(source)
        duplicate_digest_paths[digest].append(relative)
        if source_kind == "PDF":
            pdf_paths.append(relative)
        if source_kind == "DIAGRAM":
            diagram_paths.append(relative)
        if text is None:
            opaque_sources.append({"path": relative, "source_id": source_id, "source_kind": source_kind, "extraction_status": "HASHED_CONTENT_EXTRACTION_PENDING"})
        else:
            text_by_path[relative] = text
            observed_legacy_ids.update(_explicit_legacy_ids(text))

        full_line_count = len(text.splitlines()) if text is not None else None
        root_record = _record_base(
            source, "SOURCE_FILE", path.name, _line_location(relative, 1 if text is not None else None, full_line_count),
            ingestion_state="SOURCE", fragment_sha256=digest, fragment_hash_kind=digest_kind,
            parent=None, classification_status="CLASSIFIED",
        )
        root_record["_search_text"] = text or relative
        records.append(root_record)
        generated_children: list[dict[str, Any]] = []
        if text is not None:
            suffix = path.suffix.lower()
            if suffix in {".md", ".markdown"}:
                generated_children.extend(_extract_markdown_records(source, root_record["uid"], text))
            elif suffix == ".json":
                json_records, observed_from_json = _extract_json_records(source, root_record["uid"], text)
                generated_children.extend(json_records)
                observed_legacy_ids.update(observed_from_json)
            elif suffix in {".txt", ".rst"}:
                if HEADING_PATTERN.search(text):
                    generated_children.extend(_extract_markdown_records(source, root_record["uid"], text))
                else:
                    generated_children.extend(_extract_text_block_records(source, root_record["uid"], text))
            generated_children.extend(_extract_term_records(source, root_record["uid"], text))
        for child in generated_children:
            child["_search_text"] = child.get("_search_text", child.get("source_excerpt") or child["name"])
            root_record["children"].append(child["uid"])
            records.append(child)
        source["extracted_record_count"] = 1 + len(generated_children)

    source_rows.sort(key=lambda item: item["path"])
    records.sort(key=lambda item: (
        item["source_location"]["path"],
        item["source_location"]["line_start"] or 0,
        item["source_location"]["json_pointer"] or "",
        item["_record_kind"],
        item["uid"],
    ))
    cross_refs = _build_cross_references(source_rows, text_by_path)
    referenced_source_ids = {item["from_source_id"] for item in cross_refs}

    for record in records:
        source_path = record["source_location"]["path"]
        if record["_record_kind"] == "SOURCE_FILE":
            record["_search_text"] = text_by_path.get(source_path, source_path)
        else:
            record["_search_text"] = record.get("source_excerpt") or record["name"]

    views: list[dict[str, Any]] = []
    for spec in taxonomy_indexes:
        selected = [
            record for record in records
            if _view_match(spec, record, record.get("_search_text", ""), referenced_source_ids)
        ]
        selected.sort(key=lambda item: (item["source_location"]["path"], item["source_location"]["line_start"] or 0, item["uid"]))
        record_refs = [record["uid"] for record in selected]
        source_refs = sorted({record["source_id"] for record in selected})
        views.append({
            "index_id": spec["index_id"],
            "key": spec["key"],
            "name": spec["name"],
            "record_count": len(record_refs),
            "source_count": len(source_refs),
            "unresolved_count": sum(1 for record in selected if record["semantic_status"] == "UNRESOLVED"),
            "record_refs": record_refs,
            "source_refs": source_refs,
            "selection_rule": spec["scope"],
        })

    range_spec = taxonomy.get("legacy_range", {})
    start = legacy_start if legacy_start is not None else range_spec.get("start")
    end = legacy_end if legacy_end is not None else range_spec.get("end")
    if isinstance(start, int) and isinstance(end, int) and start > 0 and end >= start and (end - start) <= 100000:
        observed_in_range = {number for number in observed_legacy_ids if start <= number <= end}
        legacy_ledger = {
            "expected_start": _format_legacy(start),
            "expected_end": _format_legacy(end),
            "approximate_range": bool(range_spec.get("approximate", True)),
            "range_is_item_level_proof": False,
            "observed_explicit_ids": [_format_legacy(number) for number in sorted(observed_in_range)],
            "observed_count": len(observed_in_range),
            "unresolved_candidate_gap_ranges": _compress_ranges(observed_in_range, start, end),
            "gap_semantics": "No explicit legacy_id field or labelled legacy-ID reference was found for this range in the scanned checkout. This is not proof that an original historical record never existed.",
            "fabricated_missing_records": 0,
            "source_claim_refs": range_spec.get("source_claim_refs", []),
        }
    else:
        legacy_ledger = {
            "expected_start": None, "expected_end": None, "approximate_range": True,
            "range_is_item_level_proof": False, "observed_explicit_ids": [],
            "observed_count": 0, "unresolved_candidate_gap_ranges": [],
            "gap_semantics": "Legacy range not configured; no placeholder records are generated.",
            "fabricated_missing_records": 0, "source_claim_refs": [],
        }

    duplicate_groups = [
        {"sha256": digest, "paths": sorted(duplicate_paths), "count": len(duplicate_paths), "relationship": "EXACT_BYTE_DUPLICATE_CANDIDATE_NOT_MERGED"}
        for digest, duplicate_paths in sorted(duplicate_digest_paths.items()) if len(duplicate_paths) > 1
    ]
    source_kind_counts = dict(sorted(Counter(item["source_kind"] for item in source_rows).items()))
    coverage = {
        "schema_version": "1.0.0",
        "index_id": taxonomy["index_id"],
        "source_revision": revision,
        "source_files_discovered": len(source_rows),
        "source_records_created": sum(1 for item in records if item["_record_kind"] == "SOURCE_FILE"),
        "atomic_records_created": sum(1 for item in records if item["ingestion_state"] == "ATOMIC"),
        "records_total": len(records),
        "source_kinds": source_kind_counts,
        "opaque_or_non_text_sources": opaque_sources,
        "pdf_content_extraction_pending": sorted(pdf_paths),
        "diagram_semantic_extraction_pending": sorted(diagram_paths),
        "duplicate_content_groups": duplicate_groups,
        "source_cross_references": len(cross_refs),
        "indexes_defined": len(taxonomy_indexes),
        "indexes_populated": sum(1 for view in views if view["record_count"] > 0),
        "unresolved_semantic_records": sum(1 for record in records if record["semantic_status"] == "UNRESOLVED"),
        "canonical_promotions_performed": 0,
        "implemented_promotions_performed": 0,
        "verified_promotions_performed": 0,
        "legacy_id_coverage": legacy_ledger,
        "connector_limits": taxonomy.get("source_adapters", []),
        "limitations": [
            "This run indexes the checked-out repository only; conversation files and remote repositories require explicit adapters.",
            "Binary files are preserved by source digest but their semantic content is not extracted by this builder.",
            "The current-repository tree and source hashes do not prove complete historical 0001-2750 recovery.",
            "Source-claimed status is preserved but not independently certified by indexing.",
            "Path references are direct cross-references, not automatically promoted to semantic dependency or lineage edges.",
        ],
    }

    source_index = {
        "schema_version": "1.0.0",
        "index_id": "VAIXLNS.ZERO_LOSS.SOURCE",
        "source_revision": revision,
        "hash_algorithm": "SHA-256",
        "source_count": len(source_rows),
        "sources": source_rows,
    }
    public_records = [{key: value for key, value in record.items() if not key.startswith("_")} for record in records]
    cross_reference_index = {
        "schema_version": "1.0.0",
        "index_id": "VAIXLNS.ZERO_LOSS.CROSS_REFERENCE",
        "source_revision": revision,
        "relationship_semantics": "SOURCE_PATH_REFERENCE does not imply dependency, equivalence, alias, or lineage.",
        "reference_count": len(cross_refs),
        "references": cross_refs,
    }
    generated_payloads = {
        ARTIFACT_NAMES["sources"]: _json_bytes(source_index),
        ARTIFACT_NAMES["records"]: _jsonl_bytes(public_records),
        ARTIFACT_NAMES["coverage"]: _json_bytes(coverage),
        ARTIFACT_NAMES["cross_references"]: _json_bytes(cross_reference_index),
    }
    integrity = {
        "hash_algorithm": "SHA-256",
        "self_hash_excluded": True,
        "taxonomy_sha256": _sha256(taxonomy_bytes),
        "artifacts": {name: _sha256(payload) for name, payload in sorted(generated_payloads.items())},
    }
    index = {
        "schema_version": "1.0.0",
        "index_id": taxonomy["index_id"],
        "name": taxonomy["name"],
        "authority": taxonomy["authority"],
        "canonical_source": taxonomy["canonical_source"],
        "master_index": taxonomy["master_index"],
        "status": "RECOVERED",
        "source_revision": revision,
        "taxonomy_ref": TAXONOMY_RELATIVE_PATH.as_posix(),
        "taxonomy_sha256": _sha256(taxonomy_bytes),
        "source_index_ref": ARTIFACT_NAMES["sources"],
        "atomic_records_ref": ARTIFACT_NAMES["records"],
        "coverage_ref": ARTIFACT_NAMES["coverage"],
        "cross_reference_ref": ARTIFACT_NAMES["cross_references"],
        "source_count": len(source_rows),
        "record_count": len(public_records),
        "index_count": len(views),
        "indexes": views,
        "legacy_id_coverage_ref": f"{ARTIFACT_NAMES['coverage']}#/legacy_id_coverage",
        "invariants": taxonomy.get("invariants", []),
        "transition_gates": taxonomy.get("transition_gates", {}),
        "integrity": integrity,
    }
    _validate_bundle(index, source_rows, records, cross_refs, taxonomy)
    generated_payloads[ARTIFACT_NAMES["index"]] = _json_bytes(index)
    return generated_payloads


def verify_artifacts(root: Path, output_dir: Path) -> dict[str, Any]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    try:
        index = json.loads((output_dir / ARTIFACT_NAMES["index"]).read_text(encoding="utf-8"))
        sources_obj = json.loads((output_dir / ARTIFACT_NAMES["sources"]).read_text(encoding="utf-8"))
        coverage = json.loads((output_dir / ARTIFACT_NAMES["coverage"]).read_text(encoding="utf-8"))
        cross_obj = json.loads((output_dir / ARTIFACT_NAMES["cross_references"]).read_text(encoding="utf-8"))
        records = [
            json.loads(line)
            for line in (output_dir / ARTIFACT_NAMES["records"]).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        taxonomy_bytes = (root / TAXONOMY_RELATIVE_PATH).read_bytes()
        taxonomy = json.loads(taxonomy_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IndexBuildError(f"GENERATED_INDEX_UNREADABLE:{exc}") from exc

    if index.get("taxonomy_sha256") != _sha256(taxonomy_bytes):
        raise IndexBuildError("TAXONOMY_DIGEST_MISMATCH")
    for name, expected in index.get("integrity", {}).get("artifacts", {}).items():
        path = output_dir / name
        if not path.is_file():
            raise IndexBuildError(f"GENERATED_ARTIFACT_MISSING:{name}")
        actual = _sha256(path.read_bytes())
        if actual != expected:
            raise IndexBuildError(f"GENERATED_ARTIFACT_DIGEST_MISMATCH:{name}")
    source_rows = sources_obj.get("sources", [])
    cross_refs = cross_obj.get("references", [])
    _validate_bundle(index, source_rows, records, cross_refs, taxonomy)
    if coverage.get("source_files_discovered") != len(source_rows):
        raise IndexBuildError("COVERAGE_SOURCE_COUNT_MISMATCH")
    if coverage.get("records_total") != len(records):
        raise IndexBuildError("COVERAGE_RECORD_COUNT_MISMATCH")
    return {
        "state": "PASS",
        "source_count": len(source_rows),
        "record_count": len(records),
        "index_count": len(index.get("indexes", [])),
        "canonical_promotions_performed": coverage.get("canonical_promotions_performed"),
        "verified_hashes": len(index.get("integrity", {}).get("artifacts", {})) + 1,
        "index_sha256": _sha256((output_dir / ARTIFACT_NAMES["index"]).read_bytes()),
    }


def build_index(root: Path, output_dir: Path, legacy_start: int | None = None, legacy_end: int | None = None) -> dict[str, Any]:
    payloads = build_payloads(root, output_dir, legacy_start=legacy_start, legacy_end=legacy_end)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        target = output_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    return verify_artifacts(root, output_dir)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root to scan")
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_RELATIVE_PATH), help="generated artifact directory")
    parser.add_argument("--legacy-start", type=int, default=None, help="override expected legacy range start")
    parser.add_argument("--legacy-end", type=int, default=None, help="override expected legacy range end")
    parser.add_argument("--verify-only", action="store_true", help="verify an already-generated index bundle")
    args = parser.parse_args(argv)
    if (args.legacy_start is None) != (args.legacy_end is None):
        parser.error("--legacy-start and --legacy-end must be provided together")
    if args.legacy_start is not None and (args.legacy_start <= 0 or args.legacy_end < args.legacy_start):
        parser.error("invalid legacy range")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.verify_only:
            report = verify_artifacts(args.root, args.output_dir)
        else:
            report = build_index(args.root, args.output_dir, args.legacy_start, args.legacy_end)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (IndexBuildError, ValueError) as exc:
        print(f"ZERO_LOSS_INDEX_FAILURE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
