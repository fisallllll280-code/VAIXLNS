#!/usr/bin/env python3
"""Capture revision-pinned VX/VLNS source snapshots with fail-closed verification.

The tool only reads remote GitHub repositories. All ref creation happens inside a
throwaway mirror clone. It writes derived artifacts locally and never mutates the
source repository, VAIXLNS canonical files, or GitHub. Git LFS payloads and
submodule contents are reported as blockers unless they are present in the
captured tree; they are never silently treated as complete.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

TOOL_VERSION = "1.0.0"
PLAN_SCHEMA = "VAIXLNS.PinnedSnapshotPlan.v1"
REQUIRED_REPOSITORIES = (
    "fisallllll280-code/VX50_COMPLETE_BUILD",
    "fisallllll280-code/VX-runtime",
    "fisallllll280-code/NAXLNS",
    "fisallllll280-code/NEXENT",
)
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
LFS_POINTER_RE = re.compile(rb"(?m)^oid sha256:([0-9a-f]{64})\r?\nsize ([0-9]+)\s*$")


class SnapshotError(RuntimeError):
    """Raised when a snapshot invariant cannot be established."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], *, cwd: Path | None = None, timeout: int = 300) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SnapshotError(f"COMMAND_EXECUTION_FAILED:{command[0]}:{type(exc).__name__}") from exc
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")[-3000:]
        raise SnapshotError(f"COMMAND_FAILED:{' '.join(command[:4])}:exit={result.returncode}:{stderr}")
    return result


def git(git_dir: Path, *args: str, timeout: int = 300) -> bytes:
    return _run(["git", f"--git-dir={git_dir}", *args], timeout=timeout).stdout


def validate_plan(data: Any) -> list[dict[str, str]]:
    if not isinstance(data, dict) or data.get("schema") != PLAN_SCHEMA:
        raise SnapshotError(f"PLAN_SCHEMA_INVALID:expected {PLAN_SCHEMA}")
    entries = data.get("repositories")
    if not isinstance(entries, list):
        raise SnapshotError("PLAN_REPOSITORIES_MUST_BE_LIST")
    parsed: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise SnapshotError("PLAN_ENTRY_MUST_BE_OBJECT")
        repo = entry.get("repository")
        commit = entry.get("commit_sha")
        if not isinstance(repo, str) or repo not in REQUIRED_REPOSITORIES:
            raise SnapshotError(f"REPOSITORY_NOT_ALLOWLISTED:{repo!r}")
        if repo in parsed:
            raise SnapshotError(f"DUPLICATE_REPOSITORY:{repo}")
        if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
            raise SnapshotError(f"FULL_COMMIT_SHA_REQUIRED:{repo}")
        parsed[repo] = commit.lower()
    missing = [repo for repo in REQUIRED_REPOSITORIES if repo not in parsed]
    if missing:
        raise SnapshotError("REQUIRED_REPOSITORIES_MISSING:" + ",".join(missing))
    return [{"repository": repo, "commit_sha": parsed[repo]} for repo in REQUIRED_REPOSITORIES]


def _safe_relative_path(raw: str) -> str:
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts or raw in {".", "./"}:
        raise SnapshotError(f"UNSAFE_ARCHIVE_PATH:{raw!r}")
    normalized = path.as_posix().rstrip("/")
    if not normalized:
        raise SnapshotError(f"UNSAFE_ARCHIVE_PATH:{raw!r}")
    return normalized


def _lfs_pointer_details(prefix: bytes) -> dict[str, Any] | None:
    if not prefix.startswith(b"version https://git-lfs.github.com/spec/v1"):
        return None
    match = LFS_POINTER_RE.search(prefix)
    if not match:
        return {"detected": True, "pointer_valid": False}
    return {"detected": True, "pointer_valid": True, "oid_sha256": match.group(1).decode("ascii"), "declared_size": int(match.group(2))}


