import unittest

from treasury import PaperTreasury, TreasuryPolicy, TransactionIntent


class PaperTreasuryTests(unittest.TestCase):
    def setUp(self):
        self.treasury = PaperTreasury(
            balances={
                "a": {"USD": "500.00"},
                "b": {"USD": "50.00"},
            },
            policy=TreasuryPolicy(
                policy_version="v1",
                allowed_assets=("USD",),
                max_transaction_amount="250.00",
                allowed_wallets=("a", "b"),
                require_dual_authorization=True,
            ),
        )

    def test_happy_path_is_deterministic_and_reconciled(self):
        intent = TransactionIntent(
            event_id="evt-1",
            source_wallet="a",
            destination_wallet="b",
            asset="USD",
            amount="100.00",
            reason="test",
            policy_version="v1",
        )
        first = self.treasury.propose(intent)
        self.assertEqual(first.status, "SIMULATED")
        self.treasury.authorize(
            "evt-1",
            [
                {"role": "policy", "actor": "p"},
                {"role": "operator", "actor": "o"},
            ],
        )
        record = self.treasury.execute("evt-1")
        self.assertEqual(record.status, "RECONCILED")
        self.assertEqual(self.treasury.balances["a"]["USD"], 400)
        self.assertEqual(self.treasury.balances["b"]["USD"], 150)
        self.assertEqual(len(record.evidence_hash), 64)

    def test_policy_violation_is_quarantined(self):
        intent = TransactionIntent(
            event_id="evt-2",
            source_wallet="a",
            destination_wallet="b",
            asset="EUR",
            amount="100.00",
            reason="blocked",
            policy_version="v1",
        )
        record = self.treasury.propose(intent)
        self.assertEqual(record.status, "QUARANTINED")
        self.assertEqual(record.risk_check["status"], "BLOCKED")

    def test_dual_authorization_is_enforced(self):
        intent = TransactionIntent(
            event_id="evt-3",
            source_wallet="a",
            destination_wallet="b",
            asset="USD",
            amount="100.00",
            reason="auth",
            policy_version="v1",
        )
        self.treasury.propose(intent)
        record = self.treasury.authorize("evt-3", [{"role": "operator", "actor": "o"}])
        self.assertEqual(record.status, "QUARANTINED")
        self.assertEqual(record.authorization["status"], "BLOCKED")

    def test_invariants_remain_true_after_execution(self):
        intent = TransactionIntent(
            event_id="evt-4",
            source_wallet="a",
            destination_wallet="b",
            asset="USD",
            amount="200.00",
            reason="invariant",
            policy_version="v1",
        )
        self.treasury.propose(intent)
        self.treasury.authorize(
            "evt-4",
            [
                {"role": "policy", "actor": "p"},
                {"role": "operator", "actor": "o"},
            ],
        )
        self.treasury.execute("evt-4")
        self.assertTrue(all(self.treasury.check_invariants().values()))


if __name__ == "__main__":
    unittest.main()
