# VX Ω Genesis — minimal read-only runtime
Status: IMPLEMENTED source code; execution/CI NOT VERIFIED.

This is a first executable **inventory component**, not the complete autonomous system. It does not connect providers, start agents, publish, or modify source files.

Run from repository root:

```bash
python -m unittest discover -s tests -p 'test_vx_omega_genesis.py' -v
python -m tools.vx_omega_genesis --root . --path docs/indexes --path registry > /tmp/vx-genesis-inventory.json
```

The second command emits a deterministic JSON inventory with SHA-256 and explicit exception classifications. Exit 2 indicates incomplete inventory. Do not treat NOT_OBSERVED as MISSING, or source presence as VERIFIED.

Next: bounded provenance graph with source commits, identity reconciliation, dependency edges, baseline performance measurements, independent review, and VX G0 tests. No promotion to CANONICAL without admission evidence.
