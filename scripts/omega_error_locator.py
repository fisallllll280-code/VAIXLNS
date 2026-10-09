#!/usr/bin/env python3
"""Evidence-first failure localization; analyzes logs without executing code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "vaixlns.omega-error-locator.v1"
IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build", "target", ".next"}
SOURCE_SUFFIXES = {".py", ".rs", ".go", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift", ".kt", ".toml", ".json", ".yaml", ".yml"}
PY_FRAME = re.compile(r'File ["\']([^"\']+)["\'], line (\d+)(?:, in ([^\n]+))?')
PATH_LINE = re.compile(r'(?P<path>(?:[A-Za-z]:)?[\w./\\-]+\.(?:py|rs|go|js|jsx|ts|tsx|java|c|cc|cpp|h|hpp|cs|rb|php|swift|kt|toml|json|ya?ml)):(?P<line>\d+)(?::\d+)?')
FAILED_TEST = re.compile(r'(?im)^\s*(?:FAILED|ERROR)\s+(?P<name>[^\n]+)')
SECRET_PATTERNS = (
    (re.compile(r"(?i)(\b(?:api[_-]?key|access[_-]?token|password|passwd|secret)\b\s*[=:]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+"), r"\1[REDACTED]"),
)

def redact(text: str) -> str:
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

def resolve_repo_file(root: Path, raw_path: str) -> Path | None:
    raw = raw_path.replace("\\", "/")
    candidate = Path(raw)
    if candidate.is_absolute():
        parts = candidate.parts
        candidates = [root.joinpath(*parts[i + 1:]) for i in range(len(parts) - 1)]
        candidates.append(root / candidate.name)
        for possible in candidates:
            try:
                possible = possible.resolve()
                possible.relative_to(root.resolve())
            except (OSError, ValueError):
                continue
            if possible.is_file():
                return possible
        return None
    try:
        possible = (root / candidate).resolve()
        possible.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return possible if possible.is_file() else None

def repository_paths(root: Path, max_files: int = 30000) -> list[str]:
    found: list[str] = []
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS and not (Path(current) / d).is_symlink())
        for name in sorted(files):
            path = Path(current) / name
            if path.is_symlink() or path.suffix.lower() not in SOURCE_SUFFIXES or not path.is_file():
                continue
            found.append(path.relative_to(root).as_posix())
            if len(found) >= max_files:
                return found
    return found

def classify_signals(lines: list[str]) -> list[dict[str, Any]]:
    patterns = [
        ("DEPENDENCY_OR_IMPORT", r"ModuleNotFoundError|ImportError|cannot find module|unresolved import|no such package",
         "A dependency or import may be unresolved; verify package names, environment and pinned dependencies."),
        ("MISSING_FILE_OR_CONFIG", r"FileNotFoundError|No such file or directory|config(?:uration)? .* not found|missing required",
         "A file or configuration input may be absent; verify its path, generation step and working directory."),
        ("ASSERTION_OR_CONTRACT", r"AssertionError|assertion failed|expected .* but (?:got|was)|assert .* failed",
         "A behavioral assertion failed; compare expected and observed values and add a regression test."),
        ("TYPE_OR_SCHEMA", r"TypeError|KeyError|AttributeError|JSONDecodeError|schema validation|validation error",
         "A value type or schema may violate a consumer's assumptions; inspect the earliest failing boundary."),
        ("PERMISSION_OR_SECURITY", r"PermissionError|Permission denied|unauthorized|forbidden|access denied|EACCES",
         "An access boundary rejected the operation; check least-privilege identity and resource policy."),
        ("TIMEOUT_OR_RESOURCE", r"TimeoutError|timed out|deadline exceeded|out of memory|MemoryError|killed",
         "A time or resource bound may have been exceeded; inspect duration, memory limits and upstream waits."),
        ("NETWORK_OR_SERVICE", r"ConnectionError|ConnectionRefusedError|Name or service not known|Temporary failure in name resolution|HTTP [45]\d\d|TLS handshake",
         "A network or service boundary failed; check endpoint configuration, health and retry behavior."),
        ("SYNTAX_OR_COMPILE", r"SyntaxError|IndentationError|compilation failed|error\[E\d+\]|syntax error",
         "A parser/compiler rejected the input; inspect the earliest reported source location."),
    ]
    result = []
    for code, expression, advice in patterns:
        matcher = re.compile(expression, re.I)
        matches = [index for index, line in enumerate(lines, start=1) if matcher.search(line)]
        if matches:
            result.append({"signal": code, "evidence_log_lines": matches[:20], "interpretation": advice})
    return result

def locate(root: Path, log_text: str) -> dict[str, Any]:
    root = root.resolve()
    lines = redact(log_text).splitlines()
    locations: dict[tuple[str, int | None], dict[str, Any]] = {}

    def add(raw_path: str, line_no: int | None, evidence_line: int, method: str, symbol: str | None = None):
        source = resolve_repo_file(root, raw_path)
        if source is None:
            return
        relative = source.relative_to(root).as_posix()
        item = locations.setdefault((relative, line_no), {
            "path": relative, "line": line_no, "symbol": symbol,
            "evidence_log_lines": [], "evidence_methods": [],
        })
        if evidence_line not in item["evidence_log_lines"]:
            item["evidence_log_lines"].append(evidence_line)
        if method not in item["evidence_methods"]:
            item["evidence_methods"].append(method)

    for index, line in enumerate(lines, start=1):
        frame = PY_FRAME.search(line)
        if frame:
            add(frame.group(1), int(frame.group(2)), index, "PYTHON_TRACEBACK_FRAME", frame.group(3))
        for match in PATH_LINE.finditer(line):
            add(match.group("path"), int(match.group("line")), index, "COMPILER_OR_TEST_PATH_LOCATION")

    failed_tests = []
    for index, line in enumerate(lines, start=1):
        match = FAILED_TEST.search(line)
        if not match:
            continue
        name = match.group("name").strip()
        failed_tests.append({"name": redact(name)[:300], "evidence_log_line": index})
        test_path = re.match(r"([^:\s]+\.(?:py|rs|go|js|ts))(?:::|$)", name)
        if test_path:
            add(test_path.group(1), None, index, "FAILED_TEST_NAME", name.split(" - ", 1)[0])

    # Explicit repository path mentions are useful candidates, but weaker than line frames.
    paths = repository_paths(root)
    for index, line in enumerate(lines, start=1):
        for relative in paths:
            if relative in line and not any(item["path"] == relative for item in locations.values()):
                add(relative, None, index, "EXPLICIT_REPOSITORY_PATH")

    ranked = []
    for item in locations.values():
        methods = item["evidence_methods"]
        score = 100 if "PYTHON_TRACEBACK_FRAME" in methods else 90 if "COMPILER_OR_TEST_PATH_LOCATION" in methods else 60 if "FAILED_TEST_NAME" in methods else 35
        item["rank_score"] = score + min(10, len(item["evidence_log_lines"]))
        if item["line"] is not None:
            source = resolve_repo_file(root, item["path"])
            try:
                source_lines = source.read_text(encoding="utf-8", errors="replace").splitlines() if source else []
                if 1 <= item["line"] <= len(source_lines):
                    item["source_excerpt"] = redact(source_lines[item["line"] - 1].strip())[:240]
            except OSError:
                pass
        ranked.append(item)
    ranked.sort(key=lambda item: (-item["rank_score"], item["path"], item["line"] or 0))

    marker = re.compile(r"(?i)(error|exception|failed|failure|traceback|fatal|assert|timed out|denied|cannot|could not|not found)")
    diagnostic_lines = [
        {"line": index, "text": line.strip()[:500]}
        for index, line in enumerate(lines, start=1) if marker.search(line)
    ][:80]
    signals = classify_signals(lines)
    if ranked and ranked[0]["rank_score"] >= 90:
        state, confidence = "LOCATION_FOUND_FROM_EXPLICIT_EVIDENCE", "HIGH_FOR_LOCATION_NOT_ROOT_CAUSE"
    elif ranked:
        state, confidence = "CANDIDATE_LOCATION_FOUND", "MEDIUM_OR_LOW"
    else:
        state, confidence = "LOCALIZATION_INSUFFICIENT_EVIDENCE", "INSUFFICIENT"

    core = {
        "schema": SCHEMA,
        "state": state,
        "confidence": confidence,
        "input_sha256": sha256_text(log_text),
        "input_line_count": len(lines),
        "locations": ranked[:50],
        "failed_tests": failed_tests[:50],
        "signals": signals,
        "diagnostic_lines": diagnostic_lines,
        "next_steps": [
            "Inspect the highest-ranked location and adjacent call sites; a traceback frame is not automatically the root cause.",
            "Reproduce with the same pinned revision, environment, inputs and exact command before accepting a fix.",
            "Add a minimal regression test and retain the failing log and post-fix run receipt.",
        ],
        "limitations": [
            "Static log analysis only; no source code or commands are executed.",
            "Missing, truncated or sanitized logs can prevent localization.",
            "Signal categories and ranking are heuristics; root cause requires reproduction and counterevidence checks.",
            "Remote services and external repositories are not queried.",
        ],
    }
    digest_input = json.dumps(core, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {**core, "report_sha256": sha256_text(digest_input)}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root to inspect")
    parser.add_argument("--input", help="Log file path; reads stdin when omitted")
    parser.add_argument("--output", help="Write JSON report to this path; otherwise print")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"repository root is not a directory: {root}")
    try:
        log_text = Path(args.input).read_text(encoding="utf-8", errors="replace") if args.input else sys.stdin.read()
        report = locate(root, log_text)
        rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0 if report["state"] != "LOCALIZATION_INSUFFICIENT_EVIDENCE" else 2
    except OSError as exc:
        parser.error(str(exc))
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
