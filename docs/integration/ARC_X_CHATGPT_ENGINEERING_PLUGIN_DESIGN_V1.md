# ARC-X Ω — ChatGPT Engineering Plugin Design v1

**Status:** PROPOSAL — design artifact only; not a published ChatGPT plugin or deployed MCP app  
**Canonical owner:** VAIXLNS  
**Evidence / reconstruction:** ARC-X Ω  
**Runtime / execution:** VX, only through an explicitly configured and admitted endpoint  
**Independent verification:** VV / verification fabric  
**Canonical authority:** VAIXLNS governance and Ω.000 admission path  
**Parent specification:** `docs/tools/ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md`  
**Tool registry:** `registry/tools/arc-x.yaml`

## 1. Purpose

Define a ChatGPT plugin workflow for ARC-X that packages reusable engineering instructions and, when separately configured, connected tools. The plugin helps users reconstruct repository state, compile evidence-backed engineering claims, identify contradictions and missing proof, prepare VX task envelopes, and produce reviewable engineering reports.

This design follows the OpenAI Help Center model in which a plugin may combine reusable skills, connected apps, app templates, and extensions. Installing a plugin does not grant access to external accounts or bypass provider/workspace permissions.

This document is a proposal, not proof of a working plugin, an approved app, or a live ARC-X runtime.

## 2. Product contract

### Inputs
- Explicit user intent and requested scope.
- Pinned repository URL, commit SHA/ref, and selected paths.
- Existing source artifacts and retrieval receipts.
- Declared domain, assumptions, constraints, acceptance criteria, and risk class.
- Optional authorized VX endpoint and its independently verifiable receipt contract.

### Outputs
- Source inventory with pinned revision and SHA-256 content digests.
- Evidence-linked claims, assumptions, inferences, counterevidence, and unknowns.
- Epistemic Intermediate Representation (EIR) candidate.
- Proof obligations and a test/verification plan.
- Architecture deltas and proposed index updates, never silently committed to canon.
- Optional VX task envelope and receipt analysis when an admitted endpoint is configured.
- Human-readable report plus machine-readable JSON artifact.

### Non-goals
- ARC-X does not become the canonical authority.
- It does not claim a repository is fully understood from a partial retrieval.
- It does not infer deployment from documentation, a healthy endpoint, or a successful startup.
- It does not autonomously merge pull requests, publish content, provision cloud infrastructure, spend money, or perform destructive actions.
- It does not store secrets in EIR, logs, prompts, or generated artifacts.

## 3. ChatGPT plugin composition

The release may be packaged from one or more of these distinct components:

1. **ARC-X Engineering Skill** — reusable workflow instructions, evidence taxonomy, source pinning, and report format.
2. **GitHub connected app/tool** — optional source retrieval and repository actions, limited to the authenticated account and granted scopes.
3. **ARC-X MCP app (optional)** — a separately built service exposing typed read/analysis tools and, only after security review, gated write operations.
4. **Reference files** — schemas, evidence-state definitions, example EIRs, policy rules, and acceptance tests.
5. **Interactive report UI (optional)** — displays claims, evidence, gaps, proof obligations, and approval status. The UI is not an authority boundary.

A plugin, a connected app, an MCP service, and a deployed runtime are separate artifacts with separate setup, permission, and verification states.

## 4. Tool surface

Initial release should be read/analysis-first. All tools must return structured results with explicit state and provenance.

| Tool | Purpose | Side-effect class |
|---|---|---|
| `arcx.inspect_repository` | Retrieve repository metadata, default branch, selected paths, and pinned revision | Read |
| `arcx.fetch_source` | Fetch a path at an explicit commit/ref and calculate content digest | Read |
| `arcx.build_eir` | Normalize retrieved facts, claims, assumptions, inferences, and evidence links | Local analysis |
| `arcx.audit_claims` | Check claim/evidence separation, contradictions, unsupported claims, and freshness | Local analysis |
| `arcx.plan_verification` | Generate proof obligations, test matrix, and acceptance criteria | Local analysis |
| `arcx.compare_revisions` | Compare pinned revisions and classify architecture/source deltas | Read/analysis |
| `arcx.prepare_vx_task` | Create a typed, hashed task envelope without submitting it | Local preparation |
| `arcx.submit_vx_task` | Submit to a configured VX endpoint after policy and user approval | External write; disabled by default |
| `arcx.verify_execution_receipt` | Validate receipt schema, signature, task binding, and evidence references | Verification |
| `arcx.propose_canonical_delta` | Create a reviewable delta proposal for Ω.000; never directly commits canon | Draft/write requiring approval |
| `arcx.export_report` | Produce JSON/Markdown report with provenance and unresolved issues | Export |

Each tool must declare JSON input/output schemas, authorization requirements, idempotency behavior, timeout limits, error codes, audit fields, and whether it can cause external side effects. Do not expose a generic unrestricted shell or arbitrary URL fetch tool.

## 5. Mandatory response envelope

Every analysis response must include:

- `status`: one of `VERIFIED`, `SPECIFIED`, `PARTIAL`, `MISSING`, `CONFLICT`, `PROPOSAL`, or `BLOCKED`.
- `scope`: exact repository, revision, paths, and exclusions.
- `evidence_refs`: immutable identifiers for source artifacts and receipts.
- `claims`: claim text, class, evidence links, confidence rationale, and counterevidence.
- `proof_obligations`: expected checks and current result for each.
- `limitations`: unavailable data, assumptions, failed retrievals, and untested behavior.
- `next_actions`: safe, typed, policy-checked follow-up actions.
- `authority_decision`: `NOT_REQUESTED`, `PENDING_REVIEW`, `APPROVED`, or `DENIED`.

