#!/usr/bin/env python3
"""Measure VAIXLNS innovation registry entries conservatively.

This is a traceability/readiness tool, not a scientific benchmark.
It never converts UNKNOWN/PROPOSED into VERIFIED.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


EVIDENCE_POINTS = {
    "VERIFIED": 15,
    "IMPLEMENTED": 10,
    "CANONICAL": 7,
    "RECOVERED": 5,
    "SPECIFIED": 3,
    "NOT_YET_PROVEN_AT_ITEM_LEVEL": 0,
    "MISSING": 0,
    "CONFLICT": 0,
}

IMPLEMENTATION_POINTS = {
    "VERIFIED": 15,
    "IMPLEMENTED": 12,
    "NOT_CLAIMED": 0,
    "MISSING": 0,
    "CONFLICT": 0,
}

VERIFICATION_POINTS = {
    "VERIFIED": 15,
    "IMPLEMENTED": 5,
    "NOT_CLAIMED": 0,
    "MISSING": 0,
    "CONFLICT": 0,
}

LINEAGE_POINTS = {
    "COMPLETE": 10,
    "PARTIAL": 5,
    "REQUIRED_BUT_ITEM_MAPPING_PENDING": 0,
    "MISSING": 0,
    "CONFLICT": 0,
}


def readiness_score(item: dict[str, Any]) -> int:
    score = 0
    score += 15 if item.get("innovation_index_id") else 0
    score += 10 if item.get("category") else 0
    score += 10 if item.get("canonical_owner") else 0
    score += 10 if item.get("primary_agent_id") else 0
    score += EVIDENCE_POINTS.get(item.get("evidence_state", ""), 0)
    score += IMPLEMENTATION_POINTS.get(item.get("implementation_state", ""), 0)
    score += VERIFICATION_POINTS.get(item.get("verification_state", ""), 0)
    score += LINEAGE_POINTS.get(item.get("lineage_state", ""), 0)
    return min(score, 100)


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "registry/innovation_measurement.v1.json")
    if not path.exists():
        print(f"registry not found: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items", [])
    if not isinstance(items, list) or not items:
        print("registry contains no items", file=sys.stderr)
        return 3

    ids = set()
    failures = []
    scores = []

    for item in items:
        iid = item.get("innovation_index_id")
        if not iid or iid in ids:
            failures.append(f"duplicate/missing innovation_index_id: {iid!r}")
        ids.add(iid)

        computed = readiness_score(item)
        scores.append(computed)
        item["computed_readiness_score"] = computed

        required = [
            "innovation_index_id",
            "name",
            "category",
            "canonical_owner",
            "primary_agent_id",
            "primary_agent",
            "status",
            "evidence_state",
            "implementation_state",
            "verification_state",
            "lineage_state",
        ]
        missing = [k for k in required if k not in item]
        if missing:
            failures.append(f"{iid}: missing fields {missing}")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 4

    data["computed_summary"] = {
        "item_count": len(items),
        "min_readiness": min(scores),
        "max_readiness": max(scores),
        "average_readiness": round(sum(scores) / len(scores), 2),
        "strategic_strength_top10": [
            {
                "innovation_index_id": x["innovation_index_id"],
                "name": x["name"],
                "strategic_strength_score": x["strategic_strength_score"],
                "computed_readiness_score": x["computed_readiness_score"],
            }
            for x in sorted(
                items,
                key=lambda x: (x["strategic_strength_score"], x["computed_readiness_score"]),
                reverse=True,
            )[:10]
        ],
        "status_counts": {
            status: sum(1 for x in items if x.get("status") == status)
            for status in sorted({x.get("status") for x in items})
        },
    }

    print(json.dumps(data["computed_summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
