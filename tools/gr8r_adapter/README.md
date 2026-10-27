# Gr8r → VX local contract bridge

Derived from the user-supplied adapter ZIP; original digest is pinned in
`registry/gr8r-vx-intake.integration.v1.json`. No upstream Gr8r code is embedded.

Run from the repository root with a private `VAIXLNS_ADAPTER_KEY` of at least
24 characters configured in the process environment:

```sh
python3 -m tools.gr8r_adapter.adapter
```

The server accepts only loopback HTTP. POST `/v1/tasks/intake` with
`X-Adapter-Key` and exactly `task_id`, `title`, `source: "gr8r"`,
`requested_action: "propose"`. It persists the complete proposal, an idempotent
receipt, and a globally hash-linked event in SQLite. A changed body under the
same task ID fails. The receipt stays PENDING_AUTHORIZATION / HOLD, with
`execution_performed: false`. `/health` reports no remote VX connection.
Do not put the key in browser JavaScript. Set `VAIXLNS_ADAPTER_DB` to an absolute
private SQLite path for durable deployment; the default is `events.sqlite3`.

## Trusted backend bridge

`authorize_proposal(data, envelope, registered_principal_id=...,
registered_capabilities=..., grant=..., now=...)` uses the actual existing
`vcre.agent_orchestration.authorize_dispatch` primitive. A trusted backend must
supply independently authenticated registry identity and authority grants.
The function does not authenticate a supplied Python object or issue grants.
There is deliberately no HTTP authorize/execute endpoint.

The envelope must bind task and resource to `gr8r:<source-task-id>`, the canonical
fingerprint of the exact proposal, INTEGRATION_ENGINEER, the sole capability
`gr8r:review-proposal`, and no tools. VCRE validates time windows, identity,
capability and scoped authority. A returned DISPATCHED state means permission
for delegation at this contract layer; it is not a worker run or result proof.
Authorization records are in memory; only intake proposals/receipts are durable.
Receipts do not automatically change after a contract authorization check.

## Acceptance and limits

```sh
python3 -m unittest discover -s tests -p 'test_gr8r*.py' -v
python3 -m unittest discover -s tests -p 'test_agent_orchestration.py' -v
```

Tests use synthetic grants and a real loopback HTTP listener and SQLite store.
No external provider, paid model or live Gr8r/VX runtime is contacted. Database
hash links are not external notarization or protection from database rewriting.
Legacy v0.1 receipts replay unchanged; old payloads were never stored and cannot
be recovered from digests. Deployment requires a backend identity/tenant map,
real runtime transport, independent verification and admission. This is a
bounded proposal bridge, not a public production service.

Rollback: disable the local listener and revert this feature commit. Preserve
SQLite evidence; do not delete existing task history. Protected sovereign files
are unchanged.
