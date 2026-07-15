import minescript
import requests
import json
import re
import time
from pathlib import Path
import base64
import io
from nbt import nbt
import sqlite3
from datetime import datetime

API_KEY = "ca95fff0-23e6-4921-aa86-3cdfd4ee7198"
BASE_URL = "https://api.hypixel.net/v2/skyblock"

DATA_DIR = Path(__file__).parent / "dungeon-stats-display"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "dungeons.db"
ENV_PATH = DATA_DIR / ".env"

CHAT_PATTERN = re.compile(
    r"Party Finder > (\w+) joined the dungeon group! \((\w+) Level (\d+)\)"
)

MISSING_ITEMS_CHECK = {
    "GYROKINETIC_WAND": "Gyro",
    "ICE_SPRAY_WAND": "Ice Spray",
    "DARK_CLAYMORE": "Claymore",
    "CUSTOM_WITHER_BLADE": "Wither Blade",
    "TERMINATOR": "Terminator",
}


class Cache:
    def __init__(self, db_path: Path):
        self._db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, data TEXT, timestamp REAL)"
        )
        con.commit()
        con.close()

    def get(self, key: str) -> str | None:
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute("SELECT data FROM cache WHERE key = ?", (key,))
        row = cur.fetchone()
        con.close()
        if row:
            return row[0]
        return None

    def set(self, key: str, data: str):
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO cache (key, data, timestamp) VALUES (?, ?, ?)",
            (key, data, time.time()),
        )
        con.commit()
        con.close()


