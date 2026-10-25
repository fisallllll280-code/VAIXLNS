"""Bounded evidence-closure capacity/cost simulation; no repo writes or verified-claim promotion."""
from __future__ import annotations
from dataclasses import dataclass
from math import ceil, floor

BASE_TOTAL = 177
BASE_LINKED = 22
BASE_UNLINKED = 155

@dataclass(frozen=True)
class Scenario:
    attempts_weekly: int = 40
    first_pass_acceptance: float = 1.0
    source_availability: float = 1.0
    startup_sar: int = 12000
    weekly_sar: int = 21700
    contingency: float = 0.15
    paid_interruption_weeks: int = 0

def simulate(s: Scenario) -> dict:
    if s.attempts_weekly < 1 or not 0 <= s.first_pass_acceptance <= 1 or not 0 <= s.source_availability <= 1:
        raise ValueError("invalid attempt, acceptance or availability assumption")
    if s.startup_sar < 0 or s.weekly_sar < 0 or s.paid_interruption_weeks < 0 or s.contingency < 0:
        raise ValueError("cost and interruption parameters must be nonnegative")
    accessible = floor(BASE_UNLINKED * s.source_availability)
    accepted_week = floor(s.attempts_weekly * s.first_pass_acceptance)
    if accessible > 0 and accepted_week < 1:
        return {"status":"BLOCKED_NO_ACCEPTANCE", "accessible": accessible, "blocked_sources": BASE_UNLINKED-accessible}
    weeks = ceil(accessible / accepted_week) if accessible else 0
    total_linked = BASE_LINKED + accessible
    cost = round((s.startup_sar+(weeks+s.paid_interruption_weeks)*s.weekly_sar)*(1+s.contingency))
    return {
        "status": "SIMULATED_NOT_VERIFIED",
        "baseline_total": BASE_TOTAL,
        "baseline_linked": BASE_LINKED,
        "baseline_unlinked": BASE_UNLINKED,
        "accepted_weekly": accepted_week,
        "accessible": accessible,
        "blocked_sources": BASE_UNLINKED-accessible,
        "working_weeks": weeks,
        "elapsed_weeks": weeks+s.paid_interruption_weeks,
        "projected_linked": total_linked,
        "projected_coverage_pct": round(total_linked / BASE_TOTAL * 100, 2),
        "estimated_cost_sar": cost,
    }

if __name__ == "__main__":
    import json
    cases = {
        "ideal": Scenario(),
        "rework_15pct": Scenario(first_pass_acceptance=0.85),
        "missing_sources_10pct": Scenario(first_pass_acceptance=0.85,source_availability=0.90),
        "rework_40pct_outage": Scenario(first_pass_acceptance=0.60,paid_interruption_weeks=1),
        "accelerated": Scenario(attempts_weekly=48,first_pass_acceptance=0.85,weekly_sar=25860)
    }
    print(json.dumps({k:simulate(v) for k,v in cases.items()},indent=2,ensure_ascii=False))
