# VAIXLNS Ω∞ — Known Gaps and Unknowns

Every entry is a claim about what is **not yet evidenced**, not necessarily proof a feature does not exist.

```yaml
gap_id: GAP-0001
area: recovery # recovery | architecture | security | commercial | testing | runtime
description: Atomic reconstruction of 0001–2750 not yet independently proven.
impact: high # low | medium | high | critical
evidence_needed: Original numbered baseline, source mapping, manifest, hashes.
blocking: true
next_action: Compare baseline with extracted records and report coverage.
status: OPEN
```

| ID | Area | Known gap / uncertainty | Priority | Next evidence |
|---|---|---|---|---|
| GAP-0001 | recovery | Historical 0001–2750 coverage not verified record-by-record | High | Baseline index + provenance |
| GAP-0002 | recovery | Referenced 74 SHA-256 hashes and 2,897 references lack verified reconciliation in this review | High | Original manifest + link audit |
| GAP-0003 | architecture | Ownership boundaries between VAIXLNS, unified, core and VX require contract mapping | High | Interface map and ADRs |
| GAP-0004 | testing | Cross-repository integration and replay not verified by this bootstrap | High | Repeatable CI logs at pinned SHAs |
| GAP-0005 | security | Secret handling and agent write/merge authority not audited here | Critical | Permission matrix + secret scan |
| GAP-0006 | commercial | No independently verified customer/revenue evidence in this bootstrap | Medium | Authorized commercial ledger |
| GAP-0007 | operations | Termux/Android compatibility not verified | Medium | Device/environment test run |
| GAP-0008 | data | Private archive ingestion needs privacy and retention controls | High | Data classification + access policy |

## Closure rule
OPEN -> EVIDENCE_ATTACHED -> INDEPENDENTLY_VERIFIED -> CLOSED.
Never close solely on documentation assertions. Maintain links to failures and regressions.
