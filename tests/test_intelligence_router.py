from intelligence_federation.router import ModelCapability, RoutingRequest, eligible_models

def test_capability_routing_is_policy_driven():
    models=[ModelCapability('a','reasoner',frozenset({'reasoning','coding'})), ModelCapability('b','vision',frozenset({'vision'}))]
    selected=eligible_models(RoutingRequest(frozenset({'reasoning'})),models)
    assert [m.model_id for m in selected]==['reasoner']

def test_sovereignty_is_explicit():
    models=[ModelCapability('external','x',frozenset({'coding'}),'external'), ModelCapability('internal','y',frozenset({'coding'}),'sovereign')]
    selected=eligible_models(RoutingRequest(frozenset({'coding'}),require_sovereign=True),models)
    assert [m.model_id for m in selected]==['y']