"""Offline, bounded model-catalog index and deterministic task shortlist.

No network, provider invocation, file writes or authority admission.
"""
from __future__ import annotations
import hashlib
import json
import time
from typing import Any

CAPABILITIES = frozenset({"coding", "mathematics", "physics", "simulation", "research", "verification"})

def canonical_digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()

def build_catalog(records: list[dict[str, Any]], *, limit: int = 100000) -> dict[str, Any]:
    if not isinstance(records, list) or len(records) > limit:
        raise ValueError("catalog must be a bounded list")
    index = {}
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"record {i} must be object")
        provider, model, version = (record.get(k) for k in ("provider", "model", "version"))
        if any(not isinstance(x, str) or not x.strip() for x in (provider, model, version)):
            raise ValueError(f"record {i}: provider/model/version required")
        capabilities = record.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities or any(not isinstance(x, str) or x not in CAPABILITIES for x in capabilities):
            raise ValueError(f"record {i}: invalid capabilities")
        key = (provider.strip().casefold(), model.strip().casefold(), version.strip())
        if key in index:
            raise ValueError(f"duplicate model identity: {key}")
        index[key] = {"provider": provider.strip(), "model": model.strip(), "version": version.strip(), "capabilities": sorted(set(capabilities)), "status": "CATALOG_ONLY"}
    entries = [index[k] for k in sorted(index)]
    return {"schema": "VX.OfflineModelCatalog.v1", "status": "UNCONNECTED", "count": len(entries), "digest": canonical_digest(entries), "entries": entries}

def shortlist(catalog: dict[str, Any], capability: str, *, max_candidates: int = 5) -> list[dict[str, Any]]:
    if capability not in CAPABILITIES or not isinstance(max_candidates, int) or isinstance(max_candidates, bool) or not 1 <= max_candidates <= 16:
        raise ValueError("invalid capability or candidate bound")
    if catalog.get("status") != "UNCONNECTED":
        raise ValueError("untrusted catalog status")
    entries = catalog.get("entries")
    if not isinstance(entries, list) or catalog.get("count") != len(entries) or canonical_digest(entries) != catalog.get("digest"):
        raise ValueError("catalog integrity failure")
    return [e for e in entries if capability in e["capabilities"]][:max_candidates]

def benchmark(n: int = 10000) -> dict[str, Any]:
    if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 100000:
        raise ValueError("n must be between 1 and 100000")
    records = [{"provider": f"provider-{i % 100:03d}", "model": f"model-{i:06d}", "version": "v1", "capabilities": ["mathematics", "verification"] if i % 2 else ["coding", "research"]} for i in range(n)]
    start = time.perf_counter()
    catalog = build_catalog(records)
    built_ms = round((time.perf_counter() - start) * 1000, 3)
    start = time.perf_counter()
    selected = shortlist(catalog, "mathematics")
    query_ms = round((time.perf_counter() - start) * 1000, 3)
    return {"status": "LOCAL_SYNTHETIC_ONLY", "records": catalog["count"], "digest": catalog["digest"], "build_ms": built_ms, "query_ms": query_ms, "shortlist_size": len(selected), "provider_calls": 0, "paid_calls": 0}

if __name__ == "__main__":
    print(json.dumps(benchmark(), sort_keys=True))
