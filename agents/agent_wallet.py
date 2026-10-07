"""Paper-only economic execution layer for governed agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json


def money(value: str | int | float | Decimal) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid monetary value: {value!r}") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("amount must be finite and non-negative")
    return amount.quantize(Decimal("0.00000001"))


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class WalletReservation:
    reservation_id: str
    task_id: str
    agent_id: str
    authorized_amount: str
    asset: str
    status: str = "AUTHORIZED"


@dataclass
class AgentEconomicWallet:
    """Deterministic paper wallet. It cannot move real-world value."""

    balances: dict[str, Decimal]
    allowed_agents: tuple[str, ...] = ()
    reservations: dict[str, WalletReservation] = field(default_factory=dict)
    ledger: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.balances = {asset: money(value) for asset, value in self.balances.items()}
        self.assert_invariants()

    @property
    def mode(self) -> str:
        return "PAPER"

    def authorize(self, *, task_id: str, agent_id: str, amount: str, asset: str = "USD") -> WalletReservation:
        if not task_id or not agent_id:
            raise ValueError("task_id and agent_id are required")
        if self.allowed_agents and agent_id not in self.allowed_agents:
            raise PermissionError("agent_not_allowed_for_wallet")
        amount_d = money(amount)
        if amount_d <= 0:
            raise ValueError("authorization_amount_must_be_positive")
        available = self.balances.get(asset, Decimal("0")) - self._reserved(asset)
        if available < amount_d:
            raise ValueError("insufficient_available_balance")
        reservation_id = canonical_hash({
            "task_id": task_id,
            "agent_id": agent_id,
            "amount": format(amount_d, "f"),
            "asset": asset,
        })[:24]
        if reservation_id in self.reservations:
            raise ValueError("duplicate_reservation")
        reservation = WalletReservation(
            reservation_id=reservation_id,
            task_id=task_id,
            agent_id=agent_id,
            authorized_amount=format(amount_d, "f"),
            asset=asset,
        )
        self.reservations[reservation_id] = reservation
        self.ledger.append({
            "event": "WALLET_RESERVED",
            "reservation_id": reservation_id,
            "task_id": task_id,
            "agent_id": agent_id,
            "asset": asset,
            "amount": format(amount_d, "f"),
            "real_value_moved": False,
        })
        self.assert_invariants()
        return reservation

    def settle(self, reservation_id: str, *, actual_amount: str) -> dict:
        reservation = self.reservations.get(reservation_id)
        if reservation is None:
            raise KeyError("unknown_reservation")
        if reservation.status != "AUTHORIZED":
            raise ValueError("reservation_not_settleable")
        authorized = money(reservation.authorized_amount)
        actual = money(actual_amount)
        if actual > authorized:
            raise ValueError("actual_amount_exceeds_authorization")
        balance = self.balances.get(reservation.asset, Decimal("0"))
        if balance < actual:
            raise ValueError("insufficient_balance_at_settlement")

        self.balances[reservation.asset] = balance - actual
        refund = authorized - actual
        self.reservations[reservation_id] = WalletReservation(
            reservation_id=reservation.reservation_id,
            task_id=reservation.task_id,
            agent_id=reservation.agent_id,
            authorized_amount=reservation.authorized_amount,
            asset=reservation.asset,
            status="SETTLED",
        )
        debit = {
            "account": f"expense:{reservation.task_id}",
            "side": "DEBIT",
            "asset": reservation.asset,
            "amount": format(actual, "f"),
        }
        credit = {
            "account": f"wallet:{reservation.agent_id}",
            "side": "CREDIT",
            "asset": reservation.asset,
            "amount": format(actual, "f"),
        }
        self.ledger.append({
            "event": "WALLET_SETTLED",
            "reservation_id": reservation_id,
            "task_id": reservation.task_id,
            "agent_id": reservation.agent_id,
            "actual_amount": format(actual, "f"),
            "refund": format(refund, "f"),
            "entries": [debit, credit],
            "real_value_moved": False,
        })
        self.assert_invariants()
        return {
            "reservation_id": reservation_id,
            "status": "SETTLED",
            "authorized_amount": format(authorized, "f"),
            "actual_amount": format(actual, "f"),
            "refund": format(refund, "f"),
            "ledger_hash": canonical_hash(self.ledger),
            "real_value_moved": False,
        }

    def _reserved(self, asset: str) -> Decimal:
        return sum(
            (
                money(r.authorized_amount)
                for r in self.reservations.values()
                if r.asset == asset and r.status == "AUTHORIZED"
            ),
            Decimal("0"),
        )

    def state(self) -> dict:
        return {
            "mode": self.mode,
            "balances": {k: format(v, "f") for k, v in sorted(self.balances.items())},
            "reserved": {asset: format(self._reserved(asset), "f") for asset in sorted(self.balances)},
            "ledger_hash": canonical_hash(self.ledger),
        }

    def assert_invariants(self) -> None:
        if any(value < 0 for value in self.balances.values()):
            raise AssertionError("negative_balance")
        for entry in self.ledger:
            if entry.get("event") == "WALLET_SETTLED":
                entries = entry.get("entries", [])
                if len(entries) != 2 or entries[0].get("amount") != entries[1].get("amount"):
                    raise AssertionError("double_entry_imbalance")
