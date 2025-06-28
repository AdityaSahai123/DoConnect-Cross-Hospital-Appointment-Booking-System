
from django.core.cache import cache

def get_gav_mapping():
    cached = cache.get("GAV_MAPPING")
    if cached is not None:
        return cached

    from .doctorsMapping import build_gav_mapping
    mapping = build_gav_mapping()
    cache.set("GAV_MAPPING", mapping, timeout=None) 
    return mapping

def get_gav_mapping_app():
    cached = cache.get("GAV_MAPPINGApp")
    if cached is not None:
        return cached

    from .slotMapping import build_appointment_mapping
    mapping = build_appointment_mapping()
    cache.set("GAV_MAPPINGApp", mapping, timeout=None)
    return mapping
