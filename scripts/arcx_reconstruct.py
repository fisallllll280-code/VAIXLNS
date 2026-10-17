#!/usr/bin/env python3
"""Read-only ARC-X repository reconstruction: pinned revision, file hashes, EIR and receipt."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

EXCLUDED = {".git", ".hg", ".svn", "__pycache__", ".venv", "venv", "node_modules", "dist", "build", ".tox"}
MAX_FILE_BYTES = 5 * 1024 * 1024

def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def git_revision(root: Path):
    try:
        p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = p.stdout.strip()
    return value if p.returncode == 0 and len(value) == 40 and all(c in "0123456789abcdefABCDEF" for c in value) else None

def reconstruct(root_value, expected_revision=None):
    root = Path(root_value).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("REPOSITORY_ROOT_NOT_DIRECTORY")
    revision = git_revision(root)
    if expected_revision and revision != expected_revision:
        raise ValueError("SOURCE_REVISION_MISMATCH_OR_UNAVAILABLE")
    files, skipped, unreadable, langs = [], [], [], {}
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        base = Path(current)
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not (base / d).is_symlink())
        for name in sorted(names):
            path = base / name
            if path.is_symlink() or not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if any(part in EXCLUDED for part in Path(rel).parts):
                continue
            try:
                size = path.stat().st_size
                if size > MAX_FILE_BYTES:
                    skipped.append(rel)
                    continue
                content = path.read_bytes()
            except OSError:
                unreadable.append(rel)
                files.append({"path": rel, "state": "UNREADABLE", "sha256": None})
                continue
            suffix = path.suffix.lower()
            lang = {".py":"Python",".rs":"Rust",".go":"Go",".js":"JavaScript",".ts":"TypeScript",".json":"JSON",".yml":"YAML",".yaml":"YAML",".md":"Markdown",".toml":"TOML",".sh":"Shell"}.get(suffix, "Other")
            langs[lang] = langs.get(lang, 0) + 1
            files.append({"path": rel, "state": "HASHED", "sha256": sha256(content), "size_bytes": len(content), "language": lang})
    files.sort(key=lambda x: x["path"])
    model = {"schema_version":"arcx-repository-model-v1", "repository_root_name":root.name, "source_revision":revision, "files":files, "language_file_counts":dict(sorted(langs.items())), "skipped_large_files":sorted(skipped), "exclusion_policy":sorted(EXCLUDED)}
    digest = sha256(canonical_json(model).encode())
    gaps = []
    if not revision: gaps.append({"kind":"SOURCE_REVISION_UNAVAILABLE","severity":"HIGH"})
    if unreadable: gaps.append({"kind":"UNREADABLE_FILES","severity":"HIGH","paths":sorted(unreadable)})
    if skipped: gaps.append({"kind":"FILE_SIZE_LIMIT","severity":"MEDIUM","paths":sorted(skipped),"max_file_bytes":MAX_FILE_BYTES})
    eir = {"eir_id":"eir:sha256:"+digest,"schema_version":"arcx-eir-v1","identity":{"repository_name":root.name,"source_revision":revision},"sources":[{"path":x["path"],"sha256":x["sha256"],"state":x["state"]} for x in files],"capability_observations":[{"kind":"LANGUAGE_FILE_COUNT","language":k,"count":v,"evidence_state":"OBSERVED_FROM_FILE_SUFFIX"} for k,v in sorted(langs.items())],"claims":[],"proof_obligations":[{"id":"ARCX-C1","status":"NOT_INDEPENDENTLY_VERIFIED","requirement":"Repeatable normalized manifest for pinned source"},{"id":"ARCX-C2","status":"NOT_INDEPENDENTLY_VERIFIED","requirement":"Preserve provenance for every source record"}],"gaps":gaps,"authority_decision":"PENDING","promotion_allowed":False}
    receipt = {"tool_id":"ARC-X-OMEGA","tool_version":"1.0.0","retrieval_timestamp":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"source_revision":revision,"normalized_model_sha256":digest,"file_count_hashed":sum(x["state"]=="HASHED" for x in files),"file_count_unreadable":len(unreadable),"file_count_skipped_size_limit":len(skipped),"reconstruction_state":"PARTIAL" if gaps else "RECOVERED","authority_decision":"PENDING","execution_performed":False,"canonical_write_performed":False}
    return {"model":model,"eir":eir,"receipt":receipt}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("repository")
    p.add_argument("--expected-revision")
    p.add_argument("--output", default="arcx-output")
    args=p.parse_args(argv)
    try:
        result=reconstruct(args.repository,args.expected_revision)
        out=Path(args.output).expanduser().resolve()
        out.mkdir(parents=True,exist_ok=True)
        for filename,key in (("repository.model.json","model"),("eir.json","eir"),("reconstruction.record.json","receipt")):
            (out/filename).write_text(json.dumps(result[key],ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    except (OSError,ValueError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc)}),file=sys.stderr)
        return 2
    print(json.dumps(result["receipt"],sort_keys=True))
    return 1 if result["receipt"]["reconstruction_state"]=="PARTIAL" else 0

if __name__ == "__main__":
    raise SystemExit(main())
