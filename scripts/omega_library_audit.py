#!/usr/bin/env python3
"""Read-only offline dependency + test inventory. No installs, network or writes to repo."""
import argparse
import hashlib
import json
import pathlib
import re
from datetime import datetime, timezone

MANIFEST_NAMES = {"requirements.txt","requirements-dev.txt","pyproject.toml","Pipfile","Pipfile.lock","poetry.lock","uv.lock","package.json","package-lock.json","pnpm-lock.yaml","yarn.lock","Cargo.toml","Cargo.lock","go.mod","go.sum","Gemfile","Gemfile.lock"}
EXCLUDE = {".git","node_modules",".venv","venv","__pycache__","dist","build"}
def inventory(root: pathlib.Path):
    root = root.resolve()
    out = {"schema":"vaixlns-library-audit-v1","root":str(root),"status":"INVENTORY_ONLY","manifests":[],"tests":[],"workflows":[],"warnings":[],"execution_performed":False}
    for path in root.rglob("*"):
        if any(p in EXCLUDE for p in path.relative_to(root).parts):
            continue
        if not path.is_file() or path.is_symlink():
            continue
        rel=path.relative_to(root).as_posix()
        kind=("manifests" if path.name in MANIFEST_NAMES else "workflows" if rel.startswith(".github/workflows/") and path.suffix in {".yml",".yaml"} else "tests" if (path.name.startswith("test_") and path.suffix==".py") or (path.name.endswith(".test.js") or path.name.endswith(".spec.ts")) else None)
        if kind is None: continue
        try:
            raw=path.read_bytes()
        except OSError as err:
            out["warnings"].append({"path":rel,"error":type(err).__name__})
            continue
        out[kind].append({"path":rel,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
    for key in ("manifests","tests","workflows"):
        out[key].sort(key=lambda x:x["path"])
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",default=".")
    parser.add_argument("--output")
    args=parser.parse_args()
    root=pathlib.Path(args.root)
    if not root.is_dir(): parser.error("root is not a directory")
    result=inventory(root)
    data=json.dumps(result,indent=2,ensure_ascii=False)
    if args.output:
        out=pathlib.Path(args.output).resolve()
        if out.is_relative_to(root.resolve()):
            parser.error("output must be outside the inspected repository")
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(data+"\n",encoding="utf-8")
    else:
        print(data)
if __name__=="__main__": main()
