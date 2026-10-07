# VAIXLNS Semantic Connection Fabric V1

**Status:** IMPLEMENTED / CONFORMANCE BASELINE  
**Identity:** `VAIXLNS-CONNECTION-FABRIC-001`

## Purpose

VAIXLNS is modeled as a live semantic fabric rather than a single serialized connection.

Independent semantic channels carry different classes of meaning:

- C-SPEC — specification and intent
- C-AUTHORITY — authority and authorization
- C-EXECUTION — execution requests/events
- C-EVIDENCE — evidence and provenance
- C-SECURITY — security findings and decisions

Multiple connections may carry the same purpose. Routing selects an available channel using priority, queue depth, and deterministic channel identity.

## Anti-Stick Properties

1. **Isolation:** a blocked/compromised channel can be isolated without stopping unrelated channels.
2. **Backpressure:** each channel has bounded capacity; saturation is explicit rather than silently accumulating.
3. **Failover:** multiple channels for one purpose allow deterministic fallback.
4. **Multiplexing:** different semantic purposes can flow concurrently.
5. **Evidence:** routing, delivery, isolation, and recovery produce hash-linked event evidence.
6. **No self-authority:** the fabric transports authority decisions; it does not create authority.

## Live path

`Semantic Source → Guardian → Connection Fabric → VX/VLNS → Execution → Observation → Evidence → Verification → Finality`

The reference implementation intentionally avoids hidden threads, random scheduling, implicit retries, and unbounded queues. Production transport may later implement the same contract over a real message bus or network fabric.

## Non-goals

This baseline does not claim production-grade network security, cryptographic transport, distributed consensus, or lossless delivery. Those require separate evidence and infrastructure.

## Acceptance criteria

- Independent channels route without global blocking.
- Same-purpose channels fail over deterministically.
- Isolation is local.
- Capacity saturation becomes explicit backpressure.
- Every state transition is observable in replayable evidence.
