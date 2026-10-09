#!/usr/bin/env python3
"""Evidence-gated unit economics and offer prioritization for VAIXLNS."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

INPUT_SCHEMA = "vaixlns.omega-revenue-portfolio.v1"
REPORT_SCHEMA = "vaixlns.omega-revenue-portfolio-report.v1"
EVIDENCE_POINTS = {"IDEA": 0, "CUSTOMER_INTERVIEWS": 5, "DESIGN_PARTNER": 10, "PAID_PILOT": 15, "REPEATED_PAID": 20}
NUMERIC_FIELDS = (
    "price_per_customer_period",
    "variable_cost_per_customer_period",
    "acquisition_cost_per_customer",
    "fixed_cost_per_period",
    "expected_new_customers_per_period",
    "delivery_capacity_per_period",
    "sales_cycle_days",
    "cash_collection_days",
    "paid_pilots",
    "qualified_discovery_calls",
)
INTEGER_FIELDS = {
    "expected_new_customers_per_period", "delivery_capacity_per_period",
    "sales_cycle_days", "cash_collection_days", "paid_pilots",
    "qualified_discovery_calls",
}

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def nonnegative_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0

def analyze_opportunity(item: dict[str, Any], data_state: str) -> dict[str, Any]:
    required = ("id", "name", "evidence_stage", *NUMERIC_FIELDS, "evidence_refs")
    missing = [key for key in required if key not in item or item[key] is None]
    invalid = [key for key in NUMERIC_FIELDS if key in item and item[key] is not None and not nonnegative_number(item[key])]
    invalid.extend(
        key for key in INTEGER_FIELDS
        if key in item and item[key] is not None
        and (not isinstance(item[key], int) or isinstance(item[key], bool))
    )
    evidence_stage = item.get("evidence_stage")
    if evidence_stage not in EVIDENCE_POINTS:
        invalid.append("evidence_stage")
    if not isinstance(item.get("evidence_refs"), list):
        invalid.append("evidence_refs")
    if item.get("evidence_stage") in {"DESIGN_PARTNER", "PAID_PILOT", "REPEATED_PAID"} and not item.get("evidence_refs"):
        missing.append("evidence_refs")
    result: dict[str, Any] = {
        "id": item.get("id", "UNKNOWN"),
        "name": item.get("name", ""),
        "evidence_stage": evidence_stage,
        "target_customer": item.get("target_customer"),
        "offer": item.get("offer"),
        "economic_period": item.get("economic_period", "UNSPECIFIED"),
        "evidence_refs": item.get("evidence_refs", []),
        "data_state": data_state,
        "missing_fields": sorted(set(missing)),
        "invalid_fields": sorted(set(invalid)),
        "model_type": "UNIT_ECONOMICS_SCENARIO_NOT_A_REVENUE_FORECAST",
    }
    if missing or invalid:
        result.update({
            "decision": "COLLECT_OR_CORRECT_ECONOMIC_DATA",
            "priority_score": None,
            "score_components": {},
            "economics": None,
            "limitations": ["Incomplete or invalid input prevents a defensible unit-economics calculation."],
        })
        return result

    price = float(item["price_per_customer_period"])
    variable = float(item["variable_cost_per_customer_period"])
    acquisition = float(item["acquisition_cost_per_customer"])
    fixed = float(item["fixed_cost_per_period"])
    expected = int(item["expected_new_customers_per_period"])
    capacity = int(item["delivery_capacity_per_period"])
    sales_days = int(item["sales_cycle_days"])
    collect_days = int(item["cash_collection_days"])
    paid_pilots = int(item["paid_pilots"])
    qualified_calls = int(item["qualified_discovery_calls"])

    available_customers = min(expected, capacity)
    gross_profit = price - variable
    gross_margin = gross_profit / price if price > 0 else None
    contribution = gross_profit - acquisition
    contribution_margin = contribution / price if price > 0 else None
    modeled_revenue = price * available_customers
    modeled_operating_result = contribution * available_customers - fixed
    break_even_customers = math.ceil(fixed / contribution) if contribution > 0 else None
    acquisition_payback_periods = acquisition / gross_profit if gross_profit > 0 else None

    evidence_points = EVIDENCE_POINTS[evidence_stage]
    margin_points = min(20, max(0, round((gross_margin or 0) * 25))) if price > 0 else 0
    discovery_points = min(10, qualified_calls)
    cash_days = sales_days + collect_days
    cash_speed_points = 15 if cash_days <= 7 else 13 if cash_days <= 14 else 10 if cash_days <= 30 else 6 if cash_days <= 60 else 3 if cash_days <= 90 else 0
    contribution_points = 15 if contribution > 0 and price > 0 else 0
    pilot_points = min(10, paid_pilots * 2)
    capacity_points = 10 if capacity > 0 and expected > 0 else 0
    score_components = {
        "commercial_evidence": evidence_points,
        "qualified_discovery_calls": discovery_points,
        "gross_margin": margin_points,
        "time_to_cash": cash_speed_points,
        "contribution_after_acquisition": contribution_points,
        "paid_pilot_count": pilot_points,
        "delivery_capacity": capacity_points,
    }
    score = sum(score_components.values())

    if data_state != "OBSERVED_COMMERCIAL_EVIDENCE":
        decision = "COLLECT_REAL_CUSTOMER_AND_COST_EVIDENCE"
    elif price <= 0 or gross_profit <= 0:
        decision = "STOP_OR_REPRICE_NEGATIVE_GROSS_PROFIT"
    elif contribution <= 0:
        decision = "REWORK_PRICE_OR_ACQUISITION_COST"
    elif paid_pilots == 0:
        decision = "SELL_A_PAID_PILOT_BEFORE_BUILDING_MORE"
    elif evidence_stage == "REPEATED_PAID" and paid_pilots >= 3 and modeled_operating_result > 0:
        decision = "SCALE_GRADUALLY_WITH_USAGE_AND_MARGIN_CAPS"
    else:
        decision = "REPEAT_PAID_PILOT_AND_MEASURE_RETENTION"

    result.update({
        "decision": decision,
        "priority_score": score,
        "score_components": score_components,
        "economics": {
            "currency": item.get("currency", "SAR"),
            "price_per_customer_period": price,
            "variable_cost_per_customer_period": variable,
            "gross_profit_per_customer_period": round(gross_profit, 2),
            "gross_margin_pct": round(gross_margin * 100, 2) if gross_margin is not None else None,
            "acquisition_cost_per_customer": acquisition,
            "contribution_after_acquisition_per_new_customer": round(contribution, 2),
            "contribution_margin_pct": round(contribution_margin * 100, 2) if contribution_margin is not None else None,
            "expected_new_customers_per_period": expected,
            "delivery_capacity_per_period": capacity,
            "modeled_customers_served": available_customers,
            "modeled_revenue_per_period": round(modeled_revenue, 2),
            "fixed_cost_per_period": fixed,
            "modeled_operating_result_per_period": round(modeled_operating_result, 2),
            "break_even_new_customers_at_current_contribution": break_even_customers,
            "customer_acquisition_payback_periods": round(acquisition_payback_periods, 2) if acquisition_payback_periods is not None else None,
            "sales_cycle_days": sales_days,
            "cash_collection_days": collect_days,
            "estimated_days_to_cash_before_delivery_lag": sales_days + collect_days,
            "paid_pilots": paid_pilots,
            "qualified_discovery_calls": qualified_calls,
        },
        "limitations": [
            "Modeled revenue and operating result are arithmetic scenarios, not predictions or guaranteed outcomes.",
            "A score is a prioritization aid, not evidence of market demand.",
            "Use collected cash, refunds, customer-specific compute/labor cost and retention data to update the model.",
        ],
    })
    return result

def build_report(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"input schema must equal {INPUT_SCHEMA}")
    currency = payload.get("currency", "SAR")
    data_state = payload.get("data_state", "TEMPLATE_ONLY")
    if data_state not in {"TEMPLATE_ONLY", "OBSERVED_COMMERCIAL_EVIDENCE"}:
        raise ValueError("data_state must be TEMPLATE_ONLY or OBSERVED_COMMERCIAL_EVIDENCE")
    opportunities = payload.get("opportunities")
    if not isinstance(opportunities, list) or not opportunities:
        raise ValueError("opportunities must be a non-empty array")
    ids = [item.get("id") for item in opportunities if isinstance(item, dict)]
    if len(ids) != len(opportunities) or any(not isinstance(value, str) or not value.strip() for value in ids):
        raise ValueError("every opportunity must be an object with a non-empty id")
    if len(set(ids)) != len(ids):
        raise ValueError("opportunity ids must be unique")
    analyses = [analyze_opportunity({**item, "currency": item.get("currency", currency)}, data_state) for item in opportunities]
    sortable = sorted(analyses, key=lambda x: (
        x["priority_score"] is None,
        -(x["priority_score"] or 0),
        x["id"],
    ))
    core = {
        "schema": REPORT_SCHEMA,
        "input_schema": INPUT_SCHEMA,
        "data_state": data_state,
        "currency": currency,
        "source_input_sha256": sha256_json(payload),
        "opportunities": sortable,
        "summary": {
            "opportunity_count": len(sortable),
            "economic_data_complete_count": sum(not item["missing_fields"] and not item["invalid_fields"] for item in sortable),
            "paid_pilot_opportunity_count": sum(item.get("decision") in {"REPEAT_PAID_PILOT_AND_MEASURE_RETENTION", "SCALE_GRADUALLY_WITH_USAGE_AND_MARGIN_CAPS"} for item in sortable),
            "priority_is_not_success_probability": True,
            "forecasting_claim": "NONE",
        },
        "governance": {
            "never_invent_customer_revenue": True,
            "template_data_cannot_be_promoted_to_observed": True,
            "scale_only_after_paid_evidence_and_positive_unit_economics": True,
            "recommended_pricing_control": "SUBSCRIPTION_PLUS_CAPPED_USAGE_WHERE_COMPUTE_COSTS_VARY",
        },
    }
    return {**core, "report_sha256": sha256_json(core)}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Portfolio JSON with measured commercial data")
    parser.add_argument("--output", default="omega-revenue-portfolio.json", help="Output report")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input root must be a JSON object")
        report = build_report(payload)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"output": str(output), "data_state": report["data_state"],
                      "opportunities": report["summary"]["opportunity_count"],
                      "report_sha256": report["report_sha256"], "forecasting_claim": "NONE"}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
