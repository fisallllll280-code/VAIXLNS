#!/usr/bin/env python3
"""Run the executable treasury admission probe and emit evidence JSON."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from treasury.paper_treasury import demo


def main() -> int:
    result = demo()
    health = result["health"]
    evidence = result["evidence"]

    required = {
        "healthy": health["status"] == "HEALTHY",
        "paper_mode": health["mode"] == "PAPER",
        "one_reconciled": health["reconciled"] == 1,
        "invariants_hold": all(health["invariants"].values()),
        "event_count_positive": evidence["event_count"] > 0,
        "state_hash_present": bool(evidence["state_hash"]),
        "events_hash_present": bool(evidence["events_hash"]),
    }
    admission = "ADMITTED" if all(required.values()) else "BLOCKED"

    output = {
        "schema": "VAIXLNS.TREASURY_ADMISSION_PROBE.v1",
        "admission": admission,
        "checks": required,
        "health": health,
        "evidence": evidence,
    }
    print(json.dumps(output, indent=2, sort_keys=True))

    if admission != "ADMITTED":
        return 1

    Path(".treasury-evidence.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    raise SystemExit(main())
