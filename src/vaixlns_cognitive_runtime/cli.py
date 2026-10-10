"""Command-line entry point for creating plans and saving continuity checkpoints."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .core import MemoryStore, build_task_plan


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Turn a plain-language request into an inspectable VX work plan."
    )
    parser.add_argument("request", help="The desired outcome in natural language")
    parser.add_argument(
        "--memory",
        default=os.environ.get(
            "VAIXLNS_XV_MEMORY",
            str(Path.home() / ".vaixlns" / "xv-memory.sqlite3"),
        ),
        help="Local SQLite memory path (unfixed; protect the file with OS permissions)",
    )
    parser.add_argument("--no-store", action="store_true", help="Print the plan without saving it")
    args = parser.parse_args()

    plan = build_task_plan(args.request)
    output = {"plan": plan.to_dict(), "memory_saved": False}
    if not args.no_store:
        store = MemoryStore(args.memory)
        event = store.checkpoint_plan(plan)
        output["memory_saved"] = True
        output["memory_event_id"] = event["event_id"]
        output["memory_integrity"] = store.verify_chain()
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