def inventory_archive(archive_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inventory: list[dict[str, Any]] = []
    lfs_gaps: list[dict[str, Any]] = []
    seen: set[str] = set()
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        symlink_paths = {_safe_relative_path(m.name) for m in members if m.issym()}
        for member in members:
            if member.isdir():
                continue
            rel = _safe_relative_path(member.name)
            if rel in seen:
                raise SnapshotError(f"DUPLICATE_ARCHIVE_PATH:{rel}")
            seen.add(rel)
            parts = PurePosixPath(rel).parts
            for index in range(1, len(parts)):
                if PurePosixPath(*parts[:index]).as_posix() in symlink_paths:
                    raise SnapshotError(f"ARCHIVE_PATH_BENEATH_SYMLINK:{rel}")
            if member.issym():
                target = member.linkname
                target_normalized = posixpath.normpath(posixpath.join(posixpath.dirname(rel), target))
                if target.startswith("/") or target_normalized == ".." or target_normalized.startswith("../"):
                    raise SnapshotError(f"UNSAFE_SYMLINK_TARGET:{rel}")
                target_bytes = target.encode("utf-8")
                inventory.append({"path": rel, "kind": "SYMLINK", "size": len(target_bytes), "sha256": sha256_bytes(target_bytes), "link_target": target})
            elif member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    raise SnapshotError(f"ARCHIVE_FILE_UNREADABLE:{rel}")
                digest = hashlib.sha256()
                prefix = stream.read(4096)
                digest.update(prefix)
                size = len(prefix)
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    size += len(chunk)
                if size != member.size:
                    raise SnapshotError(f"ARCHIVE_FILE_SIZE_MISMATCH:{rel}")
                item: dict[str, Any] = {"path": rel, "kind": "FILE", "size": size, "sha256": digest.hexdigest()}
                lfs = _lfs_pointer_details(prefix)
                if lfs:
                    item["content_kind"] = "GIT_LFS_POINTER"
                    item["lfs_pointer"] = lfs
                    lfs_gaps.append({"path": rel, **lfs, "code": "GIT_LFS_PAYLOAD_NOT_CAPTURED"})
                inventory.append(item)
            else:
                raise SnapshotError(f"UNSUPPORTED_ARCHIVE_ENTRY:{rel}")
    inventory.sort(key=lambda x: x["path"])
    return inventory, lfs_gaps


def _tree_entries(git_dir: Path, commit_sha: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    raw = git(git_dir, "ls-tree", "-r", "-z", "--full-tree", commit_sha)
    entries: list[dict[str, str]] = []
    submodules: list[dict[str, str]] = []
    for record in raw.split(b"\x00"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_type, object_sha = metadata.decode("ascii").split(" ", 2)
            path = raw_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise SnapshotError("GIT_TREE_CONTAINS_UNSUPPORTED_PATH_ENCODING_OR_ENTRY") from exc
        safe_path = _safe_relative_path(path)
        entries.append({"path": safe_path, "mode": mode, "object_type": object_type, "object_sha": object_sha})
        if mode == "160000" or object_type == "commit":
            submodules.append({"path": safe_path, "commit_sha": object_sha, "code": "SUBMODULE_CONTENT_NOT_CAPTURED"})
    return entries, submodules


def _archive_commit(git_dir: Path, commit_sha: str, out_gz: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="vaixlns-archive-") as temp_name:
        raw_tar = Path(temp_name) / "source-tree.tar"
        _run(["git", f"--git-dir={git_dir}", "archive", "--format=tar", "--output", str(raw_tar), commit_sha])
        with raw_tar.open("rb") as source, out_gz.open("xb") as destination:
            with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as compressed:
                shutil.copyfileobj(source, compressed, length=1024 * 1024)


def _restore_archive(archive_path: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        safe_members: list[tuple[tarfile.TarInfo, str]] = []
        symlink_paths: set[str] = set()
        for member in members:
            if member.isdir():
                continue
            rel = _safe_relative_path(member.name)
            safe_members.append((member, rel))
            if member.issym():
                symlink_paths.add(rel)
        for _, rel in safe_members:
            parts = PurePosixPath(rel).parts
            for index in range(1, len(parts)):
                if PurePosixPath(*parts[:index]).as_posix() in symlink_paths:
                    raise SnapshotError(f"RESTORE_PATH_BENEATH_SYMLINK:{rel}")
        for member, rel in safe_members:
            if member.issym():
                target = member.linkname
                target_normalized = posixpath.normpath(posixpath.join(posixpath.dirname(rel), target))
                if target.startswith("/") or target_normalized == ".." or target_normalized.startswith("../"):
                    raise SnapshotError(f"UNSAFE_SYMLINK_TARGET:{rel}")
                continue
            if not member.isfile():
                raise SnapshotError(f"UNSUPPORTED_RESTORE_ENTRY:{rel}")
            dest_path = dest.joinpath(*PurePosixPath(rel).parts)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            src = archive.extractfile(member)
            if src is None:
                raise SnapshotError(f"RESTORE_FILE_UNREADABLE:{rel}")
            with src, dest_path.open("xb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
            os.chmod(dest_path, member.mode & 0o777)
        for member, rel in safe_members:
            if member.issym():
                dest_path = dest.joinpath(*PurePosixPath(rel).parts)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(member.linkname, dest_path)


def inventory_tree(root: Path) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    stack = [root]
    while stack:
        current = stack.pop()
        with os.scandir(current) as iterator:
            children = sorted(iterator, key=lambda entry: entry.name, reverse=True)
        for entry in children:
            path = Path(entry.path)
            rel = path.relative_to(root).as_posix()
            if entry.is_symlink():
                target = os.readlink(path)
                raw = target.encode("utf-8")
                inventory.append({"path": rel, "kind": "SYMLINK", "size": len(raw), "sha256": sha256_bytes(raw), "link_target": target})
            elif entry.is_dir(follow_symlinks=False):
                stack.append(path)
            elif entry.is_file(follow_symlinks=False):
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    prefix = stream.read(4096)
                    digest.update(prefix)
                    size = len(prefix)
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                        size += len(chunk)
                item: dict[str, Any] = {"path": rel, "kind": "FILE", "size": size, "sha256": digest.hexdigest()}
                lfs = _lfs_pointer_details(prefix)
                if lfs:
                    item["content_kind"] = "GIT_LFS_POINTER"
                    item["lfs_pointer"] = lfs
                inventory.append(item)
            else:
                raise SnapshotError(f"UNSUPPORTED_RESTORED_ENTRY:{rel}")
    return sorted(inventory, key=lambda x: x["path"])


def _verify_bundle(bundle_path: Path, expected_commit: str) -> None:
    with tempfile.TemporaryDirectory(prefix="vaixlns-bundle-restore-") as temp_name:
        restored_git = Path(temp_name) / "restored.git"
        _run(["git", "clone", "--mirror", str(bundle_path), str(restored_git)])
        actual = _run(["git", f"--git-dir={restored_git}", "rev-parse", "refs/snapshot/pinned^{commit}"]).stdout.decode().strip()
        if actual.lower() != expected_commit.lower():
            raise SnapshotError("BUNDLE_RESTORE_COMMIT_MISMATCH")
        _run(["git", f"--git-dir={restored_git}", "fsck", "--connectivity-only"])


def capture_from_mirror(git_dir: Path, repository: str, commit_sha: str, output_root: Path) -> dict[str, Any]:
    """Capture from a temporary bare mirror. The caller must not pass a source repo."""
    repo = repository.split("/", 1)[1]
    resolved = git(git_dir, "rev-parse", f"{commit_sha}^{{commit}}").decode().strip()
    if resolved.lower() != commit_sha.lower():
        raise SnapshotError("PINNED_COMMIT_RESOLUTION_MISMATCH")
    git(git_dir, "update-ref", "refs/snapshot/pinned", resolved)
    tree_entries, submodule_gaps = _tree_entries(git_dir, resolved)

    output_root.mkdir(parents=True, exist_ok=True)
    folder = output_root / f"{repo}__{resolved[:12]}"
    folder.mkdir(parents=False, exist_ok=False)
    bundle = folder / f"{repo}.git.bundle"
    archive = folder / f"{repo}.source-tree.tar.gz"
    inventory_path = folder / f"{repo}.file-inventory.json"
    receipt_path = folder / f"{repo}.snapshot-receipt.json"

    _run(["git", f"--git-dir={git_dir}", "bundle", "create", str(bundle), "--all"])
    _run(["git", f"--git-dir={git_dir}", "bundle", "verify", str(bundle)])
    _archive_commit(git_dir, resolved, archive)
    inventory, lfs_gaps = inventory_archive(archive)
    tree_hash = sha256_bytes(canonical_json_bytes(inventory))
    bundle_hash = sha256_file(bundle)
    archive_hash = sha256_file(archive)
    blockers: list[dict[str, Any]] = [*submodule_gaps, *lfs_gaps]

    with tempfile.TemporaryDirectory(prefix="vaixlns-tree-restore-") as temp_name:
        restore_root = Path(temp_name) / "restored-tree"
        _restore_archive(archive, restore_root)
        restored_inventory = inventory_tree(restore_root)
        if canonical_json_bytes(restored_inventory) != canonical_json_bytes(inventory):
            raise SnapshotError("SOURCE_TREE_RESTORE_INVENTORY_MISMATCH")
    _verify_bundle(bundle, resolved)

    receipt: dict[str, Any] = {
        "schema": "VAIXLNS.PinnedRepositorySnapshotReceipt.v1",
        "tool_version": TOOL_VERSION,
        "repository": repository,
        "repository_url": f"https://github.com/{repository}.git",
        "commit_sha": resolved,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "capture_mode": "READ_ONLY_REMOTE_TO_LOCAL_DERIVED_SNAPSHOT",
        "source_mutation": False,
        "canonical_source_mutation": False,
        "git_history_and_refs_included": True,
        "source_tree_restore_test": "PASS",
        "git_bundle_restore_test": "PASS",
        "source_tree_file_count": len(inventory),
        "git_tree_entry_count": len(tree_entries),
        "submodule_count": len(submodule_gaps),
        "git_lfs_pointer_count": len(lfs_gaps),
        "source_tree_inventory_sha256": tree_hash,
        "artifacts": {
            bundle.name: {"sha256": bundle_hash, "bytes": bundle.stat().st_size},
            archive.name: {"sha256": archive_hash, "bytes": archive.stat().st_size},
        },
        "blockers": blockers,
        "status": "BLOCKED" if blockers else "PASS",
        "non_claims": [
            "Repository presence does not prove that a runtime is online or connected.",
            "A source snapshot is not canonical admission, implementation proof, or runtime verification.",
            "Submodule and Git LFS payloads are not assumed captured unless separately materialized and verified.",
        ],
    }
    inventory_doc = {
        "schema": "VAIXLNS.PinnedRepositoryFileInventory.v1",
        "repository": repository,
        "commit_sha": resolved,
        "entries": inventory,
        "tree_inventory_sha256": tree_hash,
        "submodule_gitlinks": submodule_gaps,
        "git_lfs_gaps": lfs_gaps,
    }
    write_json(inventory_path, inventory_doc)
    receipt["artifacts"][inventory_path.name] = {"sha256": sha256_file(inventory_path), "bytes": inventory_path.stat().st_size}
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    write_json(receipt_path, receipt)
    return receipt


def capture_repository(entry: dict[str, str], output_root: Path) -> dict[str, Any]:
    repository = entry["repository"]
    commit_sha = entry["commit_sha"]
    owner, name = repository.split("/", 1)
    if owner != "fisallllll280-code" or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise SnapshotError(f"REPOSITORY_URL_NOT_ALLOWED:{repository}")
    with tempfile.TemporaryDirectory(prefix="vaixlns-mirror-") as temp_name:
        mirror = Path(temp_name) / "mirror.git"
        url = f"https://github.com/{owner}/{name}.git"
        _run(["git", "clone", "--mirror", url, str(mirror)], timeout=900)
        return capture_from_mirror(mirror, repository, commit_sha, output_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True, help="JSON with exact repository names and full commit SHAs")
    parser.add_argument("--output-dir", type=Path, required=True, help="local derived snapshot destination; must not already contain matching snapshot folders")
    parser.add_argument("--validate-plan-only", action="store_true", help="validate the plan without network access or writes")
    args = parser.parse_args()
    try:
        data = json.loads(args.plan.read_text(encoding="utf-8"))
        plan = validate_plan(data)
        if args.validate_plan_only:
            print(json.dumps({"status": "PLAN_VALID", "repositories": plan}, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        _run(["git", "--version"], timeout=10)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        if (args.output_dir / "pinned-snapshot-batch-receipt.v1.json").exists():
            raise SnapshotError("IMMUTABLE_BATCH_RECEIPT_ALREADY_EXISTS")
        receipts: list[dict[str, Any]] = []
        blocked = False
        for entry in plan:
            try:
                receipt = capture_repository(entry, args.output_dir)
                receipts.append(receipt)
                blocked = blocked or receipt["status"] != "PASS"
            except (SnapshotError, OSError) as exc:
                receipts.append({"repository": entry["repository"], "commit_sha": entry["commit_sha"], "status": "BLOCKED", "error": f"{type(exc).__name__}:{exc}"})
                blocked = True
        summary = {
            "schema": "VAIXLNS.PinnedSnapshotBatchReceipt.v1",
            "tool_version": TOOL_VERSION,
            "plan_sha256": sha256_bytes(canonical_json_bytes(data)),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "BLOCKED" if blocked else "PASS",
            "repositories_total": len(plan),
            "repositories_passed": sum(item.get("status") == "PASS" for item in receipts),
            "repositories_blocked": sum(item.get("status") != "PASS" for item in receipts),
            "receipts": receipts,
            "source_mutation": False,
            "canonical_source_mutation": False,
        }
        summary_path = args.output_dir / "pinned-snapshot-batch-receipt.v1.json"
        if summary_path.exists():
            raise SnapshotError("IMMUTABLE_BATCH_RECEIPT_ALREADY_EXISTS")
        write_json(summary_path, summary)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
        return 2 if blocked else 0
    except (OSError, json.JSONDecodeError, SnapshotError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
