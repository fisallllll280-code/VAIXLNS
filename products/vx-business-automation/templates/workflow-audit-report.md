# Workflow Audit Report

**Record ID:** TBD  
**Client / organization:** TBD — use an approved non-sensitive reference  
**Workflow owner:** TBD  
**Prepared on:** YYYY-MM-DD  
**Revision:** 0.1  
**Status:** DRAFT

## 1. Executive outcome
- Business objective:
- Workflow boundary:
- Current decision:
- Confidence / evidence limitations:
- Requested next decision:

## 2. Scope and exclusions
**Included steps:**  
**Excluded steps:**  
**Systems observed:**  
**Systems not accessed:**  
**Data permitted for this audit:**  
**Authorization reference:**  

Do not include credentials, personal identifiers, bank details, government records, or confidential raw data in this report.

## 3. Evidence ledger
| ID | Claim / observation | Status | Source reference | Timestamp / revision | Limitation |
|---|---|---|---|---|---|
| E-001 | TBD | NOT_TESTED | TBD | TBD | TBD |

Allowed statuses: OBSERVED, CLIENT_REPORTED, INFERRED, PROPOSED, NOT_TESTED, BLOCKED.

## 4. Current-state workflow
1. Trigger:
2. Input:
3. Responsible role:
4. Processing steps:
5. Decision / approval:
6. Output:
7. Exception and recovery path:
8. Audit trail:

## 5. Findings
| ID | Finding | Evidence | Impact | Priority | Confidence |
|---|---|---|---|---|---|
| F-001 | TBD | E-001 | TBD | TBD | TBD |

Separate directly observed facts from client-reported information and inference.

## 6. Proposed future state
Describe the proposal, not existing runtime behavior.
- Trigger and input validation:
- Identity and authorization:
- Human approval points:
- Idempotency / duplicate prevention:
- Output validation:
- Failure handling and rollback:
- Audit receipt:
- Monitoring and owner:
- Manual fallback:

## 7. Synthetic validation plan
| Test ID | Scenario | Expected result | Actual result | Evidence | Status |
|---|---|---|---|---|---|
| T-001 | Missing required input | Fail closed with actionable error | NOT_RUN | TBD | NOT_TESTED |
| T-002 | Duplicate request | No duplicate side effect | NOT_RUN | TBD | NOT_TESTED |
| T-003 | Unauthorized action | No external action | NOT_RUN | TBD | NOT_TESTED |
| T-004 | Invalid output | Reject and preserve trace | NOT_RUN | TBD | NOT_TESTED |
| T-005 | Downstream unavailable | Safe stop and manual recovery | NOT_RUN | TBD | NOT_TESTED |

## 8. Risk register
| Risk ID | Risk | Likelihood | Impact | Mitigation | Owner | Residual risk |
|---|---|---|---|---|---|---|
| R-001 | TBD | TBD | TBD | TBD | TBD | TBD |

## 9. Metrics and baseline
Record baseline values only when measured. Otherwise use NOT_MEASURED.
| Metric | Baseline | Target proposal | Measurement method | Owner |
|---|---|---|---|---|
| Cycle time | NOT_MEASURED | TBD | TBD | TBD |
| Manual touches | NOT_MEASURED | TBD | TBD | TBD |
| Exception rate | NOT_MEASURED | TBD | TBD | TBD |
| Rework rate | NOT_MEASURED | TBD | TBD | TBD |

## 10. Open decisions and handover
| Decision | Needed from | Due date | Status |
|---|---|---|---|
| TBD | TBD | TBD | OPEN |

**Limitations:** No live integration, production deployment, security certification, savings guarantee, or independent verification is implied unless separately evidenced.

**Review status:** DRAFT — CLIENT REVIEW REQUIRED  
**Acceptance reference:** TBD
