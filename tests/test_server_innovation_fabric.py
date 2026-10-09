import unittest

from tools.server_innovation_fabric import (
    GateStatus,
    NoveltyReviewStatus,
    ServerAssessmentDecision,
    ServerInnovationCandidate,
    assess_many,
    assess_server_candidate,
)


class ServerInnovationFabricTests(unittest.TestCase):
    def valid_candidate(self, **overrides):
        values = dict(
            server_id="S-001",
            display_name="Example capability server",
            server_class="INFERENCE",
            source_uri="https://example.org/project",
            source_revision="git:abc123",
            owner="team-research",
            capability_claims=("capability:structured-math", "capability:streaming-evidence"),
            known_capabilities=("capability:text-generation",),
            capability_gap_ids=("capability:structured-math",),
            evidence_refs=("evidence:source-001", "evidence:test-001"),
            prior_art_refs=("prior-art:search-001", "prior-art:comparison-001"),
            novelty_review_status=NoveltyReviewStatus.COMPLETE,
            identity_status=GateStatus.PASS,
            contract_status=GateStatus.PASS,
            sandbox_test_status=GateStatus.PASS,
            recovery_replay_status=GateStatus.PASS,
            security_review_status=GateStatus.PASS,
            independent_verification_status=GateStatus.PASS,
        )
        values.update(overrides)
        return ServerInnovationCandidate(**values)

    def test_complete_candidate_only_becomes_eligible_for_governance(self):
        result = assess_server_candidate(self.valid_candidate())
        self.assertEqual(result.decision, ServerAssessmentDecision.ELIGIBLE_FOR_GOVERNANCE)
        self.assertFalse(result.runtime_authorized)
        self.assertFalse(result.canonical_admission_authorized)

    def test_identity_failure_quarantines_candidate(self):
        result = assess_server_candidate(self.valid_candidate(identity_status=GateStatus.FAIL))
        self.assertEqual(result.decision, ServerAssessmentDecision.QUARANTINED)
        self.assertIn("IDENTITY_VERIFICATION_FAILED", result.blockers)

    def test_unknown_identity_requires_research_and_cannot_admit(self):
        result = assess_server_candidate(self.valid_candidate(identity_status=GateStatus.NOT_RUN))
        self.assertEqual(result.decision, ServerAssessmentDecision.RESEARCH_REQUIRED)
        self.assertIn("IDENTITY_VERIFICATION", result.missing_requirements)
        self.assertFalse(result.runtime_authorized)

    def test_prior_art_contradiction_blocks_novelty_claim(self):
        result = assess_server_candidate(self.valid_candidate(
            novelty_review_status=NoveltyReviewStatus.CONTRADICTED_BY_PRIOR_ART
        ))
        self.assertEqual(result.decision, ServerAssessmentDecision.REJECTED)
        self.assertIn("PRIOR_ART_CONTRADICTS_NOVELTY_CLAIM", result.blockers)

    def test_no_capability_delta_is_not_an_innovation(self):
        result = assess_server_candidate(self.valid_candidate(
            capability_claims=("capability:text-generation",),
            capability_gap_ids=("capability:text-generation",),
        ))
        self.assertEqual(result.decision, ServerAssessmentDecision.REJECTED)
        self.assertIn("NO_UNMET_CAPABILITY_DELTA_IDENTIFIED", result.blockers)

    def test_failed_sandbox_blocks_admission(self):
        result = assess_server_candidate(self.valid_candidate(sandbox_test_status=GateStatus.FAIL))
        self.assertEqual(result.decision, ServerAssessmentDecision.REJECTED)
        self.assertIn("SANDBOX_TESTS_FAILED", result.blockers)

    def test_source_credentials_and_non_https_web_urls_are_rejected(self):
        for source_uri in ("https://user:pass@example.org", "http://example.org", "file:///etc/passwd"):
            with self.subTest(source_uri=source_uri):
                result = assess_server_candidate(self.valid_candidate(source_uri=source_uri))
                self.assertEqual(result.decision, ServerAssessmentDecision.QUARANTINED)
                self.assertIn("SOURCE_REFERENCE_INVALID_OR_UNSAFE", result.blockers)

    def test_candidate_cannot_self_authorize(self):
        result = assess_server_candidate(self.valid_candidate(requested_runtime_admission=True))
        self.assertEqual(result.decision, ServerAssessmentDecision.ELIGIBLE_FOR_GOVERNANCE)
        self.assertFalse(result.runtime_authorized)
        self.assertFalse(result.canonical_admission_authorized)
        self.assertFalse(result.to_record()["runtime_authorized"])

    def test_batch_is_stable_and_rejects_duplicate_ids(self):
        a = self.valid_candidate(server_id="S-A")
        b = self.valid_candidate(server_id="S-B")
        self.assertEqual([x.server_id for x in assess_many([b, a])], ["S-A", "S-B"])
        with self.assertRaises(ValueError):
            assess_many([a, a])

    def test_duplicate_capability_claims_are_rejected(self):
        with self.assertRaises(ValueError):
            assess_server_candidate(self.valid_candidate(capability_claims=("x", "x")))


if __name__ == "__main__":
    unittest.main()
