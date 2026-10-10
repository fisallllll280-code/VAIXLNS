#!/usr/bin/env python3
"""Evidence-aware, bounded HTTP discovery for explicit VAIXLNS targets.

This tool performs GET-only checks. It does not scan subnets, follow redirects,
execute remote commands, or treat reachability as proof of service correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

DEFAULT_TIMEOUT_SECONDS = 3.0
MAX_TIMEOUT_SECONDS = 5.0
MAX_RESPONSE_BYTES = 65_536
DEFAULT_REGISTRY = (
    Path(__file__).resolve().parents[1]
    / "registry"
    / "infrastructure"
    / "SERVER_DISCOVERY_REGISTRY_V1.json"
)


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Return redirects as responses; never follow a server-provided Location."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def validate_target_url(url: str, *, allow_private_ip: bool = False) -> str:
    """Validate an explicit HTTP URL and return its normalized value.

    By default only loopback literal IPs and localhost are accepted. The LAN
    opt-in still accepts only a literal private IP; hostnames are rejected to
    avoid DNS rebinding or accidentally probing a public service.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("empty URL")
    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only explicit http(s) URLs are supported")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("credentials in URLs are forbidden")
    if parsed.query or parsed.fragment:
        raise ValueError("query strings and fragments are forbidden")

    host = parsed.hostname
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if host.lower() == "localhost":
            if allow_private_ip:
                return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))
            return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))
        raise ValueError("target must use localhost or a literal IP address") from None

    if address.is_loopback:
        pass
    elif allow_private_ip and address.is_private and not (
        address.is_multicast or address.is_unspecified or address.is_link_local
    ):
        pass
    else:
        raise ValueError("target is outside the allowed loopback/private-IP scope")

    # Force port parsing now so malformed ports are rejected before the request.
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("invalid target port") from exc
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))


def _public_target_label(url: str, *, redact: bool) -> str:
    if redact:
        return "<private-configured-endpoint>"
    parsed = urlsplit(url)
    # URL validation forbids credentials and query strings.
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))


