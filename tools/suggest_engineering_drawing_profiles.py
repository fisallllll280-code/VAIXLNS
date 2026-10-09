"""Suggest engineering drawing standard profiles without silently selecting a code."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAUDI_MARKERS = {"sa", "saudi", "saudi arabia", "saudi arabia (sa)", "sbc", "sa-sbc"}


def suggest_profiles(job: object, registry: object) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(job, dict):
        return {"valid_request": False, "errors": ["job must be a JSON object"], "suggestions": []}
    if not isinstance(registry, dict) or not isinstance(registry.get("profiles"), list):
        return {"valid_request": False, "errors": ["profile registry is malformed"], "suggestions": []}

    discipline = job.get("discipline")
    jurisdiction = job.get("jurisdiction")
    allowed_disciplines = {
        "architectural", "civil_structural", "mechanical", "electrical",
        "process_piping", "robotics", "scientific", "other",
    }
    if not isinstance(discipline, str) or discipline not in allowed_disciplines:
        errors.append("discipline must be explicitly supported")
    if not isinstance(jurisdiction, str) or not jurisdiction.strip():
        errors.append("jurisdiction must be explicit")
    if errors:
        return {"valid_request": False, "errors": errors, "suggestions": []}

    jurisdiction_key = jurisdiction.casefold().strip()
    is_saudi = (
        jurisdiction_key in SAUDI_MARKERS
        or "saudi arabia" in jurisdiction_key
        or jurisdiction_key.startswith("sa-sbc")
    )

    suggestions: list[dict[str, object]] = []
    for profile in registry["profiles"]:
        if not isinstance(profile, dict):
            warnings.append("Malformed profile entry skipped")
            continue
        domains = profile.get("discipline")
        if not isinstance(domains, list) or discipline not in domains:
            continue

        profile_id = profile.get("id")
        if profile_id == "SAUDI-BUILDING-2024" and not is_saudi:
            continue
        standards = profile.get("standards", [])
        if not isinstance(standards, list):
            warnings.append(f"Malformed standards list in profile {profile_id}")
            continue
        suggestions.append({
            "profile_id": profile_id,
            "purpose": profile.get("purpose", ""),
            "registry_state": registry.get("registry_state", "UNKNOWN"),
            "suggested_standards": [
                {
                    "code": item.get("code"),
                    "edition": item.get("edition"),
                    "source_uri": item.get("url"),
                }
                for item in standards
                if isinstance(item, dict)
            ],
            "selection_state": "SUGGESTED_NOT_SELECTED",
            "requires_confirmation": True,
        })

    mechanical_candidates = {
        item["profile_id"]
        for item in suggestions
        if item.get("profile_id") in {"MECHANICAL-GDT-ISO", "MECHANICAL-GDT-ASME"}
    }
    if mechanical_candidates == {"MECHANICAL-GDT-ISO", "MECHANICAL-GDT-ASME"}:
        warnings.append(
            "ISO GPS and ASME GD&T are alternatives here; select the contractual system explicitly. "
            "Do not combine their defaults implicitly."
        )
    if not suggestions:
        warnings.append("No matching reference profile was found; author a reviewed project-specific profile.")

    return {
        "schema": "VAIXLNS.EngineeringDrawingProfileSuggestion.v1",
        "valid_request": True,
        "discipline": discipline,
        "jurisdiction": jurisdiction,
        "registry_state": registry.get("registry_state", "UNKNOWN"),
        "mode": "SUGGEST_ONLY",
        "auto_selected_profiles": [],
        "human_confirmation_required": True,
        "suggestions": sorted(suggestions, key=lambda item: str(item["profile_id"])),
        "warnings": sorted(set(warnings)),
        "errors": [],
        "scope_notice": (
            "Suggestions are not standards approval, proof of applicability, code compliance, "
            "an engineering calculation, or certification. Recheck current editions and project "
            "authority requirements before use."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path, help="Job JSON containing discipline and jurisdiction")
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("registry/engineering_drawing_profiles.v1.json"),
        help="Path to the profile registry",
    )
    args = parser.parse_args()
    try:
        job = json.loads(args.job.read_text(encoding="utf-8"))
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid_request": False, "errors": [str(exc)]}, indent=2), file=sys.stderr)
        return 2

    result = suggest_profiles(job, registry)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid_request"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
