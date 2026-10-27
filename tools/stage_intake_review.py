#!/usr/bin/env python3
"""Stage non-secret text to a review branch; leave binary/cross-repo files held."""
import argparse
import json
import os
from pathlib import Path
from auto_intake import plan, hash_bytes, is_sensitive

SAFE_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".toml"}
ALLOWED_TARGETS = (
    "docs/indexes/intake/", "docs/innovation/intake/", "docs/agents/intake/",
    "docs/library/intake/", "registry/models/intake/", "registry/evidence/intake/",
    "archive/source/intake/",
)

def stage(root: Path, inbox: Path) -> dict:
    root = root.resolve()
    records, _ = plan(
        root, inbox.resolve(),
        origin_repository=os.getenv("GITHUB_REPOSITORY", "fisallllll280-code/VAIXLNS"),
        origin_sha=os.getenv("GITHUB_SHA", "UNKNOWN"))
    materialized, held = [], []
    for item in records:
        if item["decision"] != "REVIEW_REQUIRED":
            held.append(item["source_path"])
            continue
        if item.get("target_repository") != "VAIXLNS" or not item.get("target_path", "").startswith(ALLOWED_TARGETS):
            held.append(item["source_path"])
            continue
        source = root / item["source_path"]
        if source.suffix.casefold() not in SAFE_SUFFIXES or source.is_symlink() or not source.is_file():
            held.append(item["source_path"])
            continue
        raw = source.read_bytes()
        if hash_bytes(raw) != item["sha256"] or is_sensitive(raw):
            held.append(item["source_path"])
            continue
        targets = [root / item["library_object"], root / item["target_path"]]
        if any(not path.resolve().is_relative_to(root) for path in targets):
            raise ValueError("unsafe destination path")
        for target in targets:
            if target.exists() and target.read_bytes() != raw:
                raise ValueError("would overwrite a non-identical destination")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        materialized.append(item["source_path"])
    library_index = root / "library/intake/auto-intake.v1.jsonl"
    library_index.parent.mkdir(parents=True, exist_ok=True)
    with library_index.open("w", encoding="utf-8") as output:
        for item in records:
            entry = dict(item)
            entry["review_materialized"] = entry["source_path"] in materialized
            output.write(json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return {"review_materialized": len(materialized), "held_or_external": len(held), "catalog": "library/intake/auto-intake.v1.jsonl"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--inbox", type=Path, default=Path("intake/inbox"))
    args = parser.parse_args()
    root = args.root.resolve()
    inbox = args.inbox if args.inbox.is_absolute() else root / args.inbox
    print(json.dumps(stage(root, inbox), sort_keys=True))
