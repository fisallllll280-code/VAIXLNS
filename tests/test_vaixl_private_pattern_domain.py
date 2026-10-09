import unittest

from scripts.vaixl_private_pattern_domain import (
    ACTIVE,
    REVOKED,
    SEALED,
    attach_private_language,
    build_pattern_language_binding,
    build_transfer_artifact,
    deprovision_pattern,
    validate_pattern_language_boundary,
)


class PrivatePatternDomainTests(unittest.TestCase):
    def base_pattern(self):
        return {
            "pattern_id": "VX-GLOBAL-TEST-001",
            "version": "1.0.0",
            "status": "PROPOSAL",
            "intent": "build a private globally reusable system pattern",
            "provenance": {"creator": "test"},
        }

    def binding(self):
        return build_pattern_language_binding(
            pattern_id="VX-GLOBAL-TEST-001",
            language_id="synthetic-private-language-001",
            language_genome_hash="a" * 64,
        )

    def test_binding_is_pattern_bound_and_source_external(self):
        binding = self.binding()
        pattern = attach_private_language(self.base_pattern(), binding)
        self.assertEqual(pattern["private_language"]["binding_type"], "PATTERN_BOUND_PRIVATE_LANGUAGE")
        self.assertEqual(pattern["private_language"]["source"]["location"], "EXTERNAL_SECRET_VAULT")
        self.assertEqual(validate_pattern_language_boundary(pattern), [])
        self.assertFalse(pattern["private_language"]["interface"]["allows_source_export"])

    def test_no_language_source_is_persisted_or_exposed(self):
        binding = self.binding()
        pattern = attach_private_language(self.base_pattern(), binding)
        rendered = str(pattern)
        self.assertNotIn("synthetic-private-language-001", rendered)
        self.assertNotIn("language source", rendered.lower())
        self.assertTrue(pattern["private_language"]["source"]["runtime_source_exposure"] is False)
        self.assertTrue(pattern["private_language"]["source"]["agent_source_exposure"] is False)

    def test_self_authority_is_rejected_and_external_authority_succeeds(self):
        binding = self.binding()
        pattern = attach_private_language(self.base_pattern(), binding)
        with self.assertRaises(PermissionError):
            deprovision_pattern(
                pattern,
                agent_id="agent-001",
                authority_envelope={
                    "issuer": "agent-001",
                    "operation": "PATTERN_LANGUAGE_DEPROVISION",
                    "grants": ["PATTERN_LANGUAGE_DEPROVISION"],
                },
                recipient_scope="customer-demo",
                event_timestamp="2026-10-07T02:00:00Z",
            )
        result = deprovision_pattern(
            pattern,
            agent_id="agent-001",
            authority_envelope={
                "issuer": "external-pattern-authority",
                "operation": "PATTERN_LANGUAGE_DEPROVISION",
                "grants": ["PATTERN_LANGUAGE_DEPROVISION"],
            },
            recipient_scope="customer-demo",
            event_timestamp="2026-10-07T02:00:00Z",
        )
        self.assertEqual(result["status"], "DEPROVISIONED")
        self.assertEqual(result["delivered_pattern"]["private_language"]["lifecycle"]["state"], REVOKED)
        self.assertFalse(result["delivered_pattern"]["private_language"]["delivery"]["language_source_delivered"])
        self.assertTrue(result["event"]["event_hash"])
        replay = deprovision_pattern(
            pattern,
            agent_id="agent-001",
            authority_envelope={
                "issuer": "external-pattern-authority",
                "operation": "PATTERN_LANGUAGE_DEPROVISION",
                "grants": ["PATTERN_LANGUAGE_DEPROVISION"],
            },
            recipient_scope="customer-demo",
            event_timestamp="2026-10-07T02:00:00Z",
        )
        self.assertEqual(result["event"]["event_hash"], replay["event"]["event_hash"])

    def test_delivery_preserves_fabric_without_private_source(self):
        binding = self.binding()
        pattern = attach_private_language(self.base_pattern(), binding)
        transfer = build_transfer_artifact(
            pattern,
            recipient_scope="customer-demo",
            deprovision_event={"event_type": "TEST", "event_hash": "b" * 64},
        )
        delivered = transfer["private_language"]
        self.assertEqual(
            delivered["fabric"]["preserved_dimensions"],
            ["syntax","semantics","grammar","transformation","security","verification"],
        )
        self.assertEqual(delivered["source"]["location"], "NOT_DELIVERED")
        self.assertEqual(delivered["lifecycle"]["state"], REVOKED)

    def test_invalid_boundary_is_detected(self):
        binding = self.binding()
        pattern = attach_private_language(self.base_pattern(), binding)
        pattern["private_language"]["interface"]["allows_source_export"] = True
        findings = validate_pattern_language_boundary(pattern)
        self.assertIn("PRIVATE_LANGUAGE_SOURCE_EXPORT_ENABLED", findings)


if __name__ == "__main__":
    unittest.main()
