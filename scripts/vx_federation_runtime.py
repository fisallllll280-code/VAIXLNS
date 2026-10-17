#!/usr/bin/env python3
"""Fail-closed VX model federation runtime (standard library only).

This module provides deterministic connector selection, policy enforcement,
redacted evidence receipts, and explicit provider adapters. It does not activate
a connector merely because it is listed or has credentials configured.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

ACTIVE_STATE = "ACTIVE_VERIFIED"
DATA_CLASSES = ("PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Connector:
    connector_id: str
    provider: str
    model: str
    adapter: str
    status: str
    capabilities: frozenset[str]
    allowed_data_classes: frozenset[str]
    api_key_env: str | None = None
    base_url: str | None = None
    contract_digest: str = "UNVERIFIED"
    evidence_ref: str | None = None
    max_output_tokens: int = 4096
    timeout_seconds: float = 30.0

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Connector":
        return cls(
            connector_id=str(value["connector_id"]),
            provider=str(value["provider"]),
            model=str(value["model"]),
            adapter=str(value["adapter"]),
            status=str(value.get("status", "NOT_CONFIGURED")),
            capabilities=frozenset(value.get("capabilities", [])),
            allowed_data_classes=frozenset(value.get("allowed_data_classes", ["PUBLIC"])),
            api_key_env=value.get("api_key_env"),
            base_url=value.get("base_url"),
            contract_digest=str(value.get("contract_digest", "UNVERIFIED")),
            evidence_ref=value.get("evidence_ref"),
            max_output_tokens=int(value.get("max_output_tokens", 4096)),
            timeout_seconds=float(value.get("timeout_seconds", 30.0)),
        )


@dataclass(frozen=True)
class TaskRequest:
    messages: tuple[dict[str, str], ...]
    required_capabilities: frozenset[str] = frozenset({"chat"})
    data_classification: str = "PUBLIC"
    allowed_providers: frozenset[str] = frozenset()
    max_output_tokens: int = 1024
    timeout_seconds: float = 30.0
    tenant_id: str = "default"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if self.data_classification not in DATA_CLASSES:
            raise ValueError("invalid data_classification")
        if not self.messages:
            raise ValueError("messages must not be empty")
        if self.max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        for message in self.messages:
            if set(message) - {"role", "content"} or not message.get("role") or not isinstance(message.get("content"), str):
                raise ValueError("messages must contain only role and string content")


@dataclass(frozen=True)
class Policy:
    allowed_providers: frozenset[str]
    allowed_data_classes: frozenset[str] = frozenset({"PUBLIC"})
    max_output_tokens: int = 4096
    max_timeout_seconds: float = 60.0
    require_fresh_evidence: bool = True


@dataclass(frozen=True)
class RouteDecision:
    request_id: str
    selected_connector_id: str | None
    eligible_connector_ids: tuple[str, ...]
    exclusions: tuple[dict[str, str], ...]
    policy_digest: str
    outcome: str


@dataclass(frozen=True)
class EvidenceReceipt:
    receipt_id: str
    request_id: str
    connector_id: str
    provider: str
    model: str
    outcome: str
    started_at_unix: float
    duration_ms: int
    policy_digest: str
    contract_digest: str
    input_digest: str
    output_digest: str | None
    error_code: str | None
    evidence_digest: str


class Adapter(Protocol):
    def complete(self, connector: Connector, request: TaskRequest) -> dict[str, Any]: ...


class ConnectorError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class OpenAICompatibleAdapter:
    """Adapter for OpenAI Chat Completions-compatible endpoints (including Ollama)."""

    def __init__(self, *, local_no_auth: bool = False):
        self.local_no_auth = local_no_auth

    def complete(self, connector: Connector, request: TaskRequest) -> dict[str, Any]:
        if not connector.base_url:
            raise ConnectorError("CONNECTOR_MISCONFIGURED", "base_url is required")
        key = os.environ.get(connector.api_key_env, "") if connector.api_key_env else ""
        if connector.api_key_env and not key:
            raise ConnectorError("CREDENTIAL_MISSING", "required credential is not configured")
        if not connector.api_key_env and not self.local_no_auth:
            raise ConnectorError("CREDENTIAL_POLICY_MISSING", "no-auth is allowed only for explicitly local adapters")

        payload = {
            "model": connector.model,
            "messages": list(request.messages),
            "max_tokens": min(request.max_output_tokens, connector.max_output_tokens),
        }
        raw = canonical_json(payload).encode("utf-8")
        url = connector.base_url.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if key:
            headers["Authorization"] = "Bearer " + key
        http_request = urllib.request.Request(url, data=raw, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(http_request, timeout=min(request.timeout_seconds, connector.timeout_seconds)) as response:
                if response.status < 200 or response.status >= 300:
                    raise ConnectorError("HTTP_STATUS", f"provider returned HTTP {response.status}")
                body = response.read(8 * 1024 * 1024 + 1)
                if len(body) > 8 * 1024 * 1024:
                    raise ConnectorError("RESPONSE_TOO_LARGE", "provider response exceeded 8 MiB")
        except urllib.error.HTTPError as exc:
            code = "RATE_LIMITED" if exc.code == 429 else "AUTH_FAILED" if exc.code in (401, 403) else "HTTP_ERROR"
            raise ConnectorError(code, f"provider returned HTTP {exc.code}") from None
        except TimeoutError:
            raise ConnectorError("TIMEOUT", "provider request timed out") from None
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, TimeoutError):
                raise ConnectorError("TIMEOUT", "provider request timed out") from None
            raise ConnectorError("PROVIDER_UNAVAILABLE", "provider endpoint could not be reached") from None
        try:
            parsed = json.loads(body.decode("utf-8"))
            choices = parsed["choices"]
            text = choices[0]["message"]["content"]
            if not isinstance(text, str):
                raise ValueError("content must be text")
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
            raise ConnectorError("MALFORMED_RESPONSE", "provider response did not match the expected schema") from None
        return {"text": text, "provider_response_id": parsed.get("id"), "model": parsed.get("model", connector.model)}


class AnthropicMessagesAdapter:
    """Minimal Anthropic Messages API adapter; credentials remain environment-only."""

    def complete(self, connector: Connector, request: TaskRequest) -> dict[str, Any]:
        if not connector.base_url:
            raise ConnectorError("CONNECTOR_MISCONFIGURED", "base_url is required")
        key = os.environ.get(connector.api_key_env, "") if connector.api_key_env else ""
        if not key:
            raise ConnectorError("CREDENTIAL_MISSING", "required credential is not configured")
        system_parts = [m["content"] for m in request.messages if m["role"] == "system"]
        messages = [{"role": m["role"], "content": m["content"]} for m in request.messages if m["role"] != "system"]
        if not messages:
            raise ConnectorError("INVALID_REQUEST", "at least one non-system message is required")
        payload = {"model": connector.model, "max_tokens": min(request.max_output_tokens, connector.max_output_tokens), "messages": messages}
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        http_request = urllib.request.Request(
            connector.base_url.rstrip("/") + "/v1/messages",
            data=canonical_json(payload).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=min(request.timeout_seconds, connector.timeout_seconds)) as response:
                body = response.read(8 * 1024 * 1024 + 1)
                if len(body) > 8 * 1024 * 1024:
                    raise ConnectorError("RESPONSE_TOO_LARGE", "provider response exceeded 8 MiB")
        except urllib.error.HTTPError as exc:
            code = "RATE_LIMITED" if exc.code == 429 else "AUTH_FAILED" if exc.code in (401, 403) else "HTTP_ERROR"
            raise ConnectorError(code, f"provider returned HTTP {exc.code}") from None
        except (TimeoutError, urllib.error.URLError):
            raise ConnectorError("PROVIDER_UNAVAILABLE", "provider endpoint could not be reached or timed out") from None
        try:
            parsed = json.loads(body.decode("utf-8"))
            text = "".join(item["text"] for item in parsed["content"] if item.get("type") == "text")
            if not text:
                raise ValueError("empty text")
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            raise ConnectorError("MALFORMED_RESPONSE", "provider response did not match the expected schema") from None
        return {"text": text, "provider_response_id": parsed.get("id"), "model": parsed.get("model", connector.model)}


class FederationRouter:
    def __init__(self, connectors: list[Connector], policy: Policy, adapters: dict[str, Adapter]):
        ids = [item.connector_id for item in connectors]
        if len(ids) != len(set(ids)):
            raise ValueError("connector_id values must be unique")
        self.connectors = tuple(connectors)
        self.policy = policy
        self.adapters = adapters
        self.policy_digest = digest({
            "allowed_providers": sorted(policy.allowed_providers),
            "allowed_data_classes": sorted(policy.allowed_data_classes),
            "max_output_tokens": policy.max_output_tokens,
            "max_timeout_seconds": policy.max_timeout_seconds,
            "require_fresh_evidence": policy.require_fresh_evidence,
        })

    def decide(self, request: TaskRequest) -> RouteDecision:
        exclusions: list[dict[str, str]] = []
        eligible: list[Connector] = []
        if request.data_classification not in self.policy.allowed_data_classes:
            return RouteDecision(request.request_id, None, (), ({"connector_id": "*", "reason": "DATA_CLASS_BLOCKED"},), self.policy_digest, "BLOCKED_POLICY")
        if request.max_output_tokens > self.policy.max_output_tokens or request.timeout_seconds > self.policy.max_timeout_seconds:
            return RouteDecision(request.request_id, None, (), ({"connector_id": "*", "reason": "BUDGET_EXCEEDED"},), self.policy_digest, "BLOCKED_BUDGET")
        for connector in self.connectors:
            reason = None
            if connector.status != ACTIVE_STATE:
                reason = "CONNECTOR_NOT_ACTIVE_VERIFIED"
            elif connector.provider not in self.policy.allowed_providers:
                reason = "PROVIDER_NOT_ALLOWED_BY_POLICY"
            elif request.allowed_providers and connector.provider not in request.allowed_providers:
                reason = "PROVIDER_NOT_ALLOWED_BY_REQUEST"
            elif request.data_classification not in connector.allowed_data_classes:
                reason = "DATA_CLASS_NOT_ALLOWED_BY_CONNECTOR"
            elif not request.required_capabilities.issubset(connector.capabilities):
                reason = "REQUIRED_CAPABILITY_MISSING"
            elif connector.adapter not in self.adapters:
                reason = "ADAPTER_NOT_INSTALLED"
            elif self.policy.require_fresh_evidence and (not connector.evidence_ref or connector.contract_digest == "UNVERIFIED"):
                reason = "FRESH_EVIDENCE_MISSING"
            elif connector.api_key_env and not os.environ.get(connector.api_key_env):
                reason = "CREDENTIAL_MISSING"
            if reason:
                exclusions.append({"connector_id": connector.connector_id, "reason": reason})
            else:
                eligible.append(connector)
        eligible.sort(key=lambda item: (item.provider, item.model, item.connector_id))
        selected = eligible[0] if eligible else None
        return RouteDecision(
            request_id=request.request_id,
            selected_connector_id=selected.connector_id if selected else None,
            eligible_connector_ids=tuple(item.connector_id for item in eligible),
            exclusions=tuple(exclusions),
            policy_digest=self.policy_digest,
            outcome="ROUTED" if selected else "NO_ELIGIBLE_CONNECTOR",
        )

    def execute(self, request: TaskRequest) -> tuple[dict[str, Any] | None, EvidenceReceipt, RouteDecision]:
        decision = self.decide(request)
        started = time.time()
        started_perf = time.monotonic()
        input_digest = sha256_text(canonical_json({"messages": list(request.messages), "tenant_id": request.tenant_id}))
        if not decision.selected_connector_id:
            receipt = self._receipt(request, None, "BLOCKED", started, started_perf, input_digest, None, decision.policy_digest, "NO_ELIGIBLE_CONNECTOR")
            return None, receipt, decision
        connector = next(item for item in self.connectors if item.connector_id == decision.selected_connector_id)
        try:
            response = self.adapters[connector.adapter].complete(connector, request)
            if not isinstance(response, dict) or not isinstance(response.get("text"), str):
                raise ConnectorError("MALFORMED_RESPONSE", "adapter returned invalid response")
            output_digest = sha256_text(response["text"])
            receipt = self._receipt(request, connector, "SUCCESS", started, started_perf, input_digest, output_digest, decision.policy_digest, None)
            return response, receipt, decision
        except ConnectorError as exc:
            receipt = self._receipt(request, connector, "FAILED", started, started_perf, input_digest, None, decision.policy_digest, exc.code)
            return None, receipt, decision

    def _receipt(self, request: TaskRequest, connector: Connector | None, outcome: str, started: float,
                 started_perf: float, input_digest: str, output_digest: str | None, policy_digest: str,
                 error_code: str | None) -> EvidenceReceipt:
        base = {
            "request_id": request.request_id,
            "connector_id": connector.connector_id if connector else None,
            "provider": connector.provider if connector else None,
            "model": connector.model if connector else None,
            "outcome": outcome,
            "started_at_unix": started,
            "duration_ms": int((time.monotonic() - started_perf) * 1000),
            "policy_digest": policy_digest,
            "contract_digest": connector.contract_digest if connector else "UNAVAILABLE",
            "input_digest": input_digest,
            "output_digest": output_digest,
            "error_code": error_code,
        }
        return EvidenceReceipt(
            receipt_id=str(uuid.uuid4()),
            request_id=request.request_id,
            connector_id=base["connector_id"] or "NONE",
            provider=base["provider"] or "NONE",
            model=base["model"] or "NONE",
            outcome=outcome,
            started_at_unix=started,
            duration_ms=base["duration_ms"],
            policy_digest=policy_digest,
            contract_digest=base["contract_digest"],
            input_digest=input_digest,
            output_digest=output_digest,
            error_code=error_code,
            evidence_digest=digest(base),
        )


def load_registry(path: str) -> list[Connector]:
    with open(path, "r", encoding="utf-8") as stream:
        data = json.load(stream)
    if data.get("schema_version") != "vx-model-connector-registry-v1":
        raise ValueError("unsupported connector registry schema")
    raw = data.get("connectors")
    if not isinstance(raw, list):
        raise ValueError("registry connectors must be a list")
    return [Connector.from_mapping(item) for item in raw]


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="registry/federation/vx_model_connectors.v1.json")
    parser.add_argument("--check", action="store_true", help="validate registry structure without network access")
    args = parser.parse_args()
    try:
        connectors = load_registry(args.registry)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, ensure_ascii=False))
        return 2
    ids = [item.connector_id for item in connectors]
    if len(ids) != len(set(ids)):
        print(json.dumps({"status": "INVALID", "error": "duplicate connector_id"}))
        return 2
    active = [item.connector_id for item in connectors if item.status == ACTIVE_STATE]
    print(json.dumps({
        "status": "VALID" if args.check else "PREFLIGHT_ONLY",
        "connectors_total": len(connectors),
        "active_verified_connectors": active,
        "network_probes_performed": False,
        "tasks_executed": False,
        "note": "Registry validation is not a connectivity or runtime-health test."
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
