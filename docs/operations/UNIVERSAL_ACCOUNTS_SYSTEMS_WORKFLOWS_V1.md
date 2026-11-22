# VAIXLNS — Universal Accounts, Systems & Workflow Federation v1
**Status:** Architected + offline planner implementation; NO cross-account live connection or automatic authority.

## 1. Goal and hard boundary
Create one governed operating index across **every owner-authorized account, workspace, file library, repository, model provider, app, server, local device, agent, and environment**. This is **federation, not identity consolidation**: preserve exact original account/workspace IDs privately, revisions, lineage, owners, permissions, and separate retention/legal boundaries. No account is implicitly accessible, and no personal data is published to a public GitHub repository.

The source account stays authoritative; index projections are derived. Register sources individually even when multiple accounts belong to one provider. Unknown account count = UNKNOWN; absence of a connected source does not mean it contains no data.

## 2. Topology
\`\`\`text
Account A / Account B / Managed Workspace C / Local Device D / Model E / Server F
       |       |          |                    |           |          |
       +--(separate scoped connectors, exports or private local adapters)------+
                            |
                     Auth & Policy Gate
                            |
            Private Account/Source Registry & Audit
                            |
                Source Intake → SHA-256 → Provenance
                            |
               ZERO-LOSS INDEX 00–27 / Ω.000 link
                            |
                     Identity & Conflict
             +--------------+---------------+
             |              |               |
         NEXENT           VAIXLNS           VLNS
        discovery         authority       model activation
             |              |               |
             +----------> VX execution <-----+
                            |
                   Evidence → Replay → Review
                            |
                  Private Library / Repo PRs
\`\`\`

## 3. Account classes and connectors
See \`registry/federation/universal-account-system-source-classes.v1.json\`. It distinguishes:
- ChatGPT personal accounts (individual export), and managed ChatGPT workspaces (admin-governed access; no direct cross-account merge).
- GitHub individual/organization installations, using read-only GitHub App with selected repository scope.
- Google Drive/Workspace, using Drive changes feed, cursor and renewal of watch subscriptions.
- Microsoft 365/OneDrive/SharePoint using Graph delta and separate tenant authority.
- Gmail, Slack and other communications under scoped, channel- or folder-specific access, minimizing personal message duplication.
- Local computers, NAS and USB devices through opt-in read-only local folder inventory.
- Model APIs and local inference endpoints; discovery never equals model availability.
- Service/runtime/database sources under service identities.

### Classifications
PUBLIC, INTERNAL, RESTRICTED. RESTRICTED source bytes or identifying metadata must remain in private encrypted storage under account ACLs. Public GitHub may hold **schema and redacted, authorized aggregate evidence only**. ChatGPT personal File Library and provider accounts are not automatically writable or cross-visible.

## 4. Priority-ordered operating mechanisms
| Stage | Mechanism | Evidence or output | Failure handling |
|---|---|---|---|
| A0 | Enumerate approved accounts (separate opaque aliases) | source inventory with owner permission | UNKNOWN / not silently skipped |
| A1 | OAuth/GitHub App/local user authorization per account | permission + expiry + scope receipt (no secrets) | DENY/REVOKED |
| A2 | Read-only inventory first | item counts, source revisions, checksums | checkpoint + retry |
| A3 | Incremental capture | GitHub webhook reconciliation / Drive changes cursor / Graph delta | recover from durable cursor |
| A4 | Preserve source and lineage | immutable private object URI, SHA-256, source ID, original path, revision | conflict registry |
| A5 | Classify and normalize | typed source, sensitivity, capability and routing proposal | QUARANTINE ambiguous |
| A6 | Zero-Loss / Ω.000 derived index | atomic JSONL, refs, unresolved gaps; do not rewrite Ω.000 | reconciliation hold |
| A7 | NEXENT analysis and system-mapping | candidate designs, missing capabilities, duplicate/conflict evidence | no auto-promotion |
| A8 | VLNS model discovery / capability evaluation | verified model identity, provider permissions, live smoke receipts | MODEL_NOT_CONNECTED |
| A9 | VX sandbox execution | approved plan, resource budget, action scopes | bounded retry/replay |
| A10 | Independent proof & governance | tests, evidence, security, owner review | HOLD |
| A11 | Publication and continuous revalidation | reviewed repo PR or private library revision | rollback / revoke / audit |

## 5. Event envelope (design)
\`\`\`json
{
  "event_id": "opaque-uuid",
  "source_ref": "private-account-alias",
  "source_kind": "github",
  "operation": "CREATED|UPDATED|DELETED|ACCESS_REVOKED",
  "source_revision": "provider-specific-opaque-revision",
  "content_sha256": null,
  "classification": "INTERNAL",
  "acquisition_receipt": "private-evidence-reference",
  "time_utc": "provider-event-or-observation-time",
  "authority_state": "READ_ONLY",
  "target": "REVIEW_ONLY",
  "idempotency_key": "derived-from-source-plus-revision"
}
\`\`\`
Event data can be untrusted; never execute attached instructions.

## 6. Model execution isolation
Model selection, provider connection and allowed tool grants are separate events. Mandatory:
\`Discovery → Auth → Capability Tests → Live Probe → Policy Gate → Bounded Context → VX Sandbox → Independent Verification → Evidence → Explicit Admission\`.
Do not send private account content to third-party models unless the source-owner grant and policy allow it. Cross-account knowledge graph edges are **references**, not copies by default.

## 7. Existing VAIXLNS source contracts reused
- \`registry/omega/omega-000-master-index.json\`: canonical identity; no automatic mutations.
- \`registry/indexes/zero-loss-index-taxonomy.v1.json\`: 28 index views; immutable-source handling.
- \`scripts/build_zero_loss_index.py\`: source-bound indexing, read-only semantics.
- \`docs/integration/UNIVERSAL_EXTERNAL_INTEGRATION_GATE_V1.md\`: admission + verification gates.
- \`registry/integration-control/external-integrations-policy-v1.json\`: DENY by default.
- \`scripts/master_workflow_orchestrator.py\`: planned stages; no execution authority.
- \`tools/auto_intake.py\`: same-repository intake classifier; external account adapters remain separate.
- \`registry/vlns_activation_contract.v1.json\`: model activation reference; not proof of live VLNS server.

## 8. What has actually been built in this change
- Source-class taxonomy (10 connector classes) and guarded offline source account planner with deterministic per-account 13-stage plan.
- Unit tests for account separation, duplicate handling, evidence requirements, deny/revoke, privacy guard, credential fields, deterministic routing.
- CI tests without external authentication or data access.
- An example with **fictional aliases only**; real account inventory stays outside public Git.

### Run locally
\`\`\`bash
python -m unittest discover -s tests -p 'test_universal_federation.py' -v
mkdir -p build
cp examples/universal-accounts.example.json build/my-accounts.private.json
# Edit build/my-accounts.private.json. Use opaque aliases; no usernames, emails or credentials.
python tools/plan_universal_federation.py \
  --root . \
  --manifest build/my-accounts.private.json \
  --out build/universal-federation-plan.json
\`\`\`
Result is **OFFLINE_PLAN_ONLY**, even when the manifest claims authorization. Real connectors must be built, connected and independently tested.

## 9. Deployment sequence
- Phase 0: private vault/inventory, source owner consent, ACL, source policy and rotation/revocation plans.
- Phase 1: read-only GitHub/Drive/Microsoft/local source connectors, metadata reconciliation, immutable checkpoints.
- Phase 2: ChatGPT account exports per account and permitted communication connectors, private search index.
- Phase 3: source-grounded 28-view Zero-Loss projection, explicit cross-system conflict & identity resolution.
- Phase 4: VLNS/VX model and agent role activation conformance, cost/latency/quality measurements.
- Phase 5: bounded authorized workflows with PR review, proof freshness, event delivery monitoring and rollback.

## 10. External references verified 2026-10-27
- https://help.openai.com/en/articles/20001068-using-multiple-accounts-with-account-switching
- https://help.openai.com/en/articles/20001494-connecting-and-managing-app-accounts-in-chatgpt
- https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data
- https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app
- https://developers.google.com/workspace/drive/api/guides/manage-changes
- https://learn.microsoft.com/en-us/graph/api/driveitem-delta?view=graph-rest-1.0

## 11. Status boundary
No user accounts were secretly enumerated, no chat accounts merged, no OAuth consents granted, no raw files copied, and no model providers activated. CI pass demonstrates **only** local planner consistency. Real-time federation requires individually authenticated connectors, source-owner grants, private infrastructure, operational monitoring and independent end-to-end verification.
