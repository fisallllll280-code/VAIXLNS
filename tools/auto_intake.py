#!/usr/bin/env python3
"""Source-first, read-only VAIXLNS intake routing. Never promotes to Ω.000."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

SCHEMA = "VAIXLNS.AUTO_INTAKE.v1"
BLOCKED_SUFFIXES = {".env", ".pem", ".key", ".p12", ".pfx", ".kdbx", ".sqlite", ".db", ".exe", ".dll", ".so", ".dylib", ".lnk", ".sh", ".bat", ".ps1"}
BINARY_ALLOWED = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".zip", ".xlsx", ".pptx"}
TEXT_ALLOWED = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".toml", ".py", ".rs", ".ts", ".js", ".html", ".xml"}
SECRET_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb'''(?i)["']?(?:api[_-]?key|client[_-]?secret|password|access[_-]?token)["']?\s*[=:]\s*["']?[^\s"']{12,}'''),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"sk-proj-[A-Za-z0-9_-]{12,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
]
RULES = [
    ("INDEX", "VAIXLNS", "docs/indexes/intake", ("index", "indexes", "فهرس", "الفهارس", "taxonomy")),
    ("INNOVATION", "VAIXLNS", "docs/innovation/intake", ("innovation", "invention", "ابتكار", "الابتكارات")),
    ("MODEL", "VAIXLNS", "registry/models/intake", ("model", "models", "نموذج", "النماذج", "llm")),
    ("AGENT", "VAIXLNS", "docs/agents/intake", ("agent", "agents", "عقل", "الوكلاء")),
    ("RESEARCH", "NEXENT", "docs/research/intake", ("nexent", "research", "بحث", "دراسة")),
    ("RUNTIME", "VX-runtime", "docs/intake", ("runtime", "kernel", "vx-", "تنفيذ", "تشغيل")),
    ("EVIDENCE", "VAIXLNS", "registry/evidence/intake", ("evidence", "proof", "ledger", "أدلة", "إثبات")),
    ("ARCHIVE", "VAIXLNS", "archive/source/intake", ("archive", "legacy", "أرشيف")),
]

def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def is_sensitive(data: bytes) -> bool:
    return any(pattern.search(data) for pattern in SECRET_PATTERNS)

def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^\w.\-\u0600-\u06FF]+", "_", name, flags=re.UNICODE).strip("._")
    return cleaned[:100] or "unnamed"

def classify(relative_path: str, suffix: str) -> tuple[str, str | None, str | None]:
    key = relative_path.casefold()
    for category, repo, folder, words in RULES:
        if any(word in key for word in words):
            return category, repo, folder
    if suffix in {".md", ".txt", ".pdf", ".docx", ".csv", ".xlsx", ".pptx", ".png", ".jpg", ".jpeg", ".webp"}:
        return "LIBRARY", "VAIXLNS", "docs/library/intake"
    return "UNCLASSIFIED", None, None

def plan(root: Path, inbox: Path, *, max_bytes: int = 8 * 1024 * 1024,
         origin_repository: str = "fisallllll280-code/VAIXLNS",
         origin_sha: str = "UNKNOWN") -> tuple[list[dict], dict[str, bytes]]:
    root, inbox = root.resolve(), inbox.resolve()
    if not inbox.is_relative_to(root) or not inbox.is_dir():
        raise ValueError("inbox must be an existing directory inside root")
    records, objects = [], {}
    paths = sorted((p for p in inbox.rglob("*") if p.is_file() or p.is_symlink()), key=lambda p: p.relative_to(inbox).as_posix())
    for path in paths:
        suffix = path.suffix.casefold()
        entry = {"schema": SCHEMA, "source_repository": origin_repository,
                 "source_commit_sha": origin_sha, "source_path": path.relative_to(root).as_posix(),
                 "original_filename": path.name}
        if path.is_symlink():
            records.append({**entry, "decision": "BLOCKED", "reason": "SYMLINK", "sha256": None})
            continue
        size = path.stat().st_size
        if size > max_bytes:
            records.append({**entry, "decision": "HELD", "reason": "OVER_SIZE_LIMIT", "size_bytes": size, "sha256": None})
            continue
        data = path.read_bytes()
        digest = hash_bytes(data)
        entry.update(size_bytes=len(data), sha256=digest)
        if suffix in BLOCKED_SUFFIXES or path.name.casefold().startswith(".env"):
            records.append({**entry, "decision": "BLOCKED", "reason": "FORBIDDEN_FILE_TYPE"})
            continue
        if suffix not in TEXT_ALLOWED | BINARY_ALLOWED:
            records.append({**entry, "decision": "HELD", "reason": "UNKNOWN_FILE_TYPE"})
            continue
        if suffix not in BINARY_ALLOWED and is_sensitive(data):
            records.append({**entry, "decision": "BLOCKED", "reason": "POSSIBLE_CREDENTIAL"})
            continue
        category, repository, folder = classify(path.relative_to(inbox).as_posix(), suffix)
        objects[digest] = data
        entry.update(category=category, target_repository=repository,
                     library_object=f"library/objects/{digest[:2]}/{digest}",
                     review_state="PROPOSED_NOT_ADMITTED", decision="REVIEW_REQUIRED",
                     reason="BINARY_NEEDS_REVIEW" if suffix in BINARY_ALLOWED else "ROUTE_CANDIDATE")
        if repository and folder:
            entry["target_path"] = f"{folder}/{digest[:12]}-{safe_name(path.name)}"
        records.append(entry)
    return records, objects

def write_bundle(out: Path, records: list[dict], objects: dict[str, bytes], *, include_payloads: bool = False) -> None:
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": SCHEMA, "generated_by": "tools/auto_intake.py", "no_canonical_promotion": True,
                "records": records, "record_count": len(records), "readiness": "REVIEW_REQUIRED",
                "objects_written": bool(include_payloads)}
    (out / "routing-manifest.v1.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with (out / "library-index.v1.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    if include_payloads:
        for digest, data in sorted(objects.items()):
            target = out / "library/objects" / digest[:2] / digest
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for record in records:
            if not record.get("target_path") or record["decision"] != "REVIEW_REQUIRED":
                continue
            target = out / "proposals" / record["target_repository"] / record["target_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(objects[record["sha256"]])

def main() -> int:
    parser = argparse.ArgumentParser(description="Produce review-only intake manifest and content-addressed local library")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--inbox", type=Path, default=Path("intake/inbox"))
    parser.add_argument("--out", type=Path, default=Path("build/auto-intake"))
    parser.add_argument("--max-bytes", type=int, default=8 * 1024 * 1024)
    parser.add_argument("--include-payloads", action="store_true")
    args = parser.parse_args()
    if args.max_bytes <= 0:
        parser.error("max-bytes must be positive")
    root = args.root.resolve()
    inbox = args.inbox if args.inbox.is_absolute() else root / args.inbox
    out = args.out if args.out.is_absolute() else root / args.out
    if out.resolve().is_relative_to(inbox.resolve()):
        parser.error("output cannot be placed inside inbox")
    records, objects = plan(root, inbox, max_bytes=args.max_bytes,
                            origin_repository=os.getenv("GITHUB_REPOSITORY", "fisallllll280-code/VAIXLNS"),
                            origin_sha=os.getenv("GITHUB_SHA", "UNKNOWN"))
    write_bundle(out, records, objects, include_payloads=args.include_payloads)
    counts = {name: sum(1 for record in records if record["decision"] == name)
              for name in ("REVIEW_REQUIRED", "HELD", "BLOCKED")}
    print(json.dumps({"records": len(records), "counts": counts, "output": str(out),
                      "payloads_included": args.include_payloads}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
