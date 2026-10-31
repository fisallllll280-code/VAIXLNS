#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

AGENT_PATH = Path("registry/agent_registry.v1.json")
INNOVATION_PATH = Path("registry/innovation_measurement.v1.json")

def main() -> int:
    agents = json.loads(AGENT_PATH.read_text(encoding="utf-8"))
    innovations = json.loads(INNOVATION_PATH.read_text(encoding="utf-8"))

    a = agents.get("agents", [])
    i = innovations.get("items", [])

    assert len(a) == 13, f"expected 13 agents, found {len(a)}"
    assert len(i) == 61, f"expected 61 innovations, found {len(i)}"

    agent_ids = {x["agent_id"] for x in a}
    innovation_ids = [x["innovation_index_id"] for x in i]

    assert len(agent_ids) == 13
    assert innovation_ids == [f"I-{n:03d}" for n in range(1, 62)]

    for x in a:
        for key in ("agent_id", "canonical_name", "capabilities", "authority_scope", "lifecycle"):
            assert x.get(key), f"agent missing {key}: {x.get('agent_id')}"

    for x in i:
        for key in ("innovation_index_id", "name", "category", "canonical_owner", "primary_agent_id"):
            assert x.get(key), f"innovation missing {key}: {x.get('innovation_index_id')}"
        assert x["primary_agent_id"] in agent_ids
        assert x["status"] == "PROPOSED"
        assert x["verification_state"] == "NOT_CLAIMED"
        assert x["implementation_state"] == "NOT_CLAIMED"

    print(f"OK: {len(a)} agents, {len(i)} innovations, agent ownership and non-promotion rules validated.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
