# Ω Index and Fabric Benchmark Plan v1

**State:** SPECIFIED; benchmark results have not yet been collected.  
**Purpose:** measure indexing speed, retrieval quality, freshness, resource use and resilience without inventing performance claims.

## Workloads

- Small: 1,000 files / 100 MB.
- Medium: 25,000 files / 2 GB.
- Large: 250,000 files / 20 GB.
- Mutation run: 1%, 5%, and 20% of files modified plus 1% deletions.
- Search suite: 100 fixed queries spanning identifiers, exact phrases, requirements, proofs, tests, security, dependencies, math/physics, and cross-repository references.
- Network suite: provider success, timeout, 429, 5xx, malformed JSON, duplicate source, stale metadata, and server unavailable.

These are target test fixtures, not claims that such data volumes have already been benchmarked.

## Required metrics

- Cold index wall time and files/second.
- Warm no-change run wall time and number of rehashed/reparsed files.
- Mutation-run latency and number of rows updated/deleted.
- Query p50/p95/p99 latency.
- Retrieval precision@10, recall@10 and reciprocal rank on a human-labeled query set.
- Freshness lag from source update to visible indexed result.
- Peak RSS, database size, bytes read/written, outbound request count.
- Failure recovery time, error rate, duplicate rate and correctness after replay.
- Cost per 1,000 queries and per 1,000 changed files when cloud services are used.

## Protocol

1. Pin commit SHA, OS/runtime version, machine shape, storage, dataset manifest and dataset SHA-256.
2. Run one cold start and at least five warm repetitions; report median and p95, not the best run.
3. Separate local-only from network-enabled runs.
4. Use identical hardware, dataset and query suite for baseline and candidate.
5. Verify all expected files, deletions, hashes and query judgments after every run.
6. Preserve raw JSON/CSV, logs, environment manifest and command line as evidence.
7. Label every result with code revision and date; do not compare incomparable environments.
8. Set acceptance targets only after collecting a baseline.

## Initial acceptance gates

- Exact content hash matches the manifest for every indexed file.
- A second no-change run produces zero content changes.
- Changed and deleted files are reflected in the next committed index generation.
- A network timeout or rate limit does not corrupt the local index.
- All provider failures are surfaced in per-provider status.
- Retrieval quality is reported with labeled queries; do not claim quality from hit counts alone.
- CI artifacts include the benchmark manifest and result hash.

## Output contract

A future benchmark runner should emit `vaixlns.omega-index-benchmark.v1` containing:
`revision`, `environment`, `dataset_manifest_sha256`, `workload`, `runs`, `latency_ms`, `files_per_second`, `memory_peak_bytes`, `db_size_bytes`, `quality_metrics`, `correctness_checks`, and `result_sha256`.

Do not set numeric speed claims or declare a winner until reproducible measurements exist.
