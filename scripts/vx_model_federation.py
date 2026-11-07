#!/usr/bin/env python3
"""Bounded multi-provider VX model federation client.

Calls vendor APIs only when explicitly run. API credentials are read from the
process environment and are never written to reports. Results are proposals,
not authority to change canonical repository state.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "registry/models/vx-frontier-model-registry.json"
MAX_PARALLELISM = 5
DEFAULT_TIMEOUT = 45
DEFAULT_MAX_OUTPUT_CHARS = 12000


def _request_spec(provider: dict[str, Any], prompt: str, api_key: str) -> tuple[str, dict[str, str], dict[str, Any]]:
    family = provider["api_family"]
    endpoint = provider["endpoint"]
    model = provider["model_id"]
    headers = {"Content-Type": "application/json"}
    if family == "responses":
        headers["Authorization"] = f"Bearer {api_key}"
        body = {"model": model, "input": prompt, "max_output_tokens": 4096}
    elif family == "responses_compatible":
        headers["Authorization"] = f"Bearer {api_key}"
        body = {"model": model, "input": prompt, "max_output_tokens": 4096}
    elif family == "messages":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
        body = {"model": model, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}
    elif family == "generate_content":
        endpoint = f"{endpoint.rstrip('/')}/{urllib.parse.quote(model, safe='')}:generateContent"
        endpoint += "?" + urllib.parse.urlencode({"key": api_key})
        body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 4096}}
    elif family == "chat_completions":
        headers["Authorization"] = f"Bearer {api_key}"
        body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096}
    else:
        raise ValueError(f"Unsupported API family: {family}")
    return endpoint, headers, body


def _extract_text(provider: dict[str, Any], payload: dict[str, Any]) -> str:
    family = provider["api_family"]
    if family in ("responses", "responses_compatible"):
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]
        chunks = []
        for item in payload.get("output", []):
            for part in item.get("content", []) if isinstance(item, dict) else []:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    chunks.append(part["text"])
        if chunks:
            return "\n".join(chunks)
        # Some OpenAI-compatible implementations expose chat-completions shape.
        choices = payload.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            if isinstance(message.get("content"), str):
                return message["content"]
    elif family == "messages":
        return "\n".join(part["text"] for part in payload.get("content", []) if isinstance(part, dict) and isinstance(part.get("text"), str))
    elif family == "generate_content":
        candidates = payload.get("candidates", [])
        if candidates:
            return "\n".join(part["text"] for part in candidates[0].get("content", {}).get("parts", []) if isinstance(part, dict) and isinstance(part.get("text"), str))
    elif family == "chat_completions":
        choices = payload.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "\n".join(p.get("text", "") for p in content if isinstance(p, dict))
    raise ValueError("Provider response contained no supported text output")


def call_provider(provider: dict[str, Any], prompt: str, timeout: int, max_output_chars: int) -> dict[str, Any]:
    started = time.monotonic()
    result = {
        "provider": provider.get("provider"),
        "model_id": provider.get("model_id"),
        "status": "NOT_CONFIGURED",
        "latency_ms": None,
        "text": None,
        "error": None,
    }
    api_key = os.environ.get(provider.get("credential_env", ""), "").strip()
    if not api_key:
        result["latency_ms"] = 0
        return result
    try:
        endpoint, headers, body = _request_spec(provider, prompt, api_key)
        request = urllib.request.Request(endpoint, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        result["text"] = _extract_text(provider, payload)[:max_output_chars]
        result["status"] = "SUCCESS"
    except urllib.error.HTTPError as exc:
        result["status"] = "HTTP_ERROR"
        result["error"] = f"HTTP {exc.code}"
    except urllib.error.URLError:
        result["status"] = "NETWORK_ERROR"
        result["error"] = "Network request failed or timed out"
    except (TimeoutError, OSError):
        result["status"] = "NETWORK_ERROR"
        result["error"] = "Network request failed or timed out"
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        result["status"] = "RESPONSE_ERROR"
        result["error"] = "Unsupported or invalid provider response"
    finally:
        result["latency_ms"] = round((time.monotonic() - started) * 1000, 1)
    return result


def run_federation(registry: dict[str, Any], prompt: str, providers: list[str] | None = None,
                   timeout: int = DEFAULT_TIMEOUT, max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS) -> dict[str, Any]:
    configured = registry.get("providers", [])
    selected = [p for p in configured if providers is None or p.get("provider") in providers]
    if providers:
        found = {p.get("provider") for p in selected}
        unknown = sorted(set(providers) - found)
        if unknown:
            raise ValueError("Unknown providers: " + ", ".join(unknown))
    if not selected:
        raise ValueError("No providers selected")
    max_workers = min(MAX_PARALLELISM, max(1, int(registry.get("policy", {}).get("parallelism_max", MAX_PARALLELISM))), len(selected))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(call_provider, p, prompt, timeout, max_output_chars) for p in selected]
        results = [future.result() for future in futures]
    return {
        "schema_version": "vx.model-federation-result.v1",
        "status": "COMPLETED_WITH_RESULTS" if any(r["status"] == "SUCCESS" for r in results) else "NO_PROVIDER_SUCCEEDED",
        "provider_count": len(results),
        "success_count": sum(r["status"] == "SUCCESS" for r in results),
        "results_are_proposals_only": True,
        "canonical_mutation_performed": False,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True, help="Task prompt sent to every selected provider; may incur API charges.")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--providers", default="", help="Comma-separated provider IDs; default selects all registry providers.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-output-chars", type=int, default=DEFAULT_MAX_OUTPUT_CHARS)
    parser.add_argument("--out", default="-", help="JSON report path or '-' for stdout.")
    args = parser.parse_args()
    if args.timeout < 1 or args.timeout > 180:
        parser.error("--timeout must be between 1 and 180 seconds")
    if args.max_output_chars < 1 or args.max_output_chars > 100000:
        parser.error("--max-output-chars must be between 1 and 100000")
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    providers = [item.strip() for item in args.providers.split(",") if item.strip()] or None
    report = run_federation(registry, args.prompt, providers, args.timeout, args.max_output_chars)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out == "-":
        print(encoded, end="")
    else:
        Path(args.out).write_text(encoded, encoding="utf-8")
    return 0 if report["success_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
