# VAIXLNS Product Acceptance Gates v1

A public release is blocked until the applicable gates below have observable evidence.

| Gate | Required evidence | Failure status |
|---|---|---|
| Installation | Fresh environment install and smoke test | BLOCKED |
| Plain-language planning | Regression suite with representative English and Arabic requests | BLOCKED |
| Repository operation | Read-only default, isolated workspace, patch preview, scoped permissions | BLOCKED |
| Execution truth | Every reported command/test links to actual output and revision | BLOCKED |
| Memory integrity | Append/search/tamper/recovery tests plus documented encryption/backup boundary | BLOCKED |
| Repair | Reproducible incident, minimal patch, regression test, rollback record | BLOCKED |
| Multi-provider | Provider identity, health, task-quality, cost and latency evidence | BLOCKED |
| Security | Threat model, secret scanning, dependency review, least privilege, external review | BLOCKED |
| Privacy | Retention, export/delete, telemetry consent, data boundary | BLOCKED |
| Release | Versioning, license/IP review, SBOM/provenance, changelog and support route | BLOCKED |
| Market validation | Pilot users, repeat-use data, task-success measurements, support-cost estimates | BLOCKED |

Passing an isolated unit test only establishes that tested behavior under those test conditions passed. It does not establish product readiness, security, model quality, or market demand.
