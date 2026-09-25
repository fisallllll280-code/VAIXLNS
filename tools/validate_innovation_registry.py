"""Fail-closed validation for the innovation separation matrix."""
from __future__ import annotations

from pathlib import Path
import json

MATRIX=Path("docs/innovation/INNOVATION_SEPARATION_MATRIX_V1.md")
SCHEMA=Path("schemas/innovation-federation.schema.json")
GENERATED=Path("docs/innovation/innovation-federation.json")

def main()->None:
    assert MATRIX.exists(), "Missing innovation matrix"
    assert SCHEMA.exists(), "Missing innovation schema"
    assert GENERATED.exists(), "Generated innovation index is stale or missing"
    data=json.loads(GENERATED.read_text(encoding="utf-8"))
    assert data.get("schema")=="VAIXLNS.InnovationFederation.v1"
    names=[item["name"].casefold() for item in data.get("items",[])]
    assert len(names)==len(set(names)), "Duplicate canonical innovation identity"
    for item in data["items"]:
        for key in ("name","family","owner","state"):
            assert item.get(key), f"Missing {key}: {item}"
    print(f"VALID innovation federation: {len(names)} identities")

if __name__=="__main__":
    main()
