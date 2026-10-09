"""Local-only HTTP bridge for the VAIXLNS Sovereign Command Console.

Run from the repository root:
    python tools/sovereign_console/server.py

The service binds exclusively to 127.0.0.1 and exposes only allow-listed
repository operations; it is not a general-purpose shell or remote agent host.
"""
from __future__ import annotations

import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
sys.path.insert(0, str(APP_DIR))

from engine import CommandEngine  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765
MAX_BODY_BYTES = 5000
ENGINE = CommandEngine(REPO_ROOT)


class ConsoleHandler(BaseHTTPRequestHandler):
    server_version = "VAIXLNS-Console/1.0"
    sys_version = ""

    def log_message(self, fmt: str, *args: object) -> None:
        # Do not log command bodies or user-entered task text.
        print(f"[console] {self.address_string()} - {fmt % args}")

    def _headers(self, content_type: str, length: int | None = None) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:")
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.end_headers()

    def _json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            file_path = APP_DIR / "index.html"
            if not file_path.is_file():
                self._json(404, {"error": "console_ui_missing"})
                return
            body = file_path.read_bytes()
            self._headers("text/html; charset=utf-8", len(body))
            self.wfile.write(body)
            return
        if path == "/api/state":
            self._json(200, ENGINE.state())
            return
        if path == "/api/history":
            result = ENGINE.execute("history")
            self._json(200, result)
            return
        self._json(404, {"error": "not_found", "available": ["/", "/api/state", "/api/history"]})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/command":
            self._json(404, {"error": "not_found"})
            return

        origin = self.headers.get("Origin")
        allowed_origins = {f"http://{HOST}:{PORT}", f"http://localhost:{PORT}"}
        if origin and origin not in allowed_origins:
            self._json(403, {"error": "origin_rejected"})
            return

        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "application_json_required"})
            return
        raw_length = self.headers.get("Content-Length", "")
        try:
            length = int(raw_length)
        except ValueError:
            self._json(411, {"error": "content_length_required"})
            return
        if length < 1 or length > MAX_BODY_BYTES:
            self._json(413, {"error": "request_body_too_large_or_empty", "max_bytes": MAX_BODY_BYTES})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"error": "invalid_json"})
            return
        command = payload.get("command") if isinstance(payload, dict) else None
        if not isinstance(command, str):
            self._json(400, {"error": "command_must_be_a_string"})
            return
        self._json(200, ENGINE.execute(command))


def main() -> None:
    try:
        server = ThreadingHTTPServer((HOST, PORT), ConsoleHandler)
    except OSError as exc:
        raise SystemExit(
            f"Cannot bind {HOST}:{PORT}: {exc}\n"
            f"Choose a free local port by editing PORT in {Path(__file__).name}."
        ) from exc
    print("VAIXLNS Sovereign Command Console")
    print(f"Repository: {REPO_ROOT}")
    print(f"Local URL:  http://{HOST}:{PORT}")
    print("Security:   loopback only; allow-listed commands; no shell endpoint")
    print("Stop with Ctrl+C. This process-local session log is not a durable ledger.")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nStopping local console.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
