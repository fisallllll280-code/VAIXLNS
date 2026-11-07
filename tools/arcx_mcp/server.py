"""Read-only ARC-X MCP server prototype.

The repository root is configured by ARCX_REPOSITORY_ROOT. No arbitrary URL fetch,
shell tool, file writes, or command execution is exposed. Source reads are limited
to the configured root; retrieved source is untrusted data.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ARC-X Engineering Evidence (read-only)")
MAX_SOURCE_BYTES = 256 * 1024
SKIP_DIRS = {
    ".git", ".venv", ".venv-arcx", "venv", "__pycache__", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build",
}
DENY_NAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
    "credentials.json", "secrets.json",
}


class ArcxError(ValueError):
    """Raised for invalid scope or unavailable repository evidence."""


def _root() -> Path:
    configured = os.environ.get("ARCX_REPOSITORY_ROOT")
    if not configured:
        raise ArcxError("ARCX_REPOSITORY_ROOT is not configured")
    root = Path(configured).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ArcxError("Configured repository root is not a directory")
    return root


def _revision(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "UNAVAILABLE"


def _safe_source_path(root: Path, relative_path: str) -> Path:
    candidate_rel = Path(relative_path)
    if candidate_rel.is_absolute() or not relative_path.strip():
        raise ArcxError("A non-empty repository-relative path is required")
    if ".." in candidate_rel.parts:
        raise ArcxError("Path traversal is not allowed")
    if any(part.lower() in DENY_NAMES for part in candidate_rel.parts):
        raise ArcxError("Sensitive filename is not readable through ARC-X")
    candidate = (root / candidate_rel).resolve(strict=True)
    if not candidate.is_relative_to(root):
        raise ArcxError("Resolved path escapes the configured repository")
    if not candidate.is_file():
        raise ArcxError("Path must identify a regular file")
    if candidate.stat().st_size > MAX_SOURCE_BYTES:
        raise ArcxError("Source exceeds the 256 KiB read limit")
    return candidate


@mcp.tool()
def inspect_repository() -> dict[str, Any]:
    """Return a bounded inventory of the configured repository without reading file contents."""
    root = _root()
    files: list[str] = []
    truncated = False
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(
            d for d in dirs
            if d not in SKIP_DIRS and not (Path(current) / d).is_symlink()
        )
        for name in sorted(names):
            path = Path(current) / name
            if name.lower() in DENY_NAMES or path.is_symlink():
                continue
            try:
                rel = path.relative_to(root).as_posix()
            except ValueError:
                continue
            files.append(rel)
            if len(files) >= 2000:
                truncated = True
                break
        if truncated:
            break
    return {
        "status": "PARTIAL" if truncated else "SPECIFIED",
        "repository_root": str(root),
        "revision": _revision(root),
        "file_count_returned": len(files),
        "inventory_truncated": truncated,
        "files": files,
        "limitations": [
            "Inventory is not proof of semantic completeness.",
            "Ignored folders and sensitive filenames are excluded.",
            "No claim is VERIFIED by repository presence alone.",
        ],
    }


@mcp.tool()
def fetch_source(relative_path: str) -> dict[str, Any]:
    """Read one bounded UTF-8 file inside the configured repository and return its SHA-256 digest."""
    root = _root()
    path = _safe_source_path(root, relative_path)
    raw = path.read_bytes()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ArcxError("Only UTF-8 text files are supported") from exc
    return {
        "status": "SPECIFIED",
        "repository_relative_path": path.relative_to(root).as_posix(),
        "revision": _revision(root),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "content": content,
        "evidence_note": "Content hash binds this response to the bytes read; it does not prove the content is true.",
    }


@mcp.tool()
def classify_claim(claim: str, evidence_refs: list[str], verification_result: str = "NOT_RUN") -> dict[str, Any]:
    """Classify evidence coverage without asserting truth or granting canonical authority."""
    if not claim.strip():
        raise ArcxError("Claim text is required")
    if verification_result not in {"NOT_RUN", "PASS", "FAIL", "INCONCLUSIVE"}:
        raise ArcxError("Unsupported verification_result")
    refs = [ref.strip() for ref in evidence_refs if isinstance(ref, str) and ref.strip()]
    if verification_result == "PASS" and refs:
        status = "PARTIAL"
        rationale = "A passing check and evidence references are present, but independent reproducibility and authority admission are not established by this tool."
    elif verification_result == "FAIL":
        status = "CONFLICT"
        rationale = "The supplied verification result reports failure; investigate counterevidence."
    elif refs:
        status = "SPECIFIED"
        rationale = "Evidence references were supplied, but this tool does not independently verify them."
    else:
        status = "MISSING"
        rationale = "No evidence references were supplied."
    return {
        "status": status,
        "claim": claim,
        "evidence_refs": refs,
        "verification_result_supplied": verification_result,
        "rationale": rationale,
        "authority_decision": "NOT_REQUESTED",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
