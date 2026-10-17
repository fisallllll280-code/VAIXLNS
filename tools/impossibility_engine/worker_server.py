"""Typed Ω worker endpoint. Loopback by default; external binding requires bearer auth."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac, ipaddress, json, os
from typing import Any
from .engine import assess
from .fabric import canonical_hash

MAX_REQUEST_BYTES = 1024 * 1024

def _loopback(host: str) -> bool:
    if host.lower() == "localhost": return True
    try: return ipaddress.ip_address(host).is_loopback
    except ValueError: return False

def make_handler(worker_id: str, token: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "OmegaWorker/0.1"
        sys_version = ""
        def reply(self, status: int, value: dict[str, Any]) -> None:
            body = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self) -> None:
            if self.path != "/healthz": self.reply(404, {"error": "not_found"}); return
            self.reply(200, {"status": "ok", "worker_id": worker_id, "capability": "omega.assess.v1"})
        def do_POST(self) -> None:
            if self.path != "/v1/assess": self.reply(404, {"error": "not_found"}); return
            if token and not hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {token}"):
                self.reply(401, {"error": "unauthorized"}); return
            if self.headers.get_content_type() != "application/json":
                self.reply(415, {"error": "application_json_required"}); return
            try: size = int(self.headers.get("Content-Length", "0"))
            except ValueError: self.reply(400, {"error": "invalid_content_length"}); return
            if size <= 0 or size > MAX_REQUEST_BYTES:
                self.reply(413, {"error": "request_size_out_of_bounds"}); return
            try:
                request = json.loads(self.rfile.read(size).decode("utf-8"))
                if not isinstance(request, dict): raise ValueError("request must be an object")
                task_id, problem, request_hash = request.get("task_id"), request.get("problem"), request.get("request_sha256")
                if not isinstance(task_id, str) or not task_id.startswith("omega-"): raise ValueError("invalid task_id")
                if not isinstance(problem, dict): raise ValueError("problem must be an object")
                actual = canonical_hash(problem)
                if not isinstance(request_hash, str) or not hmac.compare_digest(actual, request_hash):
                    self.reply(400, {"error": "request_fingerprint_mismatch"}); return
                self.reply(200, {"task_id": task_id, "request_sha256": actual, "worker_id": worker_id,
                                 "result": assess(problem)})
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                self.reply(400, {"error": str(exc)[:300]})
        def log_message(self, fmt: str, *args: Any) -> None: return
    return Handler

def serve(host: str = "127.0.0.1", port: int = 8787, *, token_env: str = "OMEGA_WORKER_TOKEN",
          worker_id: str = "omega-worker-local") -> None:
    if not 1 <= int(port) <= 65535: raise ValueError("port must be between 1 and 65535")
    if not worker_id or len(worker_id) > 64: raise ValueError("worker_id must be 1-64 characters")
    token = os.environ.get(token_env, "")
    if not _loopback(host) and not token:
        raise ValueError(f"set {token_env} before binding to a non-loopback interface")
    server = ThreadingHTTPServer((host, int(port)), make_handler(worker_id, token))
    try:
        print(f"Ω worker {worker_id} listening on {host}:{port}; capability=omega.assess.v1")
        server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run a bounded Ω assessment worker.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--worker-id", default="omega-worker-local")
    parser.add_argument("--token-env", default="OMEGA_WORKER_TOKEN")
    args = parser.parse_args()
    serve(args.host, args.port, token_env=args.token_env, worker_id=args.worker_id)
