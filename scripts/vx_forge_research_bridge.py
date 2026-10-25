"""Offline integration: catalog + impossibility triage + existing Ω engineering cycle.

This module does not run models, simulate physics, or approve innovations.
"""
from __future__ import annotations
import json
from scripts.omega_engineering_cycle import build_engineering_cycle
from scripts.vx_forge_model_catalog import build_catalog, shortlist, canonical_digest
from tools.impossibility_engine.engine import assess

def plan_research(problem, model_records, *, memory_records=(), gaps=(), available_capabilities=()):
    if not isinstance(problem, dict) or not isinstance(problem.get("title"), str) or not problem["title"].strip():
        raise ValueError("problem.title required")
    if not isinstance(problem.get("goal"), str) or not problem["goal"].strip():
        raise ValueError("problem.goal required")
    capability = problem.get("capability", "research")
    catalog = build_catalog(model_records)
    selected = shortlist(catalog, capability)
    triage = assess({"title": problem["title"], "goal": problem["goal"],
                     "constraints": problem.get("constraints", []),
                     "resources": problem.get("resources", []),
                     "evidence": problem.get("evidence", [])})
    cycle = build_engineering_cycle(goal=problem["goal"], memory_records=memory_records,
                                    gaps=gaps, available_capabilities=available_capabilities)
    result = {"schema": "VX.ForgeResearchPlan.v1", "status": "PLANNED",
              "execution": "DISABLED", "provider_calls": 0, "simulation": "NOT_RUN",
              "catalog_digest": catalog["digest"], "selected_models": selected,
              "feasibility_triage": triage, "omega_cycle": cycle,
              "admission": "HOLD", "novelty": "UNASSESSED"}
    result["plan_digest"] = canonical_digest(result)
    return result

if __name__ == "__main__":
    sample = {"title": "VX indexing performance", "goal": "Reduce indexing latency with identical outputs",
              "capability": "mathematics",
              "constraints": [{"kind": "range", "variable": "latency_ms", "min": 0, "max": 1000}],
              "evidence": [{"state": "HYPOTHESIS", "source": "local-design"}]}
    models = [{"provider": "offline", "model": "symbolic-solver-placeholder",
               "version": "v0", "capabilities": ["mathematics"]}]
    result = plan_research(sample, models)
    print(json.dumps({"status": result["status"], "digest": result["plan_digest"],
                      "triage": result["feasibility_triage"]["status"],
                      "model_count": len(result["selected_models"]),
                      "execution": result["execution"]}, sort_keys=True))
