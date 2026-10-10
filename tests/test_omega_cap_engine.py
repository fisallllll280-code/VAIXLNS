from decimal import Decimal

import pytest

from vaixlns_omega_cap import OrderIntent, Policy, evaluate_order


@pytest.fixture
def policy():
    return Policy(
        policy_id="test-policy-v1",
        max_single_asset_weight=Decimal("0.25"),
        max_total_allocation=Decimal("0.80"),
        max_order_notional=Decimal("1000"),
        max_portfolio_notional=Decimal("5000"),
        transaction_cost_bps=Decimal("10"),
        slippage_bps=Decimal("10"),
    )


def intent(**overrides):
    values = dict(
        asset_id="ASSET-1",
        side="BUY",
        quantity=Decimal("2"),
        price=Decimal("100"),
        available_cash=Decimal("1000"),
        current_asset_weight=Decimal("0.10"),
        total_allocation_after=Decimal("0.50"),
        data_source="fixture://market-data",
        observed_at="2026-10-10T00:00:00Z",
        retrieved_at="2026-10-10T00:00:01Z",
    )
    values.update(overrides)
    return OrderIntent(**values)


def test_accepts_valid_paper_intent_and_accounts_for_costs(policy):
    result = evaluate_order(intent(), policy)
    assert result.accepted is True
    assert result.reason_code == "PAPER_ACCEPTED"
    assert Decimal(result.gross_notional) == Decimal("200")
    assert Decimal(result.estimated_cost) == Decimal("0.4")
    assert result.execution_mode == "paper"


def test_rejects_missing_provenance(policy):
    result = evaluate_order(intent(data_source=""), policy)
    assert not result.accepted
    assert result.reason_code == "MISSING_PROVENANCE"


def test_rejects_nan(policy):
    result = evaluate_order(intent(price="NaN"), policy)
    assert not result.accepted
    assert result.reason_code == "INVALID_NUMERIC_INPUT"


def test_rejects_invalid_order_size(policy):
    result = evaluate_order(intent(quantity=Decimal("0")), policy)
    assert not result.accepted
    assert result.reason_code == "INVALID_ORDER_SIZE"


def test_rejects_order_notional_above_policy(policy):
    result = evaluate_order(intent(quantity=Decimal("11")), policy)
    assert not result.accepted
    assert result.reason_code == "ORDER_NOTIONAL_LIMIT"


def test_rejects_insufficient_cash_including_costs(policy):
    result = evaluate_order(intent(available_cash=Decimal("200")), policy)
    assert not result.accepted
    assert result.reason_code == "INSUFFICIENT_CASH_AFTER_COSTS"


def test_rejects_concentration_breach(policy):
    result = evaluate_order(intent(current_asset_weight=Decimal("0.30")), policy)
    assert not result.accepted
    assert result.reason_code == "CONCENTRATION_LIMIT"


def test_rejects_total_allocation_breach(policy):
    result = evaluate_order(intent(total_allocation_after=Decimal("0.90")), policy)
    assert not result.accepted
    assert result.reason_code == "ALLOCATION_LIMIT"


def test_policy_cannot_enable_live_execution():
    with pytest.raises(ValueError, match="live execution is prohibited"):
        Policy(policy_id="unsafe", allow_live_execution=True)


def test_identical_inputs_are_deterministic(policy):
    first = evaluate_order(intent(), policy)
    second = evaluate_order(intent(), policy)
    assert first == second
