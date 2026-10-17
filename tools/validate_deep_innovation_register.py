#!/usr/bin/env python3
"""Validate the structure and preservation gates of the deep innovation register.

This validator checks inventory integrity only. It does not establish implementation,
scientific validity, readiness, canonical authority, or live deployment.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXPECTED_IDS = [f"I-{number:03d}" for number in range(1, 98)]
REQUIRED_SECTIONS = (
    "Recovery findings that govern this register",
    "Current engineering shortlist",
    "The full innovation portfolio recovered from the current master index",
    "Engineering readiness vocabulary",
    "Shortest safe execution sequence",
    "Non-negotiable preservation and safety gates",
)
FORBIDDEN_PROMOTION_CLAIMS = (
    "all 97 innovations are verified",
    "all innovations are production ready",
    "the full 2,750-item historic index is recovered",
)


def validate(text: str) -> list[str]:
    errors: list[str] = []
    ids = re.findall(r"(?<![A-Za-z0-9])I-\d{3}(?!\d)", text)
    unique_ids = sorted(set(ids))
    if unique_ids != EXPECTED_IDS:
        missing = sorted(set(EXPECTED_IDS) - set(unique_ids))
        unexpected = sorted(set(unique_ids) - set(EXPECTED_IDS))
        if missing:
            errors.append("missing portfolio IDs: " + ", ".join(missing))
        if unexpected:
            errors.append("unexpected portfolio IDs: " + ", ".join(unexpected))
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    # IDs are allowed to repeat in cross-references; only ensure all portfolio entries exist.
    del duplicates

    for heading in REQUIRED_SECTIONS:
        if heading not in text:
            errors.append(f"required section missing: {heading}")

    for claim in FORBIDDEN_PROMOTION_CLAIMS:
        if claim.casefold() in text.casefold():
            errors.append(f"unsafe blanket promotion claim found: {claim}")

    required_tokens = (
        "project.genome::v1.0.0",
        "Ω0_GENESIS_CORE",
        "UNKNOWN",
        "INCONCLUSIVE",
        "counterevidence",
        "does not itself mutate",
    )
    for token in required_tokens:
        if token.casefold() not in text.casefold():
            errors.append(f"required preservation/evidence token missing: {token}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default="docs/innovation/VAIXLNS_DEEP_INNOVATION_RECOVERY_AND_READINESS_REGISTER_V1.md",
        help="path to the markdown register",
    )
    args = parser.parse_args()
    path = Path(args.path)
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL: cannot read {path}: {exc}", file=sys.stderr)
        return 2

    errors = validate(content)
    if errors:
        print(f"FAIL: {len(errors)} register integrity issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: 97 portfolio IDs and required evidence/preservation gates are present.")
    print("NOTE: structural integrity is not implementation or readiness verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
