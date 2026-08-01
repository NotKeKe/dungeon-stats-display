from datetime import datetime
from re import Match

import minescript

from . import constants
from .api import get_profiles_data, get_selected_profile, get_uuid, save_api_key
from .display import Display
from .utils import Utils


def _log():
    logger = constants.logger
    assert logger is not None
    return logger


def on_key_command(message: str):
    parts = message.split(maxsplit=2)
    if len(parts) >= 3:
        save_api_key(parts[2].strip())
        minescript.echo_json(constants.dsd_prefix() + [
            {"text": "API key saved.", "color": "white"}
        ])
        return

    env = constants.ENV_PATH
    assert env is not None
    if env.exists():
        raw = env.read_text(encoding="utf-8").strip()
        ts = datetime.fromtimestamp(env.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        key = ""
        for line in raw.splitlines():
            if line.strip().startswith("KEY="):
                key = line.strip()[4:]
                break
        if key:
            masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "****"
            minescript.echo_json(constants.dsd_prefix() + [
                {"text": f"Key {masked} (set at {ts})", "color": "white"}
            ])
        else:
            minescript.echo_json(constants.dsd_prefix() + [
                {"text": "No API key stored. Set it with `!dsd key <key>`.", "color": "white"}
            ])
    else:
        minescript.echo_json(constants.dsd_prefix() + [
            {"text": "No API key stored. Set it with `!dsd key <key>`.", "color": "white"}
        ])


def on_chat(clean_text: str, match: Match[str]) -> bool:
    username = match.group(1)
    user_class = match.group(2)
    user_level = match.group(3)

    if username == minescript.player().name:
        return False

    _log().info(f"Processing {username}-{user_class}-{user_level}")

    process_and_display(username, user_class, user_level)
    return False


def on_search_command(message: str):
    parts = message.split(maxsplit=2)
    if len(parts) < 3:
        minescript.echo_json(constants.dsd_prefix() + [
            {"text": "Usage: !dsd search <username>", "color": "white"}
        ])
        return
    username = parts[2].strip()
    if not username:
        minescript.echo_json(constants.dsd_prefix() + [
            {"text": "Usage: !dsd search <username>", "color": "white"}
        ])
        return
    minescript.echo_json(constants.dsd_prefix() + [
        {"text": f"Searching for {username}...", "color": "white"}
    ])
    # NOTE: process_and_display 的 user_class / user_level 目前未被使用，
    #       此處傳入空字串。若未來重寫 process_and_display 使用了這些參數，
    #       需要確認 search 情境下是否要傳入不同值。
    process_and_display(username, "", "")


def process_and_display(username: str, user_class: str, user_level: str):
    try:
        _process_and_display(username, user_class, user_level)
    except Exception as e:
        _log().exception("Error processing %s: %s", username, e)
        minescript.echo_json(constants.dsd_prefix() + [
            {"text": f"Error processing {username}: {e}", "color": "white"}
        ])


def _process_and_display(username: str, user_class: str, user_level: str):
    uuid = get_uuid(username)
    if uuid is None:
        minescript.echo_json(constants.dsd_prefix() + [
            {"text": f"Cannot find user {username}", "color": "white"}
        ])
        return

    profiles_data = get_profiles_data(uuid)
    if profiles_data is None:
        return

    user_profile = get_selected_profile(profiles_data, uuid)
    if user_profile is None:
        minescript.echo_json(constants.dsd_prefix() + [
            {"text": f"No profile data for {username}", "color": "white"}
        ])
        return

    dungeon_data = user_profile.get("dungeons", {})
    if not dungeon_data:
        minescript.echo_json(constants.dsd_prefix() + [
            {"text": f"No dungeon data for {username}", "color": "white"}
        ])
        return

    classes = dungeon_data.get("player_classes", {})
    inventory = user_profile.get("inventory", {})
    pets = user_profile.get("pets_data", {}).get("pets", [])

    cata_level, cata_level_with_progress = Utils.xp_to_level(
        dungeon_data.get("dungeon_types", {}).get("catacombs", {}).get("experience", 0)
    )

    secrets = dungeon_data.get("secrets", 0)

    normal_comps = sum(
        v
        for k, v in dungeon_data.get("dungeon_types", {})
        .get("catacombs", {})
        .get("milestone_completions", {})
        .items()
        if k != "total"
    )
    master_comps = sum(
        v
        for k, v in dungeon_data.get("dungeon_types", {})
        .get("master_catacombs", {})
        .get("milestone_completions", {})
        .items()
        if k != "total"
    )
    total_runs = normal_comps + master_comps
    avg_secrets = round(secrets / total_runs, 2) if total_runs > 0 else 0.0

    class_levels: dict[str, float] = {}
    class_display_levels: list[int] = []
    for name in constants.CLASS_ORDER:
        if name in classes:
            level, lvl_with_progress = Utils.xp_to_level(classes[name].get("experience", 0))
            class_levels[name] = lvl_with_progress
            class_display_levels.append(level)
        else:
            class_levels[name] = 0.0
            class_display_levels.append(0)

    class_avg = (
        round(sum(class_display_levels) / len(class_display_levels), 1)
        if class_display_levels
        else 0.0
    )

    normal_pb, master_pb = Utils.get_all_floor_pbs(dungeon_data)

    magical_power = (
        user_profile.get("accessory_bag_storage", {}).get("highest_magical_power", 0)
    )

    armor_names: list[str] = []
    inv_armor = inventory.get("inv_armor", {})
    if inv_armor and inv_armor.get("data"):
        try:
            armor_names = Utils.get_armor_names(inv_armor["data"])
        except Exception:
            _log().exception("Armor NBT decode error for %s", username)
            armor_names = ["?", "?", "?", "?"]
    else:
        armor_names = ["None", "None", "None", "None"]

    all_inv = Utils.get_all_inventory_data(inventory)

    Display.echo_stats(
        username=username,
        cata_level=cata_level_with_progress,
        secrets=secrets,
        avg_secrets=avg_secrets,
        class_levels=class_levels,
        class_avg=class_avg,
        normal_pb=normal_pb,
        master_pb=master_pb,
        magical_power=magical_power,
        armor_names=armor_names,
        inventory_list=all_inv,
        pets=pets,
    )
