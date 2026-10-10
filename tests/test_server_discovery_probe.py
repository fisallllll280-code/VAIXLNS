import hashlib
import unittest

from tools.server_discovery_probe import (
    probe_endpoint,
    run_discovery,
    validate_target_url,
)


class FakeResponse:
    def __init__(self, body=b'{"ok":true}', status=200):
        self.body = body
        self.status = status
        self.read_sizes = []

    def getcode(self):
        return self.status

    def read(self, size=-1):
        self.read_sizes.append(size)
        return self.body[:size]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return self.response


class ServerDiscoveryProbeTests(unittest.TestCase):
    def test_loopback_is_allowed_and_public_ip_is_blocked(self):
        self.assertEqual(
            validate_target_url("http://127.0.0.1:11434/api/version"),
            "http://127.0.0.1:11434/api/version",
        )
        result = probe_endpoint(
            "http://1.1.1.1/health",
            target_id="PUBLIC",
        )
        self.assertEqual(result["observation_status"], "BLOCKED_UNSAFE_TARGET")
        self.assertFalse(result["healthy"])

    def test_private_ip_requires_explicit_private_scope(self):
        with self.assertRaises(ValueError):
            validate_target_url("http://192.168.1.20:20429/t")
        self.assertEqual(
            validate_target_url(
                "http://192.168.1.20:20429/t",
                allow_private_ip=True,
            ),
            "http://192.168.1.20:20429/t",
        )
        with self.assertRaises(ValueError):
            validate_target_url(
                "http://example.com/health",
                allow_private_ip=True,
            )

    def test_credentials_query_and_fragment_are_rejected(self):
        for url in (
            "http://user:secret@127.0.0.1:11434/api/version",
            "http://127.0.0.1:11434/api/version?token=secret",
            "http://127.0.0.1:11434/api/version#fragment",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_target_url(url)

    def test_probe_is_get_only_bounded_and_hashes_not_returns_body(self):
        body = b'{"service":"ollama","version":"test"}'
        response = FakeResponse(body=body)
        opener = FakeOpener(response)
        result = probe_endpoint(
            "http://127.0.0.1:11434/api/version",
            target_id="OLLAMA-LOCAL-001",
            timeout_seconds=90,
            opener_factory=lambda: opener,
        )
        self.assertEqual(result["observation_status"], "HTTP_200")
        self.assertTrue(result["healthy"])
        self.assertEqual(result["response_sha256"], hashlib.sha256(body).hexdigest())
        self.assertNotIn("service", result)
        self.assertEqual(opener.request.get_method(), "GET")
        self.assertLessEqual(opener.timeout, 5.0)

    def test_configured_lan_target_is_opt_in_and_redacted(self):
        registry = {
            "schema_id": "test",
            "schema_version": "1",
            "targets": [
                {
                    "id": "LAN-HTTP-001",
                    "probe": {"enabled": False},
                }
            ],
        }
        skipped = run_discovery(
            registry,
            timeout_seconds=3,
            allow_configured_lan_target=False,
            environ={"VAIXLNS_DISCOVERY_TARGET": "http://192.168.1.20:20429/t"},
        )
        self.assertEqual(
            skipped["results"][0]["observation_status"],
            "SKIPPED_NEEDS_OPT_IN",
        )

        response = FakeResponse(body=b"ready", status=200)
        opener = FakeOpener(response)
        allowed = run_discovery(
            registry,
            timeout_seconds=3,
            allow_configured_lan_target=True,
            environ={"VAIXLNS_DISCOVERY_TARGET": "http://192.168.1.20:20429/t"},
            opener_factory=lambda: opener,
        )
        row = allowed["results"][0]
        self.assertEqual(row["observation_status"], "HTTP_200")
        self.assertEqual(row["target"], "<private-configured-endpoint>")
        self.assertNotIn("192.168.1.20", row["target"])

    def test_inventory_only_targets_are_not_probed(self):
        registry = {
            "schema_id": "test",
            "schema_version": "1",
            "targets": [
                {
                    "id": "CORE",
                    "endpoint": "http://127.0.0.1:8000/health",
                    "probe": {"enabled": False, "reason": "source conflict"},
                }
            ],
        }
        result = run_discovery(
            registry,
            timeout_seconds=3,
            allow_configured_lan_target=False,
            environ={},
        )
        self.assertEqual(
            result["results"][0]["observation_status"],
            "NOT_PROBED_BY_DEFAULT",
        )


if __name__ == "__main__":
    unittest.main()
