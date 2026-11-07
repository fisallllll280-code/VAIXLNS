from __future__ import annotations
import json
import unittest
from pathlib import Path
from tools.four_system_interface_audit import DEFAULT_REGISTRY, validate

class FourSystemInterfaceAuditTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))

    def test_registry_has_four_unique_systems_and_six_edges(self):
        self.assertEqual({item["system_id"] for item in self.document["systems"]}, {"VAIXLNS", "VLNS", "VX", "NEXNET"})
        self.assertEqual(len(self.document["systems"]), 4)
        self.assertEqual(len(self.document["interface_edges"]), 6)
        self.assertEqual(validate(self.document), [])

    def test_unconfigured_transport_cannot_claim_live_verified(self):
        self.document["interface_edges"][0]["status"] = "LIVE_VERIFIED"
        self.assertIn("VAIXLNS-VLNS-01:LIVE_WITHOUT_CONFIGURED_TRANSPORT", validate(self.document))

    def test_unknown_system_edge_is_rejected(self):
        self.document["interface_edges"][0]["target"] = "UNKNOWN"
        self.assertIn("VAIXLNS-VLNS-01:UNKNOWN_ENDPOINT_SYSTEM", validate(self.document))

    def test_identity_and_repository_are_not_collapsed(self):
        vlns = next(item for item in self.document["systems"] if item["system_id"] == "VLNS")
        self.assertEqual(vlns["identity_status"], "IDENTITY_UNVERIFIED")
        self.assertTrue(any("NAXLNS" in item["repository"] for item in vlns["repository_surfaces"]))
        self.assertTrue(any("NEXENT" in item["repository"] for item in vlns["repository_surfaces"]))

if __name__ == "__main__":
    unittest.main()
