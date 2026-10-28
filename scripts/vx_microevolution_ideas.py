"""Deterministic, fail-closed evaluator for the VX MicroEvolution idea catalog."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any

REQUIRED = ("id", "title", "hypothesis", "minimal_experiment", "success_metric", "kill_criteria", "dependencies", "horizon_years", "impact", "confidence", "reversibility", "leverage", "cost", "risk", "evidence_gap", "novelty", "state")
DIMENSIONS = ("impact", "confidence", "reversibility", "leverage", "cost", "risk", "evidence_gap")


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def evaluate_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(catalog, dict) or catalog.get("schema_version") != "vx.microevolution.idea-catalog.v1":
        raise ValueError("unsupported catalog schema")
    ideas = catalog.get("ideas")
    if not isinstance(ideas, list):
        raise ValueError("ideas must be a list")
    ids: set[str] = set()
    errors: list[dict[str, str]] = []
    valid: list[dict[str, Any]] = []
    for index, idea in enumerate(ideas):
        if not isinstance(idea, dict):
            errors.append({"index": str(index), "error": "IDEA_NOT_OBJECT"})
            continue
        missing = [key for key in REQUIRED if key not in idea]
        iid = idea.get("id")
        if not isinstance(iid, str) or not iid.strip():
            errors.append({"index": str(index), "error": "INVALID_ID"})
            continue
        if iid in ids:
            errors.append({"index": str(index), "error": "DUPLICATE_ID:" + iid})
            continue
        ids.add(iid)
        if missing:
            errors.append({"index": str(index), "error": "MISSING_FIELDS:" + ",".join(missing)})
            continue
        if idea.get("novelty") != "UNASSESSED":
            errors.append({"index": str(index), "error": "NOVELTY_MUST_REMAIN_UNASSESSED:" + iid})
        if idea.get("state") not in {"PROPOSED", "RESEARCHING", "EXPERIMENT_READY", "EXPERIMENTED", "VERIFIED", "REJECTED", "SUPERSEDED"}:
            errors.append({"index": str(index), "error": "INVALID_LIFECYCLE_STATE:" + iid})
        if idea.get("horizon_years") not in (1, 3, 5):
            errors.append({"index": str(index), "error": "INVALID_HORIZON:" + iid})
        bad = [d for d in DIMENSIONS if not isinstance(idea.get(d), int) or isinstance(idea.get(d), bool) or not 0 <= idea[d] <= 5]
        if bad:
            errors.append({"index": str(index), "error": "INVALID_SCORE_DIMENSIONS:" + iid + ":" + ",".join(bad)})
        deps = idea.get("dependencies")
        if not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps):
            errors.append({"index": str(index), "error": "INVALID_DEPENDENCIES:" + iid})
        elif iid in deps:
            errors.append({"index": str(index), "error": "SELF_DEPENDENCY:" + iid})
        else:
            valid.append(idea)

    known_ids = {idea["id"] for idea in valid}
    for idea in valid:
        for dep in idea.get("dependencies", []):
            if dep not in known_ids:
                errors.append({"index": idea["id"], "error": "MISSING_DEPENDENCY:" + dep})

    # Stable topological order; cycles fail closed.
    indegree = {idea["id"]: 0 for idea in valid}
    children = {idea["id"]: [] for idea in valid}
    by_id = {idea["id"]: idea for idea in valid}
    for idea in valid:
        for dep in idea.get("dependencies", []):
            if dep in indegree:
                indegree[idea["id"]] += 1
                children[dep].append(idea["id"])
    ready = sorted(k for k, degree in indegree.items() if degree == 0)
    topo: list[str] = []
    while ready:
        current = ready.pop(0)
        topo.append(current)
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    cycles = sorted(k for k, degree in indegree.items() if degree > 0)
    if cycles:
        errors.append({"index": ",".join(cycles), "error": "DEPENDENCY_CYCLE"})

    ranked = []
    for idea in valid:
        # Multi-objective screening score is transparent and is not an adoption decision.
        benefit = idea.get("impact", 0) + idea.get("confidence", 0) + idea.get("reversibility", 0) + idea.get("leverage", 0)
        burden = idea.get("cost", 0) + idea.get("risk", 0) + idea.get("evidence_gap", 0)
        ranked.append({
            "id": idea["id"],
            "title": idea["title"],
            "horizon_years": idea["horizon_years"],
            "screening_delta": benefit - burden,
            "benefit_vector": {k: idea[k] for k in ("impact", "confidence", "reversibility", "leverage")},
            "burden_vector": {k: idea[k] for k in ("cost", "risk", "evidence_gap")},
            "novelty": "UNASSESSED",
            "adoption_decision": "NOT_AUTHORIZED",
            "state": idea["state"],
        })
    ranked.sort(key=lambda item: (-item["screening_delta"], item["horizon_years"], item["id"]))
    payload = {
        "schema_version": "vx.microevolution.idea-evaluation.v1",
        "catalog_id": catalog.get("catalog_id"),
        "catalog_digest": canonical_digest(catalog),
        "status": "BLOCKED" if errors else "SCREENED_NOT_ADMITTED",
        "idea_count": len(ideas),
        "topological_order": topo if not cycles else [],
        "dependency_cycles": cycles,
        "errors": sorted(errors, key=lambda item: (item["index"], item["error"])),
        "ranked_ideas": ranked,
        "limits": {
            "novelty_research_performed": False,
            "external_sources_checked": False,
            "experiments_executed": False,
            "runtime_verified": False,
            "authority_granted": False,
            "canonical_registry_written": False,
            "automatic_promotion": False,
        },
        "interpretation": "Screening ranks help choose experiments; they are not proof, novelty assessment, or permission to adopt.",
    }
    return payload


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default="registry/vx-microevolution-ideas.v1.json")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()
    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    report = evaluate_catalog(catalog)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\\n"
    if args.output == "-":
        print(rendered, end="")
    else:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    return 1 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
