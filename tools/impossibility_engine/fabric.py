"""Bounded concurrent coordinator for local or explicit remote Ω workers."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib, json, os, re, time
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
                              float(item.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)))
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

def run_batch(problems: list[dict[str, Any]], *, max_workers: int = 4,
              remote_workers: list[RemoteWorker] | None = None,
              allow_local_fallback: bool = True) -> dict[str, Any]:
    """Run independent tasks concurrently, preserving input order with bounded concurrency."""
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
                "completed_count": 0, "failed_count": 0, "elapsed_ms": 0.0, "results": [],
                "limits": ["An empty batch is not reported as successful execution."]}
    prepared = [(i, p, "omega-" + hashlib.sha256(f"{i}:{canonical_hash(p)}".encode()).hexdigest()[:24])
                for i, p in enumerate(problems)]
    started = time.perf_counter()
    ordered: list[dict[str, Any] | None] = [None] * len(prepared)

    def local(i: int, problem: dict[str, Any], task_id: str, status: str,
              remote_worker_id: str | None = None, remote_error: Exception | None = None) -> dict[str, Any]:
        task_start = time.perf_counter()
        try:
            value = assess(problem)
            execution = {"status": status, "transport": "local",
                         "worker_id": f"local-{i % max_workers + 1}" if status == "SUCCEEDED" else "local-fallback"}
            if remote_worker_id:
                execution["remote_worker_id"] = remote_worker_id
                execution["remote_error_type"] = type(remote_error).__name__ if remote_error else "RemoteError"
                execution["remote_error"] = str(remote_error)[:300] if remote_error else "remote task failed"
        except (TypeError, ValueError) as exc:
            execution = {"status": "FAILED", "transport": "local",
                         "worker_id": f"local-{i % max_workers + 1}",
                         "error_type": type(exc).__name__, "error": str(exc)[:300]}
            if remote_worker_id:
                execution["remote_worker_id"] = remote_worker_id
        row = {"task_id": task_id, "result": value if "value" in locals() else None, "execution": execution}
        row["execution"]["elapsed_ms"] = round((time.perf_counter() - task_start) * 1000, 3)
        return row

    def dispatch(i: int, problem: dict[str, Any], task_id: str) -> dict[str, Any]:
        task_start = time.perf_counter()
        if not workers:
            row = local(i, problem, task_id, "SUCCEEDED")
        else:
            worker = workers[i % len(workers)]
            try:
                row = _remote_assess(worker, problem, task_id)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
                if allow_local_fallback:
                    row = local(i, problem, task_id, "FALLBACK_LOCAL", worker.worker_id, exc)
                else:
                    row = {"task_id": task_id, "result": None,
                           "execution": {"status": "FAILED", "transport": "https", "worker_id": worker.worker_id,
                                         "error_type": type(exc).__name__, "error": str(exc)[:300]}}
        row["execution"]["elapsed_ms"] = round((time.perf_counter() - task_start) * 1000, 3)
        return row

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="omega-worker") as pool:
        futures = {pool.submit(dispatch, i, p, task_id): i for i, p, task_id in prepared}
        for future in as_completed(futures):
            ordered[futures[future]] = future.result()
    rows = [r for r in ordered if r is not None]
    failed = sum(r["execution"]["status"] == "FAILED" for r in rows)
    return {"engine": "OMEGA-IMPOSSIBILITY-ENGINE", "fabric": "OMEGA-DISTRIBUTED-EXECUTION-FABRIC",
            "state": "EXECUTED" if failed == 0 else "PARTIAL", "task_count": len(rows),
            "max_concurrency": max_workers, "configured_remote_workers": [w.worker_id for w in workers],
            "completed_count": len(rows) - failed, "failed_count": failed,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3), "results": rows,
            "limits": ["Local concurrency does not guarantee CPU speedup for this small pure-Python workload.",
                       "Horizontal capacity requires separately deployed and configured HTTPS worker processes.",
                       "Fingerprints correlate tasks but do not prove a remote worker is honest or correct."]}
