#!/usr/bin/env python3
"""Deterministic paper treasury for VAIXLNS.

The engine models a bounded financial-control loop without touching real funds.
It is intentionally dependency-free and deterministic so GitHub Actions can
re-run the same scenario and compare evidence hashes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Dict, List, Mapping, MutableMapping


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def money(value: str | int | float | Decimal) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid monetary value: {value!r}") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("amount must be finite and non-negative")
    return amount.quantize(Decimal("0.00000001"))


@dataclass(frozen=True)
class TreasuryPolicy:
    policy_version: str
    allowed_assets: tuple[str, ...]
    max_transaction_amount: str
    require_dual_authorization: bool = True
    allowed_wallets: tuple[str, ...] = ()

    def check_intent(self, intent: "TransactionIntent", balance: Decimal) -> List[str]:
        errors: List[str] = []
        amount = money(intent.amount)

        if intent.asset not in self.allowed_assets:
            errors.append("asset_not_allowed")
        if amount <= Decimal("0"):
            errors.append("amount_must_be_positive")
        if amount > money(self.max_transaction_amount):
            errors.append("amount_exceeds_policy_limit")
        if balance < amount:
            errors.append("insufficient_paper_balance")
        if self.allowed_wallets:
            if intent.source_wallet not in self.allowed_wallets:
                errors.append("source_wallet_not_allowed")
            if intent.destination_wallet not in self.allowed_wallets:
                errors.append("destination_wallet_not_allowed")
        if intent.source_wallet == intent.destination_wallet:
            errors.append("self_transfer_not_allowed")
        return errors


@dataclass(frozen=True)
class TransactionIntent:
    event_id: str
    source_wallet: str
    destination_wallet: str
    asset: str
    amount: str
    reason: str = "unspecified"
    policy_version: str = ""


@dataclass
class TransactionRecord:
    intent: TransactionIntent
    status: str = "PROPOSED"
    simulation: dict = field(default_factory=dict)
    risk_check: dict = field(default_factory=dict)
    authorization: dict = field(default_factory=dict)
    execution_reference: dict = field(default_factory=dict)
    reconciliation: dict = field(default_factory=dict)
    evidence_hash: str = ""

    def as_dict(self) -> dict:
        raw = asdict(self)
        return raw


class PaperTreasury:
    """Small, deterministic state machine for paper-only treasury execution."""

    def __init__(
        self,
        balances: Mapping[str, Mapping[str, str | int | float | Decimal]],
        policy: TreasuryPolicy,
    ) -> None:
        self.policy = policy
        self.balances: Dict[str, Dict[str, Decimal]] = {
            wallet: {asset: money(amount) for asset, amount in assets.items()}
            for wallet, assets in balances.items()
        }
        self.records: MutableMapping[str, TransactionRecord] = {}
        self._events: List[dict] = []
        self.assert_invariants()

    def state(self) -> dict:
        return {
            "mode": "PAPER",
            "policy_version": self.policy.policy_version,
            "balances": {
                wallet: {
                    asset: format(amount, "f")
                    for asset, amount in sorted(assets.items())
                }
                for wallet, assets in sorted(self.balances.items())
            },
        }

    def state_hash(self) -> str:
        return sha256_json(self.state())

    def _event(self, event_type: str, payload: dict) -> dict:
        event = {
            "sequence": len(self._events) + 1,
            "event_type": event_type,
            "payload": payload,
            "state_hash": self.state_hash(),
        }
        self._events.append(event)
        return event

    def observe(self) -> dict:
        snapshot = self.state()
        self._event("TREASURY_OBSERVED", {"snapshot": snapshot})
        return snapshot

    def propose(self, intent: TransactionIntent) -> TransactionRecord:
        if intent.event_id in self.records:
            raise ValueError(f"duplicate event_id: {intent.event_id}")
        if intent.policy_version != self.policy.policy_version:
            raise ValueError("policy_version_mismatch")

        balance = self.balances.get(intent.source_wallet, {}).get(intent.asset, Decimal("0"))
        errors = self.policy.check_intent(intent, balance)

        record = TransactionRecord(intent=intent)
        record.simulation = {
            "status": "PASS" if not errors else "FAIL",
            "projected_source_balance": format(max(Decimal("0"), balance - money(intent.amount)), "f"),
            "policy_errors": errors,
            "input_state_hash": self.state_hash(),
        }
        record.risk_check = {
            "status": "PASS" if not errors else "BLOCKED",
            "risk_flags": [] if not errors else ["POLICY_VIOLATION"],
            "bounded_amount": format(money(intent.amount), "f"),
        }
        record.status = "SIMULATED" if not errors else "QUARANTINED"

        self.records[intent.event_id] = record
        self._event("TRANSACTION_SIMULATED", record.as_dict())
        return record

    def authorize(
        self,
        event_id: str,
        approvals: List[Mapping[str, str]],
    ) -> TransactionRecord:
        record = self._record(event_id)
        if record.status != "SIMULATED":
            raise ValueError(f"authorization_requires_simulated_status:{record.status}")

        roles = [str(item.get("role", "")) for item in approvals]
        distinct_roles = set(roles)

        if self.policy.require_dual_authorization:
            if len(approvals) < 2 or len(distinct_roles) < 2:
                record.status = "QUARANTINED"
                record.authorization = {
                    "status": "BLOCKED",
                    "reason": "dual_authorization_required",
                    "approvals": [dict(x) for x in approvals],
                }
                self._event("TRANSACTION_AUTHORIZATION_BLOCKED", record.as_dict())
                return record

        record.authorization = {
            "status": "PASS",
            "approvals": [dict(x) for x in approvals],
            "separation_of_duties": len(distinct_roles) >= 2,
        }
        record.status = "AUTHORIZED"
        self._event("TRANSACTION_AUTHORIZED", record.as_dict())
        return record

    def execute(self, event_id: str) -> TransactionRecord:
        record = self._record(event_id)
        if record.status != "AUTHORIZED":
            raise ValueError(f"execution_requires_authorized_status:{record.status}")

        intent = record.intent
        current = self.balances.get(intent.source_wallet, {}).get(intent.asset, Decimal("0"))
        amount = money(intent.amount)

        if current < amount:
            record.status = "QUARANTINED"
            record.execution_reference = {"status": "BLOCKED", "reason": "stale_balance"}
            self._event("TRANSACTION_EXECUTION_BLOCKED", record.as_dict())
            return record

        self.balances.setdefault(intent.source_wallet, {}).setdefault(intent.asset, Decimal("0"))
        self.balances.setdefault(intent.destination_wallet, {}).setdefault(intent.asset, Decimal("0"))
        self.balances[intent.source_wallet][intent.asset] -= amount
        self.balances[intent.destination_wallet][intent.asset] += amount

        record.execution_reference = {
            "status": "PAPER_EXECUTED",
            "execution_id": f"PAPER-{event_id}",
            "real_value_moved": False,
        }
        record.status = "EXECUTED"
        self._event("TRANSACTION_PAPER_EXECUTED", record.as_dict())

        self.reconcile(event_id)
        return record

    def reconcile(self, event_id: str) -> TransactionRecord:
        record = self._record(event_id)
        if record.status != "EXECUTED":
            raise ValueError(f"reconciliation_requires_executed_status:{record.status}")

        intent = record.intent
        source = self.balances[intent.source_wallet][intent.asset]
        destination = self.balances[intent.destination_wallet][intent.asset]
        record.reconciliation = {
            "status": "PASS",
            "source_balance": format(source, "f"),
            "destination_balance": format(destination, "f"),
            "paper_only": True,
            "state_hash": self.state_hash(),
        }
        record.status = "RECONCILED"
        record.evidence_hash = self.evidence_record(event_id)["evidence_hash"]
        self._event("TRANSACTION_RECONCILED", record.as_dict())
        return record

    def _evidence_material(self, event_id: str) -> dict:
        record = self._record(event_id)
        if not record.reconciliation:
            raise ValueError("reconciliation_required_before_evidence")
        return {
            "schema": "VAIXLNS.FINANCIAL_EVIDENCE_RECORD.v1",
            "event_id": record.intent.event_id,
            "policy_version": self.policy.policy_version,
            "input_state_hash": record.simulation.get("input_state_hash", ""),
            "simulation": record.simulation,
            "risk_check": record.risk_check,
            "authorization": record.authorization,
            "execution_reference": record.execution_reference,
            "reconciliation": record.reconciliation,
        }

    def evidence_record(self, event_id: str) -> dict:
        material = self._evidence_material(event_id)
        material["evidence_hash"] = sha256_json(material)
        return material

    def evidence_bundle(self) -> dict:
        return {
            "schema": "VAIXLNS.PAPER_TREASURY_EVIDENCE_BUNDLE.v1",
            "mode": "PAPER",
            "state_hash": self.state_hash(),
            "records": {
                event_id: record.as_dict()
                for event_id, record in sorted(self.records.items())
            },
            "event_count": len(self._events),
            "events_hash": sha256_json(self._events),
        }

    def health(self) -> dict:
        statuses = [record.status for record in self.records.values()]
        return {
            "status": "HEALTHY",
            "mode": "PAPER",
            "policy_version": self.policy.policy_version,
            "transactions": len(self.records),
            "reconciled": sum(status == "RECONCILED" for status in statuses),
            "quarantined": sum(status == "QUARANTINED" for status in statuses),
            "invariants": self.check_invariants(),
        }

    def check_invariants(self) -> dict:
        non_negative = all(
            amount >= Decimal("0")
            for assets in self.balances.values()
            for amount in assets.values()
        )
        legal_statuses = all(
            record.status in {
                "PROPOSED",
                "SIMULATED",
                "AUTHORIZED",
                "EXECUTED",
                "RECONCILED",
                "QUARANTINED",
            }
            for record in self.records.values()
        )
        return {
            "non_negative_balances": non_negative,
            "legal_transaction_statuses": legal_statuses,
        }

    def assert_invariants(self) -> None:
        checks = self.check_invariants()
        failures = [name for name, ok in checks.items() if not ok]
        if failures:
            raise AssertionError(f"treasury_invariant_failure:{failures}")

    def _record(self, event_id: str) -> TransactionRecord:
        try:
            return self.records[event_id]
        except KeyError as exc:
            raise KeyError(f"unknown_event_id:{event_id}") from exc


def demo() -> dict:
    treasury = PaperTreasury(
        balances={
            "vault-a": {"USD": "1000.00"},
            "vault-b": {"USD": "100.00"},
        },
        policy=TreasuryPolicy(
            policy_version="treasury-policy-v1",
            allowed_assets=("USD",),
            max_transaction_amount="250.00",
            require_dual_authorization=True,
            allowed_wallets=("vault-a", "vault-b"),
        ),
    )

    intent = TransactionIntent(
        event_id="evt-0001",
        source_wallet="vault-a",
        destination_wallet="vault-b",
        asset="USD",
        amount="125.00",
        reason="paper-liquidity-rebalance",
        policy_version="treasury-policy-v1",
    )

    record = treasury.propose(intent)
    if record.status != "SIMULATED":
        raise AssertionError(record.as_dict())

    treasury.authorize(
        intent.event_id,
        approvals=[
            {"role": "policy", "actor": "policy-engine"},
            {"role": "operator", "actor": "paper-operator"},
        ],
    )
    treasury.execute(intent.event_id)

    result = {
        "health": treasury.health(),
        "evidence": treasury.evidence_bundle(),
    }
    if result["health"]["reconciled"] != 1:
        raise AssertionError("demo transaction was not reconciled")
    return result


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2, sort_keys=True))
