import json
import os
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from scripts.vx_verify import timestamp_is_fresh
from scripts.vx_verify import check_meeting_health

from scripts.vx_verify import check_meeting_health, check_service_health, check_service_health_detailed


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

    def test_detailed_health_reports_missing_configuration_without_weakening_gate(self):
        with patch.dict(os.environ, {}, clear=True):
            ok, outcomes, diagnostics = check_service_health_detailed()
        self.assertFalse(ok)
        self.assertEqual(set(outcomes), {"VX", "VLNS", "LNS", "NEXENT"})
        self.assertTrue(all(value == "FAIL" for value in outcomes.values()))
        self.assertTrue(all(value == "NOT_CONFIGURED" for value in diagnostics.values()))

    def test_detailed_health_identifies_missing_url_and_invalid_scheme(self):
        urls = {
            "VX": "https://example.invalid/health",
            "VLNS": "",
            "LNS": "ftp://example.invalid/health",
            "NEXENT": "https://example.invalid/health",
        }
        with patch.dict(os.environ, {"VX_SERVICE_HEALTH_URLS": json.dumps(urls)}, clear=True):
            with patch("scripts.vx_verify.http_json", return_value={"status": "healthy"}):
                ok, outcomes, diagnostics = check_service_health_detailed()
        self.assertFalse(ok)
        self.assertEqual(outcomes, {"VX": "PASS", "VLNS": "FAIL", "LNS": "FAIL", "NEXENT": "PASS"})
        self.assertEqual(diagnostics["VX"], "HEALTHY")
        self.assertEqual(diagnostics["VLNS"], "URL_NOT_CONFIGURED")
        self.assertEqual(diagnostics["LNS"], "INVALID_URL_SCHEME")
        self.assertEqual(diagnostics["NEXENT"], "HEALTHY")

    def test_detailed_health_distinguishes_unavailable_and_unhealthy_responses(self):
        urls = {name: "https://example.invalid/health" for name in ("VX", "VLNS", "LNS", "NEXENT")}
        responses = [None, {"status": "degraded"}, {"ok": True}, None]
        with patch.dict(os.environ, {"VX_SERVICE_HEALTH_URLS": json.dumps(urls)}, clear=True):
            with patch("scripts.vx_verify.http_json", side_effect=responses):
                ok, outcomes, diagnostics = check_service_health_detailed()
        self.assertFalse(ok)
        self.assertEqual(outcomes, {"VX": "FAIL", "VLNS": "FAIL", "LNS": "PASS", "NEXENT": "FAIL"})
        self.assertEqual(diagnostics["VX"], "ENDPOINT_UNAVAILABLE_OR_INVALID_RESPONSE")
        self.assertEqual(diagnostics["VLNS"], "UNHEALTHY_RESPONSE")
        self.assertEqual(diagnostics["LNS"], "HEALTHY")
        self.assertEqual(diagnostics["NEXENT"], "ENDPOINT_UNAVAILABLE_OR_INVALID_RESPONSE")

    def test_missing_meeting_endpoint_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(check_meeting_health())

    def test_stale_connector_evidence_timestamp_fails(self):
        old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self.assertFalse(timestamp_is_fresh(old))

    def test_naive_timestamp_fails_closed(self):
        self.assertFalse(timestamp_is_fresh("2026-10-18T00:00:00"))

    def test_recent_timezone_aware_timestamp_passes(self):
        self.assertTrue(timestamp_is_fresh(datetime.now(timezone.utc).isoformat()))

    def test_static_meeting_health_fixture_fails_challenge(self):
        static_payload = {
            "probe_challenge": "fixed",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "room_live": True,
            "audio_test_passed": True,
            "participant_presence_verified": True,
            "names_persisted": True,
            "session_id": "session",
            "participant_count": 2,
        }
        with patch.dict(os.environ, {"VX_MEETING_HEALTH_URL": "https://example.invalid/health"}):
            with patch("scripts.vx_verify.http_json", return_value=static_payload):
                self.assertFalse(check_meeting_health())

    def test_meeting_health_requires_fresh_challenge_echo(self):
        def live_endpoint(url, timeout=4.0, headers=None):
            return {
                "probe_challenge": headers["X-VX-Probe-Challenge"],
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "room_live": True,
                "audio_test_passed": True,
                "participant_presence_verified": True,
                "names_persisted": True,
                "session_id": "live-session",
                "participant_count": 2,
            }
        with patch.dict(os.environ, {"VX_MEETING_HEALTH_URL": "https://example.invalid/health"}):
            with patch("scripts.vx_verify.http_json", side_effect=live_endpoint):
                self.assertTrue(check_meeting_health())


if __name__ == "__main__":
    unittest.main()
