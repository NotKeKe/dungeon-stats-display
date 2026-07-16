import re
import minescript

from . import constants
from .utils import Utils


class Display:
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
                "text": constants.ARMOR_EMOJIS[i],
                "hoverEvent": {"action": "show_text", "value": clean_name},
            })
        return pieces

    @staticmethod
    def _make_missing_pieces(inventory_list: list[str], pets: list[dict]) -> list[dict]:
        missing_status = Utils.check_missing_items(inventory_list)

        names: list[str] = []
        for item_id, display_name in constants.MISSING_ITEMS_CHECK.items():
            if not missing_status[item_id]:
                names.append(display_name)

        has_spirit = any(p.get("type", "").lower() == "spirit" for p in pets)
        has_edrag = any(p.get("type", "").lower() == "ender_dragon" for p in pets)
        has_gdrag = any(p.get("type", "").lower() == "golden_dragon" for p in pets)
        if not has_spirit:
            names.append("Spirit")
        if not has_edrag:
            names.append("EDrag")
        if not has_gdrag:
            names.append("GDrag")

        if not names:
            return [{"text": "None", "color": "dark_gray"}]

        pieces: list[dict] = []
        for i, name in enumerate(names):
            if i > 0:
                pieces.append({"text": " | ", "color": "gray"})
            pieces.append({"text": "\u2716", "color": "red"})
            pieces.append({"text": " " + name, "color": "white"})
        return pieces

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
        inventory_list: list[str],
        pets: list[dict],
    ):
        normal_hover = cls._make_floor_hover(normal_pb, constants.FLOOR_NAMES)
        master_hover = cls._make_floor_hover(master_pb, constants.MASTER_FLOOR_NAMES)
        missing_pieces = cls._make_missing_pieces(inventory_list, pets)
        armor_json = cls._make_armor_json(armor_names)

        lines: list[list[dict]] = [
            [
                {"text": "---------- ", "color": "gray"},
                {"text": username, "color": "gold"},
                {"text": " ----------", "color": "gray"},
            ],
            [
                {"text": "Cata: ", "color": "gray"},
                {"text": str(cata_level), "color": "green" if cata_level < 25 else "yellow" if cata_level < 40 else "orange" if cata_level < 50 else "red"},
                {"text": " | Secrets: ", "color": "gray"},
                {"text": f"{secrets:,}", "color": "yellow"},
                {"text": f" ({avg_secrets:.2f})", "color": "aqua"},
            ],
            cls._build_classes_line(class_levels, class_avg),
            [
                {"text": "Floors: ", "color": "gray"},
                {
                    "text": "Normal",
                    "color": "white",
                    "hoverEvent": {"action": "show_text", "value": normal_hover},
                },
                {"text": " | ", "color": "dark_gray"},
                {
                    "text": "Master",
                    "color": "dark_gray",
                    "hoverEvent": {"action": "show_text", "value": master_hover},
                },
                {"text": " | ", "color": "dark_gray"},
                {"text": "MP: ", "color": "gray"},
                {"text": f"{magical_power:,}", "color": "light_purple"},
            ],
            [{"text": "Armor: ", "color": "gray"}, *armor_json],
            [{"text": "Missing: ", "color": "gray"}, *missing_pieces],
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
        for i, cls_name in enumerate(constants.CLASS_ORDER):
            if i > 0:
                parts.append({"text": "/", "color": "dark_gray"})
            lvl = class_levels[cls_name]
            cls_color = constants.CLASS_COLORS.get(cls_name, "white")
            parts.append({"text": str(lvl), "color": cls_color})
        parts.append({"text": f" (Avg: {class_avg})", "color": "dark_aqua"})
        return parts
