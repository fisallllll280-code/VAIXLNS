"""Deterministic VA Genesis prototype.

This module turns one natural-language intent into a safe, dependency-free service
scaffold and four isolated operational copies. It never executes generated files.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import ipaddress
import json
import re
import shutil
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

SCHEMA_VERSION = "va.genesis.v1"
VERSION = "0.1.0"
MAX_INTENT_CHARS = 16_000
REQUIRED_FILES = (
    "README.md",
    "app.py",
    "system.json",
    "test_system.py",
    "requirements.txt",
    "Dockerfile",
    "compose.yaml",
)
COPY_ROLES = {
    "development": "LOCAL_DEVELOPMENT",
    "validation": "VALIDATION_REQUIRED",
    "release": "RELEASE_CANDIDATE_PENDING",
    "production": "PROMOTION_BLOCKED",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_files(root: Path, excluded: set[str] | None = None) -> dict[str, str]:
    excluded = excluded or set()
    result: dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative not in excluded:
            result[relative] = sha256_bytes(path.read_bytes())
    return result


def hash_digests(digests: Mapping[str, str]) -> str:
    return sha256_bytes(canonical_json(dict(sorted(digests.items()))).encode("utf-8"))


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    slug = slug[:64].rstrip("-")
    if not slug:
        raise ValueError("name must contain at least one ASCII letter or digit")
    return slug


def _system_spec(intent: str, slug: str) -> dict[str, Any]:
    identity_material = {"intent": intent, "name": slug, "schema_version": SCHEMA_VERSION}
    system_id = "VA-" + sha256_bytes(canonical_json(identity_material).encode("utf-8"))[:16]
    return {
        "schema_version": SCHEMA_VERSION,
        "system_id": system_id,
        "name": slug,
        "version": "0.1.0",
        "intent": intent,
        "status": "SPECIFIED",
        "implementation_profile": "safe-http-service-scaffold",
        "capabilities": [
            "health_endpoint",
            "system_metadata_endpoint",
            "dependency_free_runtime",
            "container_scaffold",
            "unit_test_scaffold",
            "operational_copies",
        ],
        "limitations": [
            "The first version generates a generic executable scaffold, not arbitrary business logic.",
            "External model-driven code generation is not configured by this prototype.",
            "Production admission remains blocked until runtime, security, and domain tests pass.",
        ],
        "execution_authorization": False,
        "production_admission": "BLOCKED_UNTIL_EVIDENCE_AND_APPROVAL",
    }


APP_SOURCE = '''"""Generated VA service scaffold. The user intent is data, never executable code."""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent


def load_spec() -> dict:
    with (ROOT / "system.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def response_for(path: str) -> tuple[int, dict]:
    route = urlsplit(path).path
    spec = load_spec()
    if route == "/health":
        return 200, {"status": "ok", "system_id": spec["system_id"]}
    if route == "/info":
        return 200, {
            "system_id": spec["system_id"],
            "name": spec["name"],
            "version": spec["version"],
            "status": spec["status"],
            "capabilities": spec["capabilities"],
        }
    return 404, {"error": "not_found"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        status, payload = response_for(self.path)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string: str, *args: object) -> None:
        # Keep access logging minimal; deployments should configure their own logger.
        print("%s - %s" % (self.address_string(), format_string % args))


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("VA_PORT", "8765"))
    if not 1 <= port <= 65535:
        raise ValueError("VA_PORT must be between 1 and 65535")
    server = ThreadingHTTPServer((host, port), Handler)
    print("VA service listening on %s:%s" % (host, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
'''

TEST_SOURCE = '''"""Generated smoke/unit tests for the service contract."""
import unittest

from app import response_for


class GeneratedServiceTests(unittest.TestCase):
    def test_health_contract(self):
        status, body = response_for("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertTrue(body["system_id"].startswith("VA-"))

    def test_info_contract(self):
        status, body = response_for("/info")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "SPECIFIED")
        self.assertIn("capabilities", body)

    def test_unknown_route_is_not_found(self):
        status, body = response_for("/not-a-route")
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
'''


def _render_readme(spec: Mapping[str, Any]) -> str:
    return (
        "# " + str(spec["name"]) + "\n\n"
        "Generated by VA Genesis " + VERSION + ".\n\n"
        "## Original intent\n\n"
        "The request is preserved as data in system.json. It is not executed as code.\n\n"
        "## Run locally\n\n"
        "Run: python app.py\n"
        "Health endpoint: http://127.0.0.1:8765/health\n"
        "Metadata endpoint: http://127.0.0.1:8765/info\n\n"
        "## Tests\n\n"
        "Run: python -m unittest -v test_system.py\n\n"
        "## Deployment scaffold\n\n"
        "Run: docker compose up --build\n\n"
        "## Assurance boundary\n\n"
        "Current status is SPECIFIED. This is a generic runnable scaffold, not a finished "
        "domain-specific product. Passing structural checks is not proof of production "
        "readiness. Review security, requirements, data handling, and domain behavior first.\n"
    )


def _project_files(spec: Mapping[str, Any]) -> dict[str, str]:
    return {
        "README.md": _render_readme(spec),
        "app.py": APP_SOURCE,
        "system.json": json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "test_system.py": TEST_SOURCE,
        "requirements.txt": "# Dependency-free prototype; add reviewed dependencies as required.\n",
        "Dockerfile": (
            "FROM python:3.12-slim\n"
            "ENV PYTHONDONTWRITEBYTECODE=1\n"
            "ENV PYTHONUNBUFFERED=1\n"
            "ENV HOST=0.0.0.0\n"
            "ENV VA_PORT=8765\n"
            "WORKDIR /app\n"
            "COPY app.py system.json ./\n"
            "EXPOSE 8765\n"
            'CMD ["python", "app.py"]\n'
        ),
        "compose.yaml": (
            "services:\n"
            "  va-system:\n"
            "    build: .\n"
            "    ports:\n"
            '      - "8765:8765"\n'
            "    restart: unless-stopped\n"
            "    healthcheck:\n"
            "      test: [\"CMD\", \"python\", \"-c\", \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=2)\"]\n"
            "      interval: 15s\n"
            "      timeout: 3s\n"
            "      retries: 3\n"
        ),
    }


def _write_files(root: Path, files: Mapping[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def _copy_manifest(role: str, state: str, files: Mapping[str, str], project_hash: str) -> dict[str, Any]:
    file_digests = {
        name: sha256_bytes(content.encode("utf-8"))
        for name, content in sorted(files.items())
    }
    return {
        "schema_version": "va.operational-copy.v1",
        "tool_version": VERSION,
        "role": role,
        "status": state,
        "source_project_hash": project_hash,
        "project_hash": hash_digests(file_digests),
        "files": file_digests,
        "execution_authorization": False,
        "runtime_smoke_test": "NOT_RUN",
        "production_admission": "BLOCKED_UNTIL_EVIDENCE_AND_APPROVAL",
    }


def build_system(
    intent: str,
    name: str | None = None,
    output_dir: str | Path = "generated",
) -> dict[str, Any]:
    """Generate an isolated system scaffold and four role-specific operational copies."""
    if not isinstance(intent, str) or not intent.strip():
        raise ValueError("intent must be a non-empty string")
    normalized_intent = intent.strip()
    if len(normalized_intent) > MAX_INTENT_CHARS:
        raise ValueError("intent exceeds the %d character limit" % MAX_INTENT_CHARS)

    slug = safe_slug(name if name and name.strip() else normalized_intent[:64])
    destination_root = Path(output_dir).expanduser().resolve()
    destination_root.mkdir(parents=True, exist_ok=True)
    target = destination_root / slug
    if target.exists():
        raise FileExistsError("output already exists; choose a new name or output directory: %s" % target)

    spec = _system_spec(normalized_intent, slug)
    files = _project_files(spec)
    project_digests = {
        filename: sha256_bytes(content.encode("utf-8"))
        for filename, content in sorted(files.items())
    }
    project_hash = hash_digests(project_digests)
    build_id = "VAB-" + sha256_bytes(
        canonical_json({"project_hash": project_hash, "system_id": spec["system_id"]}).encode("utf-8")
    )[:20]

    temporary = Path(tempfile.mkdtemp(prefix="." + slug + "-", dir=destination_root))
    try:
        system_dir = temporary / "system"
        system_dir.mkdir()
        _write_files(system_dir, files)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "tool_version": VERSION,
            "build_id": build_id,
            "system_id": spec["system_id"],
            "name": slug,
            "intent_sha256": sha256_bytes(normalized_intent.encode("utf-8")),
            "source_project_hash": project_hash,
            "source_files": project_digests,
            "status": "GENERATED_NOT_RUNTIME_VERIFIED",
            "execution_authorization": False,
            "production_admission": "BLOCKED_UNTIL_EVIDENCE_AND_APPROVAL",
            "operational_copy_roles": list(COPY_ROLES),
        }
        (temporary / "BUILD_MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        copies_root = temporary / "operational-copies"
        copies_root.mkdir()
        for role, state in COPY_ROLES.items():
            copy_dir = copies_root / role
            copy_dir.mkdir()
            _write_files(copy_dir, files)
            copy_manifest = _copy_manifest(role, state, files, project_hash)
            (copy_dir / "COPY_MANIFEST.json").write_text(
                json.dumps(copy_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        first_report = verify_build(temporary, write_report=False)
        if first_report["status"] != "STRUCTURAL_PASS_RUNTIME_NOT_RUN":
            raise RuntimeError("generated artifact failed structural verification: " + canonical_json(first_report))
        temporary.rename(target)
        final_report = verify_build(target, write_report=True)
        return {
            "build_id": build_id,
            "system_id": spec["system_id"],
            "name": slug,
            "path": str(target),
            "project_hash": project_hash,
            "status": manifest["status"],
            "verification": final_report,
            "operational_copies": [
                {
                    "role": role,
                    "path": str(target / "operational-copies" / role),
                    "status": COPY_ROLES[role],
                }
                for role in COPY_ROLES
            ],
        }
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
        raise


def verify_build(build_path: str | Path, write_report: bool = True) -> dict[str, Any]:
    """Verify hashes, required files, JSON contracts, and Python syntax without executing code."""
    root = Path(build_path).expanduser().resolve()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    manifest_path = root / "BUILD_MANIFEST.json"
    system_dir = root / "system"
    if not manifest_path.is_file() or not system_dir.is_dir():
        add("build_layout", False, "BUILD_MANIFEST.json and system/ are required")
        result = _verification_result(root, checks)
        if write_report and root.is_dir():
            (root / "verification-report.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return result

    try:
        build_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        add("build_manifest_json", True, "Build manifest parses as JSON")
    except (OSError, json.JSONDecodeError) as exc:
        add("build_manifest_json", False, str(exc))
        result = _verification_result(root, checks)
        if write_report and root.is_dir():
            (root / "verification-report.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return result

    actual_source_digests = digest_files(system_dir)
    expected_source_digests = build_manifest.get("source_files", {})
    add(
        "source_file_hashes",
        actual_source_digests == expected_source_digests,
        "Per-file hashes " + ("match the build manifest" if actual_source_digests == expected_source_digests else "do not match"),
    )
    actual_project_hash = hash_digests(actual_source_digests)
    add(
        "source_project_hash",
        actual_project_hash == build_manifest.get("source_project_hash"),
        "Project hash " + ("matches" if actual_project_hash == build_manifest.get("source_project_hash") else "does not match"),
    )
    add(
        "required_files",
        all((system_dir / filename).is_file() for filename in REQUIRED_FILES),
        "Required generated files are present",
    )

    try:
        spec = json.loads((system_dir / "system.json").read_text(encoding="utf-8"))
        add(
            "system_spec",
            spec.get("schema_version") == SCHEMA_VERSION and spec.get("execution_authorization") is False,
            "System specification is parseable and does not grant execution authority",
        )
    except (OSError, json.JSONDecodeError) as exc:
        add("system_spec", False, str(exc))

    for filename in ("app.py", "test_system.py"):
        try:
            ast.parse((system_dir / filename).read_text(encoding="utf-8"), filename=filename)
            add("python_syntax:" + filename, True, "Python syntax parses; code was not executed")
        except (OSError, SyntaxError) as exc:
            add("python_syntax:" + filename, False, str(exc))

    copies_root = root / "operational-copies"
    seen_roles: set[str] = set()
    for role, expected_state in COPY_ROLES.items():
        copy_dir = copies_root / role
        manifest_copy_path = copy_dir / "COPY_MANIFEST.json"
        if not copy_dir.is_dir() or not manifest_copy_path.is_file():
            add("copy:" + role, False, "Operational copy or COPY_MANIFEST.json is missing")
            continue
        try:
            copy_manifest = json.loads(manifest_copy_path.read_text(encoding="utf-8"))
            actual_copy_digests = digest_files(copy_dir, {"COPY_MANIFEST.json"})
            expected_copy_digests = copy_manifest.get("files", {})
            role_ok = (
                copy_manifest.get("role") == role
                and copy_manifest.get("status") == expected_state
                and copy_manifest.get("source_project_hash") == actual_project_hash
                and actual_copy_digests == expected_copy_digests
                and hash_digests(actual_copy_digests) == copy_manifest.get("project_hash")
                and all((copy_dir / filename).is_file() for filename in REQUIRED_FILES)
            )
            add(
                "copy:" + role,
                role_ok,
                "Copy hashes and role contract " + ("match" if role_ok else "do not match"),
            )
            seen_roles.add(role)
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            add("copy:" + role, False, str(exc))

    add("all_operational_roles", seen_roles == set(COPY_ROLES), "Expected four operational copies are present")
    result = _verification_result(root, checks)
    if write_report and root.is_dir():
        (root / "verification-report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return result


def _verification_result(root: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    all_passed = bool(checks) and all(item["passed"] for item in checks)
    return {
        "schema_version": "va.verification-report.v1",
        "build_path": str(root),
        "status": "STRUCTURAL_PASS_RUNTIME_NOT_RUN" if all_passed else "STRUCTURAL_FAILURE",
        "checks_passed": sum(1 for item in checks if item["passed"]),
        "checks_total": len(checks),
        "checks": checks,
        "runtime_execution": "NOT_RUN",
        "production_admission": "BLOCKED_UNTIL_RUNTIME_TESTS_AND_APPROVAL",
        "execution_authorization": False,
    }


def _cmd_build(args: argparse.Namespace) -> int:
    result = build_system(args.intent, name=args.name, output_dir=args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    result = verify_build(args.path, write_report=True)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "STRUCTURAL_PASS_RUNTIME_NOT_RUN" else 1


def _cmd_serve(args: argparse.Namespace) -> int:
    output_root = Path(args.output).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        server_version = "VA-Genesis/0.1"

        def _send(self, status: int, payload: Mapping[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if urlsplit(self.path).path == "/health":
                self._send(200, {"status": "ok", "service": "va-genesis", "version": VERSION})
            else:
                self._send(404, {"error": "not_found"})

        def do_POST(self) -> None:
            try:
                remote_ip = ipaddress.ip_address(self.client_address[0])
                if not remote_ip.is_loopback:
                    self._send(403, {"error": "loopback_only"})
                    return
            except ValueError:
                self._send(403, {"error": "invalid_client_address"})
                return
            if urlsplit(self.path).path != "/generate":
                self._send(404, {"error": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send(400, {"error": "invalid_content_length"})
                return
            if length <= 0 or length > MAX_INTENT_CHARS + 4096:
                self._send(413, {"error": "request_size_out_of_range"})
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send(400, {"error": "invalid_json"})
                return
            if not isinstance(payload, dict) or set(payload) - {"intent", "name"}:
                self._send(400, {"error": "allowed_fields_are_intent_and_name"})
                return
            try:
                result = build_system(
                    payload.get("intent"),
                    name=payload.get("name"),
                    output_dir=output_root,
                )
            except FileExistsError as exc:
                self._send(409, {"error": "name_conflict", "detail": str(exc)})
                return
            except ValueError as exc:
                self._send(400, {"error": "invalid_request", "detail": str(exc)})
                return
            except Exception:
                self._send(500, {"error": "generation_failed", "detail": "Inspect local service logs"})
                raise
            self._send(201, result)

        def log_message(self, format_string: str, *args: object) -> None:
            print("VA-Genesis %s - %s" % (self.address_string(), format_string % args))

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("VA Genesis listening on http://127.0.0.1:%d" % args.port)
    print("Generated projects will be written under %s" % output_root)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VA Genesis system builder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="generate a system scaffold and four operational copies")
    build_parser.add_argument("--intent", required=True, help="the single-message system request")
    build_parser.add_argument("--name", help="safe project name; derived from the intent when omitted")
    build_parser.add_argument("--output", default="generated", help="output directory (default: generated)")
    build_parser.set_defaults(handler=_cmd_build)

    verify_parser = subparsers.add_parser("verify", help="verify hashes, contracts, file layout, and syntax")
    verify_parser.add_argument("--path", required=True, help="path to a generated build")
    verify_parser.set_defaults(handler=_cmd_verify)

    serve_parser = subparsers.add_parser("serve", help="start the loopback-only local generation API")
    serve_parser.add_argument("--port", type=int, default=8765, help="local API port (default: 8765)")
    serve_parser.add_argument("--output", default="generated", help="output directory (default: generated)")
    serve_parser.set_defaults(handler=_cmd_serve)

    args = parser.parse_args(argv)
    if getattr(args, "port", 1) < 1 or getattr(args, "port", 65535) > 65535:
        parser.error("port must be between 1 and 65535")
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
