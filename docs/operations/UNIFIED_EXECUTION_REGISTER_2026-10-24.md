# VAIXLNS / VX — Unified Execution Register
Date: 2026-10-24 (Asia/Riyadh)
Status: PROPOSED EXECUTION REGISTER / NOT VERIFIED / NO DEPLOYMENT
Authority: VAIXLNS (canonical governance); VX (only governed execution intermediary).
Change boundary: isolated branch only. No merge, production release, spend, or modification to `project.genome` or `Ω.000`.

## 0 — Repository access checked through GitHub connector
| Repository | Default branch | Access observed | Intended role |
|---|---|---|---|
| fisallllll280-code/VAIXLNS | main | read/write/admin indicated | constitution, provenance, indexes, approval |
| fisallllll280-code/VX-runtime | main | read/write/admin indicated | runtime, tool gateway, policy, agent builder |
| fisallllll280-code/VAIXLNS-unified | main | read/write/admin indicated | integration adapters and bounded tests |
| fisallllll280-code/NEXENT | main | read/write/admin indicated | discovery, research, design proposals |

The access check does **not** establish live connectivity, active agents, deployed applications, successful tests or permission to publish. Verify branch protections and required checks independently before promotion.

## 1 — Reuse before new implementation
- `docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md`: existing ordered inventory and taxonomy; not a complete historical 0001–2750 recovery.
- `docs/index/VX_VLNS_INDEX_CONTINUITY_RUNBOOK_V1.md`: existing snapshot, replay and zero-loss procedure; run it rather than duplicating.
- `scripts/federation_preflight.py` and `tests/test_federation_preflight.py`: fail-closed admission with identity blockers; test *source inspected*, execution NOT_RUN in this operation.
- `registry/federation/federation_contract_edges.v1.json`: contract edges; no activation permitted without evidence.
- `schemas/vx-tool-action-envelope.v1.schema.json`, `tools/vx_tool_control_reference.py`: existing tool governance candidates; reference evaluator alone is not enforced runtime.
- `docs/tools/ARC_X_UNIVERSAL_MODEL_GATEWAY_V1.md`: gateway design to reconcile before creating provider connectors.

## 2 — Ordered work packages (no automatic promotion)
| ID | Work package | Destination | Minimal acceptance evidence | Current state |
|---|---|---|---|---|
| P00 | G0: pin SHA, checksums, branch protection, CI secrets presence (do not expose values) | each repo | signed/hashed G0 receipt, scope and blocker list | PENDING |
| P01 | Snapshot + zero-loss reconstruction, source identity disambiguation | VAIXLNS | complete bounded inventory, per-file SHA-256, restore diff, recovery receipt | PENDING |
| P02 | Federation and tool-control tests T01–T05 | VAIXLNS / VX-runtime | exact command, exit codes, test logs and hashes | NOT_RUN |
| P03 | Agent and provider connector tests T06–T10 | VX-runtime / VAIXLNS-unified | identity, least privilege, denied unknown tools, credential redaction, mocked/live distinction | NOT_RUN |
| P04 | T15 recovery and deterministic replay | VX-runtime | fault-injection and replay receipts | NOT_RUN |
| P05 | T11–T14 end-to-end guarded orchestration | VAIXLNS-unified | isolated full-flow trace with no forbidden bypass | NOT_RUN |
| P06 | VX Agent Builder and Agents & Tasks UI | VX-runtime | runnable build, browser/mobile screenshot, accessible flow and API tests | PENDING |
| P07 | Ω Reality Forge, evidence lab, index explorer, browser/data layer | VAIXLNS-unified | real data provenance, read-only default, smoke tests on iPhone | PENDING |
| P08 | Model router: OpenAI, Anthropic Claude, Gemini, Grok, Mistral; Claude Code bridge | VX-runtime | one tested connector first, contracts and provider-specific auth; no connection claim without tests | PENDING |
| P09 | Graft, NotebookLM, OmniRoute, MiroFish, n8n, YouTube skill, agency agents | VX-runtime | license/security review, sandbox integration tests, scoped MCP/HTTP adapter and rollback | PENDING |
| P10 | Ω Arena and cognitive championship | VAIXLNS / VX-runtime | reproducible benchmark, adversarial checks, provenance, disqualification evidence | PENDING |
| P11 | Marketplace and financial agents | VX-runtime | 30% platform commission, weekly settlement *after verification*, Saudi legal/payment review, isolated financial simulation | PENDING |
| P12 | Release readiness | all | G0 and all gates PASS, dependency review, iPhone end-to-end proof, explicit owner approval | BLOCKED |

## 3 — Operational constraints
1. Fail closed on unknown provider, unknown agent, unauthorized tool or unresolved system identity.
2. Never equate a document, workflow declaration, reference test, schema or mock with live service verification.
3. `VLNS ↔ NAXLNS` and `NEXNET ↔ NEXENT` are unresolved identities until independently corroborated; no inferred merge.
4. Only VX-mediated governed edges. No direct cross-system write or secret forwarding.
5. External budget zero SAR; no paid API calls, financial transfers, publishing or production release without separate approval.
6. Original/Derived classification and source commit/path must persist through all index updates; `NOT_OBSERVED` / `INACCESSIBLE` are not `MISSING` absent complete bounded inventory.
7. No performance claim (including 10× speedup) without before/after measurements using identical hardware, workloads, and confidence intervals.
8. On any failed gate preserve receipts and halt promotion; never silence or downgrade failure.

## 4 — First runnable local gate, pending execution
From a pinned isolated checkout of VAIXLNS:

```bash
python -m unittest tests.test_federation_preflight -v
python -m unittest discover -s tests -p 'test_zero_loss_index.py' -v
python scripts/recover_zero_loss_index.py --root . --output-dir build/zero-loss-index
python scripts/omega_arena_audit.py --output build/omega-arena/audit-receipt.json
python -m unittest tests.test_omega_arena_audit -v
```

Archive stdout/stderr, exit status, commit ID and generated receipt SHA-256 for each command. These commands were **not executed** when this document was authored.

## 5 — Required proof for each task
`task_id, source_repo, source_commit, base_commit, branch, change_paths, original_or_derived, command, environment, exit_status, evidence_sha256, reviewer, verification_status, blocked_reason, timestamp_utc`.

Only independent runtime evidence permits VERIFIED. This register itself is DERIVED and PROPOSED.
