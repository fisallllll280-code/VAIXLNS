import unittest
from scripts.social_publication_gate import prepare_publication

class SocialPublicationGateTests(unittest.TestCase):
    def test_valid_input_only_prepares_draft(self):
        r = prepare_publication("VX", ["linkedin", "x"], "Announcement")
        self.assertEqual(r["status"], "DRAFT_REVIEW_REQUIRED")
        self.assertFalse(r["publish_executed"])
        self.assertFalse(r["oauth_connected"])
        self.assertEqual(len(r["receipt_sha256"]), 64)

    def test_invalid_channel_types_fail_closed(self):
        for c in ({}, [], None, 123, "unregistered"):
            with self.subTest(channel=c):
                r = prepare_publication("VX", [c], "Hello")
                self.assertEqual(r["status"], "BLOCKED")
                self.assertIn("INVALID_CHANNELS", r["blockers"])

    def test_empty_text_and_program_block(self):
        self.assertEqual(prepare_publication("", ["x"], "ok")["status"], "BLOCKED")
        self.assertEqual(prepare_publication("VX", ["x"], "")["status"], "BLOCKED")

    def test_deterministic_receipt(self):
        a = prepare_publication("VX", ["x", "linkedin"], "hello")
        b = prepare_publication("VX", ["linkedin", "x"], "hello")
        self.assertEqual(a, b)

    def test_unapproved_external_publish_is_impossible(self):
        r = prepare_publication("VX", ["x"], "hello", approvals={"owner": True})
        self.assertFalse(r["publish_executed"])
        self.assertFalse(r["oauth_connected"])
        self.assertEqual(r["external_spend_sar"], 0)

if __name__ == "__main__":
    unittest.main()
