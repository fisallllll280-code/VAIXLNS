import unittest
from datetime import date
from service_assistant import preflight

class ServiceAssistantTests(unittest.TestCase):
    def test_no_appointment_assertion(self):
        result=preflight("appointment_guidance",{},today=date(2026,10,27))
        self.assertIn("APPOINTMENT_NEED_MUST_BE_VERIFIED_OFFICIALLY",result.warnings)
        self.assertEqual(result.action_mode,"GUIDANCE_ONLY")
    def test_reject_otp(self):
        r=preflight("passport_guidance",{"otp":"123456"},today=date(2026,10,27))
        self.assertEqual(r.status,"BLOCKED")
        self.assertNotIn("123456",str(r))
    def test_reject_secret_field(self):
        self.assertEqual(preflight("passport_guidance",{"user_secret":"x"}).status,"BLOCKED")
    def test_reject_unsupported_service(self):
        self.assertEqual(preflight("unknown",{}).status,"BLOCKED")
    def test_stale_reference(self):
        r=preflight("passport_guidance",{"operation":"renew","arabic_latin_name_review":"confirmed"},source_verified_on="2026-01-01",today=date(2026,10,27))
        self.assertIn("REQUIREMENTS_STALE_OR_FUTURE",r.warnings)
    def test_ready_only_when_source_current_and_reviewed(self):
        r=preflight("passport_guidance",{"operation":"issue","arabic_latin_name_review":"confirmed"},source_verified_on="2026-10-27",today=date(2026,10,27))
        self.assertEqual(r.status,"GUIDANCE_READY")
        self.assertEqual(r.action_mode,"GUIDANCE_ONLY")
    def test_missing_source_blocks_readiness(self):
        r=preflight("passport_guidance",{"operation":"renew","arabic_latin_name_review":"confirmed"})
        self.assertEqual(r.status,"REVIEW_REQUIRED")
    def test_invalid_date(self):
        self.assertIn("INVALID_SOURCE_DATE",preflight("passport_guidance",{},source_verified_on="not-a-date").warnings)

if __name__=="__main__":
    unittest.main()
