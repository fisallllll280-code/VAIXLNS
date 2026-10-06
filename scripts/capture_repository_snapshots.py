"""Capture reproducible Git snapshots for the VAIXLNS federation registry.

The script keeps credentials outside the repository and records commit, tree and
archive digests. Accessible source trees are bundled for recovery.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "repository_registry.v1.json"

def run(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        list(args), cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"command_failed:{args[0]}")
    return result.stdout.strip()

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def clone_repository(repository: str, destination: Path) -> None:
    token = os.getenv("VAIXLNS_FEDERATION_TOKEN") or os.getenv("GITHUB_TOKEN")
    url = f"https://github.com/{repository}.git"
    if token:
        run("git", "-c", f"http.extraheader=AUTHORIZATION: bearer {token}",
            "clone", "--depth", "1", url, str(destination))
    else:
        run("git", "clone", "--depth", "1", url, str(destination))

def capture() -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    capture_root = Path(tempfile.mkdtemp(prefix="vaixlns-snapshot-"))
    sources = capture_root / "sources"
    sources.mkdir()
    records = []
    try:
        for entry in data["repositories"]:
            status = str(entry.get("status", ""))
            repository = entry.get("repository") or f"fisallllll280-code/{entry['name']}"
            if status == "planned" or entry.get("evidence_state") == "PLANNED":
                records.append({"repository": repository, "status": "SKIPPED_PLANNED"})
                continue
            destination = sources / entry["name"].replace("/", "__")
            try:
                clone_repository(repository, destination)
                commit = run("git", "rev-parse", "HEAD", cwd=destination)
                tree = run("git", "rev-parse", "HEAD^{tree}", cwd=destination)
                tar_path = capture_root / f"{entry['name'].replace('/', '__')}-{commit[:12]}.tar"
                with tarfile.open(tar_path, "w") as archive:
                    for item in sorted(destination.iterdir(), key=lambda p: p.name):
                        archive.add(item, arcname=item.name)
                records.append({
                    "repository": repository,
                    "ref": run("git", "rev-parse", "--abbrev-ref", "HEAD", cwd=destination),
                    "commit": commit,
                    "tree": tree,
                    "archive_digest": f"sha256:{sha256_file(tar_path)}",
                    "status": "CAPTURED",
                })
            except Exception as exc:
                records.append({
                    "repository": repository,
                    "status": "CAPTURE_FAILED",
                    "error": str(exc),
                })
        manifest = {
            "schema_version": "1.0",
            "capture_id": f"ARCHIVE-{timestamp}",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "policy": "zero-loss",
            "records": records,
        }
        manifest_path = capture_root / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        output_dir = ROOT / "archive" / "captures"
        output_dir.mkdir(parents=True, exist_ok=True)
        published_manifest = output_dir / f"{manifest['capture_id']}.json"
        shutil.copy2(manifest_path, published_manifest)
        bundle = ROOT / "archive" / f"vaixlns-federation-{manifest['capture_id']}.tar.gz"
        with tarfile.open(bundle, "w:gz") as archive:
            archive.add(manifest_path, arcname="manifest.json")
            for tar_path in sorted(capture_root.glob("*.tar")):
                archive.add(tar_path, arcname=tar_path.name)
        return {
            "capture_id": manifest["capture_id"],
            "manifest": str(published_manifest.relative_to(ROOT)),
            "bundle": str(bundle.relative_to(ROOT)),
            "records": records,
        }
    finally:
        shutil.rmtree(capture_root, ignore_errors=True)

if __name__ == "__main__":
    print(json.dumps(capture(), ensure_ascii=False, indent=2))
