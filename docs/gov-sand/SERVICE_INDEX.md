# GOV-MIL service & lineage index
Version: 0.1 / PROPOSED. New modules are additive; no historical index is deleted or silently merged.

| Key | Service | Input | Output | Gate |
|---|---|---|---|---|
| MIL-001 | Voluntary financial intake | Explicit voluntary input (synthetic in prototype) | Budget snapshot | Consent/privacy |
| MIL-002 | Early financial risk indicator | Income, essentials, monthly debt service | Financial pressure band, non-credit | Human review |
| MIL-003 | Bank workout options | Contract data supplied by user | Reschedule / settlement / deferment checklist | Regulated activity review |
| MIL-004 | Judicial case routing | Case claimed by user | Information on official referral | No automated legal decision |
| MIL-005 | Military family benefits finder | Public eligibility rules | Possible benefit checklist | Official rule verification |
| MIL-006 | Injury/death support navigator | Optional limited records | Specialist referral | Sensitive data gate |
| MIL-007 | Veteran transition planner | Projected retirement budget | Scenario report | Consent |
| MIL-008 | Housing affordability | Income, household expenses | Affordability simulation | No financing recommendation |
| MIL-009 | Aid fund referrals | Publicly verified programmes | Eligibility inquiry | No custody / licensed charity review |
| MIL-010 | Savings/investment education | User preferences | Education-only materials | No investment product without licence |
| MIL-011 | Evidence passport | Validated case actions | Dated receipts / provenance | Restricted access |
| MIL-012 | Impact reporting | Aggregated outcomes | Privacy-preserving dashboard | Disclosure and minimum cohort check |

Dependency pattern: Source → consent → data-minimization → computed explanation → human review → authorized external referral → auditable receipt. Any missing gate blocks the external step.
