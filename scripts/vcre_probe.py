import json
from pathlib import Path

from vcre.engine import Invariant, RealityEngine

def main() -> int:
    engine = RealityEngine("VCRE-PROBE", "1.0.0")
    engine.register_invariant(Invariant("energy-nonnegative", lambda s: s["energy"] >= 0, "energy < 0"))
    engine.create_world("W0", {"position": 0.0, "velocity": 1.5, "energy": 1.125})

    def step(s):
        s["position"] += s["velocity"]
        return s

    for _ in range(3):
        engine.transition("W0", "constant-velocity", step, observation={"kind": "synthetic"})

    cert = engine.certificate(
        result=engine.worlds["W0"].state,
        assumptions=["synthetic deterministic educational model"],
        errors={"floating_point": 0.0},
        uncertainty={"measurement": 0.0, "model_form": 0.0},
        status="NUMERICALLY_VERIFIED",
    )
    bundle = engine.evidence_bundle()
    bundle["certificate_hash"] = cert["certificate_hash"]
    bundle["status"] = "PASS" if bundle["ledger_valid"] else "FAIL"
    out = Path(".vcre-evidence.json")
    out.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(bundle, indent=2, sort_keys=True))
    return 0 if bundle["ledger_valid"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
