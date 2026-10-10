"""Deterministic, language-adapter-based diagnostic triage for VAIXLNS.

This v1 converts compiler/test diagnostics into repair work orders. It does not
edit source files, run commands, install packages, or assert a repair is correct.
Unknown and custom languages are held until an explicit adapter is registered.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Iterable


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Diagnostic:
    tool: str
    code: str | None
    message: str
    path: str | None
    line: int | None
    column: int | None
    raw_digest: str


# Adapters recognize diagnostic syntax; they do not execute the underlying tools.
PATTERNS = {
    "python": [
        ("pytest", re.compile(r"^(?P<path>.+?)::(?P<test>[^ ]+)\s+(?P<message>FAILED|ERROR)(?:\s+-\s+(?P<detail>.*))?$")),
        ("python", re.compile(r'^\s*File "(?P<path>[^"]+)", line (?P<line>\d+)(?:, in .*)?$')),
        ("ruff", re.compile(r"^(?P<path>[^:]+):(?P<line>\d+):(?P<column>\d+): (?P<code>[A-Z]+\d+) (?P<message>.*)$")),
        ("mypy", re.compile(r"^(?P<path>[^:]+):(?P<line>\d+):(?:(?P<column>\d+):)? (?P<severity>error|warning|note): (?P<message>.*?)(?:\s+\[(?P<code>[^]]+)\])?$")),
    ],
    "rust": [
        ("rustc", re.compile(r"^error(?:\[(?P<code>E\d+)\])?: (?P<message>.*)$")),
        ("rustc", re.compile(r"^\s*--> (?P<path>.+?):(?P<line>\d+):(?P<column>\d+)$")),
    ],
    "typescript": [
        ("tsc", re.compile(r"^(?P<path>.+?)\((?P<line>\d+),(?P<column>\d+)\): error (?P<code>TS\d+): (?P<message>.*)$")),
    ],
    "javascript": [
        ("eslint", re.compile(r"^(?P<path>.+?):(?P<line>\d+):(?P<column>\d+): (?P<severity>error|warning) (?P<message>.*?)(?:\s+(?P<code>[\w/-]+))?$")),
    ],
    "go": [
        ("go", re.compile(r"^(?P<path>.+?):(?P<line>\d+):(?P<column>\d+): (?P<message>.*)$")),
    ],
    "c": [
        ("gcc", re.compile(r"^(?P<path>.+?):(?P<line>\d+):(?P<column>\d+): (?P<severity>fatal error|error|warning): (?P<message>.*)$")),
    ],
    "cpp": [
        ("g++", re.compile(r"^(?P<path>.+?):(?P<line>\d+):(?P<column>\d+): (?P<severity>fatal error|error|warning): (?P<message>.*)$")),
    ],
    "java": [
        ("javac", re.compile(r"^(?P<path>.+\.java):(?P<line>\d+): error: (?P<message>.*)$")),
    ],
}


def parse_diagnostics(language: str, output: str) -> list[Diagnostic]:
    lang = language.strip().casefold()
    patterns = PATTERNS.get(lang)
    if not patterns:
        raise ValueError("UNKNOWN_LANGUAGE_ADAPTER")
    found: list[Diagnostic] = []
    pending_path = None
    for raw_line in output.splitlines():
        line = raw_line.rstrip()
        for tool, pattern in patterns:
            match = pattern.match(line)
            if not match:
                continue
            groups = match.groupdict()
            if groups.get("path"):
                pending_path = groups["path"]
            message = groups.get("message") or groups.get("detail") or groups.get("severity") or "compiler diagnostic context"
            if groups.get("test"):
                message = f"{groups['test']}: {message}"
            found.append(Diagnostic(
                tool=tool,
                code=groups.get("code"),
                message=message,
                path=groups.get("path") or pending_path,
                line=int(groups["line"]) if groups.get("line") else None,
                column=int(groups["column"]) if groups.get("column") else None,
                raw_digest=sha256_text(line),
            ))
            break
    # Stable deduplication preserves first-seen evidence order.
    unique: dict[str, Diagnostic] = {}
    for item in found:
        key = sha256_text(canonical_json(asdict(item)))
        unique.setdefault(key, item)
    return list(unique.values())


def make_work_orders(
    language: str,
    output: str,
    repository: str,
    revision: str,
    *,
    mode: str = "DIAGNOSE_ONLY",
    source_digests: dict[str, str] | None = None,
) -> list[dict]:
    lang = language.strip().casefold()
    if mode not in {"DIAGNOSE_ONLY", "PATCH_PROPOSAL", "SANDBOX_PATCH"}:
        raise ValueError("INVALID_REPAIR_MODE")
    if not repository.strip() or not re.fullmatch(r"[0-9a-fA-F]{7,64}", revision):
        raise ValueError("PINNED_REPOSITORY_AND_REVISION_REQUIRED")
    if mode == "SANDBOX_PATCH":
        # v1 does not implement patching; do not silently pretend it does.
        raise ValueError("SANDBOX_PATCH_NOT_IMPLEMENTED")
    patterns_registered = lang in PATTERNS
    if patterns_registered:
        diagnostics = parse_diagnostics(lang, output)
    else:
        # Preserve the raw evidence and make the blocker explicit; never guess
        # the syntax of a custom/system-specific language.
        diagnostics = [Diagnostic(
            tool="unclassified",
            code=None,
            message="No diagnostic adapter registered; human/adapter classification required",
            path=None,
            line=None,
            column=None,
            raw_digest=sha256_text(output),
        )] if output.strip() else []
    orders = []
    for diag in diagnostics:
        material = {
            "language": lang,
            "repository": repository,
            "revision": revision.lower(),
            "path": diag.path or "",
            "raw_digest": diag.raw_digest,
            "tool": diag.tool,
            "code": diag.code or "",
        }
        work_id = "LRE-" + sha256_text(canonical_json(material))[:16]
        registered = patterns_registered
        orders.append({
            "schema_version": "1.0.0",
            "work_order_id": work_id,
            "language": {"id": lang, "adapter_state": "REGISTERED" if registered else "CUSTOM_LANGUAGE_PENDING_ADAPTER"},
            "source": {
                "repository": repository,
                "revision": revision.lower(),
                "path": diag.path or "",
                "source_digest": (source_digests or {}).get(diag.path or ""),
            },
            "diagnostic": {
                "tool": diag.tool,
                "code": diag.code,
                "message": diag.message,
                "line": diag.line,
                "column": diag.column,
                "raw_digest": diag.raw_digest,
            },
            "repair_policy": {
                "mode": mode,
                "automatic_patch": False,
                "tests_required": ["reproduce_failure", "targeted_regression", "full_relevant_suite"],
                "independent_review": True,
            },
            "status": "READY_FOR_TRIAGE" if registered else "BLOCKED_UNKNOWN_LANGUAGE",
        })
    return orders


def summarize(orders: Iterable[dict]) -> dict:
    items = list(orders)
    return {
        "count": len(items),
        "work_order_ids": [x["work_order_id"] for x in items],
        "languages": sorted({x["language"]["id"] for x in items}),
        "source_revisions": sorted({x["source"]["revision"] for x in items}),
        "automatic_patching": "DISABLED",
        "verification_state": "NOT_VERIFIED",
    }
