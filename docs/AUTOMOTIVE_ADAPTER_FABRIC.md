# VX Automotive Adapter Fabric

Status: CANONICAL DESIGN SPECIFICATION
Scope: passenger vehicles, commercial vehicles, fleet systems, diagnostics, simulation and test benches.

## Architecture

Vehicle / Simulator
-> Vehicle Adapter
-> Protocol Adapter
-> VX Capability Contract
-> Safety + Policy Gate
-> VX Runtime
-> Event / State / Evidence
-> Verification / Replay

## Adapter layers

1. Vehicle identity and topology
2. Network transport
3. Diagnostic protocol
4. Signal/data normalization
5. ECU capability model
6. Read/observe operations
7. Simulation operations
8. Write/control operations behind explicit authorization
9. Evidence and replay
10. Recovery and safe-state handling

## Protocol families

CAN / CAN-FD
LIN
FlexRay
Automotive Ethernet
SOME/IP
ISO-TP
UDS
DoIP
OBD-II
J1939
OEM-specific gateways

Protocol support is adapter-specific; VX remains protocol-neutral.

## Vehicle model

VEHICLE
- identity
- VIN/reference
- manufacturer
- model
- model-year
- ECU topology
- supported protocols
- capabilities
- permissions
- safety constraints
- software/firmware provenance
- live state
- diagnostic evidence

## Safety invariant

No physical write operation is considered equivalent to a simulated operation. Physical control requires an explicit capability, authorization, precondition check, bounded command, acknowledgement, evidence and recovery path.

## Universal-vehicle claim

The goal is broad interoperability, not an unsupported claim that every vehicle is directly controllable. Coverage is produced incrementally through standard-protocol adapters and OEM-specific adapters, with unsupported capabilities represented explicitly as UNSUPPORTED rather than guessed.
