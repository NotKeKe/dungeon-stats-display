import requests

from . import constants


def get_uuid(username: str) -> str | None:
    cache = constants.cache
    assert cache is not None

    cache_key = f"uuid:{username}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    resp = requests.get(
        f"https://api.mojang.com/users/profiles/minecraft/{username}"
    )
    if resp.status_code != 200:
        return None

    data = resp.json()
    uuid = data.get("id")
    if uuid:
        cache.set(cache_key, uuid)
    return uuid
