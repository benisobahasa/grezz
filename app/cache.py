import time
from app.config import settings

_cache: dict = {}


def get(key: str):
    entry = _cache.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if time.time() > expires_at:
        _cache.pop(key, None)
        return None
    return value


def set(key: str, value) -> None:
    _cache[key] = (time.time() + settings.CACHE_TTL_SECONDS, value)
