import unittest

from scripts.arcx_interoperability_fabric import (
    SCHEMA_VERSION, plan_route, validate_connector
)


def manifest(state="VERIFIED", risk="READ", admitted=True):
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_id": "provider.example",
        "provider": "example",
        "adapter_version": "1.0.0",
        "contract_version": "1",
        "state": state,
        "capabilities": [{
            "name": "repository.read",
            "risk": risk,
            "input_schema_ref": "schema:input:v1",
            "output_schema_ref": "schema:output:v1",
        }],
        "authorization": {
            "granted_scopes": ["repo:read"],
            "policy_admitted": admitted,
            "credential_mode": "NO_CREDENTIALS",
        },
        "provenance": {"source": "repo://adapter", "digest": "sha256:abc"},
    }


class InteroperabilityFabricTests(unittest.TestCase):
    def test_valid_connector_manifest(self):
        self.assertTrue(validate_connector(manifest())["valid"])

    def test_registered_connector_is_not_route_eligible(self):
        result = plan_route([manifest(state="REGISTERED")], ["repository.read"])
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

    def test_missing_capability_is_explicit(self):
        result = plan_route([manifest()], ["repository.read", "cloud.deploy"])
        self.assertEqual(result["unresolved_capabilities"], ["cloud.deploy"])

    def test_bad_schema_is_rejected(self):
        item = manifest()
        item["schema_version"] = "wrong"
        self.assertFalse(validate_connector(item)["valid"])

    def test_route_is_deterministic(self):
        items = [manifest()]
        self.assertEqual(
            plan_route(items, ["repository.read"]),
            plan_route(items, ["repository.read"]),
        )


if __name__ == "__main__":
    unittest.main()
