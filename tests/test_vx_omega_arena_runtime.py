import copy
import unittest

from vx_omega_arena.core import (
    CandidateResult, EvidenceLedger, METRICS, promotion_gate,
    score_candidate,
)


def candidate():
    return CandidateResult(
        candidate_id="candidate-a", task_id="task-1", provider_id="offline-fixture",
        metrics={name: 0.8 for name in METRICS},
        evidence_refs=("fixture://task-1/result-a",),
    )


class ArenaRuntimeTests(unittest.TestCase):
    def test_score_is_deterministic_and_bounded(self):
        self.assertEqual(score_candidate(candidate()), score_candidate(candidate()))
        self.assertEqual(score_candidate(candidate()), 0.8)

    def test_missing_metric_is_rejected(self):
        item = candidate()
        with self.assertRaises(ValueError):
            score_candidate(CandidateResult(
                item.candidate_id, item.task_id, item.provider_id, {},
                item.evidence_refs,
            ))

    def test_metric_out_of_range_is_rejected(self):
        item = candidate()
        values = dict(item.metrics)
        values["security"] = 1.1
        with self.assertRaises(ValueError):
            score_candidate(CandidateResult(
                item.candidate_id, item.task_id, item.provider_id, values,
                item.evidence_refs,
            ))

    def test_evidence_chain_verifies_and_replays(self):
        ledger = EvidenceLedger()
        ledger.append("TASK_FROZEN", {"task_id": "task-1", "seed": 7})
        ledger.append("CANDIDATE_SCORED", {"candidate_id": "candidate-a", "score": 0.8})
        self.assertTrue(EvidenceLedger.verify(ledger.events))
        self.assertEqual(EvidenceLedger.replay(ledger.events)["replay_status"], "PASS")

    def test_tampered_evidence_fails_closed(self):
        ledger = EvidenceLedger()
        event = ledger.append("TASK_FROZEN", {"task_id": "task-1"})
        altered = copy.copy(event)
        object.__setattr__(altered, "payload", {"task_id": "tampered"})
        self.assertFalse(EvidenceLedger.verify((altered,)))
        with self.assertRaises(ValueError):
            EvidenceLedger.replay((altered,))

    def test_promotion_requires_every_gate_and_never_executes(self):
        blocked = promotion_gate(
            evidence_valid=True, replay_valid=True, independent_review=True,
            explicit_user_approval=False,
        )
        self.assertEqual(blocked["status"], "BLOCKED")
        eligible = promotion_gate(
            evidence_valid=True, replay_valid=True, independent_review=True,
            explicit_user_approval=True,
        )
        self.assertEqual(eligible["status"], "ELIGIBLE_FOR_SEPARATE_AUTHORIZATION")
        self.assertFalse(eligible["promotion_performed"])
        self.assertFalse(eligible["merge_performed"])
        self.assertFalse(eligible["deployment_performed"])

    def test_canonical_scope_blocks_promotion(self):
        result = promotion_gate(
            evidence_valid=True, replay_valid=True, independent_review=True,
            explicit_user_approval=True, canonical_scope=True,
        )
        self.assertEqual(result["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
