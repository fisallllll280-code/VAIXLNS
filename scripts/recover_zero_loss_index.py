#!/usr/bin/env python3
"""Recover and verify a loss-preserving index bundle from one pinned checkout.

This orchestrator runs the existing index tests, rebuilds the 28-view ZERO-LOSS
INDEX, verifies the generated hashes, and writes a separate recovery receipt.
It never edits project.genome, Ω.000, source records, or repository history.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BUILDER = Path("scripts/build_zero_loss_index.py")
TEST_PATTERN = "test_zero_loss_index.py"
ARTIFACTS = (
    "zero-loss-index.v1.json",
    "zero-loss-source-index.v1.json",
    "zero-loss-atomic-records.v1.jsonl",
    "zero-loss-coverage.v1.json",
    "zero-loss-cross-reference.v1.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository checkout to index")
    parser.add_argument("--output-dir", type=Path, default=Path("build/zero-loss-index"), help="generated output directory")
    parser.add_argument("--skip-tests", action="store_true", help="skip unit tests (not recommended)")
    args = parser.parse_args()

    root = args.root.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    builder = root / BUILDER
    if not root.is_dir() or not builder.is_file():
        print("INDEX_RECOVERY_BLOCKED: repository root or deterministic builder is missing", file=sys.stderr)
        return 2

    receipt: dict[str, Any] = {
        "schema": "VAIXLNS.IndexRecoveryReceipt.v1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(root),
        "output_dir": str(output_dir),
        "authority": "VAIXLNS",
        "canonical_source": "project.genome::v1.0.0",
        "master_index": "Ω.000",
        "source_mutation": "PROHIBITED",
        "canonical_promotion": "DISABLED",
        "status": "PENDING_VERIFICATION",
        "steps": [],
    }

    commands: list[tuple[str, list[str]]] = []
    if not args.skip_tests:
        commands.append(("unit_tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", TEST_PATTERN, "-v"]))
    commands.extend([
        ("build", [sys.executable, str(BUILDER), "--root", str(root), "--output-dir", str(output_dir)]),
        ("verify", [sys.executable, str(BUILDER), "--root", str(root), "--output-dir", str(output_dir), "--verify-only"]),
    ])

    for step_name, command in commands:
        result = run(command, root)
        step: dict[str, Any] = {
            "name": step_name,
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout[-12000:],
            "stderr": result.stderr[-12000:],
            "status": "PASS" if result.returncode == 0 else "FAIL",
        }
        if step_name in {"build", "verify"} and result.returncode == 0:
            try:
                parsed = json.loads(result.stdout)
                step["summary"] = parsed
            except json.JSONDecodeError:
                step["status"] = "FAIL"
                step["stderr"] += "\\nExpected JSON verification summary was not returned."
        receipt["steps"].append(step)
        if step["status"] != "PASS":
            receipt["status"] = "BLOCKED"
            receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "index-recovery-receipt.v1.json").write_text(
                json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\\n",
                encoding="utf-8",
            )
            print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2))
            return 2

    missing = [name for name in ARTIFACTS if not (output_dir / name).is_file()]
    if missing:
        receipt["status"] = "BLOCKED"
        receipt["missing_artifacts"] = missing
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index-recovery-receipt.v1.json").write_text(
            json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\\n",
            encoding="utf-8",
        )
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2))
        return 2

    receipt["artifact_hashes"] = {name: sha256(output_dir / name) for name in ARTIFACTS}
    coverage = json.loads((output_dir / "zero-loss-coverage.v1.json").read_text(encoding="utf-8"))
    receipt["coverage_summary"] = {
        "source_count": coverage.get("source_count"),
        "atomic_records_created": coverage.get("atomic_records_created"),
        "opaque_sources_pending_extraction": len(coverage.get("opaque_sources", [])),
        "canonical_promotions_performed": coverage.get("canonical_promotions_performed", 0),
        "legacy_id_coverage": coverage.get("legacy_id_coverage", {}),
    }
    receipt["status"] = "PASS_WITH_DECLARED_GAPS" if (
        receipt["coverage_summary"]["opaque_sources_pending_extraction"]
        or receipt["coverage_summary"]["legacy_id_coverage"].get("unresolved_candidate_gap_ranges")
    ) else "PASS"
    receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    receipt_path = output_dir / "index-recovery-receipt.v1.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