class Utils:
    XP_TABLE = {
        1: 50, 2: 75, 3: 110, 4: 160, 5: 230,
        6: 330, 7: 470, 8: 670, 9: 950, 10: 1340,
        11: 1890, 12: 2665, 13: 3760, 14: 5260, 15: 7380,
        16: 10300, 17: 14400, 18: 20000, 19: 27600, 20: 38000,
        21: 52500, 22: 71500, 23: 97000, 24: 132000, 25: 180000,
        26: 243000, 27: 328000, 28: 445000, 29: 600000, 30: 800000,
        31: 1065000, 32: 1410000, 33: 1900000, 34: 2500000, 35: 3300000,
        36: 4300000, 37: 5600000, 38: 7200000, 39: 9200000, 40: 12000000,
        41: 15000000, 42: 19000000, 43: 24000000, 44: 30000000, 45: 38000000,
        46: 48000000, 47: 60000000, 48: 75000000, 49: 93000000, 50: 116250000,
    }
    LEVEL_CAP = 50
    INFINITE_XP_PER_LV = 200_000_000

    FLOOR_NAMES = ["E", "F1", "F2", "F3", "F4", "F5", "F6", "F7"]
    MASTER_FLOOR_NAMES = ["M1", "M2", "M3", "M4", "M5", "M6", "M7"]

    @staticmethod
    def format_time(ms: float) -> str:
        total_s = int(ms / 1000)
        m = total_s // 60
        s = total_s % 60
        return f"{m}m{s:02d}s"

    @staticmethod
    def _nbt_to_dict(nbt_obj):
        if isinstance(nbt_obj, nbt.TAG_Compound):
            return {key: Utils._nbt_to_dict(value) for key, value in nbt_obj.iteritems()}
        elif isinstance(nbt_obj, nbt.TAG_List):
            return [Utils._nbt_to_dict(item) for item in nbt_obj]
        elif isinstance(nbt_obj, (nbt.TAG_Byte_Array, nbt.TAG_Int_Array)):
            return list(nbt_obj.value)
        else:
            return nbt_obj.value

    @staticmethod
    def decode_nbt_base64(base64_str: str) -> list[dict]:
        compressed_data = base64.b64decode(base64_str)
        nbt_file = nbt.NBTFile(fileobj=io.BytesIO(compressed_data))
        parsed_data = Utils._nbt_to_dict(nbt_file)
        return parsed_data["i"]

    @staticmethod
    def xp_to_level(total_xp: float) -> tuple[int, float]:
        xp = int(total_xp)
        if xp < 0:
            xp = 0

        level = 0
        for n in range(1, 51):
            need = Utils.XP_TABLE[n]
            if xp < need:
                break
            xp -= need
            level += 1

        while level >= 50 and xp >= Utils.INFINITE_XP_PER_LV:
            xp -= Utils.INFINITE_XP_PER_LV
            level += 1

        next_need = Utils.INFINITE_XP_PER_LV if level >= 50 else Utils.XP_TABLE[level + 1]
        progress = max(0.0, min(xp / next_need, 1.0)) if next_need > 0 else 0.0

        return level, round(level + progress, 2)

    @staticmethod
    def get_armor_names(inv_armor_data: str) -> list[str]:
        data = Utils.decode_nbt_base64(inv_armor_data)
        names: list[str] = []
        for item in data:
            if not item or "tag" not in item:
                names.append("None")
            else:
                names.append(item["tag"]["display"]["Name"])
        names.reverse()
        return names

    @staticmethod
    def get_floor_pb_times(dungeon_data: dict, floor_key_prefix: str) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        stats = dungeon_data.get("dungeon_types", {}).get(floor_key_prefix, {})

        s_times: dict = stats.get("fastest_time_s", {})
        sp_times: dict = stats.get("fastest_time_s_plus", {})

        all_keys = set(s_times.keys()) | set(sp_times.keys())
        for floor_key in all_keys:
            if floor_key == "best":
                continue
            floor_times: dict[str, float] = {}
            if floor_key in s_times:
                floor_times["s"] = float(s_times[floor_key])
            if floor_key in sp_times:
                floor_times["s_plus"] = float(sp_times[floor_key])
            if floor_times:
                result[floor_key] = floor_times

        return result

    @staticmethod
    def get_all_floor_pbs(dungeon_data: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
        normal_raw = Utils.get_floor_pb_times(dungeon_data, "catacombs")
        master_raw = Utils.get_floor_pb_times(dungeon_data, "master_catacombs")

        def _fmt_times(raw: dict[str, dict[str, float]], floor_names: list[str], key_offset: int = 0) -> dict[str, dict[str, str]]:
            formatted: dict[str, dict[str, str]] = {}
            for k, times in raw.items():
                idx = int(k) - key_offset
                if 0 <= idx < len(floor_names):
                    name = floor_names[idx]
                    formatted[name] = {}
                    if "s" in times:
                        formatted[name]["S"] = Utils.format_time(times["s"])
                    if "s_plus" in times:
                        formatted[name]["S+"] = Utils.format_time(times["s_plus"])
            return formatted

        return (
            _fmt_times(normal_raw, Utils.FLOOR_NAMES),
            _fmt_times(master_raw, Utils.MASTER_FLOOR_NAMES, key_offset=1),
        )


    @staticmethod
    def get_all_inventory_data(inventory: dict) -> list[str]:
        result = []
        if "inv_contents" in inventory:
            result.append(inventory["inv_contents"].get("data", ""))
        if "ender_chest_contents" in inventory:
            result.append(inventory["ender_chest_contents"].get("data", ""))
        for bp in inventory.get("backpack_contents", {}).values():
            result.append(bp.get("data", ""))
        return result

    @staticmethod
    def check_missing_items(inventory_list: list[str]) -> dict[str, bool]:
        to_check: dict[str, bool] = {item: False for item in MISSING_ITEMS_CHECK}

        for nbt_str in inventory_list:
            try:
                data = Utils.decode_nbt_base64(nbt_str)
            except Exception:
                continue

            for item in data:
                if not item or "tag" not in item:
                    continue

                extra = item["tag"].get("ExtraAttributes", {})
                item_id = extra.get("id", "")

                if item_id in to_check:
                    to_check[item_id] = True

                if "ability_scroll" in extra:
                    to_check["CUSTOM_WITHER_BLADE"] = True

        return to_check


class Display:
    CLASS_ORDER = ["archer", "berserk", "healer", "mage", "tank"]
    CLASS_COLORS = {
        "archer": "red",
        "berserk": "gold",
        "healer": "light_purple",
        "mage": "aqua",
        "tank": "green",
    }
    ARMOR_EMOJIS = ["\u26d1", "\U0001f6e1", "\U0001f456", "\U0001f462"]

    @staticmethod
    def _make_armor_json(armor_names: list[str]) -> list[dict]:
        sep = {"text": " | "}
        pieces: list[dict] = []
        for i in range(4):
            if i > 0:
                pieces.append(sep)
            name = armor_names[i] if i < len(armor_names) else "None"
            clean_name = re.sub(r"\u00a7.", "", name)
            pieces.append({
                "text": Display.ARMOR_EMOJIS[i],
                "hoverEvent": {"action": "show_text", "value": clean_name},
            })
        return pieces

    @staticmethod
    def _make_missing_text(missing_status: dict[str, bool], pets: list[dict]) -> str:
        parts: list[str] = []
        for item_id, display_name in MISSING_ITEMS_CHECK.items():
            if not missing_status[item_id]:
                parts.append(f"\u2716 {display_name}")

        has_edrag = any(p.get("type", "").lower() == "ender_dragon" for p in pets)
        has_gdrag = any(p.get("type", "").lower() == "golden_dragon" for p in pets)
        if not has_edrag:
            parts.append("\u2716 EDrag")
        if not has_gdrag:
            parts.append("\u2716 GDrag")

        return " | ".join(parts) if parts else "None"

    @staticmethod
    def _make_floor_hover(pb_times: dict[str, dict[str, str]], floor_names: list[str]) -> str:
        lines: list[str] = ["Floor | S | S+"]
        for name in floor_names:
            if name in pb_times:
                s_time = pb_times[name].get("S", "-")
                sp_time = pb_times[name].get("S+", "-")
                lines.append(f"{name}: {s_time} | {sp_time}")
        return "\n".join(lines) if len(lines) > 1 else "No data"

    @classmethod
    def echo_stats(
        cls,
        username: str,
        cata_level: float,
        secrets: int,
        avg_secrets: float,
        class_levels: dict[str, float],
        class_avg: float,
        normal_pb: dict[str, dict[str, str]],
        master_pb: dict[str, dict[str, str]],
        magical_power: int,
        armor_names: list[str],
        missing_status: dict[str, bool],
        pets: list[dict],
    ):
        normal_hover = cls._make_floor_hover(normal_pb, Utils.FLOOR_NAMES)
        master_hover = cls._make_floor_hover(master_pb, Utils.MASTER_FLOOR_NAMES)
        missing_text = cls._make_missing_text(missing_status, pets)
        armor_json = cls._make_armor_json(armor_names)

        lines: list[list[dict]] = [
            [
                {"text": "---------- ", "color": "gray"},
                {"text": username, "color": "gold"},
                {"text": " ----------", "color": "gray"},
            ],
            [
                {"text": "Cata: ", "color": "gray"},
                {"text": str(cata_level), "color": "red"},
                {"text": " | Secrets: ", "color": "gray"},
                {"text": str(secrets), "color": "green"},
                {"text": f" ({avg_secrets:.2f})", "color": "dark_green"},
            ],
            cls._build_classes_line(class_levels, class_avg),
            [
                {"text": "Floors: ", "color": "gray"},
                {
                    "text": "Normal",
                    "color": "yellow",
                    "hoverEvent": {"action": "show_text", "value": normal_hover},
                },
                {"text": " | ", "color": "dark_gray"},
                {
                    "text": "Master",
                    "color": "light_purple",
                    "hoverEvent": {"action": "show_text", "value": master_hover},
                },
                {"text": f" | MP: {magical_power}", "color": "dark_purple"},
            ],
            [{"text": "Armor: ", "color": "gray"}, *armor_json],
            [
                {"text": "Missing: ", "color": "gray"},
                {"text": missing_text, "color": "dark_gray"},
            ],
            [
                {"text": "--------------------", "color": "gray"},
            ],
        ]

        for line in lines:
            minescript.echo_json(line)

    @classmethod
    def _build_classes_line(
        cls, class_levels: dict[str, float], class_avg: float
    ) -> list[dict]:
        parts: list[dict] = [{"text": "Classes: ", "color": "gray"}]
        for i, cls_name in enumerate(cls.CLASS_ORDER):
            if i > 0:
                parts.append({"text": "/", "color": "dark_gray"})
            lvl = class_levels[cls_name]
            cls_color = cls.CLASS_COLORS.get(cls_name, "white")
            parts.append({"text": str(lvl), "color": cls_color})
        parts.append({"text": f" (Avg: {class_avg})", "color": "dark_aqua"})
        return parts


cache = Cache(DB_PATH)


def get_uuid(username: str) -> str | None:
    cache_key = f"uuid:{username}"
    cached = cache.get(cache_key)
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
        cache.set(cache_key, uuid)
    return uuid


def load_api_key() -> str:
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("KEY="):
                value = line[4:]
                if value:
                    return value
    return API_KEY


def save_api_key(key: str):
    ENV_PATH.write_text(f"KEY={key}", encoding="utf-8")


def get_api_key() -> str:
    return load_api_key()


def handle_dsd_command(message: str):
    parts = message.split(maxsplit=2)
    if len(parts) < 2 or parts[1] != "key":
        return

    if len(parts) >= 3:
        save_api_key(parts[2].strip())
        minescript.echo("DSD: API key saved.")
        return

    if ENV_PATH.exists():
        raw = ENV_PATH.read_text(encoding="utf-8").strip()
        ts = datetime.fromtimestamp(ENV_PATH.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        key = ""
        for line in raw.splitlines():
            if line.strip().startswith("KEY="):
                key = line.strip()[4:]
                break
        if key:
            masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "****"
            minescript.echo(f"DSD: Key {masked} (set at {ts})")
        else:
            minescript.echo("DSD: No API key stored. Set it with `!dsd key <key>`.")
    else:
        minescript.echo("DSD: No API key stored. Set it with `!dsd key <key>`.")


def handle_chat_message(message: str):
    match = CHAT_PATTERN.search(message)
    if not match:
        return

    username = match.group(1)
    user_class = match.group(2)
    user_level = match.group(3)

    process_and_display(username, user_class, user_level)
    cache_key = f"uuid:{username}"
    cached = cache.get(cache_key)
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
        cache.set(cache_key, uuid)
    return uuid


def get_profiles_data(uuid: str) -> dict | None:
    cache_key = f"profiles:{uuid}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    resp = requests.get(
        f"{BASE_URL}/profiles",
        params={"key": get_api_key(), "uuid": uuid},
    )

    if resp.status_code != 200:
        cause = ""
        try:
            error_data = resp.json()
            cause = error_data.get("cause", "")
        except Exception:
            pass
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


def process_and_display(username: str, user_class: str, user_level: str):
    uuid = get_uuid(username)
    if uuid is None:
        return

    profiles_data = get_profiles_data(uuid)
    if profiles_data is None:
        return

    user_profile = get_selected_profile(profiles_data, uuid)
    if user_profile is None:
        minescript.echo(f"DSD: No profile data for {username}")
        return

    dungeon_data = user_profile.get("dungeons", {})
    if not dungeon_data:
        minescript.echo(f"DSD: No dungeon data for {username}")
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
    for name in Display.CLASS_ORDER:
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
            armor_names = ["?", "?", "?", "?"]
    else:
        armor_names = ["None", "None", "None", "None"]

    all_inv = Utils.get_all_inventory_data(inventory)
    missing_status = Utils.check_missing_items(all_inv)

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
        missing_status=missing_status,
        pets=pets,
    )




def main():
    try:
        with minescript.EventQueue() as event_queue:
            event_queue.register_chat_listener()
            event_queue.register_outgoing_chat_interceptor(prefix="!dsd")
            while True:
                event = event_queue.get()
                if event.type == minescript.EventType.CHAT:
                    handle_chat_message(event.message)
                elif event.type == minescript.EventType.OUTGOING_CHAT_INTERCEPT:
                    handle_dsd_command(event.message)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
