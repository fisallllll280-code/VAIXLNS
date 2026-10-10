"""Bounded, load-aware coordinator for local or explicitly configured remote Ω workers."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import hashlib, json, os, re, threading, time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from .engine import assess

MAX_WORKERS = 64
MAX_REMOTE_NODES = 64
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 15.0

def canonical_hash(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

@dataclass(frozen=True)
class RemoteWorker:
    worker_id: str
    endpoint: str
    token_env: str = "OMEGA_WORKER_TOKEN"
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_concurrency: int = 2

    def validate(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", self.worker_id):
            raise ValueError("worker_id must be 1-64 safe ASCII characters")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", self.token_env):
            raise ValueError("token_env must be an environment variable name")
        parsed = urlsplit(self.endpoint)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("remote worker endpoint must use HTTPS")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("endpoint must not contain credentials, query, or fragment")
        if not parsed.path.rstrip("/").endswith("/v1/assess"):
            raise ValueError("endpoint path must end with /v1/assess")
        if not 0.1 <= float(self.timeout_seconds) <= 120:
            raise ValueError("timeout_seconds must be between 0.1 and 120")
        if not 1 <= int(self.max_concurrency) <= MAX_WORKERS:
            raise ValueError(f"max_concurrency must be between 1 and {MAX_WORKERS}")

def remote_workers_from_json(raw: str) -> list[RemoteWorker]:
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("remote worker config is not valid JSON") from exc
    if not isinstance(items, list) or len(items) > MAX_REMOTE_NODES:
        raise ValueError(f"worker config must be a list with at most {MAX_REMOTE_NODES} nodes")
    result, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each worker must be an object")
        if "token" in item or "authorization" in item:
            raise ValueError("credentials must be supplied via environment variables, not config")
        worker = RemoteWorker(str(item.get("worker_id", "")), str(item.get("endpoint", "")),
                              str(item.get("token_env", "OMEGA_WORKER_TOKEN")),
                              float(item.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
                              int(item.get("max_concurrency", 2)))
        worker.validate()
        if worker.worker_id in seen:
            raise ValueError(f"duplicate worker_id: {worker.worker_id}")
        seen.add(worker.worker_id)
        result.append(worker)
    return result

def _remote_assess(worker: RemoteWorker, problem: dict[str, Any], task_id: str) -> dict[str, Any]:
    worker.validate()
    token = os.environ.get(worker.token_env, "")
    if not token:
        raise RuntimeError(f"required environment variable {worker.token_env} is not set")
    request_hash = canonical_hash(problem)
    body = json.dumps({"task_id": task_id, "request_sha256": request_hash, "problem": problem},
                      separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    req = Request(worker.endpoint, data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "Authorization": f"Bearer {token}", "User-Agent": "VAIXLNS-Omega-Fabric/0.1"},
        method="POST")
    with urlopen(req, timeout=worker.timeout_seconds) as response:
        if response.status != 200:
            raise RuntimeError(f"worker {worker.worker_id} returned HTTP {response.status}")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("worker response exceeded size limit")
    envelope = json.loads(raw.decode("utf-8"))
    if not isinstance(envelope, dict) or envelope.get("task_id") != task_id or envelope.get("request_sha256") != request_hash:
        raise RuntimeError("worker response task fingerprint mismatch")
    if envelope.get("worker_id") != worker.worker_id:
        raise RuntimeError("worker identity mismatch")
    value = envelope.get("result")
    if not isinstance(value, dict) or not isinstance(value.get("assessment_sha256"), str):
        raise RuntimeError("invalid worker assessment response")
    return {"task_id": task_id, "result": value,
            "execution": {"status": "SUCCEEDED", "transport": "https", "worker_id": worker.worker_id}}

@dataclass
class _WorkerState:
    worker: RemoteWorker
    in_flight: int = 0
    successes: int = 0
    failures: int = 0
    consecutive_failures: int = 0
    ewma_latency_ms: float = 1000.0
    peak_in_flight: int = 0
    circuit_open: bool = False

class _LoadAwarePool:
    """Batch-scoped least-estimated-completion scheduler with a fail-closed circuit."""
    def __init__(self, workers: list[RemoteWorker]) -> None:
        self._cv = threading.Condition()
        self.states = {w.worker_id: _WorkerState(w) for w in workers}

    def acquire(self, excluded: set[str]) -> _WorkerState | None:
        with self._cv:
            while True:
                eligible = [s for key, s in self.states.items()
                            if key not in excluded and not s.circuit_open and s.in_flight < s.worker.max_concurrency]
                if eligible:
                    state = min(eligible, key=lambda s: (s.ewma_latency_ms * (s.in_flight + 1),
                                                          s.in_flight, s.successes, s.worker.worker_id))
                    state.in_flight += 1
                    state.peak_in_flight = max(state.peak_in_flight, state.in_flight)
                    return state
                still_possible = [s for key, s in self.states.items()
                                  if key not in excluded and not s.circuit_open]
                if not still_possible:
                    return None
                self._cv.wait(timeout=0.25)

    def release(self, state: _WorkerState, elapsed_ms: float, success: bool) -> None:
        with self._cv:
            state.in_flight = max(0, state.in_flight - 1)
            state.ewma_latency_ms = 0.3 * elapsed_ms + 0.7 * state.ewma_latency_ms
            if success:
                state.successes += 1
                state.consecutive_failures = 0
            else:
                state.failures += 1
                state.consecutive_failures += 1
                # Open for the rest of this batch after one failed request; another
                # known node may still handle the task, and the failed node is not hammered.
                state.circuit_open = True
            self._cv.notify_all()

    def metrics(self) -> list[dict[str, Any]]:
        with self._cv:
            return [{"worker_id": s.worker.worker_id, "max_concurrency": s.worker.max_concurrency,
                     "successes": s.successes, "failures": s.failures,
                     "in_flight": s.in_flight, "peak_in_flight": s.peak_in_flight,
                     "ewma_latency_ms": round(s.ewma_latency_ms, 3),
                     "circuit_open": s.circuit_open} for s in self.states.values()]

def run_batch(problems: list[dict[str, Any]], *, max_workers: int = 4,
              remote_workers: list[RemoteWorker] | None = None,
              allow_local_fallback: bool = True) -> dict[str, Any]:
    """Run independent tasks concurrently, preserving order with a load-aware remote scheduler."""
    if not isinstance(problems, list) or not all(isinstance(p, dict) for p in problems):
        raise ValueError("problems must be a list of JSON objects")
    if not 1 <= max_workers <= MAX_WORKERS:
        raise ValueError(f"max_workers must be between 1 and {MAX_WORKERS}")
    workers = remote_workers or []
    if len(workers) > MAX_REMOTE_NODES:
        raise ValueError(f"at most {MAX_REMOTE_NODES} remote workers are supported")
    for worker in workers:
        worker.validate()
    if len({w.worker_id for w in workers}) != len(workers):
        raise ValueError("remote worker IDs must be unique")
    if not problems:
        return {"engine": "OMEGA-IMPOSSIBILITY-ENGINE", "fabric": "OMEGA-DISTRIBUTED-EXECUTION-FABRIC",
                "state": "NO_TASKS", "task_count": 0, "max_concurrency": max_workers,
                "configured_remote_workers": [w.worker_id for w in workers],
                "worker_metrics": [], "completed_count": 0, "failed_count": 0, "fallback_count": 0,
                "elapsed_ms": 0.0, "results": [],
                "limits": ["An empty batch is not reported as successful execution."]}
    prepared = [(i, p, "omega-" + hashlib.sha256(f"{i}:{canonical_hash(p)}".encode()).hexdigest()[:24])
                for i, p in enumerate(problems)]
    started = time.perf_counter()
    ordered: list[dict[str, Any] | None] = [None] * len(prepared)
    pool = _LoadAwarePool(workers)

    def local(i: int, problem: dict[str, Any], task_id: str, status: str,
              remote_worker_id: str | None = None, remote_error: Exception | None = None) -> dict[str, Any]:
        try:
            value = assess(problem)
            execution = {"status": status, "transport": "local",
                         "worker_id": f"local-{i % max_workers + 1}" if status == "SUCCEEDED" else "local-fallback"}
            if remote_worker_id:
                execution.update({"remote_worker_id": remote_worker_id,
                                  "remote_error_type": type(remote_error).__name__ if remote_error else "RemoteError",
                                  "remote_error": str(remote_error)[:300] if remote_error else "remote task failed"})
        except (TypeError, ValueError) as exc:
            value = None
            execution = {"status": "FAILED", "transport": "local",
                         "worker_id": f"local-{i % max_workers + 1}",
                         "error_type": type(exc).__name__, "error": str(exc)[:300]}
            if remote_worker_id:
                execution["remote_worker_id"] = remote_worker_id
        return {"task_id": task_id, "result": value, "execution": execution}

    def dispatch(i: int, problem: dict[str, Any], task_id: str) -> dict[str, Any]:
        task_start = time.perf_counter()
        row = None
        if not workers:
            row = local(i, problem, task_id, "SUCCEEDED")
        else:
            excluded: set[str] = set()
            last_error: Exception | None = None
            # Try distinct configured nodes, at most once each, then fail or fall back.
            for _ in range(len(workers)):
                state = pool.acquire(excluded)
                if state is None:
                    break
                excluded.add(state.worker.worker_id)
                remote_start = time.perf_counter()
                try:
                    row = _remote_assess(state.worker, problem, task_id)
                    pool.release(state, (time.perf_counter() - remote_start) * 1000, True)
                    break
                except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
                    last_error = exc
                    pool.release(state, (time.perf_counter() - remote_start) * 1000, False)
            if row is None:
                if allow_local_fallback:
                    row = local(i, problem, task_id, "FALLBACK_LOCAL",
                                last_error_worker_id if False else (next(iter(excluded)) if excluded else None), last_error)
                else:
                    row = {"task_id": task_id, "result": None,
                           "execution": {"status": "FAILED", "transport": "https",
                                         "error_type": type(last_error).__name__ if last_error else "NoHealthyWorker",
                                         "error": str(last_error)[:300] if last_error else "no eligible worker"}}
        row["execution"]["elapsed_ms"] = round((time.perf_counter() - task_start) * 1000, 3)
        return row

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="omega-worker") as executor:
        futures = {executor.submit(dispatch, i, problem, task_id): i for i, problem, task_id in prepared}
        for future in as_completed(futures):
            ordered[futures[future]] = future.result()
    rows = [row for row in ordered if row is not None]
    failed = sum(row["execution"]["status"] == "FAILED" for row in rows)
    fallback = sum(row["execution"]["status"] == "FALLBACK_LOCAL" for row in rows)
    state = "FAILED" if failed == len(rows) else "PARTIAL" if failed else "DEGRADED" if fallback else "EXECUTED"
    return {"engine": "OMEGA-IMPOSSIBILITY-ENGINE", "fabric": "OMEGA-DISTRIBUTED-EXECUTION-FABRIC",
            "state": state, "task_count": len(rows), "max_concurrency": max_workers,
            "configured_remote_workers": [w.worker_id for w in workers],
            "worker_metrics": pool.metrics(), "completed_count": len(rows) - failed,
            "failed_count": failed, "fallback_count": fallback,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3), "results": rows,
            "limits": ["Local concurrency does not guarantee CPU speedup for this pure-Python triage workload.",
                       "Horizontal capacity requires separately deployed and configured HTTPS workers.",
                       "Fingerprints correlate tasks but do not prove a remote worker is honest or correct."]}
