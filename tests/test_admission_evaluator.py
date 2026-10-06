from scripts.admission_evaluator import evaluate


def candidate(**overrides):
    value = {
        "candidate_id": "TEST-001",
        "provenance": {"canonical_ref": "project.genome::v1.0.0"},
        "gates": {
            "identity": "PASS",
            "contract": "PASS",
            "source": "PASS",
            "build": "N/A",
            "execution": "PASS",
            "tests": "PASS",
            "conformance": "PASS",
            "security": "PASS",
            "performance": "N/A",
            "provenance": "PASS",
            "recovery": "PASS",
            "evidence": "PASS",
        },
    }
    for key, value_override in overrides.items():
        value[key] = value_override
    return value


def test_complete_candidate_is_admitted():
    verdict = evaluate(candidate())
    assert verdict["admission"] == "ADMITTED"
    assert verdict["failures"] == []


def test_missing_gate_blocks():
    item = candidate()
    del item["gates"]["tests"]
    verdict = evaluate(item)
    assert verdict["admission"] == "BLOCKED"
    assert "MISSING_GATE:tests" in verdict["failures"]


def test_unknown_status_blocks():
    item = candidate()
    item["gates"]["execution"] = "UNKNOWN"
    verdict = evaluate(item)
    assert verdict["admission"] == "BLOCKED"
    assert "GATE_NOT_PASS:execution:UNKNOWN" in verdict["failures"]


def test_missing_canonical_provenance_blocks():
    item = candidate()
    item["provenance"] = {}
    verdict = evaluate(item)
    assert verdict["admission"] == "BLOCKED"
    assert "CANONICAL_PROVENANCE_REQUIRED" in verdict["failures"]
