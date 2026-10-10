"""Local-first durable innovation job server for VAIXLNS.

Security posture:
- Binds to loopback by default.
- Non-loopback binding requires VAIXLNS_SERVER_TOKEN.
- Only built-in allowlisted handlers are exposed; no shell or arbitrary imports.
- SQLite queue is durable across process restarts.
- External side effects and repository writes are not implemented.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import threading
import time
import uuid
from typing import Any
from urllib.parse import urlparse

MAX_BODY_BYTES = 256 * 1024
MAX_RESULT_BYTES = 1024 * 1024
SUPPORTED_ACTIONS = {"hash_json", "echo", "tokenize"}
TERMINAL_STATES = {"COMPLETED", "FAILED", "REJECTED"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def run_builtin(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action not in SUPPORTED_ACTIONS:
        raise ValueError("ACTION_NOT_ALLOWLISTED")
    if action == "hash_json":
        return {"sha256": digest(payload), "canonical_bytes": len(canonical_json(payload).encode("utf-8"))}
    if action == "echo":
        return {"payload": payload}
    text = payload.get("text")
    if not isinstance(text, str):
        raise ValueError("tokenize requires payload.text as a string")
    import re
    tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_.:/+-]*", text.casefold())
    return {"tokens": tokens, "unique_tokens": sorted(set(tokens)), "count": len(tokens)}


class JobStore:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.session() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                idempotency_key TEXT UNIQUE,
                action TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                result_json TEXT,
                error_code TEXT
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS jobs_state_created ON jobs(state, created_at)")
            # Only built-in deterministic handlers exist; interrupted RUNNING jobs are safe to retry.
            db.execute("UPDATE jobs SET state='QUEUED', updated_at=? WHERE state='RUNNING'", (time.time(),))

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        return db

    @contextmanager
    def session(self):
        db = self.connect()
        try:
            yield db
        finally:
            db.close()

    def submit(self, action: str, payload: dict[str, Any], idempotency_key: str | None = None):
        if action not in SUPPORTED_ACTIONS:
            raise ValueError("ACTION_NOT_ALLOWLISTED")
        if not isinstance(payload, dict):
            raise ValueError("PAYLOAD_MUST_BE_OBJECT")
        encoded = canonical_json(payload)
        if len(encoded.encode("utf-8")) > MAX_BODY_BYTES:
            raise ValueError("PAYLOAD_TOO_LARGE")
        now = time.time()
        job_id = "job_" + uuid.uuid4().hex
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if idempotency_key:
                old = db.execute("SELECT * FROM jobs WHERE idempotency_key=?", (idempotency_key,)).fetchone()
                if old:
                    if old["action"] != action or old["payload_digest"] != digest(payload):
                        db.execute("ROLLBACK")
                        raise ValueError("IDEMPOTENCY_KEY_CONFLICT")
                    db.execute("COMMIT")
                    return dict(old), False
            db.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, 'QUEUED', ?, ?, NULL, NULL)",
                (job_id, idempotency_key, action, encoded, digest(payload), now, now),
            )
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            db.execute("COMMIT")
            return dict(row), True

    def claim(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE state='QUEUED' ORDER BY created_at, job_id LIMIT 1").fetchone()
            if not row:
                db.execute("COMMIT")
                return None
            now = time.time()
            db.execute("UPDATE jobs SET state='RUNNING', updated_at=? WHERE job_id=? AND state='QUEUED'", (now, row["job_id"]))
            claimed = db.execute("SELECT * FROM jobs WHERE job_id=?", (row["job_id"],)).fetchone()
            db.execute("COMMIT")
            return dict(claimed)

    def finish(self, job_id: str, state: str, result: dict[str, Any] | None = None, error_code: str | None = None):
        if state not in TERMINAL_STATES:
            raise ValueError("invalid terminal state")
        encoded = canonical_json(result) if result is not None else None
        if encoded and len(encoded.encode("utf-8")) > MAX_RESULT_BYTES:
            state, encoded, error_code = "FAILED", None, "RESULT_TOO_LARGE"
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET state=?, updated_at=?, result_json=?, error_code=? WHERE job_id=?",
                (state, time.time(), encoded, error_code, job_id),
            )

    def get(self, job_id: str):
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            return dict(row) if row else None

    def list_recent(self, limit: int = 50):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]


class Worker:
    def __init__(self, store: JobStore, poll_seconds: float = 0.15):
        self.store = store
        self.poll_seconds = poll_seconds
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, name="vaixlns-innovation-worker", daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=3)

    def run(self):
        while not self.stop_event.is_set():
            job = self.store.claim()
            if job is None:
                self.stop_event.wait(self.poll_seconds)
                continue
            try:
                payload = json.loads(job["payload_json"])
                result = run_builtin(job["action"], payload)
                self.store.finish(job["job_id"], "COMPLETED", {
                    "value": result,
                    "result_digest": digest(result),
                    "verification_state": "NOT_VERIFIED",
                    "source": "VAIXLNS_LOCAL_INNOVATION_SERVER",
                })
            except Exception as exc:
                code = str(exc) if isinstance(exc, ValueError) else "HANDLER_FAILURE"
                self.store.finish(job["job_id"], "FAILED", error_code=code)


def public_job(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": row["job_id"],
        "action": row["action"],
        "state": row["state"],
        "payload_digest": row["payload_digest"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "result": json.loads(row["result_json"]) if row.get("result_json") else None,
        "error_code": row.get("error_code"),
        "truth_boundary": "COMPLETED means handler ran; it does not mean independently verified or production-safe",
    }


def make_handler(store: JobStore, token: str | None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "VAIXLNS-Innovation-Server/0.1"

        def log_message(self, fmt, *args):
            # Avoid logging bearer tokens or arbitrary request bodies.
            print("innovation-server:", self.client_address[0], fmt % args)

        def send_json(self, status: int, value: dict[str, Any]):
            body = canonical_json(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def authorized(self):
            if not token:
                return self.client_address[0] in {"127.0.0.1", "::1"}
            supplied = self.headers.get("Authorization", "")
            expected = "Bearer " + token
            return hmac.compare_digest(supplied, expected)

        def do_GET(self):
            if not self.authorized():
                return self.send_json(401, {"error": "UNAUTHORIZED"})
            path = urlparse(self.path).path
            if path == "/health":
                return self.send_json(200, {
                    "service": "VAIXLNS Innovation Server",
                    "status": "OK",
                    "queue_backend": "SQLite WAL",
                    "actions": sorted(SUPPORTED_ACTIONS),
                    "external_effects": "DISABLED",
                })
            if path == "/v1/jobs":
                return self.send_json(200, {"jobs": [public_job(r) for r in store.list_recent()]})
            if path.startswith("/v1/jobs/"):
                row = store.get(path.rsplit("/", 1)[-1])
                return self.send_json(200, public_job(row)) if row else self.send_json(404, {"error": "JOB_NOT_FOUND"})
            return self.send_json(404, {"error": "NOT_FOUND"})

        def do_POST(self):
            if not self.authorized():
                return self.send_json(401, {"error": "UNAUTHORIZED"})
            if urlparse(self.path).path != "/v1/jobs":
                return self.send_json(404, {"error": "NOT_FOUND"})
            raw_length = self.headers.get("Content-Length", "")
            try:
                length = int(raw_length)
            except ValueError:
                return self.send_json(411, {"error": "CONTENT_LENGTH_REQUIRED"})
            if length < 0 or length > MAX_BODY_BYTES:
                return self.send_json(413, {"error": "PAYLOAD_TOO_LARGE"})
            try:
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict) or set(body) - {"action", "payload", "idempotency_key"}:
                    return self.send_json(400, {"error": "INVALID_REQUEST_SHAPE"})
                action = body.get("action")
                payload = body.get("payload", {})
                key = body.get("idempotency_key")
                if key is not None and (not isinstance(key, str) or not key.strip() or len(key) > 200):
                    return self.send_json(400, {"error": "INVALID_IDEMPOTENCY_KEY"})
                row, created = store.submit(action, payload, key)
                return self.send_json(202 if created else 200, {
                    "job": public_job(row),
                    "idempotent_replay": not created,
                })
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self.send_json(400, {"error": "INVALID_JSON"})
            except ValueError as exc:
                code = str(exc)
                status = 409 if code == "IDEMPOTENCY_KEY_CONFLICT" else 400
                return self.send_json(status, {"error": code})

    return Handler


def serve(host: str | None = None, port: int | None = None, db_path: str | None = None):
    host = host or os.getenv("VAIXLNS_SERVER_HOST", "127.0.0.1")
    port = int(port if port is not None else os.getenv("VAIXLNS_SERVER_PORT", "8765"))
    db_path = db_path or os.getenv("VAIXLNS_SERVER_DB", "./.vaixlns/innovation-jobs.sqlite3")
    token = os.getenv("VAIXLNS_SERVER_TOKEN")
    try:
        non_loopback = host not in {"127.0.0.1", "::1", "localhost"}
    except TypeError:
        non_loopback = True
    if non_loopback and (not token or len(token) < 32):
        raise RuntimeError("Non-loopback binding requires VAIXLNS_SERVER_TOKEN with at least 32 characters")
    store = JobStore(db_path)
    worker = Worker(store)
    worker.start()
    server = ThreadingHTTPServer((host, port), make_handler(store, token))
    server.daemon_threads = True
    print(f"VAIXLNS innovation server listening on {host}:{port}; external effects disabled")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        worker.stop()


if __name__ == "__main__":
    serve()
