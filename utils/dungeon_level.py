DUNGEON_XP_TABLE = {
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


def class_xp_to_level(total_xp: float):
    """回傳 (level, progress, detail_dict)"""
    xp = int(total_xp)
    if xp < 0:
        xp = 0

    level = 0
    # Lv 1~50：按 table 扣
    for n in range(1, 51):
        need = DUNGEON_XP_TABLE[n]
        if xp < need:
            break
        xp -= need
        level += 1
    # Lv 50+ infinite：每級固定 200M
    while level >= 50 and xp >= INFINITE_XP_PER_LV:
        xp -= INFINITE_XP_PER_LV
        level += 1

    next_need = INFINITE_XP_PER_LV if level >= 50 else DUNGEON_XP_TABLE[level + 1]
    progress = max(0.0, min(xp / next_need, 1.0)) if next_need > 0 else 0.0
    display_level = min(level, LEVEL_CAP)

    return display_level, round(level + progress, 2)

    return display_level, progress, {
        "level": display_level,
        "uncappedLevel": level,
        "progress": progress,
        "levelWithProgress": round(display_level + progress, 2),
        "xpCurrent": xp,
        "xpForNext": next_need,
        "totalXp": int(total_xp),
    }