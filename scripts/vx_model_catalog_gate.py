"""Offline model-catalog selection only; never connects to or invokes a model."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation

def _zero(x):
    try:
        return x is not None and not isinstance(x,bool) and Decimal(str(x)).is_finite() and Decimal(str(x)) == 0
    except (ValueError, InvalidOperation):
        return False

def select_models(catalog: dict, *, required_capability: str, allow_providers: set[str]):
    if not isinstance(catalog, dict) or not isinstance(catalog.get('models'), list):
        raise ValueError('trusted local catalog with models array required')
    if not isinstance(required_capability, str) or not required_capability:
        raise ValueError('required capability missing')
    if not isinstance(allow_providers, set) or not allow_providers:
        raise ValueError('trusted provider allowlist required')
    ready=[]; held=[]
    for row in catalog['models']:
        if not isinstance(row,dict) or not isinstance(row.get('id'),str):
            held.append({'id':None,'reason':'INVALID_RECORD'});continue
        reason=None
        if row.get('provider') not in allow_providers:reason='PROVIDER_NOT_ADMITTED'
        elif row.get('verified_connection') is not True:reason='CONNECTION_NOT_VERIFIED'
        elif required_capability not in (row.get('capabilities') if isinstance(row.get('capabilities'),list) else []):reason='CAPABILITY_NOT_VERIFIED'
        elif not _zero(row.get('price_input_sar')) or not _zero(row.get('price_output_sar')) or not _zero(row.get('request_fee_sar')):reason='NONZERO_OR_UNKNOWN_COST'
        elif row.get('quota_verified') is not True:reason='QUOTA_NOT_VERIFIED'
        if reason:held.append({'id':row['id'],'reason':reason})
        else:ready.append(row['id'])
    return {'status':'CATALOG_PREFLIGHT_ONLY','eligible_models':sorted(set(ready)),
            'held_models':held,'connected_models_proven_by_this_run':0,
            'note':'Selection does not call providers or establish billing safety.'}
