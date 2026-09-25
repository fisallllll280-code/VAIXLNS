"""Deterministically normalize the innovation matrix into a sorted JSON index."""
from __future__ import annotations

import json
import re
from pathlib import Path

SOURCE = Path("docs/innovation/INNOVATION_SEPARATION_MATRIX_V1.md")
OUTPUT = Path("docs/innovation/innovation-federation.json")
VALID = {
    "VERIFIED","IMPLEMENTED","IMPLEMENTED-BASELINE","SPECIFIED","PARTIAL",
    "MISSING","CONFLICT","PROPOSAL","RECOVERED","QUARANTINED",
    "SOURCE-ASSERTED","RECOVERED / CANONICAL","RECOVERED / DERIVED",
    "IMPLEMENTED / PARTIAL","IMPLEMENTED / PARTIAL across execution surfaces",
    "IMPLEMENTED-BASELINE / SPEC","PROPOSAL / SOURCE-ASSERTED"
}

def normalize_state(raw: str) -> str:
    s = raw.upper().strip()
    if "CONFLICT" in s:
        return "CONFLICT"
    if "QUARANTINED" in s:
        return "QUARANTINED"
    if "PROPOSAL" in s:
        return "PROPOSAL"
    if "PARTIAL" in s:
        return "PARTIAL"
    if "IMPLEMENTED" in s:
        return "IMPLEMENTED"
    if "VERIFIED" in s:
        return "VERIFIED"
    if "SPECIFIED" in s:
        return "SPECIFIED"
    if "MISSING" in s:
        return "MISSING"
    if "RECOVERED" in s and "CANONICAL" in s:
        return "CANONICAL"
    if "RECOVERED" in s:
        return "RECOVERED"
    if "SOURCE-ASSERTED" in s:
        return "SOURCE-ASSERTED"
    return "PROPOSAL"


def parse() -> list[dict[str,str]]:
    rows=[]
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        cols=[c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 4 or cols[0] in {"Innovation","Family"}:
            continue
        name,family,owner,state=cols[:4]
        rows.append({
            "name":name,
            "family":family,
            "owner":owner,
            "state":normalize_state(state),
        })
    return sorted(rows,key=lambda r:(r["owner"].lower(),r["family"].lower(),r["name"].lower()))

def main() -> None:
    items=parse()
    seen=set()
    dupes=[]
    for item in items:
        key=item["name"].casefold()
        if key in seen:
            dupes.append(item["name"])
        seen.add(key)
    if dupes:
        raise SystemExit("Duplicate innovation identity: " + ", ".join(dupes))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "schema":"VAIXLNS.InnovationFederation.v1",
        "snapshot":"2026-09-25",
        "ordering":"owner -> family -> name",
        "items":items
    },indent=2,ensure_ascii=False)+"
",encoding="utf-8")

if __name__=="__main__":
    main()
