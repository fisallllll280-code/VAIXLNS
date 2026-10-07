import unittest

from agents.agent_wallet import AgentEconomicWallet


class AgentWalletTests(unittest.TestCase):
    def test_reservation_and_settlement_keep_paper_double_entry(self):
        wallet = AgentEconomicWallet(
            balances={"USD": "50.00"},
            allowed_agents=("AG-004",),
        )
        reservation = wallet.authorize(
            task_id="T1",
            agent_id="AG-004",
            amount="12.00",
            asset="USD",
        )
        settlement = wallet.settle(reservation.reservation_id, actual_amount="9.00")
        self.assertEqual(settlement["actual_amount"], "9.00000000")
        self.assertEqual(settlement["refund"], "3.00000000")
        self.assertFalse(settlement["real_value_moved"])
        self.assertEqual(wallet.state()["balances"]["USD"], "41.00000000")

    def test_agent_not_allowed(self):
        wallet = AgentEconomicWallet(
            balances={"USD": "50.00"},
            allowed_agents=("AG-004",),
        )
        with self.assertRaises(PermissionError):
            wallet.authorize(task_id="T2", agent_id="AG-005", amount="1.00")

    def test_cannot_settle_above_authorization(self):
        wallet = AgentEconomicWallet(
            balances={"USD": "50.00"},
            allowed_agents=("AG-004",),
        )
        reservation = wallet.authorize(
            task_id="T3",
            agent_id="AG-004",
            amount="5.00",
        )
        with self.assertRaises(ValueError):
            wallet.settle(reservation.reservation_id, actual_amount="5.01")


if __name__ == "__main__":
    unittest.main()
