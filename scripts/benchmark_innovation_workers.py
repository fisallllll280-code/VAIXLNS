#!/usr/bin/env python3
"""Measure local innovation-worker throughput and end-to-end job latency.

Run from the repository root:
  python scripts/benchmark_innovation_workers.py --jobs 100 --workers 1 2 4 8

This is a local microbenchmark, not a production capacity test.
"""
from __future__ import annotations
import argparse
import json
import math
import statistics
import sys
import tempfile
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from services.innovation_server.server import JobStore, WorkerPool  # noqa: E402

def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(p * len(ordered)) - 1))
    return ordered[index]

def run_case(worker_count: int, job_count: int, timeout_seconds: float) -> dict:
    with tempfile.TemporaryDirectory(prefix="vaixlons-bench-") as tmp:
        store = JobStore(str(Path(tmp) / "jobs.sqlite3"))
        ids = [store.submit("hash_json", {"benchmark_job": i, "payload": "x" * 256})[0]["job_id"] for i in range(job_count)]
        started = time.perf_counter()
        pool = WorkerPool(store, workers=worker_count, poll_seconds=0.002)
        pool.start()
        deadline = started + timeout_seconds
        try:
            while True:
                rows = [store.get(job_id) for job_id in ids]
                if all(row and row["state"] in {"COMPLETED", "FAILED", "REJECTED"} for row in rows):
                    break
                if time.perf_counter() >= deadline:
                    raise TimeoutError(f"{worker_count} workers exceeded {timeout_seconds}s timeout")
                time.sleep(0.01)
        finally:
            pool.stop()
        elapsed = time.perf_counter() - started
        latencies = [max(0.0, (r["updated_at"] - r["created_at"]) * 1000.0) for r in rows if r]
        completed = sum(r["state"] == "COMPLETED" for r in rows if r)
        failed = sum(r["state"] != "COMPLETED" for r in rows if r)
        return {"workers": worker_count, "submitted_jobs": job_count, "completed_jobs": completed,
                "failed_jobs": failed, "elapsed_seconds": round(elapsed, 6),
                "throughput_jobs_per_second": round(completed / elapsed, 3) if elapsed else 0.0,
                "latency_ms_p50": round(statistics.median(latencies), 3) if latencies else 0.0,
                "latency_ms_p95": round(percentile(latencies, 0.95), 3),
                "measurement": "local SQLite + deterministic hash_json handler"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=100)
    parser.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4, 8])
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be >= 1")
    if args.timeout <= 0:
        parser.error("--timeout must be > 0")
    if not args.workers or any(n < 1 or n > 32 for n in args.workers):
        parser.error("--workers values must be between 1 and 32")
    results = [run_case(n, args.jobs, args.timeout) for n in args.workers]
    baseline = next((r["throughput_jobs_per_second"] for r in results if r["workers"] == 1), None)
    for result in results:
        result["speedup_vs_one_worker"] = round(result["throughput_jobs_per_second"] / baseline, 3) if baseline else None
    print(json.dumps({"status": "MEASURED_LOCAL_MICROBENCHMARK",
                      "warning": "Do not generalize these results to production workloads.",
                      "results": results}, indent=2))
    return 0 if all(r["failed_jobs"] == 0 for r in results) else 1

if __name__ == "__main__":
    raise SystemExit(main())
