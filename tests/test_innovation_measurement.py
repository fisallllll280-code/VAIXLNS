from pathlib import Path
import json
import importlib.util

REG = Path("registry/innovation_measurement.v1.json")
SCRIPT = Path("scripts/measure_innovations.py")

def load_module():
    spec = importlib.util.spec_from_file_location("measure_innovations", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_registry_has_all_61_innovation_entries():
    data = json.loads(REG.read_text(encoding="utf-8"))
    assert len(data["items"]) == 61
    assert [x["innovation_index_id"] for x in data["items"]] == [
        f"I-{i:03d}" for i in range(1, 62)
    ]

def test_every_innovation_has_agent_and_owner():
    data = json.loads(REG.read_text(encoding="utf-8"))
    for item in data["items"]:
        assert item["canonical_owner"]
        assert item["primary_agent_id"]
        assert item["primary_agent"]

def test_proposed_baseline_is_not_verified():
    mod = load_module()
    data = json.loads(REG.read_text(encoding="utf-8"))
    for item in data["items"]:
        assert item["status"] == "PROPOSED"
        assert item["verification_state"] == "NOT_CLAIMED"
        assert mod.readiness_score(item) == 45
