import json

import minescript
import requests

from . import constants
from src.core.api import get_uuid


def get_api_key() -> str:
    env = constants.ENV_PATH
    assert env is not None
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("KEY="):
                value = line[4:]
                if value:
                    return value
    return ""


def save_api_key(key: str):
    env = constants.ENV_PATH
    assert env is not None
    env.write_text(f"KEY={key}", encoding="utf-8")


def get_profiles_data(uuid: str) -> dict | None:
    cache = constants.cache
    assert cache is not None

    cache_key = f"profiles:{uuid}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    api_key = get_api_key()
    if not api_key:
        minescript.echo("DSD: No API key set. Set it with `!dsd key <key>`.")
        return None

    resp = requests.get(
        f"{constants.BASE_URL}/profiles",
        params={"key": get_api_key(), "uuid": uuid},
    )

    if resp.status_code != 200:
        cause = ""
        try:
            error_data = resp.json()
            cause = error_data.get("cause", "")
        except Exception:
            log = constants.logger
            assert log is not None
            log.exception("Hypixel API error response parse failed")
        msg = f"DSD: Hypixel API error: {resp.status_code}"
        if cause:
            msg += f" ({cause})"
        minescript.echo(msg)
        return None

    data = resp.json()
    cache.set(cache_key, json.dumps(data, ensure_ascii=False))
    return data


def get_selected_profile(profiles_data: dict, uuid: str) -> dict | None:
    profiles: list = profiles_data.get("profiles", [])
    if not profiles:
        return None

    for p in profiles:
        if p.get("selected"):
            members = p.get("members", {})
            return members.get(uuid)

    for p in profiles:
        members = p.get("members", {})
        if uuid in members:
            return members[uuid]

    return None
