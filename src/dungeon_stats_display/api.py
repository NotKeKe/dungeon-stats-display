import json

import minescript
import requests

from . import constants


def get_api_key() -> str:
    if constants.ENV_PATH.exists():
        for line in constants.ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("KEY="):
                value = line[4:]
                if value:
                    return value
    return ""


def save_api_key(key: str):
    constants.ENV_PATH.write_text(f"KEY={key}", encoding="utf-8")


def get_uuid(username: str) -> str | None:
    cache_key = f"uuid:{username}"
    cached = constants.cache.get(cache_key)
    if cached:
        return cached

    resp = requests.get(
        f"https://api.mojang.com/users/profiles/minecraft/{username}"
    )
    if resp.status_code != 200:
        minescript.echo(f"DSD: Cannot find user {username}")
        return None

    data = resp.json()
    uuid = data.get("id")
    if uuid:
        constants.cache.set(cache_key, uuid)
    return uuid


def get_profiles_data(uuid: str) -> dict | None:
    cache_key = f"profiles:{uuid}"
    cached = constants.cache.get(cache_key)
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
            constants.logger.exception("Hypixel API error response parse failed")
        msg = f"DSD: Hypixel API error: {resp.status_code}"
        if cause:
            msg += f" ({cause})"
        minescript.echo(msg)
        return None

    data = resp.json()
    constants.cache.set(cache_key, json.dumps(data, ensure_ascii=False))
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
