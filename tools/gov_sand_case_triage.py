"""VAIXLNS GOV/SAND synthetic-only financial pressure illustration.

No banking/Defence interfaces, legal decisions, credit scoring, or real case storage.
"""
from dataclasses import dataclass, asdict
import json

@dataclass(frozen=True)
class Scenario:
    income_sar: float
    essentials_sar: float
    installments_sar: float
    voluntary_opt_in: bool = False

def assess(s: Scenario) -> dict:
    for name in ("income_sar", "essentials_sar", "installments_sar"):
        v = getattr(s, name)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not (0 <= v <= 1e9):
            raise ValueError(f"Invalid {name}")
    if not s.voluntary_opt_in:
        return {"status": "BLOCKED_NO_CONSENT", "external_action_allowed": False}
    free_cash = round(s.income_sar - s.essentials_sar - s.installments_sar, 2)
    if free_cash < 0:
        band = "BUDGET_DEFICIT"
    elif s.income_sar and s.installments_sar / s.income_sar > 0.4:
        band = "PAYMENT_PRESSURE"
    else:
        band = "NO_IMMEDIATE_BUDGET_DEFICIT"
    return {
        "status": "SYNTHETIC_SIMULATION",
        "financial_band": band,
        "monthly_balance_sar": free_cash,
        "referral_options": [
            "Review essentials and all repayment schedules",
            "Request bank-approved hardship or restructuring review",
            "Seek qualified legal assistance for any court enforcement",
        ],
        "human_review_required": True,
        "external_action_allowed": False,
        "credit_rating": None,
        "government_entitlement_decision": None,
    }

if __name__ == "__main__":
    example = Scenario(8500, 4500, 3900, True)
    print(json.dumps(assess(example), ensure_ascii=False, indent=2))
