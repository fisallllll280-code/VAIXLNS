import copy
import json
import unittest

from scripts.validate_federation_contract_edges import (
    CONTRACT,
    SYSTEMS_MANIFEST,
    REQUIRED_EDGES,
    validate,
)


class FederationContractEdgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.systems = json.loads(SYSTEMS_MANIFEST.read_text(encoding="utf-8"))

    def errors_for(self, mutate=None):
        data = copy.deepcopy(self.data)
        systems = copy.deepcopy(self.systems)
        if mutate:
            mutate(data, systems)
        return validate(data, systems)

    def edge(self, data, kind):
        return next(item for item in data["edges"] if item["kind"] == kind)

    def test_current_contract_passes_structural_gates(self):
        self.assertEqual(validate(self.data, self.systems), [])

    def test_all_required_edges_have_explicit_adapters(self):
        actual = {(e["from_system"], e["to_system"], e["kind"]) for e in self.data["edges"]}
        self.assertTrue(REQUIRED_EDGES.issubset(actual))
        self.assertTrue(all(e["adapter"] and e["contract_ref"] for e in self.data["edges"]))

    def test_cross_repository_direct_imports_are_forbidden(self):
        errors = self.errors_for(
            lambda d, s: d["boundary_rules"].update(
                direct_cross_repository_imports_allowed=True
            )
        )
        self.assertTrue(any("direct_cross_repository_imports_allowed" in e for e in errors))

    def test_unverified_identity_cannot_be_enabled(self):
        def mutate(data, systems):
            edge = next(e for e in data["edges"] if e["from_system"] == "VLNS")
            edge["enabled"] = True
            edge["status"] = "ADMISSION_REQUIRED"
        errors = self.errors_for(mutate)
        self.assertTrue(any("unresolved system identity" in e for e in errors))

    def test_blocked_identity_must_remain_disabled(self):
        errors = self.errors_for(
            lambda d, s: self.edge(d, "discovery_proposal").update(enabled=True)
        )
        self.assertTrue(any("BLOCKED_IDENTITY edges must be disabled" in e for e in errors))

    def test_unscoped_execution_and_self_authorization_are_forbidden(self):
        def mutate(data, systems):
            edge = self.edge(data, "execution_request")
            edge["forbidden_effects"].remove("self_authorization")
            edge["requires_authority_grant"] = False
        errors = self.errors_for(mutate)
        self.assertTrue(any("explicit authority grant" in e for e in errors))
        self.assertTrue(any("self-authorization" in e for e in errors))

    def test_proposals_cannot_write_canonical_state(self):
        def mutate(data, systems):
            edge = self.edge(data, "discovery_proposal")
            edge["forbidden_effects"].remove("canonical_write")
        errors = self.errors_for(mutate)
        self.assertTrue(any("cannot carry canonical or execution authority" in e for e in errors))

    def test_unknown_system_endpoint_is_rejected(self):
        errors = self.errors_for(
            lambda d, s: self.edge(d, "knowledge_observation").update(
                from_system="NAXLNS"
            )
        )
        self.assertTrue(any("declared system IDs" in e for e in errors))

    def test_missing_adapter_is_rejected(self):
        errors = self.errors_for(
            lambda d, s: self.edge(d, "execution_evidence").update(adapter="")
        )
        self.assertTrue(any("adapter is required" in e for e in errors))

    def test_active_edge_requires_revision_bound_evidence(self):
        def mutate(data, systems):
            edge = self.edge(data, "execution_evidence")
            edge["status"] = "ACTIVE_VERIFIED"
            edge["enabled"] = True
            edge["activation_evidence"] = {"evidence_uri": "https://example.invalid/receipt"}
        errors = self.errors_for(mutate)
        self.assertTrue(any("revision-bound activation evidence" in e for e in errors))

    def test_specified_edge_cannot_claim_active_connection(self):
        errors = self.errors_for(
            lambda d, s: self.edge(d, "execution_request").update(enabled=True)
        )
        self.assertTrue(any("SPECIFIED_NOT_CONNECTED edges must remain disabled" in e for e in errors))

    def test_unknown_contract_status_is_rejected(self):
        errors = self.errors_for(
            lambda d, s: d.update(status="VERIFIED")
        )
        self.assertTrue(any("contract status must remain non-verified" in e for e in errors))

    def test_every_edge_is_fail_closed(self):
        errors = self.errors_for(
            lambda d, s: self.edge(d, "execution_request").update(failure_mode="ALLOW")
        )
        self.assertTrue(any("failure_mode must be FAIL_CLOSED" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
