import unittest
from intelligence_federation.adaptive_router import Candidate, Task, Receipt, rank, select

class RouterTests(unittest.TestCase):
    def setUp(self):
        self.task = Task("t", frozenset({"coding"}), max_unit_cost=0)
        self.a = Candidate("a", "alpha", frozenset({"coding"}), state="ACTIVE")
        self.b = Candidate("b", "beta", frozenset({"coding"}), state="ACTIVE")

    def test_default_deny(self):
        self.assertEqual(select(self.task, [Candidate("a", "x", frozenset({"coding"}))])["status"], "BLOCKED")

    def test_zero_budget_blocks_paid_model(self):
        self.assertEqual(select(self.task, [Candidate("a", "x", frozenset({"coding"}), "ACTIVE", unit_cost=.01)])["status"], "BLOCKED")

    def test_verified_feedback_affects_order(self):
        receipts = [Receipt("t", "b", "beta", 1, "proof-1", True)]
        self.assertEqual(rank(self.task, [self.a, self.b], receipts)[0]["provider"], "b")

    def test_unverified_feedback_ignored(self):
        receipts = [Receipt("t", "b", "beta", 1, "claim", False)]
        self.assertEqual(rank(self.task, [self.a, self.b], receipts)[0]["provider"], "a")

    def test_missing_evidence_ignored(self):
        receipts = [Receipt("t", "b", "beta", 1, "", True)]
        self.assertEqual(rank(self.task, [self.a, self.b], receipts)[0]["provider"], "a")

    def test_provider_and_sovereignty_filter(self):
        t = Task("t", frozenset({"coding"}), frozenset({"a"}), require_sovereign=True)
        self.assertEqual(select(t, [self.a, self.b])["status"], "BLOCKED")

    def test_required_capability(self):
        self.assertEqual(select(Task("t", frozenset({"vision"})), [self.a])["status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
