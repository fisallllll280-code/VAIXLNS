#!/usr/bin/env python3
"""Fail-closed ARC-X -> VX engineering-task bridge client.

No network activity occurs at import time. Remote submission is explicit and
requires an operator-configured endpoint, bearer token, request-signing key,
and independent receipt-verification key. This client does not confer runtime
admission: the remote server must revalidate policy and authorization.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import ipaddress
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "arcx-vx-engineering-task.schema.json"
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
MAX_TASK_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 5
RECEIPT_STATES = {
    "RECEIVED", "QUEUED", "PENDING_VERIFICATION", "BLOCKED", "REJECTED"
}


class BridgeError(ValueError):
    """Raised for unsafe configuration or protocol violations."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _signature(payload: dict[str, Any], key: bytes) -> str:
    unsigned = dict(payload)
    unsigned.pop("signature", None)
    unsigned.pop("response_signature", None)
    return hmac.new(key, canonical_json(unsigned), hashlib.sha256).hexdigest()


def validate_task(task: Any) -> list[str]:
    """Check safety-critical invariants before network access.

    Full JSON Schema validation and policy evaluation remain responsibilities of
    the receiving service. A successful preflight is not authorization.
    """
    if not isinstance(task, dict):
        return ["TASK_MUST_BE_JSON_OBJECT"]

    errors: list[str] = []
    required = {
        "schema_version", "task_id", "idempotency_key", "created_at",
        "source_revision", "input_artifacts", "eir_ref", "memory_context", "domain", "operation",
        "required_capabilities", "assumptions", "constraints", "proof_obligations",
        "verification_profile", "resource_request", "security", "reproducibility",
        "execution_mode", "policy_version", "authorization_ref", "lineage",
    }
    missing = sorted(required - set(task))
    if missing:
        errors.append("MISSING_REQUIRED_FIELDS:" + ",".join(missing))
        return errors

    if task["schema_version"] != "1.0":
        errors.append("UNSUPPORTED_SCHEMA_VERSION")
    if not isinstance(task["task_id"], str) or not task["task_id"].strip():
        errors.append("INVALID_TASK_ID")
    if not isinstance(task["idempotency_key"], str) or len(task["idempotency_key"]) < 16:
        errors.append("INVALID_IDEMPOTENCY_KEY")
    if not isinstance(task["source_revision"], str) or not task["source_revision"].strip():
        errors.append("MISSING_SOURCE_REVISION")
    if not isinstance(task["eir_ref"], str) or not task["eir_ref"].strip():
        errors.append("MISSING_EIR_REFERENCE")

    memory = task["memory_context"]
    if not isinstance(memory, dict):
        errors.append("MEMORY_CONTEXT_REQUIRED")
    else:
        coverage = memory.get("coverage_state")
        if not isinstance(coverage, str) or coverage not in {"COMPLETE_FOR_SCOPE", "PARTIAL", "NONE", "CONFLICT"}:
            errors.append("INVALID_MEMORY_COVERAGE_STATE")
        if not isinstance(memory.get("query_ref"), str) or not memory.get("query_ref", "").strip():
            errors.append("MEMORY_QUERY_REFERENCE_REQUIRED")
        if not isinstance(memory.get("rationale"), str) or not memory.get("rationale", "").strip():
            errors.append("MEMORY_COVERAGE_RATIONALE_REQUIRED")
        refs = memory.get("record_refs")
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            errors.append("INVALID_MEMORY_RECORD_REFERENCES")
        if coverage == "COMPLETE_FOR_SCOPE":
            if not isinstance(refs, list) or not refs:
                errors.append("COMPLETE_MEMORY_SCOPE_REQUIRES_RECORDS")
            if not isinstance(memory.get("index_revision"), str) or not memory.get("index_revision", "").strip():
                errors.append("COMPLETE_MEMORY_SCOPE_REQUIRES_INDEX_REVISION")
            if not isinstance(memory.get("retrieval_receipt_ref"), str) or not memory.get("retrieval_receipt_ref", "").strip():
                errors.append("COMPLETE_MEMORY_SCOPE_REQUIRES_RETRIEVAL_RECEIPT")
            if memory.get("uncovered_scopes") != []:
                errors.append("COMPLETE_MEMORY_SCOPE_CANNOT_HIDE_UNCOVERED_SCOPES")

    if not isinstance(task["policy_version"], str) or not task["policy_version"].strip():
        errors.append("MISSING_POLICY_VERSION")

    artifacts = task["input_artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("INPUT_ARTIFACTS_REQUIRED")
    else:
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"INVALID_ARTIFACT:{index}")
                continue
            digest = artifact.get("sha256")
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                errors.append(f"INVALID_ARTIFACT_DIGEST:{index}")
            trust_state = artifact.get("trust_state")
            if not isinstance(trust_state, str) or trust_state not in {
                "UNTRUSTED", "SCREENED", "TRUSTED_FOR_DECLARED_USE"
            }:
                errors.append(f"INVALID_ARTIFACT_TRUST_STATE:{index}")

    capabilities = task["required_capabilities"]
    if not isinstance(capabilities, list) or not capabilities or any(
        not isinstance(item, str) or not item.strip() for item in capabilities
    ):
        errors.append("REQUIRED_CAPABILITIES_INVALID")

    obligations = task["proof_obligations"]
    if not isinstance(obligations, list) or not obligations:
        errors.append("PROOF_OBLIGATIONS_REQUIRED")

    profile = task["verification_profile"]
    if not isinstance(profile, dict) or profile.get("fail_closed") is not True:
        errors.append("FAIL_CLOSED_VERIFICATION_PROFILE_REQUIRED")

    security = task["security"]
    if not isinstance(security, dict):
        errors.append("SECURITY_CONTRACT_REQUIRED")
    elif security.get("external_side_effects_allowed") is not False:
        errors.append("EXTERNAL_SIDE_EFFECTS_MUST_BE_DISABLED")

    mode = task["execution_mode"]
    if not isinstance(mode, str) or mode not in {"ANALYZE", "SIMULATE", "TEST", "EXECUTE"}:
        errors.append("INVALID_EXECUTION_MODE")
    if mode == "EXECUTE" and not (
        isinstance(task["authorization_ref"], str)
        and task["authorization_ref"].strip()
    ):
        errors.append("EXECUTE_REQUIRES_AUTHORIZATION_REFERENCE")
    if task["domain"] == "PHYSICS_SIMULATION" and mode == "EXECUTE":
        errors.append("PHYSICS_ACTUATION_NOT_ALLOWED_BY_BRIDGE_CLIENT")

    resource = task["resource_request"]
    if not isinstance(resource, dict):
        errors.append("RESOURCE_REQUEST_REQUIRED")
    else:
        if not isinstance(resource.get("wall_time_seconds"), int) or resource["wall_time_seconds"] < 1:
            errors.append("INVALID_WALL_TIME")
        attempts = resource.get("max_attempts")
        if not isinstance(attempts, int) or not 1 <= attempts <= 5:
            errors.append("INVALID_MAX_ATTEMPTS")

    if not isinstance(task["lineage"], dict):
        errors.append("LINEAGE_REQUIRED")
    return errors


