"""Validate the source-pinned engineering idea fusion registry (stdlib only)."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

REVISION = re.compile(r"^[0-9a-f]{40}$")
SYSTEMS = {"VAIXLNS", "VLNS", "VX", "NEXNET"}
CANONICAL_REPOSITORY = "fisallllll280-code/VAIXLNS"
REQUIRED_FORMULAS = {
    "FORMULA-VAMM-01",
    "FORMULA-THEORY-01",
    "FORMULA-SYSTEM-FORGE-01",
    "FORMULA-EXECUTION-01",
    "FORMULA-RECOVERY-01",
    "FORMULA-DIGITAL-TWIN-01",
    "FORMULA-PATTERN-FOREST-01",
    "FORMULA-EVOLUTION-01",
    "FORMULA-INTELLIGENCE-01",
}


def validate_documents(manifest: Any, schema: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(schema, dict):
        return ["SCHEMA_NOT_OBJECT"]
    if not isinstance(manifest, dict):
        return ["MANIFEST_NOT_OBJECT"]

    schema_required = set(schema.get("required", []))
    for key in (
        "schema_version", "manifest_id", "snapshot_date", "state", "purpose",
        "authority", "official_system_crosswalk", "source_repositories",
        "canonical_integration_pipeline", "recovered_engineering_pipelines",
        "non_mergeable_or_deferred", "acceptance_gates",
    ):
        if key not in schema_required:
            errors.append(f"SCHEMA_REQUIRED_FIELD_MISSING:{key}")
        if key not in manifest:
            errors.append(f"MANIFEST_FIELD_MISSING:{key}")

    if manifest.get("schema_version") != "1.0.0":
        errors.append("UNSUPPORTED_MANIFEST_SCHEMA_VERSION")
    if manifest.get("state") != "PROPOSAL":
        errors.append("FUSION_MUST_REMAIN_PROPOSAL_UNTIL_REVIEWED")
    try:
        date.fromisoformat(str(manifest.get("snapshot_date", "")))
    except ValueError:
        errors.append("INVALID_SNAPSHOT_DATE")

    authority = manifest.get("authority")
    if not isinstance(authority, dict):
        errors.append("AUTHORITY_NOT_OBJECT")
    else:
        expected = {
            "repository": CANONICAL_REPOSITORY,
            "project_genome": "READ_ONLY",
            "omega_000_master_index": "READ_ONLY",
            "canonical_mutation": "DISABLED",
        }
        for field, required_value in expected.items():
            if authority.get(field) != required_value:
                errors.append(f"CANONICAL_BOUNDARY_MISMATCH:{field}")

    crosswalk = manifest.get("official_system_crosswalk")
    if not isinstance(crosswalk, list):
        errors.append("SYSTEM_CROSSWALK_NOT_ARRAY")
        crosswalk = []
    system_ids = [x.get("system_id") for x in crosswalk if isinstance(x, dict)]
    if len(system_ids) != len(set(system_ids)):
        errors.append("DUPLICATE_OFFICIAL_SYSTEM_ID")
    if set(system_ids) != SYSTEMS or len(system_ids) != 4:
        errors.append("OFFICIAL_SYSTEM_SET_MISMATCH")
    by_id = {x.get("system_id"): x for x in crosswalk if isinstance(x, dict)}
    for name in ("VAIXLNS", "VLNS", "VX", "NEXNET"):
        if name not in by_id:
            continue
        item = by_id[name]
        if not isinstance(item.get("repository_candidates"), list):
            errors.append(f"INVALID_REPOSITORY_CANDIDATES:{name}")
        if not isinstance(item.get("identity_state"), str) or not item["identity_state"]:
            errors.append(f"MISSING_IDENTITY_STATE:{name}")
    if "VLNS" in by_id:
        if any(str(candidate).rstrip("/").split("/")[-1].casefold() == "naxlns" for candidate in by_id["VLNS"].get("repository_candidates", [])):
            errors.append("UNSUPPORTED_VLNS_NAXLNS_ALIAS")
        if "UNVERIFIED" not in by_id["VLNS"].get("identity_state", ""):
            errors.append("VLNS_MAPPING_MUST_REMAIN_UNVERIFIED")
    if "NEXNET" in by_id:
        if by_id["NEXNET"].get("repository_candidates"):
            errors.append("NEXNET_IDENTITY_CANDIDATES_REQUIRE_EVIDENCE")
        if not any(term in by_id["NEXNET"].get("identity_state", "") for term in ("UNRESOLVED", "NOT_RESOLVED")):
            errors.append("NEXNET_MAPPING_MUST_REMAIN_UNRESOLVED")

    sources = manifest.get("source_repositories")
    if not isinstance(sources, list) or len(sources) < 8:
        errors.append("SOURCE_REPOSITORY_INVENTORY_INCOMPLETE")
        sources = sources if isinstance(sources, list) else []
    repositories: list[str] = []
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"SOURCE_ENTRY_NOT_OBJECT:{index}")
            continue
        repo = source.get("repository")
        revision = source.get("source_revision")
        blob_sha = source.get("source_blob_sha")
        path = source.get("source_path")
        url = source.get("source_url")
        label = str(repo or index)
        if not isinstance(repo, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            errors.append(f"INVALID_SOURCE_REPOSITORY:{label}")
        else:
            repositories.append(repo)
        if not isinstance(revision, str) or not REVISION.fullmatch(revision):
            errors.append(f"INVALID_SOURCE_REVISION:{label}")
        if not isinstance(blob_sha, str) or not REVISION.fullmatch(blob_sha):
            errors.append(f"INVALID_SOURCE_BLOB_SHA:{label}")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            errors.append(f"INVALID_SOURCE_PATH:{label}")
        if all(isinstance(v, str) and v for v in (repo, revision, path, url)):
            expected_url = f"https://github.com/{repo}/blob/{revision}/{path}"
            if url != expected_url:
                errors.append(f"SOURCE_URL_NOT_PINNED:{label}")
        if not isinstance(source.get("evidence_class"), str) or not source["evidence_class"]:
            errors.append(f"MISSING_EVIDENCE_CLASS:{label}")
        if not isinstance(source.get("integration_candidates"), list):
            errors.append(f"INVALID_INTEGRATION_CANDIDATES:{label}")
    if len(repositories) != len(set(repositories)):
        errors.append("DUPLICATE_SOURCE_REPOSITORY")

    if "fisallllll280-code/NEXENT" not in repositories:
        errors.append("NEXENT_SOURCE_LINEAGE_MISSING")
    if "fisallllll280-code/NAXLNS" not in repositories:
        errors.append("NAXLNS_REVIEW_SOURCE_MISSING")

    formulas = manifest.get("recovered_engineering_pipelines")
    if not isinstance(formulas, list):
        errors.append("RECOVERED_FORMULAS_NOT_ARRAY")
        formulas = []
    formula_ids = [x.get("id") for x in formulas if isinstance(x, dict)]
    if len(formula_ids) != len(set(formula_ids)):
        errors.append("DUPLICATE_FORMULA_ID")
    if set(formula_ids) != REQUIRED_FORMULAS:
        errors.append("RECOVERED_FORMULA_SET_INCOMPLETE_OR_UNEXPECTED")
    for formula in formulas:
        if not isinstance(formula, dict):
            errors.append("FORMULA_ENTRY_NOT_OBJECT")
            continue
        if formula.get("state") != "RECOVERED_FORMULATION":
            errors.append(f"FORMULA_STATE_MUST_NOT_PROMOTE:{formula.get('id')}")
        stages = formula.get("stages")
        if not isinstance(stages, list) or len(stages) < 2 or any(not isinstance(x, str) or not x for x in stages):
            errors.append(f"INVALID_FORMULA_STAGES:{formula.get('id')}")

    pipeline = manifest.get("canonical_integration_pipeline")
    if not isinstance(pipeline, list) or len(pipeline) < 10 or any(not isinstance(x, str) for x in pipeline):
        errors.append("INTEGRATION_PIPELINE_INCOMPLETE")
    gates = manifest.get("acceptance_gates")
    if not isinstance(gates, list) or len(gates) < 5:
        errors.append("ACCEPTANCE_GATES_INCOMPLETE")
    if not isinstance(manifest.get("non_mergeable_or_deferred"), dict):
        errors.append("DEFERRED_BOUNDARIES_NOT_OBJECT")

    return errors


def load_and_validate(root: Path) -> list[str]:
    try:
        manifest = json.loads((root / "registry/federation/engineering_idea_fusion.v1.json").read_text(encoding="utf-8"))
        schema = json.loads((root / "schemas/engineering-idea-fusion.v1.schema.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"INPUT_READ_FAILED:{type(exc).__name__}:{exc}"]
    return validate_documents(manifest, schema)


def main(argv: list[str] | None = None) -> int:
    root = Path(argv[0]).resolve() if argv else Path(__file__).resolve().parents[1]
    errors = load_and_validate(root)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({
        "valid": True,
        "state": "PROPOSAL",
        "source_count": 8,
        "recovered_formula_count": 9,
        "canonical_mutation": "DISABLED",
        "identity_aliasing": "BLOCKED_UNLESS_EVIDENCED",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
