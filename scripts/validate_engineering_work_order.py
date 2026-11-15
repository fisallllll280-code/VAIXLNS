#!/usr/bin/env python3
"""Read-only Engineering Work Order validator and deterministic planner.

The validator enforces every assertion keyword currently used by the repository's
JSON Schema contract. If a new assertion keyword is introduced that this bounded
implementation does not support, schema validation fails closed rather than
silently ignoring it. This tool never dispatches tasks or authorizes side effects.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
EXECUTION_RANK = {"PLAN_ONLY": 0, "SANDBOX": 1, "AUTHORIZED_EXECUTION": 2}
DATA_RANK = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}
ACTIVE_STATES = {"QUEUED", "LEASED", "RUNNING", "RESULT_SUBMITTED", "VERIFYING", "ACCEPTED"}

ANNOTATION_KEYWORDS = {"$schema", "$id", "$comment", "title", "description", "default", "examples"}
ASSERTION_KEYWORDS = {
    "type", "properties", "required", "additionalProperties", "items", "enum", "const",
    "minLength", "maxLength", "pattern", "format", "minItems", "maxItems", "uniqueItems",
    "minimum", "maximum",
}
SUPPORTED_KEYWORDS = ANNOTATION_KEYWORDS | ASSERTION_KEYWORDS
SUPPORTED_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}
SUPPORTED_FORMATS = {"uri", "date-time"}


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool/int equality ambiguity."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isfinite(left) and math.isfinite(right) and left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(_json_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, dict):
        return (
            left.keys() == right.keys()
            and all(_json_equal(left[key], right[key]) for key in left)
        )
    return left == right


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _is_uri(value: str) -> bool:
    if not value or any(char.isspace() for char in value):
        return False
    if re.search(r"%(?![0-9A-Fa-f]{2})", value):
        return False
    try:
        parts = urlsplit(value)
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*", parts.scheme):
            return False
        if parts.scheme.lower() in {"http", "https"} and not parts.netloc:
            return False
        _ = parts.port  # Force validation of malformed ports.
        return True
    except ValueError:
        return False


def _is_rfc3339_datetime(value: str) -> bool:
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
        return True
    except ValueError:
        return False


def validate_schema_definition(schema: Any) -> list[str]:
    """Reject malformed schemas and every unsupported assertion keyword."""
    errors: list[str] = []
    if not isinstance(schema, dict):
        return ["schema must be a JSON object"]
    if schema.get("$schema") != SCHEMA_DIALECT:
        errors.append(f"schema.$schema must be {SCHEMA_DIALECT}")

    def walk(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            errors.append(f"{path}: subschema must be an object")
            return
        for keyword in node:
            if keyword not in SUPPORTED_KEYWORDS:
                errors.append(f"{path}: unsupported schema keyword: {keyword}")

        if "type" in node:
            expected = node["type"]
            types = expected if isinstance(expected, list) else [expected]
            if (
                not types
                or any(not isinstance(item, str) or item not in SUPPORTED_TYPES for item in types)
                or len(types) != len(set(types))
            ):
                errors.append(f"{path}.type: unsupported or malformed JSON type declaration")

        if "properties" in node:
            properties = node["properties"]
            if not isinstance(properties, dict):
                errors.append(f"{path}.properties: must be an object")
            else:
                for name, child in properties.items():
                    walk(child, f"{path}.properties.{name}")

        if "items" in node:
            if not isinstance(node["items"], dict):
                errors.append(f"{path}.items: only a schema object is supported")
            else:
                walk(node["items"], f"{path}.items")

        if "additionalProperties" in node:
            additional = node["additionalProperties"]
            if isinstance(additional, dict):
                walk(additional, f"{path}.additionalProperties")
            elif not isinstance(additional, bool):
                errors.append(f"{path}.additionalProperties: must be boolean or schema object")

        if "required" in node:
            required = node["required"]
            if (
                not isinstance(required, list)
                or any(not isinstance(item, str) for item in required)
                or len(required) != len(set(required))
            ):
                errors.append(f"{path}.required: must be an array of unique strings")

        if "pattern" in node:
            try:
                re.compile(node["pattern"])
            except (TypeError, re.error):
                errors.append(f"{path}.pattern: invalid regular expression")

        if "format" in node and node["format"] not in SUPPORTED_FORMATS:
            errors.append(f"{path}.format: unsupported format assertion")

        for key in ("minLength", "maxLength", "minItems", "maxItems"):
            if key in node and (
                not isinstance(node[key], int) or isinstance(node[key], bool) or node[key] < 0
            ):
                errors.append(f"{path}.{key}: must be a non-negative integer")

        for key in ("minimum", "maximum"):
            if key in node and (
                not isinstance(node[key], (int, float))
                or isinstance(node[key], bool)
                or not math.isfinite(node[key])
            ):
                errors.append(f"{path}.{key}: must be a finite number")

        if "enum" in node and (not isinstance(node["enum"], list) or not node["enum"]):
            errors.append(f"{path}.enum: must be a non-empty array")

    walk(schema, "$")
    return errors


def validate_json_schema(instance: Any, schema: Any, path: str = "$") -> list[str]:
    """Validate JSON data against the bounded, fail-closed schema dialect above."""
    errors: list[str] = []
    if not isinstance(schema, dict):
        return [f"{path}: invalid schema node"]

    if "const" in schema and not _json_equal(instance, schema["const"]):
        errors.append(f"{path}: value does not match const")
    if "enum" in schema and not any(_json_equal(instance, item) for item in schema["enum"]):
        errors.append(f"{path}: value is not in enum")

    if "type" in schema:
        expected = schema["type"]
        types = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(instance, item) for item in types):
            errors.append(f"{path}: expected type {expected}")
            return errors

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for name in required if isinstance(required, list) else []:
            if name not in instance:
                errors.append(f"{path}.{name}: required property is missing")

        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            return errors
        additional = schema.get("additionalProperties", True)
        for name, value in instance.items():
            child_schema = properties.get(name)
            if child_schema is not None:
                errors.extend(validate_json_schema(value, child_schema, f"{path}.{name}"))
            elif additional is False:
                errors.append(f"{path}.{name}: additional property is not allowed")
            elif isinstance(additional, dict):
                errors.extend(validate_json_schema(value, additional, f"{path}.{name}"))

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: array has fewer than minItems")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: array exceeds maxItems")
        if schema.get("uniqueItems") is True:
            for index, value in enumerate(instance):
                if any(_json_equal(value, previous) for previous in instance[:index]):
                    errors.append(f"{path}[{index}]: array items must be unique")
                    break
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, value in enumerate(instance):
                errors.extend(validate_json_schema(value, item_schema, f"{path}[{index}]"))

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: string is shorter than minLength")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: string exceeds maxLength")
        if "pattern" in schema:
            try:
                if re.search(schema["pattern"], instance) is None:
                    errors.append(f"{path}: string does not match pattern")
            except (TypeError, re.error):
                errors.append(f"{path}: schema contains an invalid pattern")
        if schema.get("format") == "uri" and not _is_uri(instance):
            errors.append(f"{path}: value is not a valid absolute URI")
        elif schema.get("format") == "date-time" and not _is_rfc3339_datetime(instance):
            errors.append(f"{path}: value is not a valid RFC 3339 date-time")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if not math.isfinite(instance):
            errors.append(f"{path}: number must be finite")
        else:
            if "minimum" in schema and instance < schema["minimum"]:
                errors.append(f"{path}: number is below minimum")
            if "maximum" in schema and instance > schema["maximum"]:
                errors.append(f"{path}: number exceeds maximum")

    return errors


def deterministic_task_order(work_order: dict[str, Any]) -> list[str]:
    """Return a stable topological order, rejecting malformed or cyclic task graphs."""
    tasks = work_order.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks must be a non-empty array")

    by_id: dict[str, dict[str, Any]] = {}
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValueError(f"tasks[{index}] must be an object")
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError(f"tasks[{index}].task_id must be a non-empty string")
        if task_id in by_id:
            raise ValueError(f"task_id values must be unique: {task_id}")
        by_id[task_id] = task

    indegree = {task_id: 0 for task_id in by_id}
    outgoing: dict[str, list[str]] = {task_id: [] for task_id in by_id}
    for task_id, task in by_id.items():
        dependencies = task.get("depends_on")
        if not isinstance(dependencies, list):
            raise ValueError(f"{task_id}: depends_on must be an array")
        if any(not isinstance(dep, str) or not dep.strip() for dep in dependencies):
            raise ValueError(f"{task_id}: dependencies must be non-empty strings")
        if len(dependencies) != len(set(dependencies)):
            raise ValueError(f"{task_id}: duplicate dependency")
        for dep in dependencies:
            if dep not in by_id:
                raise ValueError(f"{task_id}: unknown dependency {dep}")
            outgoing[dep].append(task_id)
            indegree[task_id] += 1

    ready = deque(sorted(task_id for task_id, degree in indegree.items() if degree == 0))
    ordered: list[str] = []
    while ready:
        current = ready.popleft()
        ordered.append(current)
        for child in sorted(outgoing[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready = deque(sorted(ready))

    if len(ordered) != len(by_id):
        cyclic = sorted(task_id for task_id, degree in indegree.items() if degree > 0)
        raise ValueError("dependency cycle detected involving: " + ", ".join(cyclic))
    return ordered


def validate_work_order(work_order: Any, schema: Any | None = None) -> list[str]:
    """Return structural, schema, and cross-field contract violations."""
    if not isinstance(work_order, dict):
        return ["work order must be a JSON object"]
    if not isinstance(schema, dict):
        return ["schema must be a JSON object"]

    errors = validate_schema_definition(schema)
    errors.extend(validate_json_schema(work_order, schema))
    if errors:
        # Structural errors are returned before semantic code touches nested values.
        # This also prevents malformed unhashable dependencies from crashing validation.
        return errors

    if work_order.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")

    tasks = work_order["tasks"]
    task_ids = [task["task_id"] for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        errors.append("task_id values must be unique")

    domains = set(work_order["domains"])
    for task in tasks:
        if task["domain"] not in domains:
            errors.append(f"{task['task_id']}: task domain is not declared in work_order.domains")

    for collection_name, id_key in (
        ("requested_outcomes", "outcome_id"),
        ("acceptance_criteria", "criterion_id"),
    ):
        values = [item[id_key] for item in work_order[collection_name]]
        if len(values) != len(set(values)):
            errors.append(f"{id_key} values must be unique")

    try:
        deterministic_task_order(work_order)
    except (ValueError, KeyError, TypeError) as exc:
        errors.append(str(exc))

    policy = work_order["policy"]
    work_mode = policy["execution_mode"]
    for task in tasks:
        if EXECUTION_RANK[task["execution_mode"]] > EXECUTION_RANK[work_mode]:
            errors.append(
                f"{task['task_id']}: task execution mode exceeds work-order policy"
            )

    approval_refs = policy.get("approval_refs", [])
    for effect in ("external_writes", "physical_actuation"):
        if policy[effect] is True:
            if work_mode != "AUTHORIZED_EXECUTION":
                errors.append(f"policy.{effect} requires AUTHORIZED_EXECUTION mode")
            if not approval_refs:
                errors.append(f"policy.{effect} requires at least one approval reference")

    if policy.get("network_access") is True:
        allowed_domains = policy.get("allowed_domains", [])
        if not allowed_domains:
            errors.append("network access requires an explicit non-empty allowed_domains list")

    budget = work_order["resource_budget"]
    budget_approval_ref = policy.get("budget_approval_ref")
    if budget["max_cost_usd"] > 0 and (
        not isinstance(budget_approval_ref, str) or not budget_approval_ref.strip()
    ):
        errors.append(
            "non-zero max_cost_usd requires policy.budget_approval_ref; "
            "the reference is not itself proof of approval"
        )

    federation = work_order["federation"]
    targets = federation["targets"]
    target_ids = [target["target_id"] for target in targets]
    if len(target_ids) != len(set(target_ids)):
        errors.append("federation target_id values must be unique")
    target_by_id = {target["target_id"]: target for target in targets}

    requested_targets = federation["requested_target_ids"]
    for target_id in requested_targets:
        if target_id not in target_by_id:
            errors.append(f"requested target does not exist in federation.targets: {target_id}")

    if work_order["state"] in ACTIVE_STATES:
        tenant_id = policy["tenant_id"]
        data_class = policy["data_classification"]
        for target_id in requested_targets:
            target = target_by_id.get(target_id)
            if target is None:
                continue
            if target["connection_state"] != "HEALTHY":
                errors.append(f"active work requires HEALTHY target: {target_id}")
            if target["tenant_id"] != tenant_id:
                errors.append(f"tenant mismatch for target: {target_id}")
            target_class = target["max_data_classification"]
            if DATA_RANK[target_class] < DATA_RANK[data_class]:
                errors.append(f"target does not permit work-order data classification: {target_id}")
            if target["kind"] == "PARTNER_WORKER" and not target.get("authorization_ref"):
                errors.append(f"partner target requires authorization_ref: {target_id}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work_order", help="Path to a work-order JSON file")
    parser.add_argument(
        "--schema",
        default=str(ROOT / "schemas" / "engineering-work-order.schema.json"),
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Print deterministic task order after validation; never dispatch tasks",
    )
    args = parser.parse_args()

    try:
        schema = read_json(args.schema)
        work_order = read_json(args.work_order)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"result": "INVALID", "error": str(exc)}, indent=2))
        return 2

    errors = validate_work_order(work_order, schema)
    if errors:
        print(json.dumps({"result": "INVALID", "errors": errors}, indent=2))
        return 2

    result: dict[str, Any] = {
        "result": "CONTRACT_VALID",
        "work_order_id": work_order["work_order_id"],
        "state": work_order["state"],
        "task_count": len(work_order["tasks"]),
        "deterministic_task_order": deterministic_task_order(work_order) if args.plan_only else None,
        "plan_state": "PLAN_ONLY_NOT_DISPATCHED" if args.plan_only else "VALIDATED_NOT_DISPATCHED",
        "execution_performed": False,
        "network_access_performed": False,
        "external_writes_performed": False,
        "physical_actuation_performed": False,
        "budget_approval_verified": False,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
