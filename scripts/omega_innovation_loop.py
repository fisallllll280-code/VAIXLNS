"""Bounded, read-only Ω engineering loop: index -> graph -> scenario -> evidence.
No network calls, repository writes, approvals or deployments.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def analyze(index_path: Path, scenario: str = "dependency-loss") -> dict:
    raw = index_path.read_bytes()
    obj = json.loads(raw)
    records = obj.get("records")
    if not isinstance(records, list):
        raise ValueError("master index must contain records list")
    nodes = {}
    for rec in records:
        if not isinstance(rec, dict) or not isinstance(rec.get("id"), str):
            raise ValueError("invalid index record")
        ident = rec["id"]
        if ident in nodes:
            raise ValueError("duplicate record ID: " + ident)
        nodes[ident] = rec
    edges = []
    for ident, rec in nodes.items():
        parent = rec.get("parent")
        if isinstance(parent, str):
            edges.append({"source": ident, "target": parent, "type": "parent", "resolved": parent in nodes})
    unresolved = [e for e in edges if not e["resolved"]]
    if scenario != "dependency-loss":
        raise ValueError("unsupported scenario")
    # Deterministic static fault-injection: model the loss of one indexed node.
    selected = sorted(nodes)[0] if nodes else None
    affected = sorted(e["source"] for e in edges if e["target"] == selected)
    return {
        "schema_version": "1.0",
        "status": "SIMULATED_NOT_VERIFIED",
        "source_sha256": digest(raw),
        "index_id": obj.get("index_id"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "unresolved_edges": unresolved,
        "simulation": {"scenario": scenario, "failed_node": selected, "direct_dependents": affected},
        "admission": {"eligible": False, "reason": "No independent verification or authorized approval"},
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="registry/omega/omega-000-master-index.json")
    parser.add_argument("--output", help="optional local JSON report path")
    args = parser.parse_args()
    result = analyze(Path(args.index))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

if __name__ == "__main__":
    main()
