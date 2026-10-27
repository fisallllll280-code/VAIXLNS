# VX Business Automation Service — Workflow Audit & Automation Blueprint

**Status:** PROPOSED SERVICE PACKAGE — NOT YET SOLD OR DELIVERED  
**Owner approval:** Required before client-specific engagement, external offer, pricing, contract, or data intake.  
**Execution mode:** Offline-first; synthetic or explicitly redacted examples only until a separate data-handling agreement and access review exist.

## 1. Service outcome
Assess one bounded business workflow and deliver a reviewable blueprint for safer, measurable automation. The initial service is advisory and design-led; it does not require a live Zapier, MiroFish, model-provider, banking, government, or customer-system connection.

## 2. Standard scope
1. Define one workflow boundary, owner, trigger, inputs, outputs, and exception paths.
2. Map the current workflow and identify manual effort, failure modes, duplicated entry, and control points.
3. Produce a proposed future-state flow with explicit human approvals and fail-closed conditions.
4. Define data classifications, least-privilege access, retention, audit evidence, and rollback considerations.
5. Specify synthetic acceptance tests, expected outcomes, and operational metrics.
6. Provide a prioritized implementation plan with dependencies, risks, and unresolved decisions.
7. Hold a handover walkthrough and record accepted, rejected, and deferred items.

## 3. Deliverables
- workflow-intake.md — bounded scope and assumptions.
- workflow-audit-report.md — current-state findings and evidence labels.
- automation-blueprint.md — proposed flow, integrations, authorization points, and exception handling.
- test-and-acceptance-matrix.md — synthetic test cases and measurable acceptance criteria.
- risk-register.md — risk, impact, mitigation, owner, and residual uncertainty.
- implementation-roadmap.md — sequenced work packages and dependencies.
- handover-acceptance.md — client review and acceptance record.

These are deliverable definitions; no client-specific deliverable exists until an engagement is agreed and completed.

## 4. Evidence and status rules
Use only these labels in reports:
- OBSERVED — directly inspected evidence with source reference.
- CLIENT_REPORTED — stated by the client but not independently checked.
- INFERRED — reasoned from identified evidence; assumptions are explicit.
- PROPOSED — design recommendation, not deployed behavior.
- NOT_TESTED — no relevant test was run.
- BLOCKED — a named dependency or permission prevents progress.

A workflow diagram, test plan, successful local test, or planning result does not prove a live integration or production readiness. Record repository, commit, source path, test command, result, and timestamp when applicable.

## 5. Out of scope for the initial service
- Deploying to production or modifying a customer's live systems.
- Connecting accounts, issuing credentials, granting OAuth, or transmitting client data to third parties.
- Autonomous financial, legal, eligibility, employment, health, or other high-impact decisions.
- Paid API calls, subscriptions, purchases, or cloud spend without separate written approval.
- Legal, regulatory, security, or compliance certification.
- Guaranteed savings, accuracy, ROI, or business outcomes.
- Merging VAIXLNS changes into main or modifying protected canonical files.

Any extension requires explicit scope, authorization, security review, rollback plan, and acceptance criteria before execution.

## 6. Engagement gates
1. Intake: one workflow, named owner, objective, constraints, and permitted evidence sources.
2. Authorization: written scope and data-handling permission; otherwise use synthetic data only.
3. Audit: traceable observations and clearly marked assumptions.
4. Blueprint: proposed design and failure/approval paths.
5. Validation: synthetic tests and client review; no live write actions.
6. Handover: deliverables, limitations, open risks, and acceptance status recorded.
7. Optional implementation: separate approval and scope; not included by default.

## 7. Acceptance criteria
An engagement can be marked DELIVERED_PENDING_ACCEPTANCE only when all agreed files are present, the scope is traceable, assumptions and limitations are listed, the test matrix is included, and open risks have owners or explicit acceptance. Mark ACCEPTED only when the authorized client representative records acceptance. Do not infer acceptance from silence.

## 8. Commercial controls
Pricing, taxes, payment terms, legal entity details, service levels, and contract language remain TBD / OWNER APPROVAL REQUIRED. Do not invent a price or represent this proposal as an active registered business offer. Record opportunity, proposal, acceptance, delivery, invoice, and payment as separate evidence stages. Never commit secrets or sensitive customer records to this repository.
