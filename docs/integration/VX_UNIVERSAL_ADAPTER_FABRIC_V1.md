# VX Universal Adapter Fabric v1

## Purpose

VX is the canonical execution boundary. It must not contain vendor-specific logic for every external platform. Instead, all external systems enter through typed, capability-scoped adapters.

```
WORLD / EXTERNAL SYSTEM
        |
        v
DISCOVERY + IDENTITY
        |
        v
PROTOCOL / TRANSPORT ADAPTER
        |
        v
SEMANTIC NORMALIZER
        |
        v
CAPABILITY CONTRACT
        |
        v
VV / POLICY GATE
        |
        v
VX EXECUTION
        |
        +--> EVENT / STATE / LEDGER
        +--> EVIDENCE / VERIFICATION / PROOF
        |
        v
REPLAY / RECOVERY / EVOLUTION
```

## Universal adapter classes

1. OS/runtime: Linux, Windows, macOS, Android, embedded Linux, containers, VMs.
2. Compute: CPU/GPU/NPU/accelerators through explicit runtime backends.
3. Cloud/API: HTTP, WebSocket, gRPC, message queues, databases, object stores.
4. Repositories/dev tools: GitHub and future Git providers through repository adapters.
5. AI/model systems: model APIs, local models, agent runtimes, MCP/tool surfaces.
6. Data: SQL/NoSQL/files/streams/vector stores.
7. Industrial/IoT: MQTT, OPC UA, Modbus, fieldbus and gateway adapters where licensed and supported.
8. Robotics: ROS/ROS 2 and robot-specific transport/capability adapters.
9. Automotive: VSS/VISS semantic layer plus CAN/DBC, UDS/ISO-TP, J1939 and OEM/API adapters.
10. Human interfaces: web, desktop, mobile, CLI, voice and multimodal front ends.

## Automotive boundary

The vehicle integration is deliberately split into:

```
Vehicle identity
  -> transport discovery
  -> CAN/SocketCAN/DBC or OEM API
  -> VSS semantic mapping
  -> capability classification
  -> safety policy
  -> VX execution
```

COVESA VSS is the semantic normalization layer; KUKSA CAN Provider demonstrates DBC-to-VSS mapping and replay; commaAI opendbc provides a large, continuously updated vehicle interface/data layer. These are upstream references, not automatically copied into VAIXLNS.

### Vehicle capability classes

- OBSERVE: telemetry/read-only.
- DIAGNOSE: diagnostic read/clear operations.
- SIMULATE: replay/digital twin.
- COMMAND: non-safety-critical command where explicitly authorized.
- ACTUATE: steering/braking/powertrain or other safety-critical control.

ACTUATE is never enabled merely because an adapter exists. It requires vehicle-specific support, authorization, safety interlocks, deterministic execution, evidence, verification and an explicit policy decision.

## Claude / external AI repository boundary

The repository `A3S-Lab/claude-fable-5` is treated as an external reference/tooling input, not as a VX runtime. Its `claude-fable-5.md` is a prompt artifact. VX should integrate such systems through an AI-provider/agent adapter:

```
Claude/other model
    -> provider adapter
    -> normalized intent/tool call
    -> policy gate
    -> VX
```

No provider receives canonical authority from being connected.

## Adapter contract

Every adapter must publish:

- identity and provenance
- supported transports
- capability list
- input/output schemas
- permissions
- safety class
- rate/resource limits
- failure modes
- recovery behavior
- observability hooks
- evidence format
- replay strategy
- version and compatibility matrix

## Hard rule

“Works with any system” means **any system for which VX has a valid adapter/standard interface and the required authorization**, not an assumption of universal compatibility.

The architecture therefore grows by adding adapters and capability manifests, not by modifying the VX kernel for every vendor.
