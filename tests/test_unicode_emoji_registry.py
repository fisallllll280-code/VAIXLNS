"""Boundary and deterministic tests with miniature official-format fixtures."""
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from unicode_emoji_registry import build_registry

HEADER = "# emoji-test.txt\n# Version: 18.0\n# group: Smileys & Emotion\n# subgroup: face-smiling\n"
BODY = (
    "1F600 ; fully-qualified # 😀 E1.0 grinning face\n"
    "1F44B 1F3FD ; fully-qualified # 👋🏽 E1.0 waving hand: medium skin tone\n"
    "1F469 200D 1F4BB ; fully-qualified # 👩‍💻 E4.0 woman technologist\n"
    "1F1F8 1F1E6 ; fully-qualified # 🇸🇦 E2.0 flag: Saudi Arabia\n"
)

class UnicodeEmojiRegistryTests(unittest.TestCase):
    def test_compound_modifier_flag_and_zwj(self):
        raw = (HEADER + BODY).encode()
        data = build_registry(raw)
        self.assertEqual(data["record_count"], 4)
        self.assertEqual(data["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(data["records"][2]["codepoints"], ["U+1F469", "U+200D", "U+1F4BB"])
        self.assertEqual(data["records"][3]["sequence"], "🇸🇦")

    def test_reproducible(self):
        raw = (HEADER + BODY).encode()
        self.assertEqual(build_registry(raw), build_registry(raw))

    def test_wrong_version_fails_closed(self):
        with self.assertRaises(ValueError):
            build_registry((HEADER + BODY).replace("18.0", "17.0").encode())

    def test_wrong_display_fails_closed(self):
        with self.assertRaises(ValueError):
            build_registry((HEADER + BODY).replace("😀 E1.0", "😎 E1.0").encode())

    def test_duplicate_fails_closed(self):
        with self.assertRaises(ValueError):
            build_registry((HEADER + BODY + BODY).encode())

    def test_malformed_and_surrogate_fail_closed(self):
        with self.assertRaises(ValueError):
            build_registry((HEADER + "D800 ; fully-qualified # x E1.0 bad\n").encode())

    def test_invalid_utf8_fails_closed(self):
        with self.assertRaises(UnicodeDecodeError):
            build_registry(b"\xff")

if __name__ == "__main__":
    unittest.main()
