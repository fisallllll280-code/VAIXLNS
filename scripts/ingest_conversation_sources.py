#!/usr/bin/env python3
"""Preservation-first local intake for owner-supplied conversation exports.

The raw source is copied byte-for-byte into a vault outside any Git checkout.
Normalized conversation records remain private. An optional public manifest
contains opaque IDs, digests and counts only; it never contains titles,
filenames, user identifiers or message text.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
PARSER_VERSION = "1.0.0"
DEFAULT_MAX_JSON_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_SOURCE_BYTES = 1024 * 1024 * 1024
SUPPORTED_TEXT = {".txt", ".md"}


class IntakeError(ValueError):
    """Input cannot be safely or unambiguously interpreted."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(prefix: str, *parts: str) -> str:
    material = "\0".join(parts).encode("utf-8")
    return prefix + hashlib.sha256(material).hexdigest()[:24]


def is_inside_git_checkout(path: Path) -> bool:
    current = path.resolve()
    for candidate in (current, *current.parents):
        marker = candidate / ".git"
        if marker.exists():
            return True
    return False


def _load_json_conversations(data: bytes, limit: int) -> list[dict[str, Any]]:
    if len(data) > limit:
        raise IntakeError("conversation JSON exceeds configured size limit")
    try:
        payload = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntakeError("conversation JSON is not valid UTF-8 JSON") from exc

    if isinstance(payload, list):
        conversations = payload
    elif isinstance(payload, dict) and isinstance(payload.get("conversations"), list):
        conversations = payload["conversations"]
    else:
        raise IntakeError("unrecognized conversation export structure")

    if not all(isinstance(item, dict) for item in conversations):
        raise IntakeError("conversation export contains non-object entries")
    return conversations


def _read_zip_conversations(raw: bytes, limit: int) -> list[dict[str, Any]]:
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            matches = [
                info for info in archive.infolist()
                if Path(info.filename).name == "conversations.json"
                and not info.is_dir()
            ]
            if len(matches) != 1:
                raise IntakeError("ZIP must contain exactly one conversations.json")
            info = matches[0]
            if info.file_size > limit:
                raise IntakeError("conversations.json exceeds configured size limit")
            if info.file_size and info.compress_size == 0:
                raise IntakeError("invalid ZIP compression metadata")
            if info.compress_size and info.file_size / info.compress_size > 250:
                raise IntakeError("conversation JSON compression ratio exceeds safety limit")
            data = archive.read(info)
    except zipfile.BadZipFile as exc:
        raise IntakeError("source is not a valid ZIP archive") from exc
    return _load_json_conversations(data, limit)


def _conversation_record(conversation: dict[str, Any], source_id: str, source_digest: str) -> dict[str, Any]:
    source_conversation_id = str(
        conversation.get("id") or conversation.get("conversation_id")
        or sha256(json.dumps(conversation, sort_keys=True, ensure_ascii=False).encode("utf-8"))[:24]
    )
    conversation_uid = stable_id("CONV-", source_id, source_conversation_id)
    mapping = conversation.get("mapping")
    messages = conversation.get("messages")

    # Keep the full message/node objects and their parent/child graph. Do not
    # flatten branches into a single guessed chronology.
    if mapping is not None and not isinstance(mapping, dict):
        raise IntakeError("conversation mapping must be an object")
    if messages is not None and not isinstance(messages, list):
        raise IntakeError("conversation messages must be an array")

    node_count = len(mapping) if isinstance(mapping, dict) else (len(messages) if isinstance(messages, list) else 0)
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "CONVERSATION_SOURCE_RECORD",
        "conversation_uid": conversation_uid,
        "source_id": source_id,
        "source_sha256": source_digest,
        "source_conversation_id": source_conversation_id,
        "title": conversation.get("title"),
        "create_time": conversation.get("create_time"),
        "update_time": conversation.get("update_time"),
        "current_node": conversation.get("current_node"),
        "mapping": mapping,
        "messages": messages,
        "node_count": node_count,
        "preservation_rule": "FULL_NODE_GRAPH_PRESERVED; NO_BRANCH_FLATTENING",
    }


def inspect_source(path: Path, limit: int, max_source_bytes: int) -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
    path = path.expanduser()
    if path.is_symlink() or not path.is_file():
        raise IntakeError("source must be a regular, non-symlink file")
    if path.stat().st_size > max_source_bytes:
        raise IntakeError("source exceeds configured byte limit")
    raw = path.read_bytes()
    digest = sha256(raw)
    source_id = "SRC-" + digest[:24]
    suffix = path.suffix.lower()
    normalized: list[dict[str, Any]] = []
    conversation_count = 0
    message_count = 0

    try:
        if suffix == ".zip":
            conversations = _read_zip_conversations(raw, limit)
            normalized = [_conversation_record(c, source_id, digest) for c in conversations]
            source_kind = "CHATGPT_EXPORT_ZIP"
            parser_state = "PARSED"
            conversation_count = len(normalized)
            message_count = sum(int(item["node_count"]) for item in normalized)
        elif suffix == ".json":
            conversations = _load_json_conversations(raw, limit)
            normalized = [_conversation_record(c, source_id, digest) for c in conversations]
            source_kind = "CHATGPT_CONVERSATIONS_JSON"
            parser_state = "PARSED"
            conversation_count = len(normalized)
            message_count = sum(int(item["node_count"]) for item in normalized)
        elif suffix in SUPPORTED_TEXT:
            try:
                body = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                source_kind, parser_state = "TEXT_TRANSCRIPT", "PRESERVED_UNPARSED_ENCODING"
            else:
                source_kind, parser_state = "TEXT_TRANSCRIPT", "PARSED_AS_SINGLE_SOURCE"
                normalized = [{
                    "schema_version": SCHEMA_VERSION,
                    "record_type": "TRANSCRIPT_SOURCE_RECORD",
                    "source_id": source_id,
                    "source_sha256": digest,
                    "content": body,
                    "preservation_rule": "SOURCE_TEXT_PRESERVED_VERBATIM",
                }]
                conversation_count = 1
        else:
            source_kind, parser_state = "OPAQUE_SOURCE_FILE", "PRESERVED_CONTENT_EXTRACTION_PENDING"
    except IntakeError as exc:
        # Preserve the original bytes even when parsing fails; quarantine only
        # the derived interpretation, never discard the source.
        source_kind = "CHATGPT_EXPORT_ZIP" if suffix == ".zip" else "CHATGPT_CONVERSATIONS_JSON"
        parser_state = "QUARANTINED_PARSE_ERROR"
        parse_error_type = type(exc).__name__

    occurrence_id = stable_id("OCC-", source_id, str(path.resolve()))
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "parser_version": PARSER_VERSION,
        "source_id": source_id,
        "source_occurrence_id": occurrence_id,
        "source_sha256": digest,
        "original_name": path.name,
        "byte_length": len(raw),
        "source_kind": source_kind,
        "parser_state": parser_state,
        "conversation_count": conversation_count,
        "message_node_count": message_count,
        "normalized_ids": [item.get("conversation_uid", source_id) for item in normalized],
        "parse_error_type": locals().get("parse_error_type"),
    }
    return raw, metadata, normalized