def probe_endpoint(
    url: str,
    *,
    target_id: str,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    allow_private_ip: bool = False,
    redact_target: bool = False,
    opener_factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Perform one bounded GET and record minimal, non-content evidence."""
    timeout = min(max(float(timeout_seconds), 0.5), MAX_TIMEOUT_SECONDS)
    try:
        safe_url = validate_target_url(url, allow_private_ip=allow_private_ip)
    except (TypeError, ValueError) as exc:
        return {
            "target_id": target_id,
            "target": "<rejected>",
            "observation_status": "BLOCKED_UNSAFE_TARGET",
            "reason": str(exc),
            "healthy": False,
            "duration_ms": 0,
            "response_sha256": None,
            "response_bytes_hashed": 0,
            "response_truncated": False,
        }

    request = urllib.request.Request(
        safe_url,
        headers={"Accept": "application/json, text/plain, */*", "User-Agent": "VAIXLNS-ServerDiscovery/1.0"},
        method="GET",
    )
    make_opener = opener_factory or (lambda: urllib.request.build_opener(NoRedirectHandler()))
    started = time.monotonic()
    status_code: int | None = None
    body = b""
    failure_type: str | None = None

    try:
        with make_opener().open(request, timeout=timeout) as response:
            status_code = int(response.getcode())
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        # Redirects are intentionally surfaced here, not followed.
        status_code = int(exc.code)
        try:
            body = exc.read(MAX_RESPONSE_BYTES + 1)
        finally:
            exc.close()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", None)
        failure_type = type(reason).__name__ if reason is not None else type(exc).__name__
    except Exception as exc:  # Keep the evidence record resilient to adapter failures.
        failure_type = type(exc).__name__

    duration_ms = round((time.monotonic() - started) * 1000)
    truncated = len(body) > MAX_RESPONSE_BYTES
    bounded_body = body[:MAX_RESPONSE_BYTES]
    healthy = status_code is not None and 200 <= status_code < 300
    if status_code is not None:
        observation_status = f"HTTP_{status_code}"
    else:
        observation_status = f"UNREACHABLE_{failure_type or 'UnknownError'}"

    return {
        "target_id": target_id,
        "target": _public_target_label(safe_url, redact=redact_target),
        "observation_status": observation_status,
        "http_status": status_code,
        "healthy": healthy,
        "duration_ms": duration_ms,
        "response_sha256": hashlib.sha256(bounded_body).hexdigest() if status_code is not None else None,
        "response_bytes_hashed": len(bounded_body),
        "response_truncated": truncated,
        "evidence_scope": "single bounded GET; reachability only",
    }


def run_discovery(
    registry: dict[str, Any],
    *,
    timeout_seconds: float,
    allow_configured_lan_target: bool,
    environ: dict[str, str] | None = None,
    opener_factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    targets = registry.get("targets")
    if not isinstance(targets, list):
        raise ValueError("registry must contain a targets array")

    ids = [t.get("id") for t in targets if isinstance(t, dict)]
    if len(ids) != len(targets) or len(set(ids)) != len(ids):
        raise ValueError("every target must be an object with a unique id")

    results: list[dict[str, Any]] = []
    for target in targets:
        target_id = target["id"]
        probe = target.get("probe", {})
        if target_id == "LAN-HTTP-001":
            if not allow_configured_lan_target:
                results.append({
                    "target_id": target_id,
                    "observation_status": "SKIPPED_NEEDS_OPT_IN",
                    "healthy": False,
                    "reason": "Pass --allow-configured-lan-target and set VAIXLNS_DISCOVERY_TARGET.",
                })
                continue
            configured_url = env.get("VAIXLNS_DISCOVERY_TARGET", "").strip()
            if not configured_url:
                results.append({
                    "target_id": target_id,
                    "observation_status": "SKIPPED_NO_ENV",
                    "healthy": False,
                    "reason": "VAIXLNS_DISCOVERY_TARGET is not set.",
                })
                continue
            results.append(probe_endpoint(
                configured_url,
                target_id=target_id,
                timeout_seconds=timeout_seconds,
                allow_private_ip=True,
                redact_target=True,
                opener_factory=opener_factory,
            ))
            continue

        if not probe.get("enabled", False):
            results.append({
                "target_id": target_id,
                "observation_status": "NOT_PROBED_BY_DEFAULT",
                "healthy": False,
                "reason": probe.get("reason", "Target is inventory-only until its contract is reconciled."),
            })
            continue

        endpoint = target.get("endpoint")
        if not endpoint:
            results.append({
                "target_id": target_id,
                "observation_status": "SKIPPED_NO_ENDPOINT",
                "healthy": False,
            })
            continue

        results.append(probe_endpoint(
            endpoint,
            target_id=target_id,
            timeout_seconds=timeout_seconds,
            allow_private_ip=False,
            opener_factory=opener_factory,
        ))

    return {
        "schema_id": "VAIXLNS.SERVER_DISCOVERY_EVIDENCE",
        "schema_version": "1.0.0",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "registry_id": registry.get("schema_id"),
        "registry_version": registry.get("schema_version"),
        "policy": {
            "method": "GET_ONLY",
            "redirects_followed": False,
            "subnet_scanning": False,
            "max_timeout_seconds": MAX_TIMEOUT_SECONDS,
            "max_response_bytes_hashed": MAX_RESPONSE_BYTES,
            "private_target_opt_in": allow_configured_lan_target,
        },
        "results": results,
        "interpretation": (
            "Observations are point-in-time reachability evidence only. They do not "
            "establish identity, authorization, semantic correctness, production readiness, "
            "or permission to execute workloads."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, help="Optional local JSON evidence output path.")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--allow-configured-lan-target",
        action="store_true",
        help="Explicitly opt in to one literal private-IP URL from VAIXLNS_DISCOVERY_TARGET.",
    )
    args = parser.parse_args()

    try:
        raw_registry = args.registry.read_bytes()
        registry = json.loads(raw_registry.decode("utf-8"))
        if not isinstance(registry, dict):
            raise ValueError("registry root must be a JSON object")
        evidence = run_discovery(
            registry,
            timeout_seconds=args.timeout_seconds,
            allow_configured_lan_target=args.allow_configured_lan_target,
        )
        evidence["registry_sha256"] = hashlib.sha256(raw_registry).hexdigest()
        rendered = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
