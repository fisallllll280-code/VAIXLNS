"""Run the executable Ω-RAC benchmark smoke suite without external dependencies."""
from omega_rac import assess

CASES=[
 ("I-Ω2", {"claim_id":"A","obligations":[]}, {"edges":{"A":["B"],"B":["A"]}},
  "INSUFFICIENT_RECURSIVE_ASSURANCE"),
 ("I-Ω4", {"claim_id":"U","obligations":[]}, {"unknown_vector":{"dependency":1},"tolerance":{"dependency":0}},
  "QUARANTINE_INSUFFICIENT_ASSURANCE"),
 ("I-Ω10", {"claim_id":"O","obligations":["observe.x"]}, {"evidence":{"satisfied_obligations":[]}},
  "REQUIRES_OBSERVATION"),
 ("I-Ω13", {"claim_id":"C","obligations":[]}, {"edges":{"C":["E"],"E":[]}},
  "PROVEN"),
]
for ident,claim,kwargs,expected in CASES:
    got=assess(claim,**kwargs).status
    print(f"{ident}: {'PASS' if got==expected else 'FAIL'} ({got})")
    if got!=expected: raise SystemExit(1)
print("Ω-RAC executable benchmark: PASS")
