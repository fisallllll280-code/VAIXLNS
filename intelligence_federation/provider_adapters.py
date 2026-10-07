"""Provider-neutral adapters for Ω-Arena.

The adapter boundary is intentionally small. Real provider credentials/endpoints
are environment configuration and are never stored in repository source.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Mapping
from urllib import request, error


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    display_name: str
    adapter_id: str
    adapter_version: str
    model_id: str
    capabilities: tuple[str, ...]
    sovereignty: str = "external"


@dataclass(frozen=True)
class InvocationRequest:
    invocation_id: str
    arena_id: str
    task_id: str
    input_payload: Mapping[str, Any]
    allowed_tools: tuple[str, ...] = ()
    timeout_seconds: int = 120


@dataclass(frozen=True)
class ProviderResponse:
    invocation_id: str
    status: str
    output: Any = None
    error: str | None = None
    provider_metadata: Mapping[str, Any] = None


class ProviderAdapter:
    descriptor: ProviderDescriptor

    def __init__(self, descriptor: ProviderDescriptor) -> None:
        self.descriptor = descriptor

    def discover(self) -> ProviderDescriptor:
        return self.descriptor

    def capabilities(self) -> tuple[str, ...]:
        return self.descriptor.capabilities

    def conform(self) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []
        if not self.descriptor.provider_id:
            errors.append("PROVIDER_ID_REQUIRED")
        if not self.descriptor.adapter_id:
            errors.append("ADAPTER_ID_REQUIRED")
        if not self.descriptor.adapter_version:
            errors.append("ADAPTER_VERSION_REQUIRED")
        return (not errors, tuple(errors))

    def invoke(self, request: InvocationRequest) -> ProviderResponse:
        raise NotImplementedError


class EnvironmentJSONAdapter(ProviderAdapter):
    """Optional live adapter.

    Configure:
      VAIXLNS_PROVIDER_<NORMALIZED_ID>_URL
      VAIXLNS_PROVIDER_<NORMALIZED_ID>_TOKEN (optional)

    The endpoint must accept a JSON InvocationRequest-compatible object and
    return {status, output, error?, provider_metadata?}. This adapter is not
    enabled merely by declaration; the conformance gate must pass first.
    """

    def invoke(self, invocation: InvocationRequest) -> ProviderResponse:
        normalized = self.descriptor.provider_id.upper().replace("-", "_").replace("/", "_")
        endpoint = os.getenv(f"VAIXLNS_PROVIDER_{normalized}_URL")
        if not endpoint:
            return ProviderResponse(
                invocation_id=invocation.invocation_id,
                status="UNCONFIGURED",
                error="PROVIDER_ENDPOINT_NOT_CONFIGURED",
                provider_metadata={"provider_id": self.descriptor.provider_id},
            )

        payload = json.dumps(
            {
                "invocation_id": invocation.invocation_id,
                "arena_id": invocation.arena_id,
                "task_id": invocation.task_id,
                "input_payload": invocation.input_payload,
                "allowed_tools": list(invocation.allowed_tools),
                "timeout_seconds": invocation.timeout_seconds,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        token = os.getenv(f"VAIXLNS_PROVIDER_{normalized}_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = request.Request(endpoint, data=payload, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=invocation.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
                return ProviderResponse(
                    invocation_id=invocation.invocation_id,
                    status=str(body.get("status", "UNKNOWN")),
                    output=body.get("output"),
                    error=body.get("error"),
                    provider_metadata=body.get("provider_metadata") or {},
                )
        except (error.URLError, TimeoutError, ValueError) as exc:
            return ProviderResponse(
                invocation_id=invocation.invocation_id,
                status="ERROR",
                error=f"{type(exc).__name__}:{exc}",
                provider_metadata={"provider_id": self.descriptor.provider_id},
            )


DEFAULT_PROVIDER_DESCRIPTORS = (
    ProviderDescriptor("openai", "OpenAI", "openai.environment_json", "1.0.0", "configured", ("reasoning", "coding", "analysis", "verification")),
    ProviderDescriptor("anthropic", "Claude", "anthropic.environment_json", "1.0.0", "configured", ("reasoning", "coding", "analysis", "architecture")),
    ProviderDescriptor("anthropic-code", "Claude Code", "anthropic_code.environment_json", "1.0.0", "configured", ("coding", "execution", "repair", "repository")),
    ProviderDescriptor("google", "Gemini", "google.environment_json", "1.0.0", "configured", ("reasoning", "multimodal", "research", "analysis")),
    ProviderDescriptor("xai", "Grok", "xai.environment_json", "1.0.0", "configured", ("reasoning", "exploration", "adversarial")),
    ProviderDescriptor("mistral", "Mistral", "mistral.environment_json", "1.0.0", "configured", ("reasoning", "coding", "research")),
    ProviderDescriptor("atomkit", "Atomkit", "atomkit.environment_json", "1.0.0", "service", ("product_development", "engineering", "qa", "devops")),
)


def default_adapters() -> tuple[EnvironmentJSONAdapter, ...]:
    return tuple(EnvironmentJSONAdapter(descriptor) for descriptor in DEFAULT_PROVIDER_DESCRIPTORS)
