"""Ω Economic Kernel v1 — ledger and budget reference model.

Accounting-analysis only. This module does not connect to payment rails, bank accounts,
exchanges, wallets, procurement systems, or deployment infrastructure.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping

CURRENCIES = {"SAR", "USD", "EUR", "GBP"}
KINDS = {"REVENUE", "COST"}
MODES = {"REALIZED", "SIMULATED"}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                     allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def _valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(ID_RE.fullmatch(value))


def validate_entry(entry: Mapping[str, Any]) -> list[str]:
    """Return validation errors; amount_minor uses integer minor currency units."""
    errors: list[str] = []
    if not isinstance(entry, Mapping):
        return ["ENTRY_NOT_OBJECT"]
    for field in ("entry_id", "task_id", "agent_id"):
        if not _valid_id(entry.get(field)):
            errors.append(f"INVALID_{field.upper()}")
    if entry.get("kind") not in KINDS:
        errors.append("INVALID_KIND")
    if entry.get("mode") not in MODES:
        errors.append("INVALID_MODE")
    amount = entry.get("amount_minor")
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        errors.append("AMOUNT_MUST_BE_POSITIVE_INTEGER_MINOR_UNITS")
    if entry.get("currency") not in CURRENCIES:
        errors.append("UNSUPPORTED_CURRENCY")
    if not _valid_id(entry.get("occurred_at")):
        errors.append("INVALID_OCCURRED_AT")
    if entry.get("mode") == "REALIZED":
        if not _valid_id(entry.get("evidence_ref")):
            errors.append("REALIZED_ENTRY_REQUIRES_EVIDENCE_REF")
        if entry.get("evidence_status") != "VERIFIED":
            errors.append("REALIZED_ENTRY_REQUIRES_VERIFIED_EVIDENCE_STATUS")
    elif entry.get("mode") == "SIMULATED":
        if entry.get("evidence_status") == "VERIFIED":
            errors.append("SIMULATED_ENTRY_CANNOT_CLAIM_REALIZED_VERIFICATION")
    return errors


def build_ledger(entries: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate and hash an ordered ledger snapshot; does not claim immutable storage."""
    rows = []
    seen = set()
    errors = []
    try:
        source = list(entries)
    except TypeError:
        return {"status": "INCOMPLETE", "errors": ["ENTRIES_NOT_ITERABLE"], "entries": []}
    for index, entry in enumerate(source):
        row_errors = validate_entry(entry)
        entry_id = entry.get("entry_id") if isinstance(entry, Mapping) else None
        if entry_id in seen:
            row_errors.append("DUPLICATE_ENTRY_ID")
        if _valid_id(entry_id):
            seen.add(entry_id)
        errors.extend({"index": index, "entry_id": entry_id, "code": e} for e in row_errors)
        if not row_errors:
            rows.append(dict(entry))
    rows.sort(key=lambda x: (x["occurred_at"], x["entry_id"]))
    payload = {"schema_version": "1.0.0", "entries": rows}
    return {"status": "READY_FOR_REVIEW" if not errors else "INCOMPLETE",
            "entries": rows, "errors": errors, "ledger_digest": _digest(payload),
            "limitations": ["Digest is not a signature or immutable storage.",
                            "Evidence status is an input assertion until independently attested.",
                            "No external payment or accounting system is queried."]}


def summarize_economics(entries: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Keep realized and simulated totals separate; never mix currencies."""
    ledger = build_ledger(entries)
    totals: dict[str, dict[str, dict[str, int]]] = {}
    for entry in ledger["entries"]:
        currency, mode, kind = entry["currency"], entry["mode"], entry["kind"]
        totals.setdefault(currency, {}).setdefault(mode, {"REVENUE": 0, "COST": 0})
        totals[currency][mode][kind] += entry["amount_minor"]
    results = {}
    for currency, modes in sorted(totals.items()):
        results[currency] = {}
        for mode, amounts in sorted(modes.items()):
            results[currency][mode] = {
                **amounts,
                "net_operating_result_minor": amounts["REVENUE"] - amounts["COST"],
            }
    return {"status": ledger["status"], "totals": results,
            "errors": ledger["errors"], "ledger_digest": ledger["ledger_digest"],
            "currency_units": "Integer minor units; no FX conversion is performed."}


def evaluate_budget(*, budget_minor: int, committed_minor: int, proposed_cost_minor: int) -> dict[str, Any]:
    """Calculate budget admission only; does not authorize payment or execution."""
    values = (budget_minor, committed_minor, proposed_cost_minor)
    if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in values):
        return {"decision": "INCOMPLETE", "reason": "BUDGET_VALUES_MUST_BE_NONNEGATIVE_INTEGERS",
                "execution_authorized": False}
    remaining = budget_minor - committed_minor
    if committed_minor > budget_minor:
        return {"decision": "REJECTED", "reason": "EXISTING_COMMITMENTS_EXCEED_BUDGET",
                "remaining_minor": remaining, "execution_authorized": False}
    if proposed_cost_minor > remaining:
        return {"decision": "REJECTED", "reason": "PROPOSED_COST_EXCEEDS_REMAINING_BUDGET",
                "remaining_minor": remaining, "execution_authorized": False}
    return {"decision": "ELIGIBLE_FOR_SEPARATE_POLICY_GATE",
            "remaining_after_proposal_minor": remaining - proposed_cost_minor,
            "execution_authorized": False}


def propose_reinvestment(*, realized_net_minor: int, rate_bps: int,
                         currency: str, evidence_refs: Iterable[str]) -> dict[str, Any]:
    """Produce a reinvestment proposal, never a transfer instruction."""
    refs = list(evidence_refs) if not isinstance(evidence_refs, str) else []
    if (not isinstance(realized_net_minor, int) or isinstance(realized_net_minor, bool)
            or realized_net_minor < 0 or not isinstance(rate_bps, int)
            or isinstance(rate_bps, bool) or not 0 <= rate_bps <= 10000
            or currency not in CURRENCIES or not refs
            or any(not _valid_id(x) for x in refs)):
        return {"status": "INCOMPLETE", "reason": "INVALID_OR_MISSING_REALIZED_BASIS",
                "transfer_executed": False}
    amount = realized_net_minor * rate_bps // 10000
    proposal = {"currency": currency, "basis_net_realized_minor": realized_net_minor,
                "rate_bps": rate_bps, "proposed_reinvestment_minor": amount,
                "evidence_refs": sorted(set(refs)), "status": "PROPOSAL_ONLY",
                "transfer_executed": False}
    proposal["proposal_digest"] = _digest(proposal)
    return proposal
