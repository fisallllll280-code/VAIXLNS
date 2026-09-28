import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "omega-world-adapter.schema.json"
CATALOG = ROOT / "registry" / "omega" / "VAIXLNS_WORLD_ADAPTER_CATALOG.json"

def test_world_adapter_schema_is_valid_json():
    data = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert data["title"] == "VAIXLNS Ω∞ World Adapter Contract"

def test_world_adapter_catalog_has_required_domains():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    ids = {item["id"] for item in data["domains"]}
    assert {"AI","AGENT","DATA","CLOUD","ORCH","CICD","OBS","SEC","SCI","SIM","EDGE","UX","RESEARCH","OPS"} <= ids