def load_task(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BridgeError(f"cannot read task file: {exc}") from exc
    if len(raw) > MAX_TASK_BYTES:
        raise BridgeError("task file exceeds maximum allowed size")
    try:
        task = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BridgeError(f"task file is not valid UTF-8 JSON: {exc}") from exc
    errors = validate_task(task)
    if errors:
        raise BridgeError("task preflight failed: " + "; ".join(errors))
    return task


def _secret(name: str, minimum_length: int = 32) -> bytes:
    value = os.getenv(name, "")
    if len(value.encode("utf-8")) < minimum_length:
        raise BridgeError(f"{name} must be configured and at least {minimum_length} bytes")
    return value.encode("utf-8")


def _configured_endpoint() -> str:
    raw = os.getenv("VX_ENGINEERING_SERVER_URL", "").strip()
    if not raw:
        raise BridgeError("VX_ENGINEERING_SERVER_URL is required for remote submission")
    try:
        parsed = urlsplit(raw)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        raise BridgeError("endpoint URL is malformed") from exc
    if parsed.scheme not in {"https", "http"} or not hostname:
        raise BridgeError("endpoint must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise BridgeError("endpoint must not contain credentials, query, or fragment")

    host = hostname.lower()
    loopback = host == "localhost"
    try:
        loopback = loopback or ipaddress.ip_address(host).is_loopback
    except ValueError:
        pass

    if parsed.scheme != "https":
        if not loopback or os.getenv("VX_ENGINEERING_ALLOW_INSECURE_LOOPBACK") != "true":
            raise BridgeError("HTTPS is required; HTTP is permitted only for explicitly enabled loopback tests")
    return raw.rstrip("/")


def build_envelope(task: dict[str, Any], signing_key: bytes) -> dict[str, Any]:
    digest = sha256_hex(canonical_json(task))
    envelope: dict[str, Any] = {
        "protocol_version": "arcx-vx-task-envelope.v1",
        "task_id": task["task_id"],
        "idempotency_key": task["idempotency_key"],
        "task_digest": digest,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task": task,
    }
    envelope["signature"] = hmac.new(
        signing_key, canonical_json(envelope), hashlib.sha256
    ).hexdigest()
    return envelope


def verify_receipt(
    receipt: Any,
    *,
    expected_task_id: str,
    expected_task_digest: str,
    receipt_key: bytes,
) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise BridgeError("server receipt must be a JSON object")
    required = {"receipt_id", "task_id", "task_digest", "status", "issued_at", "response_signature"}
    missing = sorted(required - set(receipt))
    if missing:
        raise BridgeError("receipt missing fields: " + ", ".join(missing))
    if receipt["task_id"] != expected_task_id:
        raise BridgeError("receipt task_id mismatch")
    if receipt["task_digest"] != expected_task_digest:
        raise BridgeError("receipt task digest mismatch")
    status = receipt["status"]
    if not isinstance(status, str) or status not in RECEIPT_STATES:
        raise BridgeError("receipt contains an unrecognized lifecycle state")

    unsigned = dict(receipt)
    actual = unsigned.pop("response_signature")
    expected = hmac.new(receipt_key, canonical_json(unsigned), hashlib.sha256).hexdigest()
    if not isinstance(actual, str) or not hmac.compare_digest(actual, expected):
        raise BridgeError("receipt signature verification failed")
    return receipt


def _request_json(url: str, *, method: str, payload: dict[str, Any] | None,
                  bearer_token: str, timeout: float) -> dict[str, Any]:
    body = canonical_json(payload) if payload is not None else None
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer " + bearer_token,
        "User-Agent": "VAIXLNS-ARCX-VX-Bridge/1.0",
    }
    if body is not None:
        if len(body) > MAX_TASK_BYTES:
            raise BridgeError("request exceeds maximum allowed size")
        headers["Content-Type"] = "application/json"
        headers["Content-Digest"] = "sha-256=:" + base64.b64encode(
            hashlib.sha256(body).digest()
        ).decode("ascii") + ":"
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        # Do not print response bodies; servers may include sensitive diagnostics.
        raise BridgeError(f"server returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise BridgeError(f"server request failed: {type(exc).__name__}") from exc

    if len(raw) > MAX_RESPONSE_BYTES:
        raise BridgeError("server response exceeds maximum allowed size")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BridgeError("server returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise BridgeError("server response must be a JSON object")
    return value


def submit_task(task: dict[str, Any], *, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    endpoint = _configured_endpoint()
    token = os.getenv("VX_ENGINEERING_BEARER_TOKEN", "")
    if not token:
        raise BridgeError("VX_ENGINEERING_BEARER_TOKEN is required")
    try:
        token.encode("ascii")
    except UnicodeEncodeError as exc:
        raise BridgeError("bearer token must be ASCII") from exc
    if any(ord(char) <= 32 or ord(char) == 127 for char in token):
        raise BridgeError("bearer token contains whitespace or control characters")
    request_key = _secret("VX_ENGINEERING_REQUEST_SIGNING_KEY")
    receipt_key = _secret("VX_ENGINEERING_RECEIPT_SIGNING_KEY")
    if hmac.compare_digest(request_key, receipt_key):
        raise BridgeError("request-signing and receipt-verification keys must be different")

    envelope = build_envelope(task, request_key)
    task_digest = envelope["task_digest"]
    response = _request_json(
        endpoint + "/v1/engineering/tasks",
        method="POST",
        payload=envelope,
        bearer_token=token,
        timeout=timeout,
    )
    receipt = verify_receipt(
        response,
        expected_task_id=task["task_id"],
        expected_task_digest=task_digest,
        receipt_key=receipt_key,
    )
    # A signed receipt acknowledges the state shown; it is not proof of correctness
    # and cannot by itself set a canonical/verified state.
    return {
        "task_id": task["task_id"],
        "task_digest": task_digest,
        "receipt_id": receipt["receipt_id"],
        "server_status": receipt["status"],
        "semantic_verification": "NOT_ESTABLISHED_BY_SUBMISSION_RECEIPT",
        "canonical_admission": "NOT_GRANTED_BY_BRIDGE_CLIENT",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ARC-X to VX engineering task bridge")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="preflight a task without network access")
    validate_parser.add_argument("task_file", type=Path)
    submit_parser = subparsers.add_parser("submit", help="submit an explicitly authorized task to a configured server")
    submit_parser.add_argument("task_file", type=Path)
    submit_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)

    try:
        task = load_task(args.task_file)
        if args.command == "validate":
            print(json.dumps({
                "task_id": task["task_id"],
                "preflight": "PASS",
                "network_used": False,
                "authorization": "NOT_GRANTED_BY_PREFLIGHT",
            }, sort_keys=True))
            return 0
        if args.timeout <= 0 or args.timeout > 60:
            raise BridgeError("timeout must be between 0 and 60 seconds")
        result = submit_task(task, timeout=args.timeout)
        print(json.dumps(result, sort_keys=True))
        return 0
    except BridgeError as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
