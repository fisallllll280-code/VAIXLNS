import unittest

from scripts.arcx_interoperability_fabric import (
    SCHEMA_VERSION, plan_route, validate_connector
)
from scripts.arcx_secret_boundary import validate_secret_reference


def manifest(state="VERIFIED", risk="READ", admitted=True, scopes=None, required_scopes=None):
    item = {
        "schema_version": SCHEMA_VERSION,
        "tool_id": "provider.example",
        "provider": "example",
        "adapter_version": "1.0.0",
        "contract_version": "1",
        "policy_version": "policy/1",
        "state": state,
        "capabilities": [{
            "name": "repository.read",
            "risk": risk,
            "required_scopes": ["repo:read"] if required_scopes is None else required_scopes,
            "input_schema_ref": "schema:input:v1",
            "output_schema_ref": "schema:output:v1",
        }],
        "authorization": {
            "granted_scopes": ["repo:read"] if scopes is None else scopes,
            "policy_admitted": admitted,
            "credential_mode": "NO_CREDENTIALS",
        },
        "provenance": {
            "source": "repo://adapter",
            "digest": "sha256:" + "a" * 64,
        },
        "verification": {
            "verifier_id": "independent-verifier.example",
            "receipt_digest": "sha256:" + "b" * 64,
        },
    }
    return item


class InteroperabilityFabricTests(unittest.TestCase):
    def test_valid_connector_manifest(self):
        self.assertTrue(validate_connector(manifest())["valid"])

    def test_registered_connector_is_not_route_eligible(self):
        result = plan_route([manifest(state="REGISTERED")], ["repository.read"])
        self.assertEqual(result["state"], "CAPABILITY_GAPS")

    def test_connected_connector_is_not_route_eligible(self):
        result = plan_route([manifest(state="CONNECTED")], ["repository.read"])
        self.assertEqual(result["state"], "CAPABILITY_GAPS")

    def test_policy_admission_is_required(self):
        result = plan_route([manifest(admitted=False)], ["repository.read"])
        self.assertEqual(result["state"], "CAPABILITY_GAPS")

    def test_write_capability_is_blocked_by_default(self):
        result = plan_route([manifest(risk="WRITE")], ["repository.read"])
        self.assertEqual(result["state"], "CAPABILITY_GAPS")

    def test_write_capability_can_only_be_candidate_with_explicit_flag(self):
        result = plan_route([manifest(risk="WRITE")], ["repository.read"], allow_write=True)
        self.assertEqual(result["state"], "CANDIDATES_AVAILABLE")
        self.assertFalse(result["execution_performed"])
        self.assertFalse(result["authority_granted"])

    def test_missing_capability_is_explicit(self):
        result = plan_route([manifest()], ["repository.read", "cloud.deploy"])
        self.assertEqual(result["unresolved_capabilities"], ["cloud.deploy"])

    def test_bad_schema_is_rejected(self):
        item = manifest()
        item["schema_version"] = "wrong"
        self.assertFalse(validate_connector(item)["valid"])

    def test_missing_required_scope_blocks_route(self):
        result = plan_route([manifest(scopes=["profile:read"])], ["repository.read"])
        self.assertEqual(result["state"], "CAPABILITY_GAPS")

    def test_malformed_provenance_digest_is_rejected(self):
        item = manifest()
        item["provenance"]["digest"] = "sha256:abc"
        self.assertIn("PROVENANCE_DIGEST_INVALID", validate_connector(item)["errors"])

    def test_verified_label_without_receipt_is_rejected(self):
        item = manifest()
        item.pop("verification")
        self.assertIn("VERIFICATION_RECEIPT_REQUIRED", validate_connector(item)["errors"])

    def test_malformed_verification_receipt_is_rejected(self):
        item = manifest()
        item["verification"]["receipt_digest"] = "sha256:fake"
        self.assertIn("VERIFICATION_RECEIPT_DIGEST_INVALID", validate_connector(item)["errors"])

    def test_route_is_deterministic(self):
        items = [manifest()]
        self.assertEqual(
            plan_route(items, ["repository.read"]),
            plan_route(items, ["repository.read"]),
        )

    def test_secret_reference_requires_allowlisted_scheme(self):
        self.assertTrue(validate_secret_reference("vault://kv/arcx/signing-key")["valid"])
        self.assertFalse(validate_secret_reference("https://example.com/key")["valid"])

    def test_secret_reference_rejects_path_traversal(self):
        self.assertFalse(validate_secret_reference("vault://kv/../prod/key")["valid"])

    def test_secret_reference_rejects_inline_credentials(self):
        self.assertFalse(validate_secret_reference("vault://user:password@kv/key")["valid"])


if __name__ == "__main__":
    unittest.main()
