import unittest

from scripts.omega_economic_kernel import (
    build_ledger, evaluate_budget, propose_reinvestment, summarize_economics,
)


def entry(entry_id, kind, amount, mode="REALIZED", currency="SAR", **extra):
    row = {
        "entry_id": entry_id, "task_id": "task-1", "agent_id": "agent-1",
        "kind": kind, "amount_minor": amount, "mode": mode, "currency": currency,
        "occurred_at": "2026-10-10T12:00:00Z",
    }
    if mode == "REALIZED":
        row.update(evidence_ref="receipt:1", evidence_status="VERIFIED")
    row.update(extra)
    return row


class OmegaEconomicKernelTests(unittest.TestCase):
    def test_realized_and_simulated_totals_are_separate(self):
        result = summarize_economics([
            entry("r1", "REVENUE", 10000, "REALIZED"),
            entry("c1", "COST", 2500, "REALIZED"),
            entry("sr1", "REVENUE", 90000, "SIMULATED"),
        ])
        sar = result["totals"]["SAR"]
        self.assertEqual(sar["REALIZED"]["net_operating_result_minor"], 7500)
        self.assertEqual(sar["SIMULATED"]["net_operating_result_minor"], 90000)

    def test_realized_revenue_without_evidence_is_incomplete(self):
        row = entry("r1", "REVENUE", 1000)
        row.pop("evidence_ref")
        result = build_ledger([row])
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("REALIZED_ENTRY_REQUIRES_EVIDENCE_REF",
                      [x["code"] for x in result["errors"]])

    def test_evidence_status_must_be_verified_for_realized_entry(self):
        result = build_ledger([entry("r1", "REVENUE", 1000, evidence_status="SUPPORTED")])
        self.assertEqual(result["status"], "INCOMPLETE")

    def test_simulated_entry_cannot_claim_realized_verification(self):
        result = build_ledger([entry("s1", "REVENUE", 1000, "SIMULATED",
                                     evidence_status="VERIFIED")])
        self.assertEqual(result["status"], "INCOMPLETE")

    def test_duplicate_entry_ids_are_rejected(self):
        result = build_ledger([entry("same", "REVENUE", 100),
                               entry("same", "COST", 50)])
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("DUPLICATE_ENTRY_ID", [x["code"] for x in result["errors"]])

    def test_amount_must_be_positive_integer_minor_units(self):
        for amount in (0, -1, 1.5, True):
            with self.subTest(amount=amount):
                result = build_ledger([entry("r1", "REVENUE", amount)])
                self.assertEqual(result["status"], "INCOMPLETE")

    def test_currency_totals_are_not_combined(self):
        result = summarize_economics([
            entry("r-sar", "REVENUE", 100, currency="SAR"),
            entry("r-usd", "REVENUE", 100, currency="USD"),
        ])
        self.assertEqual(set(result["totals"]), {"SAR", "USD"})

    def test_ledger_digest_is_order_independent_for_same_entries(self):
        a, b = entry("a", "REVENUE", 10), entry("b", "COST", 2)
        self.assertEqual(build_ledger([a, b])["ledger_digest"],
                         build_ledger([b, a])["ledger_digest"])

    def test_budget_rejects_cost_above_remaining(self):
        result = evaluate_budget(budget_minor=1000, committed_minor=800, proposed_cost_minor=201)
        self.assertEqual(result["decision"], "REJECTED")
        self.assertFalse(result["execution_authorized"])

    def test_budget_admission_is_not_execution_authority(self):
        result = evaluate_budget(budget_minor=1000, committed_minor=200, proposed_cost_minor=300)
        self.assertEqual(result["decision"], "ELIGIBLE_FOR_SEPARATE_POLICY_GATE")
        self.assertFalse(result["execution_authorized"])

    def test_reinvestment_requires_evidence_and_is_proposal_only(self):
        result = propose_reinvestment(realized_net_minor=10001, rate_bps=2500,
                                      currency="SAR", evidence_refs=["ledger:abc"])
        self.assertEqual(result["proposed_reinvestment_minor"], 2500)
        self.assertEqual(result["status"], "PROPOSAL_ONLY")
        self.assertFalse(result["transfer_executed"])

    def test_reinvestment_cannot_use_negative_or_invalid_rate(self):
        for net, rate in ((-1, 1000), (1000, 10001), (1000, -1)):
            with self.subTest(net=net, rate=rate):
                result = propose_reinvestment(realized_net_minor=net, rate_bps=rate,
                                              currency="SAR", evidence_refs=["ledger:abc"])
                self.assertEqual(result["status"], "INCOMPLETE")

    def test_budget_rejects_boolean_as_integer(self):
        result = evaluate_budget(budget_minor=True, committed_minor=0, proposed_cost_minor=0)
        self.assertEqual(result["decision"], "INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
