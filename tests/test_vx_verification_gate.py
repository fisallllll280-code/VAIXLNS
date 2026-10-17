import os
import unittest
from unittest.mock import patch

from scripts.vx_verify import check_meeting_health, check_service_health


class VXVerificationGateTests(unittest.TestCase):
    def test_missing_service_urls_fail_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            ok, services = check_service_health()
        self.assertFalse(ok)
        self.assertEqual(set(services), {"VX", "VLNS", "LNS", "NEXENT"})
        self.assertTrue(all(value == "FAIL" for value in services.values()))

    def test_invalid_service_json_fails_closed(self):
        with patch.dict(os.environ, {"VX_SERVICE_HEALTH_URLS": "not-json"}, clear=True):
            ok, services = check_service_health()
        self.assertFalse(ok)
        self.assertTrue(all(value == "INVALID_HEALTH_URLS_JSON" for value in services.values()))

    def test_missing_meeting_endpoint_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(check_meeting_health())


if __name__ == "__main__":
    unittest.main()
