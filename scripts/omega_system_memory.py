#!/usr/bin/env python3
"""Append-only, hash-chained memory journal for cross-system VAIXLNS engineering.

The journal preserves versions and conflicts; it never has a delete event.
It is tamper-evident, not an absolute backup or WORM storage guarantee.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVENT_SCHEMA = "vaixlns.omega-system-memory.event.v1"
SNAPSHOT_SCHEMA = "vaixlns.omega-system-memory-snapshot.v1"
GENESIS_PREVIOUS_HASH = "0" * 64
ALLOWED_STATES = {
    "VERIFIED", "SPECIFIED", "PARTIAL", "MISSING", "CONFLICT", "PROPOSAL",
    "RECOVERED", "IMPLEMENTED", "CANONICAL", "SOURCE-ASSERTED",
    "SUPERSEDED", "NOT_CONFIGURED", "UNKNOWN",
}
EVENT_TYPES = {
    "RECORD_CREATED", "RECORD_UPDATED", "RELATION_ADDED",
    "CONFLICT_RECORDED", "CONFLICT_RESOLVED", "RECORD_SUPERSEDED",
}
RECORD_REQUIRED = {"record_id", "kind", "title", "body", "state", "source_refs", "system_refs", "tags"}
RELATION_TYPES = {
    "GOVERNS", "DEPENDS_ON", "IMPLEMENTS", "DERIVED_FROM", "SUPERSEDES",
    "CONTAINS", "CONTRADICTS", "RELATED_TO", "REQUIRES_EVIDENCE",
    "REALIZED_BY", "INDEXES", "VERIFIED_BY", "COMMERCIALIZES",
}

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValueError(f"memory ledger is missing: {path}")
    events = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"blank line is not permitted in append-only JSONL ledger (line {line_number})")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at ledger line {line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"ledger event at line {line_number} must be an object")
        events.append(event)
    if not events:
        raise ValueError("memory ledger is empty; refusing to treat an empty history as valid memory")
    return events

def validate_record(record: Any, expected_record_id: str) -> None:
    if not isinstance(record, dict):
        raise ValueError("payload.record must be an object")
    missing = sorted(RECORD_REQUIRED - set(record))
    if missing:
        raise ValueError("memory record missing fields: " + ", ".join(missing))
    if record.get("record_id") != expected_record_id:
        raise ValueError("payload.record.record_id must exactly match event.record_id")
    for key in ("kind", "title", "body"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f"memory record {key} must be a non-empty string")
    if record.get("state") not in ALLOWED_STATES:
        raise ValueError(f"unsupported memory evidence state: {record.get('state')}")
    for key in ("source_refs", "system_refs", "tags"):
        if not isinstance(record.get(key), list):
            raise ValueError(f"memory record {key} must be an array")
    for ref in record["source_refs"]:
        if not isinstance(ref, dict) or not isinstance(ref.get("ref"), str) or not ref["ref"].strip():
            raise ValueError("each source_ref must be an object with a non-empty ref")
    for key in ("system_refs", "tags"):
        if any(not isinstance(value, str) or not value.strip() for value in record[key]):
            raise ValueError(f"every {key} value must be a non-empty string")

def make_event(sequence: int, event_type: str, record_id: str,
               payload: dict[str, Any], previous_hash: str, recorded_at: str | None = None) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unsupported event type: {event_type}; deletion events are prohibited")
    core = {
        "schema": EVENT_SCHEMA,
        "sequence": sequence,
        "event_id": f"OMEGA-MEM-E{sequence:08d}",
        "recorded_at": recorded_at or now_utc(),
        "event_type": event_type,
        "record_id": record_id,
        "payload": payload,
        "previous_event_sha256": previous_hash,
    }
    return {**core, "event_sha256": sha256_json(core)}

def validate_chain(events: list[dict[str, Any]]) -> dict[str, Any]:
    records: dict[str, dict[str, Any]] = {}
    event_ids: set[str] = set()
    conflicts: dict[str, dict[str, Any]] = {}
    relations: list[dict[str, Any]] = []
    superseded: dict[str, dict[str, Any]] = {}
    previous_hash = GENESIS_PREVIOUS_HASH

    for expected_sequence, event in enumerate(events, start=1):
        if event.get("schema") != EVENT_SCHEMA:
            raise ValueError(f"schema mismatch at event sequence {expected_sequence}")
        if event.get("sequence") != expected_sequence:
            raise ValueError(f"sequence gap or reorder: expected {expected_sequence}, got {event.get('sequence')}")
        expected_event_id = f"OMEGA-MEM-E{expected_sequence:08d}"
        if event.get("event_id") != expected_event_id:
            raise ValueError(f"event_id mismatch at sequence {expected_sequence}")
        if event["event_id"] in event_ids:
            raise ValueError(f"duplicate event_id: {event['event_id']}")
        event_ids.add(event["event_id"])
        if event.get("previous_event_sha256") != previous_hash:
            raise ValueError(f"broken hash-chain pointer at sequence {expected_sequence}")
        claimed = event.get("event_sha256")
        core = {key: value for key, value in event.items() if key != "event_sha256"}
        if not isinstance(claimed, str) or not re.fullmatch(r"[a-f0-9]{64}", claimed):
            raise ValueError(f"missing or invalid event hash at sequence {expected_sequence}")
        if sha256_json(core) != claimed:
            raise ValueError(f"event hash mismatch at sequence {expected_sequence}")
        event_type = event.get("event_type")
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported event type at sequence {expected_sequence}; deletion is never accepted")
        record_id = event.get("record_id")
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError(f"record_id missing at sequence {expected_sequence}")
        payload = event.get("payload")
        if not isinstance(payload, dict):
            raise ValueError(f"payload must be an object at sequence {expected_sequence}")

        if event_type == "RECORD_CREATED":
            if record_id in records:
                raise ValueError(f"duplicate RECORD_CREATED for {record_id}; append RECORD_UPDATED instead")
            validate_record(payload.get("record"), record_id)
            records[record_id] = {
                "versions": [{"event_id": event["event_id"], "event_sha256": claimed,
                              "recorded_at": event.get("recorded_at"), "record": copy.deepcopy(payload["record"])}],
                "created_event_id": event["event_id"],
            }
        elif event_type == "RECORD_UPDATED":
            if record_id not in records:
                raise ValueError(f"cannot update unknown memory record: {record_id}")
            validate_record(payload.get("record"), record_id)
            reason = payload.get("change_reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("RECORD_UPDATED requires a non-empty change_reason")
            records[record_id]["versions"].append({
                "event_id": event["event_id"], "event_sha256": claimed,
                "recorded_at": event.get("recorded_at"), "record": copy.deepcopy(payload["record"]),
                "change_reason": reason,
            })
        elif event_type == "RELATION_ADDED":
            if record_id not in records:
                raise ValueError(f"relation source record does not exist: {record_id}")
            target = payload.get("target_record_id")
            relation_type = payload.get("relation_type")
            if target not in records:
                raise ValueError(f"relation target record does not exist: {target}")
            if relation_type not in RELATION_TYPES:
                raise ValueError(f"unsupported relation_type: {relation_type}")
            if target == record_id:
                raise ValueError("self-relations are not accepted")
            refs = payload.get("evidence_refs", [])
            if not isinstance(refs, list):
                raise ValueError("evidence_refs must be an array")
            relations.append({
                "relation_id": event["event_id"], "from_record_id": record_id,
                "to_record_id": target, "relation_type": relation_type,
                "evidence_refs": copy.deepcopy(refs), "state": payload.get("state", "DECLARED_NOT_VERIFIED"),
                "event_sha256": claimed,
            })
        elif event_type == "CONFLICT_RECORDED":
            if record_id not in records:
                raise ValueError(f"conflict record does not exist: {record_id}")
            claim = payload.get("claim")
            conflicts_with = payload.get("conflicts_with")
            reason = payload.get("reason")
            if not all(isinstance(value, str) and value.strip() for value in (claim, conflicts_with, reason)):
                raise ValueError("CONFLICT_RECORDED requires claim, conflicts_with and reason")
            if conflicts_with not in records and conflicts_with not in event_ids:
                raise ValueError(f"conflicts_with must reference an existing record_id or event_id: {conflicts_with}")
            conflicts[event["event_id"]] = {
                "conflict_id": event["event_id"], "record_id": record_id,
                "claim": claim, "conflicts_with": conflicts_with, "reason": reason,
                "source_refs": copy.deepcopy(payload.get("source_refs", [])),
                "state": "OPEN", "resolution": None, "event_sha256": claimed,
            }
        elif event_type == "CONFLICT_RESOLVED":
            conflict_id = payload.get("conflict_event_id")
            conflict = conflicts.get(conflict_id)
            resolution = payload.get("resolution")
            if conflict is None:
                raise ValueError(f"cannot resolve unknown conflict event: {conflict_id}")
            if conflict["state"] == "RESOLVED":
                raise ValueError(f"conflict already resolved: {conflict_id}")
            if not isinstance(resolution, str) or not resolution.strip():
                raise ValueError("CONFLICT_RESOLVED requires an evidence-backed resolution description")
            conflict["state"] = "RESOLVED"
            conflict["resolution"] = resolution
            conflict["resolved_by_event_id"] = event["event_id"]
            conflict["resolution_refs"] = copy.deepcopy(payload.get("evidence_refs", []))
        elif event_type == "RECORD_SUPERSEDED":
            if record_id not in records:
                raise ValueError(f"cannot supersede unknown memory record: {record_id}")
            target = payload.get("superseded_by_record_id")
            reason = payload.get("reason")
            if target not in records or target == record_id:
                raise ValueError(f"superseded_by_record_id must reference a different existing record: {target}")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("RECORD_SUPERSEDED requires a reason")
            superseded[record_id] = {
                "superseded_by_record_id": target, "event_id": event["event_id"],
                "reason": reason, "event_sha256": claimed,
            }
        previous_hash = claimed

    return {
        "records": records, "event_ids": event_ids, "conflicts": conflicts,
        "relations": relations, "superseded": superseded, "last_event_sha256": previous_hash,
    }

def replay_snapshot(events: list[dict[str, Any]]) -> dict[str, Any]:
    state = validate_chain(events)
    memory_records = []
    for record_id in sorted(state["records"]):
        entry = state["records"][record_id]
        current_version = entry["versions"][-1]
        open_conflicts = [
            copy.deepcopy(conflict) for conflict in state["conflicts"].values()
            if conflict["record_id"] == record_id and conflict["state"] == "OPEN"
        ]
        relations_out = [copy.deepcopy(rel) for rel in state["relations"] if rel["from_record_id"] == record_id]
        relations_in = [copy.deepcopy(rel) for rel in state["relations"] if rel["to_record_id"] == record_id]
        supersession = state["superseded"].get(record_id)
        record_state = "CONFLICT" if open_conflicts else current_version["record"]["state"]
        if supersession:
            record_state = "SUPERSEDED"
        memory_records.append({
            "record_id": record_id,
            "kind": current_version["record"]["kind"],
            "title": current_version["record"]["title"],
            "body": current_version["record"]["body"],
            "state": record_state,
            "source_state": current_version["record"]["state"],
            "source_refs": current_version["record"]["source_refs"],
            "system_refs": current_version["record"]["system_refs"],
            "tags": current_version["record"]["tags"],
            "current_version": {
                "event_id": current_version["event_id"],
                "event_sha256": current_version["event_sha256"],
                "recorded_at": current_version["recorded_at"],
                "record_version": len(entry["versions"]),
            },
            "history": [
                {"event_id": version["event_id"], "event_sha256": version["event_sha256"],
                 "recorded_at": version["recorded_at"], "state": version["record"]["state"],
                 "title": version["record"]["title"], "body": version["record"]["body"]}
                for version in entry["versions"]
            ],
            "relations_outbound": relations_out,
            "relations_inbound": relations_in,
            "open_conflicts": open_conflicts,
            "supersession": copy.deepcopy(supersession),
            "evidence_assessment": "REFERENCES_REQUIRE_INDEPENDENT_VALIDATION",
        })
    core = {
        "schema": SNAPSHOT_SCHEMA,
        "state": "REPLAYED_FROM_VERIFIED_APPEND_ONLY_JOURNAL",
        "ledger_event_count": len(events),
        "ledger_last_event_sha256": state["last_event_sha256"],
        "ledger_content_sha256": sha256_bytes(b"\n".join(canonical_bytes(event) for event in events) + b"\n"),
        "memory_records": memory_records,
        "relations": sorted(state["relations"], key=lambda row: (row["from_record_id"], row["relation_type"], row["to_record_id"], row["relation_id"])),
        "conflicts": sorted(state["conflicts"].values(), key=lambda row: row["conflict_id"]),
        "superseded_record_count": len(state["superseded"]),
        "open_conflict_count": sum(conflict["state"] == "OPEN" for conflict in state["conflicts"].values()),
        "retention_contract": {
            "source_events_deleted": 0,
            "historical_versions_preserved": True,
            "silent_overwrite_supported": False,
            "deletion_event_supported": False,
            "tamper_evident_not_immutable_storage": True,
            "backup_and_repository_branch_protection_required_for_disaster_recovery": True,
        },
        "limitations": [
            "Only information recorded in this journal or cited through preserved references can be retrieved by this memory tool.",
            "Hash chaining detects changes relative to the checked-in chain; it cannot recover an entirely deleted journal without an external backup.",
            "Repository and URL references are not proven valid merely because the ledger is hash-valid.",
            "Do not store credentials, private customer data, or restricted source contents in this public repository journal.",
        ],
    }
    return {**core, "snapshot_sha256": sha256_json(core)}

def append_event(ledger_path: Path, request_path: Path) -> dict[str, Any]:
    events = read_ledger(ledger_path)
    state = validate_chain(events)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if not isinstance(request, dict):
        raise ValueError("append request must be a JSON object")
    event_type = request.get("event_type")
    record_id = request.get("record_id")
    payload = request.get("payload")
    if not isinstance(record_id, str) or not record_id.strip():
        raise ValueError("append request requires record_id")
    if not isinstance(payload, dict):
        raise ValueError("append request payload must be an object")
    event = make_event(len(events) + 1, event_type, record_id, payload,
                       state["last_event_sha256"], request.get("recorded_at"))
    # Validate the complete proposed history before appending anything.
    validate_chain(events + [event])
    with ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
    return event

def search_snapshot(snapshot: dict[str, Any], query: str, include_history: bool = False) -> list[dict[str, Any]]:
    query_tokens = {token for token in re.findall(r"[a-zA-Z0-9Ω.]+", query.lower()) if len(token) >= 2}
    if not query_tokens:
        return []
    result = []
    for record in snapshot["memory_records"]:
        fields = [record["record_id"], record["title"], record["body"], *record["system_refs"], *record["tags"]]
        if include_history:
            for version in record["history"]:
                fields.extend([version["title"], version["body"], version["state"]])
        text = " ".join(fields).lower()
        found = sorted(token for token in query_tokens if token in text)
        if not found:
            continue
        current_title_tokens = set(re.findall(r"[a-zA-Z0-9Ω.]+", record["title"].lower()))
        title_hits = sum(token in current_title_tokens for token in found)
        result.append({
            "record_id": record["record_id"], "title": record["title"], "state": record["state"],
            "matched_terms": found, "rank_score": len(found) * 10 + title_hits * 5,
            "current_version_event_id": record["current_version"]["event_id"],
            "open_conflict_count": len(record["open_conflicts"]),
            "source_refs": record["source_refs"],
        })
    result.sort(key=lambda item: (-item["rank_score"], item["record_id"]))
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify", help="Verify event ordering and hash chain")
    verify.add_argument("--ledger", required=True)
    replay = sub.add_parser("replay", help="Verify ledger and emit full memory snapshot")
    replay.add_argument("--ledger", required=True)
    replay.add_argument("--output", default="system-memory-snapshot.json")
    search = sub.add_parser("search", help="Search verified replayed memory")
    search.add_argument("--ledger", required=True)
    search.add_argument("--query", required=True)
    search.add_argument("--include-history", action="store_true")
    search.add_argument("--output")
    append = sub.add_parser("append", help="Append a new event; never edits or deletes old events")
    append.add_argument("--ledger", required=True)
    append.add_argument("--request", required=True, help="JSON event request")
    args = parser.parse_args()

    try:
        ledger = Path(args.ledger)
        events = read_ledger(ledger)
        state = validate_chain(events)
        if args.command == "verify":
            print(json.dumps({
                "state": "VERIFIED_HASH_CHAIN",
                "event_count": len(events),
                "record_count": len(state["records"]),
                "open_conflict_count": sum(conflict["state"] == "OPEN" for conflict in state["conflicts"].values()),
                "last_event_sha256": state["last_event_sha256"],
                "delete_event_supported": False,
            }, sort_keys=True))
            return 0
        if args.command == "replay":
            snapshot = replay_snapshot(events)
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"output": str(output), "state": snapshot["state"],
                              "record_count": len(snapshot["memory_records"]),
                              "event_count": snapshot["ledger_event_count"],
                              "snapshot_sha256": snapshot["snapshot_sha256"]}, sort_keys=True))
            return 0
        if args.command == "search":
            snapshot = replay_snapshot(events)
            results = search_snapshot(snapshot, args.query, args.include_history)
            output_obj = {
                "schema": "vaixlns.omega-system-memory-search.v1",
                "query": args.query,
                "ledger_last_event_sha256": state["last_event_sha256"],
                "result_count": len(results),
                "results": results,
                "no_match_policy": "RETURN_EMPTY_AND_MARK_UNKNOWN; DO_NOT_INVENT_MEMORY",
            }
            if args.output:
                Path(args.output).write_text(json.dumps(output_obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            else:
                print(json.dumps(output_obj, ensure_ascii=False, sort_keys=True, indent=2))
            return 0 if results else 3
        if args.command == "append":
            event = append_event(ledger, Path(args.request))
            print(json.dumps({"state": "APPENDED_NEW_EVENT", "event_id": event["event_id"],
                              "event_sha256": event["event_sha256"], "event_type": event["event_type"],
                              "historical_events_deleted": 0}, sort_keys=True))
            return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"state": "ERROR", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
