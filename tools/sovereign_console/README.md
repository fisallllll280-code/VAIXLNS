# VAIXLNS Sovereign Command Console v1

## Purpose

The Sovereign Command Console is a local, evidence-aware operations surface over existing VAIXLNS assets. It reads `project.genome`, the `Ω.000` master index, and `registry/agent_registry.v1.json`; it does not create a parallel canonical registry.

## Run locally

From the repository root, with Python 3.10 or newer:

```bash
python tools/sovereign_console/server.py
```

Then open http://127.0.0.1:8765.

The HTTP bridge binds only to loopback. It has no public listener and no free-form shell endpoint. Do not expose this server to the internet by changing the bind address.

## Command reference

| Command | Behavior |
|---|---|
| `help` | List the allow-listed command surface |
| `status` | Read canonical surface and session status |
| `map` | Display declared system boundaries |
| `index list` | Read the records currently in `Ω.000` |
| `index search <terms>` | Search `Ω.000` and agent registry metadata |
| `agents list` | List registry definitions; does not imply live processes |
| `agents inspect <agent-id>` | Inspect capabilities, authority scope, and hard rule |
| `agents route <capabilities>` | Find registry definitions that declare all requested capabilities; metadata-only routing preview |
| `federation status` | List the four indexed system identities and recorded connection state; does not probe remote systems |
| `federation inspect <system-id>` | Inspect role, identity state, repository surfaces and source references |
| `federation capabilities [query]` | Search the capability catalog and distinguish specification from implementation evidence |
| `federation attributes [query]` | Search individual VLNS properties and evidence references |
| `federation gaps` | Show integration blockers and the evidence needed for closure |
| `genome inspect` | Inspect the canonical genome record |
| `genome verify` | Recompute the declared SHA-256 canonical digest |
| `proof verify` | Run local structural and digest checks |
| `runtime status` | Inspect the VX connection boundary and reference artifacts |
| `runtime simulate <intent>` | Produce deterministic hash-linked rehearsal events without changing files |
| `tests run` | Run the repository unittest suite with a 60-second timeout |
| `history` | Show recent process-local hash-linked command events |

## Trust boundaries

- Commands are parsed and dispatched from a fixed allow-list. Arbitrary shell text is rejected.
- The session hash chain lives in memory and resets when the server restarts. It is not a durable evidence ledger.
- A simulation is labelled `SIMULATION_ONLY`; it does not call a model provider or execute VX.
- `VX_RUNTIME_URL` may be set by the operator to declare that an endpoint is configured, but this version does not infer health from the variable and does not claim live connectivity.
- Registry definitions are not the same as running agent processes.
- The console is a local operator tool. It does not perform model inference, internet-wide research, deployment, privileged mutation, or canonical status promotion.
- `VERIFIED` requires appropriate executable evidence outside this UI. A structural `PASS` is not production uptime or proof of model quality.

## Validation

```bash
python -m unittest discover -s tests -p 'test_sovereign_console*.py'
```

The automated test suite covers digest tampering, canonical surfaces, registry inspection, fail-closed command parsing, simulation determinism, and session hash chaining.


## VLNS federation and engineering panels

The dashboard adds a source-linked local catalog at `registry/federation/vlns-capability-index.v1.json`. Its seven navigation items/command paths cover federation overview, VLNS inspection, capabilities, deep properties, integration edges and gap/release readiness.

The catalog retains VLNS↔NAXLNS as `UNVERIFIED`. The connection entry is a recorded status from 2026-10-06, not a fresh live health probe. These new commands perform local reads only; they do not contact remote systems or claim connectivity.

For the canonical design, property inventory and connection acceptance rules, see [VLNS System Federation and Engineering Dashboard v1](../../docs/federation/VLNS_SYSTEM_FEDERATION_AND_ENGINEERING_DASHBOARD_V1.md).

The UI is responsive, but the server deliberately binds to loopback. For phone access to a remote host, use an authenticated HTTPS gateway or approved hosted deployment. Do not expose the loopback bridge by merely changing the bind address.
