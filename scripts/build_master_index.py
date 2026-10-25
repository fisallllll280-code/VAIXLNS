#!/usr/bin/env python3
"""Build immutable, source-bound MASTER INDEX views over Zero-Loss records.

Consumes a captured GitHub metadata envelope, never probes services, merges
identities, promotes claims or rewrites canonical source files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import quote

try:
    from .build_zero_loss_index import build_payloads, ARTIFACT_NAMES, IndexBuildError
except ImportError:
    from build_zero_loss_index import build_payloads, ARTIFACT_NAMES, IndexBuildError

SCHEMA = "VAIXLNS.MasterIndexCapture.v1"
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
OID = re.compile(r"[0-9a-f]{40}")


class MasterIndexError(ValueError):
    pass


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, reason):
    if not condition:
        raise MasterIndexError(reason)


def valid_oid(value):
    return isinstance(value, str) and OID.fullmatch(value) is not None


def validate_capture(capture):
    require(isinstance(capture, dict) and capture.get("schema") == SCHEMA, "CAPTURE_SCHEMA_INVALID")
    require(isinstance(capture.get("observed_at"), str) and bool(capture["observed_at"]), "OBSERVATION_TIME_REQUIRED")
    known = set()
    for repo in capture["repositories"]:
        name = repo["repository"]
        require(isinstance(name, str) and REPO.fullmatch(name), "REPOSITORY_ID_INVALID")
        require(name not in known, "DUPLICATE_REPOSITORY")
        require(repo.get("visibility") == "public", "RESTRICTED_METADATA_REQUIRES_PRIVATE_STORAGE")
        known.add(name)
    for scope in ("repositories", "trees", "branches", "pull_requests"):
        coverage = capture.get("coverage", {}).get(scope, {})
        # A metadata capture cannot prove global or historical completeness.
        require(coverage.get("state") == "PARTIAL" and bool(coverage.get("reason")), "COVERAGE_MUST_DECLARE_LIMITS")
    trees_seen, branches_seen, prs_seen = set(), set(), set()
    for tree in capture["trees"]:
        require(tree["repository"] in known, "UNKNOWN_TREE_REPOSITORY")
        require(valid_oid(tree["commit"]) and valid_oid(tree["tree_sha"]), "TREE_REVISION_NOT_PINNED")
        require(tree.get("truncated") is False, "TRUNCATED_TREE_REJECTED")
        identity = (tree["repository"], tree["commit"])
        require(identity not in trees_seen, "DUPLICATE_TREE")
        trees_seen.add(identity)
        paths = set()
        for entry in tree["entries"]:
            path = entry["path"]
            require(isinstance(path, str) and bool(path) and not PurePosixPath(path).is_absolute()
                    and ".." not in PurePosixPath(path).parts and "\\" not in path
                    and PurePosixPath(path).as_posix() == path and path != ".", "UNSAFE_TREE_PATH")
            require(path not in paths, "DUPLICATE_TREE_PATH")
            paths.add(path)
            require(valid_oid(entry["sha"]), "INVALID_GIT_OBJECT_ID")
            allowed = {"blob": {"100644", "100755", "120000"}, "tree": {"040000"}, "commit": {"160000"}}
            require(entry.get("mode") in allowed.get(entry["type"], set()), "UNSUPPORTED_GIT_OBJECT")
    for branch in capture["branches"]:
        require(branch["repository"] in known and valid_oid(branch["commit"]), "INVALID_BRANCH_SOURCE")
        require(isinstance(branch["name"], str) and bool(branch["name"]), "INVALID_BRANCH_NAME")
        key = (branch["repository"], branch["name"])
        require(key not in branches_seen, "DUPLICATE_BRANCH")
        branches_seen.add(key)
    for pr in capture["pull_requests"]:
        require(pr["repository"] in known and type(pr["number"]) is int and pr["number"] > 0, "INVALID_PR_IDENTITY")
        require(valid_oid(pr["head_commit"]) and valid_oid(pr["base_commit"]), "UNPINNED_PR")
        require(pr.get("state") in {"open", "closed"}, "INVALID_PR_STATE")
        key = (pr["repository"], pr["number"])
        require(key not in prs_seen, "DUPLICATE_PR")
        prs_seen.add(key)


def build_records(capture):
    validate_capture(capture)
    result = []

    def add(kind, identity, source, value):
        result.append({
            "id": "MASTER-" + sha(encode([kind, identity, value])),
            "kind": kind, "identity": identity, "source": source,
            "observation_sha256": sha(encode(value)), "observed_at": capture["observed_at"],
            "adoption_status": "UNVERIFIED", "metadata": value,
        })

    for repo in sorted(capture["repositories"], key=lambda r: r["repository"]):
        name = repo["repository"]
        add("REPOSITORY", name, f"https://api.github.com/repos/{name}", repo)
    for tree in sorted(capture["trees"], key=lambda t: (t["repository"], t["commit"])):
        name, commit = tree["repository"], tree["commit"]
        for entry in sorted(tree["entries"], key=lambda e: e["path"]):
            path = entry["path"]
            kind = {"blob": "FILE", "tree": "DIRECTORY", "commit": "SUBMODULE"}[entry["type"]]
            add(kind, f"{name}@{commit}/{path}",
                f"https://github.com/{name}/{'tree' if kind == 'DIRECTORY' else 'blob'}/{commit}/{quote(path, safe='/')}",
                {**entry, "repository": name, "source_commit": commit,
                 "git_object_digest": {"algorithm": "git-sha1", "value": entry["sha"]},
                 "content_sha256": None, "content_state": "NOT_FETCHED"})
    for branch in sorted(capture["branches"], key=lambda b: (b["repository"], b["name"])):
        add("BRANCH", f"{branch['repository']}:{branch['name']}",
            f"https://api.github.com/repos/{branch['repository']}/branches/{quote(branch['name'], safe='')}", branch)
    for pr in sorted(capture["pull_requests"], key=lambda p: (p["repository"], p["number"])):
        add("PULL_REQUEST", f"{pr['repository']}#{pr['number']}",
            f"https://github.com/{pr['repository']}/pull/{pr['number']}", pr)
    return result


def build_master_index(capture_path: Path, output: Path, *, root: Path | None = None):
    raw = capture_path.read_bytes()
    capture = json.loads(raw)
    records = build_records(capture)
    zero_loss = {}
    if root is not None:
        # Reuse the existing semantic/innovation extractor and its 28 views.
        # It hashes exact local bytes; it does not certify remote tree content.
        zero_loss = build_payloads(root, output)
        for line in zero_loss[ARTIFACT_NAMES["records"]].decode().splitlines():
            atomic = json.loads(line)
            records.append({
                "id": "ZEROLOSS-" + atomic["uid"], "kind": "SEMANTIC_RECORD",
                "identity": atomic["uid"], "source": atomic["source_location"],
                "content_sha256": atomic["source_sha256"],
                "adoption_status": "UNVERIFIED", "source_claimed_status": atomic["source_claimed_status"],
                "metadata": atomic,
            })
    records.sort(key=lambda r: (r["kind"], r["identity"], r["id"]))
    record_bytes = b"".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() + b"\n" for r in records)
    payloads = {"capture.json": raw, "records.jsonl": record_bytes, **zero_loss}
    manifest = {
        "schema": "VAIXLNS.MasterIndex.v1", "name": "VAIXLNS MASTER INDEX Ω∞",
        "authority": "VAIXLNS", "canonical_source": "project.genome", "master_index": "Ω.000",
        "status": "DERIVED_UNVERIFIED", "capture_sha256": sha(raw),
        "observed_at": capture["observed_at"], "coverage": capture["coverage"],
        "counts": dict(sorted(Counter(r["kind"] for r in records).items())),
        "semantic_extraction": "ZERO_LOSS_28_VIEWS" if root is not None else "NOT_CAPTURED",
        "source_checkout_revision": json.loads(zero_loss[ARTIFACT_NAMES["index"]])["source_revision"] if zero_loss else None,
        "identity_merges": 0, "canonical_promotions": 0,
        "limitations": ["No historical completeness claim.", "Git object IDs are not raw-content SHA-256.",
                        "Metadata and source claims do not prove runtime or adoption.",
                        "Local Zero-Loss source bytes are a separate scope from captured remote trees.",
                        "No alias equivalence inferred for VLNS/NAXLNS or NEXNET/NEXENT."],
        "artifacts": {name: sha(value) for name, value in sorted(payloads.items())},
    }
    payloads["manifest.json"] = encode(manifest)
    snapshot_id = sha(payloads["manifest.json"])
    destination = output / snapshot_id
    if destination.exists():
        for name, value in payloads.items():
            require((destination / name).read_bytes() == value, "IMMUTABLE_SNAPSHOT_CONFLICT")
    else:
        # Each build has a content-addressed directory; earlier builds are retained.
        # Stage the complete bundle before exposing the final directory.
        import tempfile
        output.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".master-stage-", dir=output) as stage:
            for name, value in payloads.items():
                (Path(stage) / name).write_bytes(value)
            Path(stage).rename(destination)
    return verify_snapshot(destination)


def verify_snapshot(directory: Path):
    manifest_bytes = (directory / "manifest.json").read_bytes()
    require(sha(manifest_bytes) == directory.name, "MANIFEST_DIGEST_MISMATCH")
    manifest = json.loads(manifest_bytes)
    require(manifest.get("schema") == "VAIXLNS.MasterIndex.v1", "MANIFEST_SCHEMA_INVALID")
    require(manifest.get("canonical_promotions") == 0 and manifest.get("identity_merges") == 0, "FORBIDDEN_PROMOTION_OR_MERGE")
    for name, expected in manifest["artifacts"].items():
        require(Path(name).name == name and name not in {".", ".."}, "UNSAFE_ARTIFACT_PATH")
        require(sha((directory / name).read_bytes()) == expected, "ARTIFACT_DIGEST_MISMATCH:" + name)
    capture = json.loads((directory / "capture.json").read_bytes())
    validate_capture(capture)
    rows = [json.loads(line) for line in (directory / "records.jsonl").read_bytes().splitlines()]
    require(len({r["id"] for r in rows}) == len(rows), "DUPLICATE_RECORD_ID")
    require(all(r["adoption_status"] == "UNVERIFIED" for r in rows), "AUTOMATIC_ADOPTION_FORBIDDEN")
    require(dict(Counter(r["kind"] for r in rows)) == manifest["counts"], "COUNTS_MISMATCH")
    expected = build_records(capture)
    require([r for r in rows if r["kind"] != "SEMANTIC_RECORD"] == sorted(expected, key=lambda r: (r["kind"], r["identity"], r["id"])), "CAPTURE_RECORDS_MISMATCH")
    return {"state": "PASS", "snapshot_id": directory.name, "counts": manifest["counts"],
            "canonical_promotions": 0, "identity_merges": 0, "coverage": "PARTIAL"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("build/master-index"))
    parser.add_argument("--root", type=Path, help="Optional checkout for existing Zero-Loss semantic extraction")
    parser.add_argument("--verify", type=Path, help="Verify a content-addressed snapshot directory")
    args = parser.parse_args(argv)
    if bool(args.capture) == bool(args.verify):
        parser.error("provide exactly one of --capture or --verify")
    try:
        result = verify_snapshot(args.verify) if args.verify else build_master_index(args.capture, args.output_dir, root=args.root)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexBuildError) as exc:
        print(f"MASTER_INDEX_FAILURE:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
