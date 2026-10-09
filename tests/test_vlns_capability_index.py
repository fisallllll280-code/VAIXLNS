import copy
import json
import unittest
from pathlib import Path

from scripts.validate_vlns_capability_index import DEFAULT_INDEX, validate


class VlnsCapabilityIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(DEFAULT_INDEX.read_text(encoding="utf-8"))

    def test_canonical_catalog_is_consistent(self):
        errors = validate(self.catalog)
        self.assertEqual(errors, [])
        self.assertEqual(self.catalog["catalog_depth"]["attribute_families"], 15)
        self.assertEqual(self.catalog["catalog_depth"]["indexed_attribute_fields"], 302)

    def test_duplicate_fields_are_rejected(self):
        damaged = copy.deepcopy(self.catalog)
        damaged["attribute_families"][0]["fields"].append(damaged["attribute_families"][0]["fields"][0])
        self.assertTrue(any(error.startswith("duplicate_attribute_field:") for error in validate(damaged)))

    def test_live_unauthed_connection_cannot_be_marked_verified(self):
        damaged = copy.deepcopy(self.catalog)
        damaged["connections"][0]["live_state"] = "VERIFIED"
        damaged["connections"][0]["authenticated"] = False
        self.assertTrue(any(error.startswith("verified_live_link_requires_authentication:") for error in validate(damaged)))

    def test_catalog_depth_mismatch_is_rejected(self):
        damaged = copy.deepcopy(self.catalog)
        damaged["catalog_depth"]["indexed_attribute_fields"] = 999
        self.assertTrue(any(error.startswith("catalog_depth_mismatch:indexed_attribute_fields") for error in validate(damaged)))

    def test_candidate_repository_identity_cannot_be_promoted_by_name_only(self):
        damaged = copy.deepcopy(self.catalog)
        next(row for row in damaged["systems"] if row["system_id"] == "VLNS")["identity_status"] = "CANONICAL"
        self.assertTrue(any(error == "candidate_identity_must_remain_unverified:VLNS" for error in validate(damaged)))


if __name__ == "__main__":
    unittest.main()
