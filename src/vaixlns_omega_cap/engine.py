"""Deterministic risk checks for research/paper trading; no live execution."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping


def _decimal(value: object, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be a finite decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


@dataclass(frozen=True)
class Policy:
    policy_id: str
    max_single_asset_weight: Decimal = Decimal("0.25")
    max_total_allocation: Decimal = Decimal("1")
    max_order_notional: Decimal = Decimal("1000")
    max_portfolio_notional: Decimal = Decimal("10000")
    transaction_cost_bps: Decimal = Decimal("10")
    slippage_bps: Decimal = Decimal("10")
    allow_live_execution: bool = False

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("policy_id must not be empty")
        for name in ("max_single_asset_weight", "max_total_allocation"):
            value = _decimal(getattr(self, name), name)
            if value < 0 or value > 1:
                raise ValueError(f"{name} must be in [0, 1]")
        for name in ("max_order_notional", "max_portfolio_notional"):
            if _decimal(getattr(self, name), name) <= 0:
                raise ValueError(f"{name} must be positive")
        for name in ("transaction_cost_bps", "slippage_bps"):
            if _decimal(getattr(self, name), name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.allow_live_execution:
            raise ValueError("live execution is prohibited by Ω-CAP v1")


@dataclass(frozen=True)
class OrderIntent:
    asset_id: str
    side: str
    quantity: Decimal
    price: Decimal
    available_cash: Decimal
    current_asset_weight: Decimal
    total_allocation_after: Decimal
    data_source: str
    observed_at: str
    retrieved_at: str


@dataclass(frozen=True)
class Decision:
    accepted: bool
    reason_code: str
    reason: str
    gross_notional: str
    estimated_cost: str
    estimated_cash_required: str
    execution_mode: str = "paper"


def evaluate_order(intent: OrderIntent, policy: Policy) -> Decision:
    """Evaluate an intent without submitting or transmitting any order."""
    if not intent.asset_id.strip() or not intent.data_source.strip():
        return _reject("MISSING_PROVENANCE", "asset_id and data_source are required")
    if not intent.observed_at.strip() or not intent.retrieved_at.strip():
        return _reject("MISSING_TIMESTAMP", "observed_at and retrieved_at are required")
    if intent.side not in {"BUY", "SELL"}:
        return _reject("INVALID_SIDE", "side must be BUY or SELL")

    try:
        quantity = _decimal(intent.quantity, "quantity")
        price = _decimal(intent.price, "price")
        cash = _decimal(intent.available_cash, "available_cash")
        weight = _decimal(intent.current_asset_weight, "current_asset_weight")
        allocation = _decimal(intent.total_allocation_after, "total_allocation_after")
    except ValueError as exc:
        return _reject("INVALID_NUMERIC_INPUT", str(exc))

    if quantity <= 0 or price <= 0:
        return _reject("INVALID_ORDER_SIZE", "quantity and price must be positive")
    if cash < 0:
        return _reject("INVALID_CASH", "available_cash must be non-negative")
    if not (0 <= weight <= 1) or not (0 <= allocation <= 1):
        return _reject("INVALID_ALLOCATION", "weights must be in [0, 1]")
    if weight > policy.max_single_asset_weight:
        return _reject("CONCENTRATION_LIMIT", "current asset weight exceeds policy")
    if allocation > policy.max_total_allocation:
        return _reject("ALLOCATION_LIMIT", "total allocation exceeds policy")

    notional = quantity * price
    cost_rate = (policy.transaction_cost_bps + policy.slippage_bps) / Decimal("10000")
    estimated_cost = notional * cost_rate
    cash_required = notional + estimated_cost if intent.side == "BUY" else estimated_cost

    if notional > policy.max_order_notional:
        return _reject("ORDER_NOTIONAL_LIMIT", "gross order notional exceeds policy",
                       notional, estimated_cost, cash_required)
    if notional > policy.max_portfolio_notional:
        return _reject("PORTFOLIO_NOTIONAL_LIMIT", "order notional exceeds portfolio cap",
                       notional, estimated_cost, cash_required)
    if intent.side == "BUY" and cash_required > cash:
        return _reject("INSUFFICIENT_CASH_AFTER_COSTS", "cash does not cover notional plus estimated costs",
                       notional, estimated_cost, cash_required)

    return Decision(
        True, "PAPER_ACCEPTED", "accepted by local policy; no real order was sent",
        str(notional), str(estimated_cost), str(cash_required)
    )


def _reject(code: str, reason: str, notional: Decimal = Decimal("0"),
            cost: Decimal = Decimal("0"), cash_required: Decimal = Decimal("0")) -> Decision:
    return Decision(False, code, reason, str(notional), str(cost), str(cash_required))
