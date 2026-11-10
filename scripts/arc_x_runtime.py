#!/usr/bin/env python3
"""ARC-X Ω minimal deterministic repository reconstruction runtime.

Inventories a pinned Git worktree, hashes source files, emits provenance-bearing
EIR artifacts, and verifies/replays them. It does not prove semantics or grant
canonical authority.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_ID = "ARC-X-OMEGA"
TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = "arc-x.eir.v1"
GENERATED_DIR = ".arcx"
EXCLUDED_DIRS = {".git", ".arcx", "__pycache__", ".venv", "venv", "env",
                 ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules",
                 "dist", "build", ".tox"}
EXCLUDED_FILE_NAMES = {".env", ".env.local", ".env.production", ".env.development"}
EXCLUDED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore"}
EXCLUDED_SECRET_DIRS = {"secrets", "private_keys", "credentials"}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(canonical_json_bytes(value))


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                            text=True, encoding="utf-8", errors="replace", check=False)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(f"GIT_COMMAND_FAILED:{' '.join(args)}:{detail}")
    return result


def _inside(rel: str, parent: str | None) -> bool:
    rel = rel.replace("\\", "/").strip("/")
    if rel == GENERATED_DIR or rel.startswith(GENERATED_DIR + "/"):
        return True
    if parent:
        parent = parent.replace("\\", "/").strip("/")
        return rel == parent or rel.startswith(parent + "/")
    return False


def git_state(root: Path, output_dir: Path) -> dict[str, Any]:
    revision = _git(root, "rev-parse", "HEAD").stdout.strip()
    raw_status = _git(root, "status", "--porcelain", "-z", "--untracked-files=all").stdout
    try:
        output_rel = output_dir.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        output_rel = None
    dirty_paths = []
    for entry in raw_status.split("\0"):
        if not entry:
            continue
        rel = entry[3:] if len(entry) >= 4 else entry[2:]
        rel = rel.strip()
        if rel and not _inside(rel, output_rel):
            dirty_paths.append(rel)
    return {"revision": revision, "working_tree_clean": not dirty_paths,
            "dirty_paths": sorted(set(dirty_paths))}


def _exclude_file(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    if any(part.lower() in EXCLUDED_SECRET_DIRS for part in parts[:-1]):
        return True
    name = path.name.lower()
    return (name in EXCLUDED_FILE_NAMES or name.startswith(".env.")
            or path.suffix.lower() in EXCLUDED_SUFFIXES
            or name in {"id_rsa", "id_ed25519", "credentials.json", "service-account.json"})


def source_manifest(root: Path, output_dir: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    try:
        output_rel = output_dir.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        output_rel = None
    manifest: list[dict[str, Any]] = []
    excluded = {"generated_or_cache": 0, "secret_material": 0, "symlink": 0}
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept = []
        for name in sorted(dirnames):
            child = current_path / name
            rel = child.relative_to(root).as_posix()
            if name in EXCLUDED_DIRS or _inside(rel, output_rel):
                excluded["generated_or_cache"] += 1
            elif child.is_symlink():
                excluded["symlink"] += 1
            else:
                kept.append(name)
        dirnames[:] = kept
        for filename in sorted(filenames):
            path = current_path / filename
            rel = path.relative_to(root).as_posix()
            if _inside(rel, output_rel):
                excluded["generated_or_cache"] += 1
                continue
            if path.is_symlink():
                excluded["symlink"] += 1
                continue
            if _exclude_file(path, root):
                excluded["secret_material"] += 1
                continue
            try:
                payload = path.read_bytes()
            except OSError as exc:
                raise RuntimeError(f"SOURCE_READ_FAILED:{rel}:{exc}") from exc
            manifest.append({"path": rel, "sha256": digest_bytes(payload), "size_bytes": len(payload)})
    manifest.sort(key=lambda item: item["path"])
    return manifest, excluded


def extract_identity(root: Path) -> dict[str, Any]:
    path = root / "project.genome"
    if not path.is_file():
        return {"state": "MISSING", "system_id": root.name, "canonical_repository": None,
                "authority_anchor": None, "master_index": None, "source_ref": None}
    try:
        genome = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"state": "CONFLICT", "system_id": root.name, "canonical_repository": None,
                "authority_anchor": None, "master_index": None, "source_ref": "project.genome",
                "issue": "PROJECT_GENOME_PARSE_FAILURE"}
    system = genome.get("system", {}) if isinstance(genome, dict) else {}
    genesis = genome.get("genesis", {}) if isinstance(genome, dict) else {}
    master = genome.get("master_index", {}) if isinstance(genome, dict) else {}
    canonical = genome.get("canonical_source", {}) if isinstance(genome, dict) else {}
    return {"state": "OBSERVED", "system_id": system.get("id") or root.name,
            "canonical_repository": system.get("canonical_repository"),
            "authority_anchor": genesis.get("authority_anchor"), "master_index": master.get("id"),
            "canonical_source_status": canonical.get("status"), "source_ref": "project.genome"}


def build_snapshot(root: Path, output_dir: Path, expected_revision: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise RuntimeError(f"ROOT_NOT_DIRECTORY:{root}")
    output_dir = output_dir.resolve()
    git = git_state(root, output_dir)
    if expected_revision and expected_revision != git["revision"]:
        raise RuntimeError(f"REVISION_PIN_MISMATCH:expected={expected_revision}:actual={git['revision']}")
    manifest, exclusions = source_manifest(root, output_dir)
    return {"root": root, "output_dir": output_dir, "git": git, "manifest": manifest,
            "exclusions": exclusions, "content_hash": digest_json(manifest),
            "identity": extract_identity(root)}


def build_eir(snapshot: dict[str, Any]) -> dict[str, Any]:
    manifest = snapshot["manifest"]
    paths = [item["path"] for item in manifest]
    path_set = set(paths)
    tests = [p for p in paths if p.startswith("tests/") or "/tests/" in p]
    scripts = [p for p in paths if p.startswith("scripts/") or p.startswith("tools/")]
    workflows = [p for p in paths if p.startswith(".github/workflows/")]
    schemas = [p for p in paths if p.startswith("schemas/") or "/schemas/" in p]
    identity = snapshot["identity"]
    source = {"repository": identity.get("canonical_repository") or snapshot["root"].name,
              "revision": snapshot["git"]["revision"], "content_hash": snapshot["content_hash"],
              "working_tree_clean": snapshot["git"]["working_tree_clean"]}
    observations = [
        {"observation_id": "repository.file_count", "kind": "FILE_COUNT",
         "value": len(manifest), "source_refs": paths, "classification": "OBSERVATION"},
        {"observation_id": "repository.test_surface", "kind": "FILE_SURFACE",
         "value": {"count": len(tests), "present": bool(tests)},
         "source_refs": tests, "classification": "OBSERVATION"},
        {"observation_id": "repository.workflow_surface", "kind": "FILE_SURFACE",
         "value": {"count": len(workflows), "present": bool(workflows)},
         "source_refs": workflows, "classification": "OBSERVATION"},
        {"observation_id": "repository.implementation_surface", "kind": "FILE_SURFACE",
         "value": {"count": len(scripts), "present": bool(scripts)},
         "source_refs": scripts, "classification": "OBSERVATION"},
        {"observation_id": "repository.schema_surface", "kind": "FILE_SURFACE",
         "value": {"count": len(schemas), "present": bool(schemas)},
         "source_refs": schemas, "classification": "OBSERVATION"},
    ]
    if "project.genome" in path_set:
        observations.append({"observation_id": "repository.project_genome", "kind": "IDENTITY_SOURCE",
            "value": {key: identity.get(key) for key in ("state", "system_id", "canonical_repository",
                     "authority_anchor", "master_index", "canonical_source_status")},
            "source_refs": ["project.genome"], "classification": "OBSERVATION"})
    gaps = []
    if identity["state"] == "MISSING":
        gaps.append({"gap_id": "gap.project_genome", "type": "IDENTITY_SOURCE_NOT_OBSERVED", "status": "OPEN"})
    elif identity["state"] == "CONFLICT":
        gaps.append({"gap_id": "gap.project_genome_parse", "type": "IDENTITY_SOURCE_PARSE_CONFLICT", "status": "OPEN"})
    return {"schema_version": SCHEMA_VERSION, "object_type": "EpistemicIntermediateRepresentation",
            "tool_id": TOOL_ID, "tool_version": TOOL_VERSION,
            "eir_id": "EIR-" + snapshot["content_hash"][:20], "source": source, "identity": identity,
            "observations": observations, "claims": [], "inferences": [], "proof_obligations": [],
            "contradiction_analysis": {"status": "NOT_RUN", "records": []}, "gaps": gaps,
            "governance": {"self_authority": False, "authority_decision": "PENDING",
                           "canonical_write_permitted": False},
            "verification": {"source_integrity": "NOT_RUN", "semantic_correctness": "NOT_CLAIMED",
                             "formal_proof": "NOT_RUN"}}


def build_artifacts(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    manifest = snapshot["manifest"]
    eir = build_eir(snapshot)
    revision = snapshot["git"]["revision"]
    identity = snapshot["identity"]
    captured = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    repository = identity.get("canonical_repository") or snapshot["root"].name
    receipt = {"schema_version": "arc-x.source-receipt.v1", "kind": "SOURCE_RETRIEVAL_RECEIPT",
        "tool_id": TOOL_ID, "tool_version": TOOL_VERSION, "repository": repository,
        "source_revision": revision, "working_tree_clean": snapshot["git"]["working_tree_clean"],
        "dirty_paths": snapshot["git"]["dirty_paths"], "content_hash": snapshot["content_hash"],
        "hash_algorithm": "SHA-256", "manifest_entry_count": len(manifest), "materials": manifest,
        "excluded_file_counts": snapshot["exclusions"], "retrieval_timestamp": captured,
        "revision_pin_enforced": True}
    count = lambda prefixes: sum(1 for item in manifest if item["path"].startswith(prefixes))
    model = {"schema_version": "arc-x.repository-model.v1", "repository": repository,
        "source_revision": revision, "content_hash": snapshot["content_hash"], "identity": identity,
        "summary": {"file_count": len(manifest),
            "test_files": sum(1 for item in manifest if item["path"].startswith("tests/") or "/tests/" in item["path"]),
            "workflow_files": count(".github/workflows/"),
            "implementation_surface_files": count(("scripts/", "tools/")),
            "schema_files": sum(1 for item in manifest if item["path"].startswith("schemas/") or "/schemas/" in item["path"])},
        "manifest": manifest,
        "scope_limit": "File inventory and identity extraction only; no semantic code analysis is claimed."}
    record = {"tool_id": TOOL_ID, "tool_version": TOOL_VERSION,
        "system_id": identity.get("system_id") or snapshot["root"].name, "repository": repository,
        "source_revision": revision, "content_hash": snapshot["content_hash"], "retrieval_timestamp": captured,
        "reconstruction_id": "RCN-" + snapshot["content_hash"][:20], "eir_id": eir["eir_id"],
        "eir_digest": digest_json(eir), "verification_state": "PARTIAL",
        "dependency_resolution": "PENDING", "startup_result": "PENDING", "health_result": "PENDING",
        "test_result": "PENDING", "proof_status": "PENDING", "authority_decision": "PENDING",
        "execution_evidence": None, "previous_state": None,
        "transition_reason": "Deterministic repository inventory generated; semantic proof, runtime startup, and governed admission not attempted.",
        "working_tree_clean": snapshot["git"]["working_tree_clean"], "self_authority": False}
    return {"source.receipt.json": receipt, "repository.model.json": model,
            "eir.json": eir, "reconstruction.record.json": record}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def reconstruct(root: Path, output_dir: Path, expected_revision: str | None = None) -> dict[str, Any]:
    snapshot = build_snapshot(root, output_dir, expected_revision)
    artifacts = build_artifacts(snapshot)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in artifacts.items():
        _write_json(output_dir / name, value)
    return {"result": "RECONSTRUCTION_CREATED", "tool_id": TOOL_ID,
            "source_revision": snapshot["git"]["revision"], "content_hash": snapshot["content_hash"],
            "file_count": len(snapshot["manifest"]), "working_tree_clean": snapshot["git"]["working_tree_clean"],
            "verification_state": "PARTIAL", "authority_decision": "PENDING",
            "output_dir": str(output_dir), "eir_id": artifacts["eir.json"]["eir_id"],
            "eir_digest": digest_json(artifacts["eir.json"])}


def verify_artifacts(root: Path, output_dir: Path) -> dict[str, Any]:
    root, output_dir = root.resolve(), output_dir.resolve()
    names = ("source.receipt.json", "repository.model.json", "eir.json", "reconstruction.record.json")
    loaded = {}
    for name in names:
        path = output_dir / name
        if not path.is_file():
            raise RuntimeError(f"ARTIFACT_MISSING:{name}")
        try:
            loaded[name] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"ARTIFACT_INVALID_JSON:{name}:{exc}") from exc
    receipt = loaded["source.receipt.json"]
    snapshot = build_snapshot(root, output_dir, receipt.get("source_revision"))
    if snapshot["content_hash"] != receipt.get("content_hash"):
        raise RuntimeError("SOURCE_CONTENT_HASH_MISMATCH")
    if snapshot["manifest"] != receipt.get("materials"):
        raise RuntimeError("SOURCE_MANIFEST_MISMATCH")
    if snapshot["git"]["working_tree_clean"] != receipt.get("working_tree_clean"):
        raise RuntimeError("WORKTREE_STATE_MISMATCH")
    expected_eir = build_eir(snapshot)
    if canonical_json_bytes(expected_eir) != canonical_json_bytes(loaded["eir.json"]):
        raise RuntimeError("EIR_RECONSTRUCTION_MISMATCH")
    if digest_json(loaded["eir.json"]) != loaded["reconstruction.record.json"].get("eir_digest"):
        raise RuntimeError("EIR_DIGEST_MISMATCH")
    if loaded["reconstruction.record.json"].get("authority_decision") != "PENDING":
        raise RuntimeError("INVALID_AUTHORITY_STATE:reconstruction cannot self-authorize")
    if loaded["reconstruction.record.json"].get("verification_state") == "VERIFIED":
        raise RuntimeError("INVALID_VERIFICATION_PROMOTION:reconstruction alone is not semantic proof")
    report = {"schema_version": "arc-x.integrity-report.v1", "result": "PASS",
        "source_revision": snapshot["git"]["revision"], "content_hash": snapshot["content_hash"],
        "eir_id": expected_eir["eir_id"], "eir_digest": digest_json(expected_eir),
        "checks": {"revision_pin": "PASS", "source_manifest": "PASS", "source_hash": "PASS",
                   "eir_reconstruction": "PASS", "eir_digest": "PASS", "no_self_authority": "PASS",
                   "no_semantic_proof_claim": "PASS"},
        "semantic_correctness": "NOT_CLAIMED", "authority_decision": "PENDING",
        "verification_state": "PARTIAL"}
    _write_json(output_dir / "verification.report.json", report)
    return report


def inspect_artifacts(output_dir: Path) -> dict[str, Any]:
    path = output_dir / "reconstruction.record.json"
    if not path.is_file():
        raise RuntimeError("ARTIFACT_MISSING:reconstruction.record.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    return {"result": "INSPECTED", "tool_id": record.get("tool_id"),
        "source_revision": record.get("source_revision"), "content_hash": record.get("content_hash"),
        "eir_id": record.get("eir_id"), "verification_state": record.get("verification_state"),
        "test_result": record.get("test_result"), "proof_status": record.get("proof_status"),
        "authority_decision": record.get("authority_decision"),
        "self_authority": record.get("self_authority"), "execution_evidence": record.get("execution_evidence")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARC-X Ω deterministic source-to-EIR runtime")
    subs = parser.add_subparsers(dest="command", required=True)
    for name in ("reconstruct", "verify", "replay"):
        item = subs.add_parser(name)
        item.add_argument("--root", type=Path, default=Path.cwd())
        item.add_argument("--output", type=Path, default=Path.cwd() / GENERATED_DIR)
        if name == "reconstruct":
            item.add_argument("--revision", help="Require this exact Git HEAD commit SHA.")
    inspect = subs.add_parser("inspect")
    inspect.add_argument("--output", type=Path, default=Path.cwd() / GENERATED_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "reconstruct":
            result = reconstruct(args.root, args.output, args.revision)
        elif args.command == "verify":
            result = verify_artifacts(args.root, args.output)
        elif args.command == "replay":
            result = {**verify_artifacts(args.root, args.output), "result": "REPLAY_MATCH"}
        else:
            result = inspect_artifacts(args.output)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        print(json.dumps({"result": "FAIL", "command": args.command, "error": str(exc),
            "verification_state": "PARTIAL", "authority_decision": "PENDING"},
            ensure_ascii=False, sort_keys=True, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
