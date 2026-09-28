from dataclasses import dataclass
from typing import FrozenSet

@dataclass(frozen=True)
class ModelCapability:
    provider: str
    model_id: str
    capabilities: FrozenSet[str]
    sovereignty: str = 'external'

@dataclass(frozen=True)
class RoutingRequest:
    required: FrozenSet[str]
    allowed_providers: FrozenSet[str] = frozenset()
    require_sovereign: bool = False

def eligible_models(request: RoutingRequest, models: list[ModelCapability]) -> list[ModelCapability]:
    result=[]
    for model in models:
        if request.allowed_providers and model.provider not in request.allowed_providers: continue
        if request.require_sovereign and model.sovereignty != 'sovereign': continue
        if not request.required.issubset(model.capabilities): continue
        result.append(model)
    return result