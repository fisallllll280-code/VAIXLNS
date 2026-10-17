# Bounded Parallel Execution v1

## Status

- Implementation state: `IMPLEMENTED` on feature branch.
- Runtime test state: pending GitHub Actions result for the branch head.
- Cross-repository integration state: `PARTIAL`; only the VAIXLNS innovation server is changed in this slice.
- Production and multi-host readiness: `NOT VERIFIED`.

## Scope

The local innovation server now supports a bounded worker pool controlled by `VAIXLNS_SERVER_WORKERS` (default 4; accepted range 1 through 32). Workers use the existing SQLite transactional claim path and fixed allowlisted deterministic handlers. Each job remains idempotency-aware at submission, and a handler completion is still explicitly `NOT_VERIFIED`.

## Why this is safe

- No arbitrary shell, Python import, network action, or external side effect is introduced.
- The existing transactional `BEGIN IMMEDIATE` claim path serializes queue claims, preventing two workers from claiming the same queued job.
- Worker count is validated and capped to limit accidental resource exhaustion.
- Existing single-worker `Worker` API remains available for current callers and tests.
- Shutdown signals all workers before joining them.

## Configuration

```bash
VAIXLNS_SERVER_WORKERS=4 python -m services.innovation_server.server
```

Set the count based on measured workload and host capacity. More workers are most likely to improve throughput for I/O-bound or waiting tasks; the current built-in handlers are lightweight and deterministic, so production throughput gains must be measured rather than assumed. SQLite remains a single-host queue and may become a contention bottleneck under load.

## Verification plan

1. Run `python -m unittest tests.test_innovation_server -v`.
2. Confirm the concurrency regression test observes at least two simultaneous handler executions.
3. Exercise worker counts 1, 2, 4, and 8 under representative synthetic workloads; report jobs/second, p50/p95 queue wait, p50/p95 execution latency, failures, and CPU/memory.
4. Add distributed queue infrastructure only if measured load and consistency requirements justify it.
5. Do not mark any of the four systems integrated until repository identity, adapters, and end-to-end evidence are verified.

## Four-system federation boundary

The requested names are VAIXLNS, VLNS, VX, and NEXNET. At this audit, exact GitHub repository URLs for `VLNS`, `VX`, and `NEXNET` under the current owner returned not found. Search surfaced `NAXLNS`, `VX-runtime`, `VX50_COMPLETE_BUILD`, and `NEXENT`, but these are not treated as aliases without explicit evidence. This branch therefore improves the VAIXLNS server only and leaves the canonical genome and master index untouched.
