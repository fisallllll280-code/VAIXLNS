"""Restore one repository from a federation archive bundle with digest verification."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile


def digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def safe_members(members: list[tarfile.TarInfo], destination: Path) -> list[tarfile.TarInfo]:
    root = destination.resolve()
    safe = []
    for member in members:
        target = (destination / member.name).resolve()
        if target != root and root not in target.parents:
            raise RuntimeError(f"ARCHIVE_PATH_TRAVERSAL:{member.name}")
        safe.append(member)
    return safe


def restore(bundle: Path, repository: str, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(bundle, "r:gz") as outer:
        manifest = json.loads(
            outer.extractfile(outer.getmember("manifest.json")).read().decode("utf-8")
        )
        record = next(
            (
                item for item in manifest.get("records", [])
                if item.get("repository") == repository and item.get("status") == "CAPTURED"
            ),
            None,
        )
        if record is None:
            raise RuntimeError("CAPTURED_REPOSITORY_NOT_FOUND")

        archive_name = next(
            name for name in outer.getnames()
            if name.endswith(".tar") and record["commit"][:12] in name
            and Path(repository.split("/", 1)[-1]).name in name
        )
        raw = outer.extractfile(outer.getmember(archive_name)).read()
        expected = record.get("archive_digest")
        if expected and digest_bytes(raw) != expected:
            raise RuntimeError("ARCHIVE_DIGEST_MISMATCH")

        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as source:
            members = safe_members(source.getmembers(), destination)
            source.extractall(destination, members=members)

    return {
        "repository": repository,
        "commit": record["commit"],
        "tree": record["tree"],
        "archive_digest": record.get("archive_digest"),
        "restored_to": str(destination),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("repository")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(args.bundle, args.repository, args.destination), ensure_ascii=False, indent=2))
