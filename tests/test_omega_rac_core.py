import json
from omega_rac import assess, detect_cycles, dependency_closure

def base_claim():
    return {"claim_id":"C1","obligations":["o1","o2"]}

def test_provenance_and_determinism():
    kwargs=dict(evidence={"satisfied_obligations":["o1","o2"]},
                edges={"C1":["E1"],"E1":[]},unknown_vector={"dependency":0},
                tolerance={"dependency":0})
    a=assess(base_claim(),**kwargs)
    b=assess(base_claim(),**kwargs)
    assert a.status=="PROVEN"
    assert a.to_dict()==b.to_dict()

def test_unknown_budget_quarantines():
    r=assess(base_claim(),evidence={"satisfied_obligations":["o1","o2"]},
             unknown_vector={"dependency":1.0},tolerance={"dependency":0.5})
    assert r.status=="QUARANTINE_INSUFFICIENT_ASSURANCE"
    assert r.boundary_zone=="UNKNOWN"

def test_missing_observation_is_not_false():
    r=assess(base_claim(),evidence={"satisfied_obligations":["o1"]})
    assert r.status=="REQUIRES_OBSERVATION"
    assert r.boundary_zone=="UNOBSERVABLE"

def test_recursive_assurance_is_rejected():
    assert detect_cycles({"A":["B"],"B":["A"]})
    r=assess({"claim_id":"A","obligations":[]},edges={"A":["B"],"B":["A"]})
    assert r.status=="INSUFFICIENT_RECURSIVE_ASSURANCE"

def test_dependency_closure_and_frontier():
    edges={"C1":["E1"],"E1":["V1"],"V1":[],"U":["C1"]}
    assert dependency_closure("V1",edges)==("V1",)
    r=assess({"claim_id":"V1","obligations":[]},edges=edges)
    assert r.dependency_closure==("V1",)
