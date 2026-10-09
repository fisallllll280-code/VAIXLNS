"""Tests for evidence-gated revenue prioritization."""
from __future__ import annotations

import unittest

from scripts.omega_revenue_portfolio import INPUT_SCHEMA, build_report


def opportunity(**overrides):
    item = {
        "id": "PILOT_A",
        "name": "CI failure triage",
        "evidence_stage": "PAID_PILOT",
        "price_per_customer_period": 1000,
        "variable_cost_per_customer_period": 200,
        "acquisition_cost_per_customer": 100,
        "fixed_cost_per_period": 500,
        "expected_new_customers_per_period": 3,
        "delivery_capacity_per_period": 4,
        "sales_cycle_days": 7,
        "cash_collection_days": 2,
        "paid_pilots": 1,
        "qualified_discovery_calls": 5,
        "evidence_refs": ["CRM-OBS-01"],
    }
    item.update(overrides)
    return item


def payload(items, data_state="OBSERVED_COMMERCIAL_EVIDENCE"):
    return {"schema": INPUT_SCHEMA, "currency": "SAR", "data_state": data_state, "opportunities": items}


class OmegaRevenuePortfolioTests(unittest.TestCase):
    def test_positive_unit_economics_and_paid_pilot_are_calculated(self):
        report = build_report(payload([opportunity()]))
        item = report["opportunities"][0]
        self.assertEqual(item["decision"], "REPEAT_PAID_PILOT_AND_MEASURE_RETENTION")
        self.assertEqual(item["economics"]["gross_margin_pct"], 80.0)
        self.assertEqual(item["economics"]["contribution_after_acquisition_per_new_customer"], 700.0)
        self.assertEqual(item["economics"]["modeled_operating_result_per_period"], 1600.0)
        self.assertFalse(report["summary"]["forecasting_claim"] == "GUARANTEED")

    def test_template_data_never_promotes_to_scale_decision(self):
        item = opportunity(evidence_stage="REPEATED_PAID", paid_pilots=10)
        report = build_report(payload([item], data_state="TEMPLATE_ONLY"))
        self.assertEqual(report["opportunities"][0]["decision"], "COLLECT_REAL_CUSTOMER_AND_COST_EVIDENCE")

    def test_negative_gross_profit_requires_stop_or_repricing(self):
        report = build_report(payload([opportunity(variable_cost_per_customer_period=1200)]))
        self.assertEqual(report["opportunities"][0]["decision"], "STOP_OR_REPRICE_NEGATIVE_GROSS_PROFIT")

    def test_negative_contribution_flags_acquisition_economics(self):
        report = build_report(payload([opportunity(acquisition_cost_per_customer=900)]))
        self.assertEqual(report["opportunities"][0]["decision"], "REWORK_PRICE_OR_ACQUISITION_COST")

    def test_scale_gate_requires_repeated_paid_evidence_and_positive_result(self):
        report = build_report(payload([opportunity(evidence_stage="REPEATED_PAID", paid_pilots=3)]))
        self.assertEqual(report["opportunities"][0]["decision"], "SCALE_GRADUALLY_WITH_USAGE_AND_MARGIN_CAPS")

    def test_missing_data_is_not_interpreted_as_zero_cost(self):
        report = build_report(payload([opportunity(variable_cost_per_customer_period=None)]))
        item = report["opportunities"][0]
        self.assertEqual(item["decision"], "COLLECT_OR_CORRECT_ECONOMIC_DATA")
        self.assertIsNone(item["economics"])
        self.assertIn("variable_cost_per_customer_period", item["missing_fields"])

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be unique"):
            build_report(payload([opportunity(), opportunity()]))

    def test_report_is_deterministic(self):
        source = payload([opportunity()])
        self.assertEqual(build_report(source), build_report(source))


if __name__ == "__main__":
    unittest.main()
