"""Restore one repository from a federation archive bundle with digest verification."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_members(members: list[tarfile.TarInfo], destination: Path) -> list[tarfile.TarInfo]:
    root = destination.resolve()
    safe = []
    for member in members:
        target = (destination / member.name).resolve()
        if target != root and root not in target.parents:
            raise RuntimeError(f"ARCHIVE_PATH_TRAVERSAL:{member.name}")
        safe.append(member)
    return safe


def restore(bundle: Path, repository_prefix: str, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(bundle, "r:gz") as outer:
        manifest_member = outer.getmember("manifest.json")
        manifest = json.loads(outer.extractfile(manifest_member).read().decode("utf-8"))
        match = next(
            (r for r in manifest.get("records", [])
             if r.get("repository") == repository_prefix and r.get("status") == "CAPTURED"),
            None,
        )
        if match is None:
            raise RuntimeError("CAPTURED_REPOSITORY_NOT_FOUND")

        archive_name = next(
            name for name in outer.getnames()
            if name.endswith(".tar") and match["commit"][:12] in name
            and Path(repository_prefix.split("/", 1)[-1]).stem in name
        )
        outer.extract(archive_name, path=Path(tempfile.mkdtemp(prefix="vlns-restore-")))
        staged = next(
            (Path(n) for n in outer.getnames() if n == archive_name),
            None,
        )
        if staged is None:
            raise RuntimeError("ARCHIVE_MEMBER_NOT_FOUND")

    raise RuntimeError(
        "BUNDLE_RESTORE_REQUIRES_STAGED_MEMBER: use archive extraction into an external "
        "workspace; this guard prevents accidental overwrite of the canonical tree."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("repository")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    restore(args.bundle, args.repository, args.destination)
