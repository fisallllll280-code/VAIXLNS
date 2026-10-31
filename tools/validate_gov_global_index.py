import json
from pathlib import Path

PATH=Path(__file__).resolve().parents[1]/"registry/gov-sand/global-systems.v1.json"
ALLOWED={"PROPOSED","DOCUMENTED","PROPOSED_LINK","DESIGNED","TESTED_LIMITED","VERIFIED","DEPLOYED"}
def validate(data):
    assert data["government_endorsement"] is False
    ids=set()
    for x in data["systems"]:
        assert x["id"] not in ids
        ids.add(x["id"])
        assert x["status"] in ALLOWED
        assert isinstance(x["verified_runtime"],bool)
        assert x["repo"].startswith("fisallllll280-code/")
        if x["status"] in ("VERIFIED","DEPLOYED"):
            assert x["verified_runtime"] is True and x.get("runtime_evidence")
    for x in data["evidence"]:
        assert x["source"].startswith("https://github.com/")
        assert x["scope"]
    return len(ids)
if __name__=="__main__":
    print("validated systems:", validate(json.loads(PATH.read_text(encoding="utf-8"))))
