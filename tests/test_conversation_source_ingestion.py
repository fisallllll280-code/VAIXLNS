import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.ingest_conversation_sources import IntakeError, ingest


class ConversationSourceIngestionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.sources = self.root / "incoming"
        self.sources.mkdir()
        self.vault = self.root / "private-vault"

    def tearDown(self):
        self.tmp.cleanup()

    def sample_conversation(self):
        return [{
            "id": "conversation-1",
            "title": "private title must not leak",
            "mapping": {
                "root": {"id": "root", "parent": None, "children": ["user", "branch"], "message": None},
                "user": {"id": "user", "parent": "root", "children": ["assistant"], "message": {"author": {"role": "user"}, "content": {"parts": ["secret text"]}}},
                "assistant": {"id": "assistant", "parent": "user", "children": [], "message": {"author": {"role": "assistant"}, "content": {"parts": ["answer"]}}},
                "branch": {"id": "branch", "parent": "root", "children": [], "message": {"author": {"role": "assistant"}, "content": {"parts": ["alternate branch"]}}},
            },
            "current_node": "assistant",
        }]

    def test_json_export_preserves_all_nodes_and_branches(self):
        source = self.sources / "conversations.json"
        source.write_text(json.dumps(self.sample_conversation()), encoding="utf-8")
        result = ingest([source], self.vault, False, None, 10_000_000, 20_000_000)
        self.assertEqual(result["total_conversations"], 1)
        self.assertEqual(result["total_message_nodes"], 4)
        self.assertFalse(self.vault.exists())

    def test_zip_export_is_parsed_without_extracting_archive_paths(self):
        source = self.sources / "export.zip"
        payload = json.dumps(self.sample_conversation()).encode()
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("user/conversations.json", payload)
            archive.writestr("../../outside.txt", b"must never be extracted")
        result = ingest([source], self.vault, False, None, 10_000_000, 20_000_000)
        self.assertEqual(result["sources"][0]["source_kind"], "CHATGPT_EXPORT_ZIP")
        self.assertFalse((self.root / "outside.txt").exists())

    def test_text_transcript_is_preserved_verbatim(self):
        source = self.sources / "session.txt"
        source.write_text("USER: first\\nASSISTANT: second\\n", encoding="utf-8")
        result = ingest([source], self.vault, False, None, 10_000_000, 20_000_000)
        self.assertEqual(result["sources"][0]["parser_state"], "PARSED_AS_SINGLE_SOURCE")
        self.assertEqual(result["total_conversations"], 1)

    def test_apply_writes_immutable_raw_and_normalized_records_idempotently(self):
        source = self.sources / "conversations.json"
        source.write_text(json.dumps(self.sample_conversation()), encoding="utf-8")
        ingest([source], self.vault, True, None, 10_000_000, 20_000_000)
        manifest = self.vault / "manifests" / "sources.jsonl"
        self.assertTrue(manifest.exists())
        self.assertEqual(len(manifest.read_text(encoding="utf-8").splitlines()), 1)
        ingest([source], self.vault, True, None, 10_000_000, 20_000_000)
        self.assertEqual(len(manifest.read_text(encoding="utf-8").splitlines()), 1)
        normalized = list((self.vault / "normalized").glob("*.json"))
        self.assertEqual(len(normalized), 1)
        record = json.loads(normalized[0].read_text(encoding="utf-8"))
        self.assertEqual(len(record["mapping"]), 4)
        self.assertIn("alternate branch", json.dumps(record, ensure_ascii=False))

    def test_public_manifest_does_not_leak_titles_filenames_or_content(self):
        source = self.sources / "conversations.json"
        source.write_text(json.dumps(self.sample_conversation()), encoding="utf-8")
        public = self.root / "public" / "manifest.json"
        ingest([source], self.vault, True, public, 10_000_000, 20_000_000)
        payload = public.read_text(encoding="utf-8")
        self.assertNotIn("private title", payload)
        self.assertNotIn("conversations.json", payload)
        self.assertNotIn("secret text", payload)

    def test_vault_inside_git_checkout_is_rejected(self):
        checkout = self.root / "repo"
        (checkout / ".git").mkdir(parents=True)
        vault = checkout / "archive" / "sessions"
        source = self.sources / "session.txt"
        source.write_text("safe sample", encoding="utf-8")
        with self.assertRaises(IntakeError):
            ingest([source], vault, False, None, 10_000_000, 20_000_000)

    def test_duplicate_content_keeps_each_source_occurrence(self):
        first = self.sources / "session-a.txt"
        second = self.sources / "session-b.txt"
        first.write_text("same source bytes", encoding="utf-8")
        second.write_text("same source bytes", encoding="utf-8")
        ingest([first, second], self.vault, True, None, 10_000_000, 20_000_000)
        manifest = self.vault / "manifests" / "sources.jsonl"
        rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["source_id"], rows[1]["source_id"])
        self.assertNotEqual(rows[0]["source_occurrence_id"], rows[1]["source_occurrence_id"])
        self.assertEqual(len(list((self.vault / "raw").glob("*.bin"))), 1)

    def test_malformed_json_is_preserved_but_quarantined(self):
        source = self.sources / "broken.json"
        original = b"{not valid json"
        source.write_bytes(original)
        result = ingest([source], self.vault, True, None, 10_000_000, 20_000_000)
        self.assertEqual(result["sources"][0]["parser_state"], "QUARANTINED_PARSE_ERROR")
        raw_path = self.vault / "raw" / (result["sources"][0]["source_sha256"] + ".bin")
        self.assertEqual(raw_path.read_bytes(), original)
        self.assertFalse(list((self.vault / "normalized").glob("*.json")))

    def test_unknown_binary_is_preserved_as_opaque(self):
        source = self.sources / "diagram.bin"
        source.write_bytes(b"opaque bytes")
        result = ingest([source], self.vault, False, None, 10_000_000, 20_000_000)
        self.assertEqual(result["sources"][0]["parser_state"], "PRESERVED_CONTENT_EXTRACTION_PENDING")


if __name__ == "__main__":
    unittest.main()
