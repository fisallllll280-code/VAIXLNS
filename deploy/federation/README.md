# VAIXLNS Four-System Operational Federation

This directory defines the server-side wiring between the four independent system identities and their GitHub repository surfaces.

| System ID | System | Repository surface | Runtime responsibility |
|---|---|---|---|
| VAIXLNS | VAIXLNS | `VAIXLNS` | Control plane, canonical registry, governance, evidence, recovery |
| VLNS | VLNS | `NAXLNS` (identity mapping UNVERIFIED) | Knowledge / adversarial analysis / discovery |
| VX | VX | `VX-runtime`, `VX50_COMPLETE_BUILD` | Governed execution, state, replay, verification |
| NEXNET | NEXNET | `NEXENT` (identity mapping UNVERIFIED) | Discovery, architecture search, research, synthesis |

Runtime path:

```
Ingress -> VAIXLNS Control -> System Router
       -> VLNS / VX / NEXNET
       -> Event + Evidence Boundary
       -> Registry / Ledger
       -> Observability
```

A deployment is not VERIFIED from this manifest alone. Verification requires dependency resolution, startup, health, tests, evidence capture and reproducible verification.
