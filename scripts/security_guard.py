#!/usr/bin/env python3
"""Deterministic repository malware guard for VAIXLNS.

Scans every tracked file for high-confidence malware, persistence,
reverse-shell, download-and-execute, credential-exfiltration, and miner
indicators.

Default action is DETECT/BLOCK. Remediation is opt-in and only quarantines
high-confidence findings; it never silently deletes repository history.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(os.getenv("VAIXLNS_REPOSITORY_ROOT", Path(__file__).resolve().parents[1]))
QUARANTINE = ROOT / ".security-quarantine"

SKIP_DIRS = {".git", ".security-quarantine", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}

HIGH_CONFIDENCE = [
    ("REVERSE_SHELL", re.compile(r"(?:bash\s+-i\s+>&\s*/dev/tcp/|nc\s+(?:-[^\n]*e|--exec)|socat\s+[^\n]*exec:)")),
    ("DOWNLOAD_EXECUTE", re.compile(r"(?:curl|wget)\s+[^\n]*(?:\||;|&&)\s*(?:bash|sh|zsh|python(?:3)?|perl|ruby|php)\b")),
    ("POWERSHELL_ENCODED", re.compile(r"(?i)powershell(?:\.exe)?\s+[^\n]*-(?:enc|encodedcommand)\b")),
    ("POWERSHELL_DOWNLOAD_EXECUTE", re.compile(r"(?i)(?:iwr|invoke-webrequest|invoke-restmethod)\s+[^\n]*\|\s*(?:iex|invoke-expression)\b")),
    ("PYTHON_OBFUSCATED_EXEC", re.compile(r"(?i)(?:exec|eval)\s*\(\s*(?:compile\s*\(|marshal\.loads\s*\(|base64\.b64decode\s*\()")),
    ("CRYPTO_MINER", re.compile(r"(?i)(?:xmrig|minerd|cpuminer|stratum\+tcp://|stratum\+ssl://)")),
    ("PERSISTENCE_CRON", re.compile(r"(?i)(?:crontab\s+-[el]|/etc/cron(?:\.d|\.daily|\.hourly|\.weekly)|/var/spool/cron)")),
    ("PERSISTENCE_SYSTEMD", re.compile(r"(?i)(?:/etc/systemd/system/|systemctl\s+(?:enable|daemon-reload))")),
    ("PERSISTENCE_STARTUP", re.compile(r"(?i)(?:HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run|/etc/rc\.local)")),
    ("CREDENTIAL_EXFIL", re.compile(r"(?i)(?:curl|wget)\s+[^\n]*(?:\$\{?(?:AWS_|GITHUB_|OPENAI_|SECRET|TOKEN|PASSWORD|PRIVATE_KEY)|/proc/\d+/environ)")),
]

REVIEW_PATTERNS = [
    ("SHELL_TRUE", re.compile(r"subprocess\.(?:run|Popen|call|check_call|check_output)\([^\n]*shell\s*=\s*True")),
    ("DYNAMIC_EXEC", re.compile(r"(?i)\b(?:eval|exec)\s*\(")),
    ("NETWORK_TOOL", re.compile(r"(?i)\b(?:curl|wget|nc|netcat|socat)\b")),
]

BINARY_MAGIC = {
    b"\x7fELF": "ELF_EXECUTABLE",
    b"MZ": "PE_EXECUTABLE",
    b"\xcf\xfa\xed\xfe": "MACHO_EXECUTABLE",
    b"\xfe\xed\xfa\xcf": "MACHO_EXECUTABLE",
}


def tracked_files() -> list[Path]:
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-files", "-co", "--exclude-standard"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        paths = [ROOT / line for line in raw.splitlines() if line]
        return sorted(set(p for p in paths if p.exists() or p.is_symlink()))
    except (OSError, subprocess.CalledProcessError):
        files: list[Path] = []
        for base, dirs, names in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in names:
                files.append(Path(base) / name)
        return sorted(files)


def is_binary(data: bytes) -> bool:
    return b"\x00" in data[:8192]


def scan_file(path: Path) -> list[dict[str, object]]:
    rel = path.relative_to(ROOT).as_posix()
    findings: list[dict[str, object]] = []
    if path.is_symlink():
        findings.append({"severity": "HIGH", "kind": "SYMLINK", "path": rel})
        return findings

    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    for magic, kind in BINARY_MAGIC.items():
        if data.startswith(magic):
            findings.append({
                "severity": "REVIEW",
                "kind": kind,
                "path": rel,
                "sha256": digest,
            })
            return findings

    if is_binary(data):
        return findings

    text = data.decode("utf-8", errors="replace")
    for line_no, line in enumerate(text.splitlines(), 1):
        for kind, pattern in HIGH_CONFIDENCE:
            if pattern.search(line):
                findings.append({
                    "severity": "HIGH",
                    "kind": kind,
                    "path": rel,
                    "line": line_no,
                    "sha256": digest,
                })
        for kind, pattern in REVIEW_PATTERNS:
            if pattern.search(line):
                findings.append({
                    "severity": "REVIEW",
                    "kind": kind,
                    "path": rel,
                    "line": line_no,
                    "sha256": digest,
                })
    return findings


def quarantine(path: Path, finding: dict[str, object]) -> str:
    QUARANTINE.mkdir(parents=True, exist_ok=True)
    digest = str(finding.get("sha256") or hashlib.sha256(path.read_bytes()).hexdigest())
    destination = QUARANTINE / digest
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / path.name
    shutil.move(str(path), str(target))
    return target.relative_to(ROOT).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remediate", action="store_true",
                        help="quarantine files with HIGH-confidence findings")
    args = parser.parse_args()

    files = tracked_files()
    findings: list[dict[str, object]] = []
    for path in files:
        try:
            findings.extend(scan_file(path))
        except OSError as exc:
            findings.append({
                "severity": "HIGH",
                "kind": "SCAN_ERROR",
                "path": path.relative_to(ROOT).as_posix(),
                "error": str(exc),
            })

    high = [f for f in findings if f["severity"] == "HIGH"]
    quarantined: list[dict[str, object]] = []
    if args.remediate:
        for finding in high:
            path = ROOT / str(finding["path"])
            if path.exists() and path.is_file():
                item = dict(finding)
                item["quarantined_to"] = quarantine(path, item)
                quarantined.append(item)

    report = {
        "schema": "VAIXLNS_SECURITY_SCAN_V1",
        "root": str(ROOT),
        "files_scanned": len(files),
        "findings": findings,
        "high_confidence_count": len(high),
        "review_count": sum(f["severity"] == "REVIEW" for f in findings),
        "quarantined_count": len(quarantined),
        "verdict": "BLOCKED" if high else "PASS_WITH_REVIEW" if findings else "CLEAN",
        "remediation": "QUARANTINED_HIGH_CONFIDENCE" if args.remediate else "DETECTION_ONLY",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if high else 0


if __name__ == "__main__":
    raise SystemExit(main())
