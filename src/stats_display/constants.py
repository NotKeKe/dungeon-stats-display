from src.core.constants import (
    CHAT_PATTERN, DATA_DIR, DB_PATH, ENV_PATH, LOG_PATH,
    logger, cache,
)

BASE_URL = "https://api.hypixel.net/v2/skyblock"

MISSING_ITEMS_CHECK = {
    "GYROKINETIC_WAND": "Gyro",
    "ICE_SPRAY_WAND": "Ice Spray",
    "DARK_CLAYMORE": "Claymore",
    "CUSTOM_WITHER_BLADE": "Wither Blade",
    "TERMINATOR": "Terminator",
}

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

CLASS_ORDER = ["archer", "berserk", "healer", "mage", "tank"]
CLASS_COLORS = {
    "archer": "red",
    "berserk": "gold",
    "healer": "light_purple",
    "mage": "aqua",
    "tank": "green",
}
ARMOR_EMOJIS = ["\u26d1", "\U0001f6e1", "\U0001f456", "\U0001f462"]
