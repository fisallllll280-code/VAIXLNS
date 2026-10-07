from patterns.vaixl_pattern_factory import DIRECTIONS, diagnose_route

def test_quarantine_classification_matrix():
    routes = [
        None,
        {"candidate_id":"c","architecture":"a","language_id":"l","direction":"semantic"},
        {"candidate_id":"c","architecture":"a","language_id":"l","direction":"invalid","binding_fingerprint":"f"*64},
        {"candidate_id":"c","architecture":"a","language_id":"l","direction":"semantic","binding_fingerprint":"f"*64},
    ]
    states = [diagnose_route(r)["state"] for r in routes]
    assert states == ["MISSING", "SECURITY_REJECTION", "INVARIANT_BREACH", "VALID"]

def test_all_four_directions_are_explicitly_classified():
    for direction in DIRECTIONS:
        result = diagnose_route({
            "candidate_id":"c","architecture":"a","language_id":"l",
            "direction":direction,"binding_fingerprint":"f"*64,
        })
        assert result["state"] == "VALID"