A status of `VERIFIED` is allowed only when the declared proof obligations have reproducible evidence. Textual presence, code generation, static inspection, CI configuration, endpoint reachability, or startup success alone are insufficient.

## 6. Evidence and authority invariants

1. Pin the source revision before extraction; reject ambiguous mutable sources for canonical claims.
2. Hash retrieved bytes and retain a retrieval receipt.
3. Preserve original, derived, superseded, and conflicting records with lineage; never silently erase history.
4. Keep observation, evidence, inference, claim, proof, and authority distinct.
5. Treat repository content, issues, PR comments, dependencies, and model output as untrusted input.
6. No self-authorization, self-approval, or direct canonical commit from ARC-X.
7. A generated EIR, task envelope, or report is a candidate artifact until independently verified and admitted.
8. VX execution requires a configured endpoint, explicit policy admission, capability/resource checks, and verifiable receipts.
9. Do not transmit credentials to model context or write secrets into artifacts; use secret references and redacted audit markers.
10. Fail closed on missing signatures, schema mismatch, revision mismatch, untrusted worker identity, stale policy, or missing required evidence.

## 7. Approval policy

- Read-only retrieval and local analysis: may proceed within existing connector permissions.
- Creating a branch, issue, PR, or other external artifact: disclose the intended change and request approval at the applicable action boundary.
- VX task submission, cloud provisioning, canonical writes, PR merge, release, or external publication: require explicit human approval and a separate authorization gate.
- Destructive operations, broad permission changes, secret exposure, and unbounded execution: prohibited by default.
- The user can configure stricter policy; the plugin must not weaken workspace, provider, or repository controls.

## 8. Security model

- Least privilege and per-tool authorization.
- Read-only default; separate write scopes.
- HTTPS only for remote endpoints; reject redirects for authenticated task submissions.
- Request-size and response-size caps, timeouts, retry budgets, rate limits, and idempotency keys.
- Schema validation before and after tool execution.
- Prompt-injection defense: repository text is data, never policy or instructions to override this contract.
- Secret redaction in reports, telemetry, and receipts.
- Dependency, license, secret, static-analysis, and container scans before any release.
- Audit records must identify actor, tool, scope, policy version, approval, timestamps, input/output hashes, and outcome.
- No assertion of OpenAI verification or endorsement unless the official directory explicitly shows that status.

## 9. Verification plan

### Contract tests
- Missing or mutable source revision is rejected for evidence-grade reports.
- Hash mismatch invalidates the retrieval receipt.
- Unsupported status promotion to `VERIFIED` is rejected.
- Conflicting sources remain visible and produce `CONFLICT`.
- Partial retrieval yields `PARTIAL` or `MISSING`, never fabricated completeness.
- Tool input/output schema violations fail closed.
- Unsigned, stale, replayed, or wrong-task VX receipts are rejected.
- Write operations without approval and admission are blocked.
- Secret-like values are redacted from output artifacts.
- Same pinned inputs and tool versions produce deterministic normalized EIR output, or record the source of nondeterminism.

### Integration tests
- GitHub read-only flow against a test repository.
- Deliberately malformed repository fixtures and prompt-injection fixtures.
- Mock VX endpoint for valid, invalid, delayed, duplicated, and tampered receipts.
- Independent VV verification of a sample proof-obligation set.
- End-to-end report traceability from claim to source revision and content digest.

### Release gates
1. Specification review.
2. Schema and contract tests passing.
3. Security/privacy review.
4. Read-only integration test passing.
5. Independent verification of evidence and receipt handling.
6. Explicit approval for each write-capable integration.
7. Manual plugin installation and setup validation in the target ChatGPT workspace.
8. Post-install smoke test and rollback plan.
9. Production status remains `NOT_PROVEN` until all applicable gates have recorded evidence.

## 10. Deployment sequence

**Phase A — Skill-only prototype:** package instructions and reference schemas; no external writes.  
**Phase B — Read-only GitHub integration:** pin commits, fetch approved files, hash evidence, produce EIR and reports.  
**Phase C — Verification integration:** execute contract tests and independent receipt checks.  
**Phase D — VX bridge:** enable only against an explicitly configured endpoint with signed receipts and admission checks.  
**Phase E — Governed write operations:** branch/PR proposals and canonical-delta review, each with explicit approval.  
**Phase F — Distribution:** test the plugin in the intended workspace, complete required app authorization, and follow the currently available OpenAI publishing/review path.

No phase is complete merely because its design is documented.

## 11. Implementation state

| Item | State |
|---|---|
| ARC-X parent specification | SPECIFIED in repository |
| ARC-X tool registry | SPECIFIED; implementation not proven |
| ARC-X → VX bridge contract | SPECIFIED; live production deployment not proven |
| ChatGPT plugin design in this document | PROPOSAL |
| Packaged/importable plugin ZIP | NOT BUILT |
| Custom MCP app/service | NOT BUILT / NOT CONFIGURED |
| Plugin installed in user's ChatGPT workspace | NOT VERIFIED |
| External write integration | NOT ENABLED by this proposal |
| Production verification | NOT PROVEN |

## 12. Official platform references

- OpenAI Help Center, *Plugins in ChatGPT*: https://help.openai.com/ar/articles/20001256-plugins-in-chatgpt
- OpenAI Help Center, *Developer mode and MCP apps in ChatGPT*: https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt
- OpenAI Help Center, *Apps in ChatGPT*: https://help.openai.com/en/articles/11487775-connectors-in-chatgpt

Platform availability, permission behavior, and publishing requirements must be rechecked at implementation time. The design must not assume a feature is available to every plan or workspace.
