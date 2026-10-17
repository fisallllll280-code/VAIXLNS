import io
import json
import os
import unittest
from unittest.mock import patch

from scripts.vx_model_federation import call_provider, run_federation


class ModelFederationTests(unittest.TestCase):
    def test_missing_credentials_are_reported_without_network_call(self):
        provider = {
            "provider": "openai", "model_id": "gpt-test", "api_family": "responses",
            "endpoint": "https://api.openai.com/v1/responses", "credential_env": "VX_TEST_OPENAI_KEY"
        }
        with patch.dict(os.environ, {}, clear=True), patch("urllib.request.urlopen") as network:
            result = call_provider(provider, "test", timeout=1, max_output_chars=100)
        self.assertEqual(result["status"], "NOT_CONFIGURED")
        network.assert_not_called()
        self.assertNotIn("api_key", result)

    def test_openai_responses_shape_and_secret_redaction(self):
        provider = {
            "provider": "openai", "model_id": "gpt-test", "api_family": "responses",
            "endpoint": "https://api.openai.com/v1/responses", "credential_env": "VX_TEST_OPENAI_KEY"
        }
        fake_response = io.BytesIO(json.dumps({"output_text": "verified output"}).encode("utf-8"))
        with patch.dict(os.environ, {"VX_TEST_OPENAI_KEY": "never-print-this"}), patch("urllib.request.urlopen", return_value=fake_response) as network:
            result = call_provider(provider, "hello", timeout=1, max_output_chars=100)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["text"], "verified output")
        self.assertNotIn("never-print-this", json.dumps(result))
        request = network.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertIn("Bearer never-print-this", request.get_header("Authorization"))

    def test_registry_fanout_is_bounded_and_missing_keys_fail_closed(self):
        registry = {
            "policy": {"parallelism_max": 99},
            "providers": [
                {"provider": f"p{i}", "model_id": "test", "api_family": "responses",
                 "endpoint": "https://example.invalid", "credential_env": f"VX_UNUSED_KEY_{i}"}
                for i in range(8)
            ]
        }
        with patch.dict(os.environ, {}, clear=True):
            report = run_federation(registry, "task", timeout=1, max_output_chars=100)
        self.assertEqual(report["provider_count"], 8)
        self.assertEqual(report["success_count"], 0)
        self.assertEqual(report["status"], "NO_PROVIDER_SUCCEEDED")
        self.assertTrue(all(item["status"] == "NOT_CONFIGURED" for item in report["results"]))
        self.assertFalse(report["canonical_mutation_performed"])


if __name__ == "__main__":
    unittest.main()
