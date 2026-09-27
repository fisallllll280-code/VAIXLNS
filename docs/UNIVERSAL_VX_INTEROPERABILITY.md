# VX Universal Interoperability Architecture

Status: CANONICAL DESIGN SPECIFICATION
Owner: VAIXLNS
Runtime owner: VX

## 1. Canonical rule

All external systems are integrated through typed adapters. No external platform bypasses VX policy, identity, capability, event, state, evidence, verification, or recovery boundaries.

WORLD SYSTEM -> ADAPTER -> VX CONTRACT -> POLICY GATE -> VX EXECUTION -> EVENT/STATE/LEDGER -> PROOF

## 2. Adapter families

- OS / compute: Linux, Windows, macOS, BSD, POSIX, containers, VMs, bare metal
- Cloud / control plane: HTTP, REST, GraphQL, gRPC, WebSocket, queues, object stores, schedulers
- Data: SQL, NoSQL, filesystems, streams, vector stores, graph stores
- AI: model gateways, inference servers, tool APIs, MCP-style tool surfaces, local models
- Industrial / embedded: PLC, fieldbus, OPC UA, Modbus, MQTT, RTOS and device APIs
- Robotics: ROS/ROS2, simulation bridges, sensor/actuator interfaces
- Automotive: CAN/CAN-FD, LIN, FlexRay, Automotive Ethernet, SOME/IP, ISO-TP, UDS, DoIP, OBD-II and OEM-specific interfaces
- Mobile / desktop: native APIs, browser automation boundaries, filesystem and IPC adapters
- Network: TCP/IP, UDP, QUIC, TLS, SSH, DNS and service-discovery adapters

## 3. Universal adapter contract

Every adapter MUST declare:
identity
capabilities
supported operations
input/output schemas
preconditions
postconditions
timeouts
failure modes
resource limits
security boundary
observability
evidence hooks
replay support
recovery semantics
version
vendor/protocol metadata

## 4. Safety rule for physical systems

VX may orchestrate physical systems only through explicit capability grants and safety contracts. Automotive and industrial adapters default to observe/simulate modes until a verified execution contract is present.

## 5. Cloud/agent migration

A cloud/agent implementation is not renamed into VX by text replacement. It is rehoused:

legacy implementation
-> adapter
-> canonical VX contract
-> execution backend
-> verification/replay
-> operational assurance

The legacy lineage remains recorded.

## 6. Repository role

VAIXLNS = constitutional architecture and registry
vaixlns-core = sovereign core vertical slice
vaixlns-csd-kernel = signed/replayable kernel capability
VAIXLNS-unified = integrated runtime/fabric
VX-runtime = canonical execution runtime
NEXENT = discovery/search/design/evolution plane
VAIXLNS-Intent-to-Reality = intent/reality specification
VX50_COMPLETE_BUILD = historical/buildable VX extension pack

No repository is treated as canonical merely because its name is newer.

## 7. Acceptance gate

A new integration becomes CANONICAL only after:
1. identity and lineage registration
2. contract validation
3. adapter conformance tests
4. simulation/replay
5. security/policy validation
6. evidence generation
7. operational readiness
8. explicit adoption record
