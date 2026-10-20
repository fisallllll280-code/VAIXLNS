# ARC-X Bounded Self-Provisioning Compute Fabric v1

**State:** SPECIFIED. No cloud resource is provisioned by this document.

## Purpose

Allow the system to calculate, propose, verify and—only after authorization—request compute environments suited to its workload, without giving an optimizer unrestricted cloud-account authority.

## Control-plane separation

- **Workload Planner:** describes workload requirements and benchmarks.
- **Capacity Planner:** estimates CPU, memory, GPU/accelerator, storage, network, region, duration and concurrency.
- **Policy & Budget Gate:** validates account/region allowlists, data residency, spend ceiling, quotas, image allowlist and security posture.
- **Infrastructure Compiler:** emits a reviewable declarative plan and immutable plan digest.
- **Provisioning Adapter:** a separately authorized cloud-specific component; absent adapter or credentials means `PLAN_ONLY`.
- **Bootstrap Verifier:** checks image signature, patch level, identity, network policy, secret injection, telemetry and isolation before workload admission.
- **Workload Scheduler:** runs only approved jobs with scoped identity, quotas, timeouts and egress restrictions.
- **Destroy/Reconciler:** expires ephemeral resources, detects drift and tears down only resources owned by the deployment's explicit ownership tags.
- **Audit Ledger:** stores plan, approval, provider operation IDs, observed resources, costs, drift and teardown evidence.

## Lifecycle

`NEED_DETECTED -> CAPACITY_ESTIMATED -> PLAN_GENERATED -> POLICY_CHECKED -> HUMAN_APPROVED -> PROVISION_REQUESTED -> BOOTSTRAP_VERIFIED -> WORKLOAD_ADMITTED -> COST/HEALTH_MONITORED -> EXPIRED_OR_RECONCILED`

Only `PLAN_GENERATED` is available to a pure planner. Every later transition needs a real provider adapter, authorized credentials and returned evidence. Do not mark resources as running based on desired-state configuration alone.

## Required hard limits

- account/project/subscription and region allowlists;
- maximum hourly and monthly spend, including a hard-stop budget;
- per-workload TTL, idle shutdown, concurrency and quota limits;
- approved signed base images; no self-modifying host images in production;
- private-by-default networking; no public IP or inbound port unless specifically approved;
- scoped workload identities; no long-lived credentials in images;
- encrypted storage and transport, tenant isolation and secret-manager integration;
- outbound network allowlists, rate limits, monitoring and incident shutdown;
- data classification and residency checks before scheduling;
- independent health checks and rollback to a known-good image/configuration.

If pricing, permissions, quotas or policy are unknown, fail closed and return a blocker instead of choosing an unbounded resource.

## Self-improvement boundary

The system may autonomously profile workloads, run isolated benchmarks, compare candidate configurations and produce a plan. It must not grant itself cloud IAM roles, increase its own budget, disable audit, alter canonical policy, expose services publicly, or promote a candidate into production. Those are separate governed actions.

## Readiness evidence

A resource is `ACTIVE_VERIFIED` only when the provider operation ID, observed resource identity, configuration digest, bootstrap test results, owner, expiry, budget allocation and monitoring status are present. Otherwise the state remains `PLAN_ONLY`, `PENDING_VERIFICATION` or `BLOCKED`.
