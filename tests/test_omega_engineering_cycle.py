import hashlib
import unittest

from scripts.omega_memory_task_kernel import GENESIS_HASH, digest_json, KernelError
from scripts.omega_engineering_cycle import build_engineering_cycle, derive_innovation_candidates


def memory():
    record = {
        "schema_version": "1.0.0",
        "record_id": "MEM-VX-001",
        "memory_type": "DECISION",
        "subject": "VX task execution and evidence",
        "summary": "Engineering tasks require scoped authority, deterministic replay, source provenance, and independent verification.",
        "epistemic_state": "IMPLEMENTED",
        "lifecycle_state": "ACTIVE",
        "provenance": {
            "repository": "fisallllll280-code/VAIXLNS",
            "revision": "a" * 40,
            "path": "docs/agents/VAIXLNS_AGENT_OPERATING_MODEL_V1.md",
            "content_sha256": hashlib.sha256(b"source").hexdigest(),
        },
        "evidence": [{
            "kind": "repository_document",
            "ref": "docs/agents/VAIXLNS_AGENT_OPERATING_MODEL_V1.md",
            "digest": hashlib.sha256(b"evidence").hexdigest(),
        }],
        "verification": {"method": "reviewed fixture", "result": "NOT_RUN"},
        "lineage": {"derived_from": [], "supersedes": [], "related": []},
        "recorded_at": "2026-10-10T00:00:00Z",
        "previous_record_hash": GENESIS_HASH,
    }
    record["record_hash"] = digest_json(record)
    return record


def gap(gap_id="GAP-1", depends=None):
    return {
        "gap_id": gap_id,
        "title": "Independent task result verification",
        "description": "Build source-bound completion checks for engineering task outputs.",
        "domain": "governed task execution",
        "priority": "P0",
        "acceptance_criteria": [
            "reject results without an evidence digest",
            "prevent the producer from self-verifying",
        ],
        "required_capabilities": ["research.read"],
        "depends_on_gap_ids": depends or [],
    }


class InnovationCycleTests(unittest.TestCase):
    def test_candidate_is_a_hypothesis_not_a_novelty_claim(self):
        ctx = {
            "matches": [{
                "record_id": "MEM-VX-001",
                "record_hash": "c" * 64,
                "subject": "VX task execution and evidence",
                "summary": "Engineering tasks require scoped authority, deterministic replay, source provenance, and independent verification.",
                "repository": "fisallllll280-code/VAIXLNS",
                "revision": "a" * 40,
                "path": "docs/agents/VAIXLNS_AGENT_OPERATING_MODEL_V1.md",
            }]
        }
        candidate = derive_innovation_candidates([gap()], ctx)[0]
        self.assertEqual(candidate["proposal_state"], "PROPOSAL")
        self.assertEqual(candidate["novelty_state"], "UNASSESSED")
        self.assertEqual(candidate["originality_claim"], "NOT_CLAIMED")
        self.assertTrue(candidate["prior_art_review_required"])
        self.assertIn("MEM-VX-001", candidate["source_memory_ids"])

    def test_candidate_id_is_deterministic(self):
        first = derive_innovation_candidates([gap()], {"matches": []})
        second = derive_innovation_candidates([gap()], {"matches": []})
        self.assertEqual(first[0]["candidate_id"], second[0]["candidate_id"])
        self.assertEqual(first[0]["candidate_digest"], second[0]["candidate_digest"])

    def test_end_to_end_cycle_recovers_memory_and_builds_plan(self):
        result = build_engineering_cycle(
            goal="engineering task execution evidence verification",
            memory_records=[memory()],
            gaps=[gap()],
            available_capabilities=["research.read"],
        )
        self.assertEqual(result["state"], "PLANNED")
        self.assertEqual(result["memory_recovery"]["matches"][0]["record_id"], "MEM-VX-001")
        self.assertEqual(result["innovation_candidates"][0]["novelty_state"], "UNASSESSED")
        self.assertEqual(result["task_plan"]["tasks"][0]["status"], "READY")
        self.assertEqual(result["canonical_mutation"], "DISABLED")
        self.assertEqual(result["verified_promotion"], "NOT_PERFORMED")
        self.assertRegex(result["cycle_digest"], r"^[0-9a-f]{64}$")

    def test_cycle_holds_when_research_capability_is_missing(self):
        result = build_engineering_cycle(
            goal="engineering task execution evidence verification",
            memory_records=[memory()],
            gaps=[gap()],
            available_capabilities=[],
        )
        self.assertEqual(result["task_plan"]["tasks"][0]["status"], "BLOCKED")
        self.assertEqual(result["task_plan"]["tasks"][0]["missing_capabilities"], ["research.read"])

    def test_missing_gap_dependency_is_rejected(self):
        with self.assertRaisesRegex(KernelError, "missing gap dependencies"):
            build_engineering_cycle(
                goal="goal",
                memory_records=[],
                gaps=[gap(depends=["GAP-UNKNOWN"])],
                available_capabilities=["research.read"],
            )

    def test_no_memory_match_does_not_stop_proposal_but_leaves_prior_art_open(self):
        result = build_engineering_cycle(
            goal="a totally unrelated subsystem",
            memory_records=[memory()],
            gaps=[gap()],
            available_capabilities=["research.read"],
        )
        candidate = result["innovation_candidates"][0]
        self.assertEqual(result["memory_recovery"]["matches"], [])
        self.assertEqual(candidate["source_memory_ids"], [])
        self.assertEqual(candidate["novelty_state"], "UNASSESSED")
        self.assertTrue(candidate["prior_art_review_required"])


if __name__ == "__main__":
    unittest.main()
