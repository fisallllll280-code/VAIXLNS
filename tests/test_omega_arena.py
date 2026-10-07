import unittest
from datetime import datetime, timezone, timedelta

from intelligence_federation.arena import (
    ArenaManifest,
    Candidate,
    MatchResult,
    OmegaArena,
    build_invention_record,
    validate_attribution,
)
from intelligence_federation.provider_adapters import default_adapters


class OmegaArenaTests(unittest.TestCase):
    def setUp(self):
        self.manifest = ArenaManifest(
            arena_id="TEST",
            task_id="TASK",
            protocol_version="1.0.0",
            task_corpus_hash="corpus",
            environment_hash="env",
            participants=("a", "b"),
            phases=("execution", "verification", "final_verdict"),
        )
        self.arena = OmegaArena(self.manifest)
        self.t0 = datetime(2026, 10, 1, tzinfo=timezone.utc)

    def result(self, candidate_id="c1", days_old=8, replay=True, hard_failures=()):
        first = (self.t0 - timedelta(days=days_old)).isoformat()
        return MatchResult(
            candidate_id,
            first,
            {"correctness": 100, "reproducibility": 100, "security": 100,
             "completeness": 100, "contradiction_resistance": 100,
             "evidence_quality": 100, "robustness": 100, "innovation": 100},
            ("e1", "e2"),
            replay,
            tuple(hard_failures),
            "fp",
            "event:first",
            "event:success",
        )

    def test_requires_evidence_and_replay(self):
        candidate = Candidate("c1", "openai")
        bad = MatchResult("c1", self.result().first_success_at, self.result().metrics, (), False)
        result = self.arena.rank([(candidate, bad)], now=self.t0.isoformat())
        self.assertEqual(result.status, "NO_ELIGIBLE_CANDIDATE")

    def test_week_gate_blocks_early_champion(self):
        candidate = Candidate("c1", "openai")
        result = self.arena.rank([(candidate, self.result(days_old=2))], now=self.t0.isoformat())
        self.assertEqual(result.status, "PROVISIONAL")
        self.assertIsNone(result.champion_candidate_id)

    def test_week_gate_announces_scoped_champion(self):
        candidate = Candidate("c1", "openai")
        result = self.arena.rank([(candidate, self.result())], now=self.t0.isoformat())
        self.assertEqual(result.status, "TOURNAMENT_CHAMPION")
        self.assertEqual(result.champion_candidate_id, "c1")

    def test_hard_failure_can_never_win(self):
        candidate = Candidate("c1", "openai")
        bad = self.result(hard_failures=("SECURITY_VIOLATION",))
        result = self.arena.rank([(candidate, bad)], now=self.t0.isoformat())
        self.assertEqual(result.status, "NO_ELIGIBLE_CANDIDATE")

    def test_originator_and_contribution_lineage(self):
        candidate = Candidate("c1", "anthropic", ("openai",), derived_from=("INV-OLD",))
        record = build_invention_record(candidate, self.result())
        valid, errors = validate_attribution(record)
        self.assertTrue(valid, errors)
        self.assertEqual(record["originator"]["id"], "anthropic")
        self.assertEqual(record["contributions"][0]["contributor_id"], "openai")
        self.assertEqual(record["derived_from"], ["INV-OLD"])

    def test_all_declared_provider_adapters_conform(self):
        adapters = default_adapters()
        self.assertGreaterEqual(len(adapters), 7)
        self.assertTrue(all(adapter.conform()[0] for adapter in adapters))


if __name__ == "__main__":
    unittest.main()
