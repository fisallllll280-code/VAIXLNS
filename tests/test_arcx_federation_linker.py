import unittest
from scripts.arcx_federation_linker import plan_links

class ArcxFederationLinkerTests(unittest.TestCase):
    def setUp(self):
        self.systems = [{"system_id": x} for x in ("VAIXLNS", "VX", "VV", "NEXENT", "NEXNET", "VLNS", "NAXLNS")]

    def candidate(self, source="VAIXLNS", target="VX", **overrides):
        value = {"link_id":"link-1","source_system":source,"target_system":target,"link_type":"API","source_revision":"a"*40,"contract_sha256":"b"*64}
        value.update(overrides)
        return value

    def test_valid_candidate_remains_pending_without_authority(self):
        plan = plan_links(self.systems, [self.candidate()])
        self.assertEqual(plan["state"], "PENDING_VERIFICATION")
        self.assertEqual(plan["links"][0]["state"], "PENDING_VERIFICATION")
        self.assertFalse(plan["links"][0]["authority_granted"])
        self.assertFalse(plan["execution_performed"])

    def test_unresolved_identity_pair_is_blocked(self):
        plan = plan_links(self.systems, [self.candidate("NEXNET", "NEXENT")])
        self.assertEqual(plan["links"][0]["state"], "BLOCKED")
        self.assertIn("IDENTITY_EQUIVALENCE_UNRESOLVED", plan["links"][0]["blockers"])

    def test_unknown_contract_digest_blocks(self):
        plan = plan_links(self.systems, [self.candidate(contract_sha256="not-a-digest")])
        self.assertEqual(plan["links"][0]["state"], "BLOCKED")

    def test_unknown_system_blocks(self):
        plan = plan_links(self.systems, [self.candidate("NOT-REGISTERED", "VX")])
        self.assertIn("UNKNOWN_SYSTEM_ID", plan["links"][0]["blockers"])

    def test_plan_is_deterministic(self):
        a = plan_links(self.systems, [self.candidate()])
        b = plan_links(list(reversed(self.systems)), [self.candidate()])
        self.assertEqual(a["plan_sha256"], b["plan_sha256"])

    def test_execution_never_happens_in_planner(self):
        plan = plan_links(self.systems, [self.candidate()])
        self.assertFalse(plan["execution_performed"])
        self.assertFalse(plan["canonical_write_performed"])

    def test_malformed_system_identifier_fails_closed(self):
        plan = plan_links(self.systems, [self.candidate(source=["VAIXLNS"])])
        self.assertEqual(plan["links"][0]["state"], "BLOCKED")
        self.assertIn("INVALID_SYSTEM_ID_TYPE", plan["links"][0]["blockers"])

    def test_invalid_source_revision_is_blocked(self):
        plan = plan_links(self.systems, [self.candidate(source_revision="main")])
        self.assertIn("INVALID_SOURCE_REVISION", plan["links"][0]["blockers"])

    def test_malformed_direction_is_blocked(self):
        plan = plan_links(self.systems, [self.candidate(direction=["BIDIRECTIONAL"])])
        self.assertIn("INVALID_LINK_DIRECTION", plan["links"][0]["blockers"])

if __name__ == "__main__":
    unittest.main()
