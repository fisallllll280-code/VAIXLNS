"""Tests for append-only, hash-chained system memory."""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

from scripts.omega_system_memory import (
    make_event, replay_snapshot, search_snapshot, validate_chain, read_ledger,
)


def memory_record(record_id="MEM-TEST-1", title="Index authority", body="Preserve source lineage."):
    return {
        "record_id": record_id,
        "kind": "ENGINEERING_DECISION",
        "title": title,
        "body": body,
        "state": "SPECIFIED",
        "source_refs": [{"kind": "test_fixture", "ref": "fixture://memory", "verification": "NOT_A_REAL_SOURCE"}],
        "system_refs": ["VAIXLNS", "VX"],
        "tags": ["memory", "lineage"],
    }


def chain(*requests):
    events = []
    previous = "0" * 64
    for sequence, (event_type, record_id, payload) in enumerate(requests, start=1):
        event = make_event(sequence, event_type, record_id, payload, previous, f"2026-10-09T00:00:{sequence:02d}Z")
        events.append(event)
        previous = event["event_sha256"]
    validate_chain(events)
    return events


class OmegaSystemMemoryTests(unittest.TestCase):
    def test_journal_replay_preserves_previous_versions(self):
        events = chain(
            ("RECORD_CREATED", "MEM-TEST-1", {"record": memory_record()}),
            ("RECORD_UPDATED", "MEM-TEST-1", {"record": memory_record(title="Index authority v2"), "change_reason": "Clarify lineage."}),
        )
        snapshot = replay_snapshot(events)
        row = snapshot["memory_records"][0]
        self.assertEqual(row["title"], "Index authority v2")
        self.assertEqual(len(row["history"]), 2)
        self.assertEqual(row["history"][0]["title"], "Index authority")
        self.assertEqual(snapshot["retention_contract"]["source_events_deleted"], 0)

    def test_tampering_is_detected(self):
        events = chain(("RECORD_CREATED", "MEM-TEST-1", {"record": memory_record()}))
        altered = copy.deepcopy(events)
        altered[0]["payload"]["record"]["body"] = "Silent overwrite"
        with self.assertRaisesRegex(ValueError, "event hash mismatch"):
            validate_chain(altered)

    def test_delete_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "deletion events are prohibited"):
            make_event(1, "RECORD_DELETED", "MEM-TEST-1", {}, "0" * 64)

    def test_open_conflicts_are_visible(self):
        events = chain(
            ("RECORD_CREATED", "MEM-TEST-1", {"record": memory_record()}),
            ("RECORD_CREATED", "MEM-TEST-2", {"record": memory_record("MEM-TEST-2", "Conflicting record", "Different content.")}),
            ("CONFLICT_RECORDED", "MEM-TEST-1", {"claim": "A differs from B", "conflicts_with": "MEM-TEST-2", "reason": "Compare primary sources."}),
        )
        snapshot = replay_snapshot(events)
        row = next(item for item in snapshot["memory_records"] if item["record_id"] == "MEM-TEST-1")
        self.assertEqual(row["state"], "CONFLICT")
        self.assertEqual(snapshot["open_conflict_count"], 1)

    def test_supersession_does_not_delete_history(self):
        events = chain(
            ("RECORD_CREATED", "MEM-TEST-1", {"record": memory_record()}),
            ("RECORD_CREATED", "MEM-TEST-2", {"record": memory_record("MEM-TEST-2", "Replacement", "Newer version.")}),
            ("RECORD_SUPERSEDED", "MEM-TEST-1", {"superseded_by_record_id": "MEM-TEST-2", "reason": "Reviewed replacement."}),
        )
        row = next(item for item in replay_snapshot(events)["memory_records"] if item["record_id"] == "MEM-TEST-1")
        self.assertEqual(row["state"], "SUPERSEDED")
        self.assertEqual(row["history"][0]["title"], "Index authority")

    def test_search_returns_existing_memory_or_empty(self):
        snapshot = replay_snapshot(chain(("RECORD_CREATED", "MEM-TEST-1", {"record": memory_record()})))
        self.assertEqual(search_snapshot(snapshot, "index authority")[0]["record_id"], "MEM-TEST-1")
        self.assertEqual(search_snapshot(snapshot, "fictional unsupported claim"), [])

    def test_checked_in_memory_ledger_is_hash_valid(self):
        ledger = Path(__file__).resolve().parents[1] / "registry" / "omega" / "system-memory" / "ledger.v1.jsonl"
        events = read_ledger(ledger)
        state = validate_chain(events)
        snapshot = replay_snapshot(events)
        self.assertEqual(len(events), 18)
        self.assertEqual(len(state["records"]), 10)
        self.assertGreater(len(snapshot["relations"]), 0)
        self.assertEqual(snapshot["retention_contract"]["source_events_deleted"], 0)


if __name__ == "__main__":
    unittest.main()
