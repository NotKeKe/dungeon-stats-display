import base64
import io
import re
from nbt import nbt

from . import constants


class Utils:
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
            need = constants.XP_TABLE[n]
            if xp < need:
                break
            xp -= need
            level += 1

        while level >= 50 and xp >= constants.INFINITE_XP_PER_LV:
            xp -= constants.INFINITE_XP_PER_LV
            level += 1

        next_need = constants.INFINITE_XP_PER_LV if level >= 50 else constants.XP_TABLE[level + 1]
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
            _fmt_times(normal_raw, constants.FLOOR_NAMES),
            _fmt_times(master_raw, constants.MASTER_FLOOR_NAMES, key_offset=1),
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
        to_check: dict[str, bool] = {item: False for item in constants.MISSING_ITEMS_CHECK}

        for nbt_str in inventory_list:
            try:
                data = Utils.decode_nbt_base64(nbt_str)
            except Exception:
                constants.logger.exception("NBT decode error")
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
