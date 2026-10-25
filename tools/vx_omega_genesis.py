"""Read-only provenance and gap inventory. No network, agents, or repository writes."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
MAX_BYTES = 2_000_000

def inventory(root: Path, paths: list[str]) -> dict:
    root = root.resolve(strict=True)
    records, errors = [], []
    for relative in sorted(set(paths)):
        target = (root / relative).resolve()
        if not target.is_relative_to(root):
            errors.append({"path": relative, "error": "OUTSIDE_ROOT"})
            continue
        if not target.exists():
            errors.append({"path": relative, "error": "NOT_OBSERVED"})
            continue
        candidates = [target] if target.is_file() else sorted(p for p in target.rglob("*") if p.is_file())
        for path in candidates:
            if any(part in SKIP for part in path.relative_to(root).parts):
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                errors.append({"path": str(path.relative_to(root)), "error": "SYMLINK_OR_ESCAPE"})
                continue
            try:
                if path.stat().st_size > MAX_BYTES:
                    errors.append({"path": str(path.relative_to(root)), "error": "SIZE_LIMIT"})
                    continue
                data = path.read_bytes()
                records.append({"path": path.relative_to(root).as_posix(),
                                "sha256": hashlib.sha256(data).hexdigest(),
                                "bytes": len(data), "state": "OBSERVED"})
            except (OSError, PermissionError) as exc:
                errors.append({"path": str(path.relative_to(root)), "error": type(exc).__name__})
    unique = {r["path"]: r for r in records}
    return {"schema": "vx-omega-genesis.inventory.v1", "mode": "READ_ONLY",
            "records": [unique[k] for k in sorted(unique)], "exceptions": errors,
            "claims": {"verified": False, "historical_complete": False}}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--path", action="append", dest="paths")
    args = parser.parse_args()
    result = inventory(args.root, args.paths or ["docs/indexes", "registry"])
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["exceptions"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
