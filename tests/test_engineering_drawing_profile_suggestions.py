from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from suggest_engineering_drawing_profiles import suggest_profiles  # noqa: E402


def registry():
    return {
        "registry_state": "REFERENCE_ONLY",
        "profiles": [
            {"id": "TPD-GENERAL-ISO", "discipline": ["mechanical", "architectural"], "purpose": "Technical drawing", "standards": [{"code": "ISO 128-1", "edition": "2020", "url": "https://example.test/iso128"}]},
            {"id": "MECHANICAL-GDT-ISO", "discipline": ["mechanical"], "purpose": "ISO GPS", "standards": [{"code": "ISO 1101", "edition": "2017", "url": "https://example.test/iso1101"}]},
            {"id": "MECHANICAL-GDT-ASME", "discipline": ["mechanical"], "purpose": "ASME GDT", "standards": [{"code": "ASME Y14.5", "edition": "2018 (R2024)", "url": "https://example.test/asme"}]},
            {"id": "BIM-ISO-IFC", "discipline": ["architectural"], "purpose": "BIM", "standards": []},
            {"id": "SAUDI-BUILDING-2024", "discipline": ["architectural", "civil_structural"], "jurisdiction": "Saudi Arabia", "purpose": "Saudi codes", "standards": []},
        ],
    }


class EngineeringDrawingProfileSuggestionTests(unittest.TestCase):
    def test_mechanical_job_suggests_both_gdt_families_but_selects_none(self):
        result = suggest_profiles({"discipline": "mechanical", "jurisdiction": "ISO"}, registry())
        self.assertTrue(result["valid_request"])
        ids = {item["profile_id"] for item in result["suggestions"]}
        self.assertIn("MECHANICAL-GDT-ISO", ids)
        self.assertIn("MECHANICAL-GDT-ASME", ids)
        self.assertEqual(result["auto_selected_profiles"], [])
        self.assertTrue(result["human_confirmation_required"])
        self.assertTrue(any("alternatives" in warning for warning in result["warnings"]))

    def test_saudi_profile_is_suggested_only_for_sufficiently_explicit_jurisdiction(self):
        domestic = suggest_profiles({"discipline": "civil_structural", "jurisdiction": "Saudi Arabia / SBC"}, registry())
        international = suggest_profiles({"discipline": "civil_structural", "jurisdiction": "International"}, registry())
        self.assertIn("SAUDI-BUILDING-2024", {x["profile_id"] for x in domestic["suggestions"]})
        self.assertNotIn("SAUDI-BUILDING-2024", {x["profile_id"] for x in international["suggestions"]})

    def test_missing_discipline_or_jurisdiction_is_rejected(self):
        result = suggest_profiles({"discipline": "mechanical"}, registry())
        self.assertFalse(result["valid_request"])
        self.assertTrue(result["errors"])

    def test_nonmatching_discipline_does_not_force_a_profile(self):
        result = suggest_profiles({"discipline": "robotics", "jurisdiction": "International"}, registry())
        self.assertTrue(result["valid_request"])
        self.assertEqual(result["suggestions"], [])
        self.assertTrue(result["warnings"])

    def test_malformed_entries_are_skipped_with_warning(self):
        data = registry()
        data["profiles"].append("malformed")
        result = suggest_profiles({"discipline": "mechanical", "jurisdiction": "ISO"}, data)
        self.assertTrue(result["valid_request"])
        self.assertTrue(any("Malformed profile" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