def _write_immutable(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_bytes()
        if sha256(existing) != sha256(data):
            raise IntakeError(f"immutable destination collision: {path.name}")
        return
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def ingest(sources: list[Path], vault_dir: Path, apply: bool, public_manifest: Path | None, limit: int, max_source_bytes: int) -> dict[str, Any]:
    vault_dir = vault_dir.expanduser().resolve()
    if is_inside_git_checkout(vault_dir):
        raise IntakeError("vault must be outside every Git checkout; raw session content must not enter a public repository")

    inspected = []
    for source in sources:
        raw, metadata, normalized = inspect_source(source, limit, max_source_bytes)
        inspected.append((raw, metadata, normalized))

    public_entries = []
    for raw, metadata, normalized in inspected:
        public_entries.append({
            "source_id": metadata["source_id"],
            "source_sha256": metadata["source_sha256"],
            "byte_length": metadata["byte_length"],
            "source_kind": metadata["source_kind"],
            "parser_state": metadata["parser_state"],
            "conversation_count": metadata["conversation_count"],
            "message_node_count": metadata["message_node_count"],
        })

    result = {
        "schema_version": SCHEMA_VERSION,
        "mode": "APPLY" if apply else "DRY_RUN",
        "vault_dir": str(vault_dir),
        "sources": [metadata for _, metadata, _ in inspected],
        "total_sources": len(inspected),
        "total_conversations": sum(m["conversation_count"] for _, m, _ in inspected),
        "total_message_nodes": sum(m["message_node_count"] for _, m, _ in inspected),
        "raw_sources_modified": False,
        "canonical_promotion": False,
    }

    if not apply:
        return result

    manifest_path = vault_dir / "manifests" / "sources.jsonl"
    existing_occurrence_ids: set[str] = set()
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                existing_occurrence_ids.add(json.loads(line)["source_occurrence_id"])

    for raw, metadata, normalized in inspected:
        source_id = metadata["source_id"]
        raw_path = vault_dir / "raw" / (metadata["source_sha256"] + ".bin")
        _write_immutable(raw_path, raw)
        for record in normalized:
            record_id = record.get("conversation_uid", source_id)
            payload = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
            _write_immutable(vault_dir / "normalized" / (record_id + ".json"), payload)
        occurrence_id = metadata["source_occurrence_id"]
        if occurrence_id not in existing_occurrence_ids:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with manifest_path.open("ab") as stream:
                stream.write(json.dumps(metadata, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n")
            existing_occurrence_ids.add(occurrence_id)

    if public_manifest is not None:
        public_payload = {
            "schema_version": SCHEMA_VERSION,
            "manifest_type": "PRIVACY_MINIMIZED_CONVERSATION_SOURCE_MANIFEST",
            "sources": sorted(public_entries, key=lambda item: item["source_id"]),
        }
        target = public_manifest.expanduser().resolve()
        encoded = json.dumps(public_payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
        _write_immutable(target, encoded)

    result["raw_sources_modified"] = False
    result["private_vault_written"] = True
    result["public_manifest_written"] = public_manifest is not None
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", required=True, help="Export ZIP/JSON, transcript TXT/MD, or opaque attachment; repeatable")
    parser.add_argument("--vault-dir", required=True, help="Private vault directory outside all Git checkouts")
    parser.add_argument("--apply", action="store_true", help="Persist sources and normalized records; default is dry-run")
    parser.add_argument("--public-manifest", help="Optional privacy-minimized manifest path; no filenames, titles, IDs or content")
    parser.add_argument("--max-json-bytes", type=int, default=DEFAULT_MAX_JSON_BYTES)
    parser.add_argument("--max-source-bytes", type=int, default=DEFAULT_MAX_SOURCE_BYTES)
    args = parser.parse_args()
    try:
        result = ingest(
            [Path(item) for item in args.source],
            Path(args.vault_dir),
            args.apply,
            Path(args.public_manifest) if args.public_manifest else None,
            args.max_json_bytes,
            args.max_source_bytes,
        )
    except (OSError, IntakeError, json.JSONDecodeError) as exc:
        print(json.dumps({"state": "QUARANTINED", "error_type": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
