#!/usr/bin/env python3
"""Run deterministic Ω-Arena conformance/simulation.

This command does not claim live provider execution unless an adapter endpoint
is configured. It can still validate the full orchestration, scoring, attribution,
and seven-day revalidation mechanics locally.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path

from intelligence_federation.arena import (
    ArenaManifest,
    Candidate,
    MatchResult,
    OmegaArena,
    build_invention_record,
    validate_attribution,
)
from intelligence_federation.provider_adapters import default_adapters


ROOT = Path(__file__).resolve().parents[1]


def build_demo(now: datetime) -> dict:
    manifest = ArenaManifest(
        arena_id="Ω-ARENA-DEMO-001",
        task_id="capability-composition-demo",
        protocol_version="1.0.0",
        task_corpus_hash="demo-corpus",
        environment_hash="local-deterministic",
        participants=tuple(adapter.descriptor.provider_id for adapter in default_adapters()),
        phases=(
            "independent_solution",
            "evidence_submission",
            "execution",
            "verification",
            "adversarial_attack",
            "repair",
            "re_execution",
            "final_verdict",
        ),
    )
    arena = OmegaArena(manifest)

    first_success = (now - timedelta(days=8)).isoformat().replace("+00:00", "Z")
    candidates = [
        (
            Candidate("team-claude-gpt", "anthropic", ("openai", "anthropic-code"), capability_ids=("reasoning", "coding")),
            MatchResult(
                "team-claude-gpt", first_success,
                {"correctness": 96, "reproducibility": 92, "security": 95, "completeness": 94,
                 "contradiction_resistance": 91, "evidence_quality": 93, "robustness": 90, "innovation": 97},
                ("demo:evidence:001", "demo:verification:001", "demo:replay:001"),
                True, innovation_fingerprint="demo-innovation-001",
                first_observation_event="event:arena:001", first_success_event="event:success:001",
            ),
        ),
        (
            Candidate("team-gemini-mistral", "google", ("mistral",), capability_ids=("research", "reasoning")),
            MatchResult(
                "team-gemini-mistral", first_success,
                {"correctness": 94, "reproducibility": 89, "security": 93, "completeness": 92,
                 "contradiction_resistance": 88, "evidence_quality": 90, "robustness": 87, "innovation": 95},
                ("demo:evidence:002", "demo:verification:002", "demo:replay:002"),
                True, innovation_fingerprint="demo-innovation-002",
                first_observation_event="event:arena:002", first_success_event="event:success:002",
            ),
        ),
        (
            Candidate("team-atomkit", "atomkit", ("anthropic-code",), capability_ids=("engineering", "qa")),
            MatchResult(
                "team-atomkit", first_success,
                {"correctness": 91, "reproducibility": 90, "security": 94, "completeness": 93,
                 "contradiction_resistance": 86, "evidence_quality": 88, "robustness": 92, "innovation": 84},
                ("demo:evidence:003", "demo:verification:003", "demo:replay:003"),
                True, innovation_fingerprint="demo-innovation-003",
                first_observation_event="event:arena:003", first_success_event="event:success:003",
            ),
        ),
    ]
    result = arena.rank(candidates, now=now.isoformat())
    attribution = {
        item.candidate_id: build_invention_record(candidate, match)
        for candidate, match in candidates
        if match.innovation_fingerprint
    }
    attribution_checks = {
        candidate_id: validate_attribution(record)
        for candidate_id, record in attribution.items()
    }
    return {
        "arena_id": manifest.arena_id,
        "frozen_hash": arena.frozen_hash,
        "status": result.status,
        "champion_candidate_id": result.champion_candidate_id,
        "ranking": [item.__dict__ for item in result.ranking],
        "attribution": attribution,
        "attribution_checks": {
            key: {"valid": value[0], "errors": list(value[1])}
            for key, value in attribution_checks.items()
        },
        "provider_conformance": [
            {"provider_id": a.descriptor.provider_id, "ok": a.conform()[0], "errors": list(a.conform()[1])}
            for a in default_adapters()
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("simulate", "conformance"), default="simulate")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    if args.mode == "simulate":
        payload = build_demo(now)
    else:
        adapters = default_adapters()
        payload = {
            "mode": "conformance",
            "providers": [
                {
                    "provider_id": a.descriptor.provider_id,
                    "ok": a.conform()[0],
                    "errors": list(a.conform()[1]),
                    "capabilities": list(a.capabilities()),
                }
                for a in adapters
            ],
        }
        if any(not entry["ok"] for entry in payload["providers"]):
            return_code = 1
        else:
            return_code = 0

    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        print(rendered, end="")
    else:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
