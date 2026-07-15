import requests
import json
from pathlib import Path

from config import KEY, BASE_URL, UUID

from utils import class_xp_to_level, decode_nbt_base64

DATA = {
    'profiles': {}
}

profiles_path = Path('profiles.json')
if not profiles_path.exists():
    with open(profiles_path, 'w', encoding='utf-8') as f:
        resp = requests.get(f'{BASE_URL}/profiles', params={'key': KEY, "uuid": UUID})
        json.dump(resp.json(), f, indent=4, ensure_ascii=False)

with open(profiles_path, 'r', encoding='utf-8') as f:
    DATA['profiles'] = json.load(f)



# data fetching
profiles: list = DATA['profiles']['profiles']
single_profile = next(p for p in profiles if p.get('selected'))
user_profile = next(v for user_id, v in single_profile['members'].items() if user_id == UUID)

pets: list[dict] = user_profile['pets_data']['pets']
dungeon_data = user_profile['dungeons']
classes = dungeon_data['player_classes']
inventory = user_profile['inventory']


def get_pet_missing_info(pets: list[dict]) -> tuple[bool, str]:
    has_spirit = any(p['type'].lower() == 'spirit' for p in pets)
    has_gdrag = any(p['type'].lower() == 'golden_dragon' for p in pets)
    has_edrag = any(p['type'].lower() == 'ender_dragon' for p in pets)

    format_string = (
        f"user {"has a" if has_spirit else "don't have a"} spirit\n"
        f"user {"has a" if has_gdrag else "don't have a"} golden dragon\n"
        f"user {"has a" if has_edrag else "don't have a"} ender dragon"
    )

    return has_spirit, format_string

def get_secrets_info(dungeon_data: dict) -> tuple[int, str]:
    secrets = dungeon_data['secrets']
    format_string = f"user has {secrets} secrets"
    return secrets, format_string


def get_dungeon_pb_info(dungeon_data: dict) -> tuple[dict, str]:
    pb_data = {
        'normal_s': dungeon_data['dungeon_types']['catacombs']['fastest_time_s'],
        'normal_s_plus': dungeon_data['dungeon_types']['catacombs']['fastest_time_s_plus'],
        'master_s': dungeon_data['dungeon_types']['master_catacombs']['fastest_time_s'],
        'master_s_plus': dungeon_data['dungeon_types']['master_catacombs']['fastest_time_s_plus'],
    }
    format_string = (
        f"normal s: {pb_data['normal_s']}\n"
        f"normal s+: {pb_data['normal_s_plus']}\n"
        f"master s: {pb_data['master_s']}\n"
        f"master s+: {pb_data['master_s_plus']}"
    )
    return pb_data, format_string


def get_class_levels_info(classes: dict) -> tuple[list, str]:
    cls_levels = []
    lines = []
    for name, data in classes.items():
        xp_data = class_xp_to_level(data['experience'])
        lines.append(
            f"{name}:\n"
            f"  level: {xp_data[0]}\n"
            f"  levelWithProgress: {xp_data[1]}"
        )
        cls_levels.append(xp_data[0])
    class_avg = sum(cls_levels) / len(cls_levels)
    lines.append(f"class avg: {class_avg:.2f}")
    format_string = '\n'.join(lines) + '\n'
    return cls_levels, format_string


def get_current_class_info(dungeon_data: dict) -> tuple[str, str]:
    current_class = dungeon_data['selected_dungeon_class']
    format_string = f"current class: {current_class}"
    return current_class, format_string


def get_run_stats_info(dungeon_data: dict) -> tuple[dict, str]:
    normal_runs = sum(v for k, v in dungeon_data['dungeon_types']['catacombs']['milestone_completions'].items() if k != 'total')
    master_runs = sum(v for k, v in dungeon_data['dungeon_types']['master_catacombs']['milestone_completions'].items() if k != 'total')
    total_runs = normal_runs + master_runs
    secrets = dungeon_data['secrets']
    secrets_per_run = secrets / total_runs if total_runs > 0 else 0
    stats = {
        'normal_runs': normal_runs,
        'master_runs': master_runs,
        'total_runs': total_runs,
        'secrets_per_run': secrets_per_run,
    }
    format_string = f"total runs: {total_runs}\nsecret/run: {secrets_per_run:.2f}"
    return stats, format_string

def get_magical_power() -> tuple[int, str]: 
    power = user_profile['accessory_bag_storage']['highest_magical_power']
    format_string = f"magical power: {power}"
    return power, format_string


def get_catacombs_level_info(dungeon_data: dict) -> tuple[tuple, str]:
    xp_data = class_xp_to_level(dungeon_data['dungeon_types']['catacombs']['experience'])
    format_string = "dungeon level(cata): " + str(xp_data)
    return xp_data, format_string

def display_armor(inv_armor_data: str) -> tuple[list, str]:
    data = decode_nbt_base64(inv_armor_data)

    format_string: str = '\n'.join(item['tag']['display']['Name'] for item in data)

    return data, format_string


def check_weapon(all_inventory: list[str]):
    to_check_dict = {
        item: False 
        for item in (
            'GYROKINETIC_WAND',
            'ICE_SPRAY_WAND',
            'DARK_CLAYMORE',
            "CUSTOM_WITHER_BLADE",
            "TERMINATOR"
        )
    }

    for string in all_inventory:
        data = decode_nbt_base64(string)

        for item in data:
            if 'tag' not in item:
                continue

            if item['tag']['ExtraAttributes']['id'] in to_check_dict:
                to_check_dict[item['tag']['ExtraAttributes']['id']] = True

            if 'ability_scroll' in item['tag']['ExtraAttributes']:
                to_check_dict['CUSTOM_WITHER_BLADE'] = True
        
    return to_check_dict

# pet
has_spirit, spirit_str = get_pet_missing_info(pets)
print(spirit_str)
print()

# secrets
secrets, secrets_str = get_secrets_info(dungeon_data)
print(secrets_str)
print()

# dungeon pb times
pb_data, pb_str = get_dungeon_pb_info(dungeon_data)
print(pb_str)
print()

# class levels
cls_levels, cls_str = get_class_levels_info(classes)
print(cls_str, end='')

# current class
current_class, cls_str = get_current_class_info(dungeon_data)
print(cls_str)
print()

# run stats
run_stats, stats_str = get_run_stats_info(dungeon_data)
print(stats_str)
print()

# magical power
magical_power, power_str = get_magical_power()
print(power_str)
print()

# catacombs level
cata_xp_data, cata_str = get_catacombs_level_info(dungeon_data)
print(cata_str)
print()

# inv armor
armor, armor_str = display_armor(inventory['inv_armor']['data'])
print(armor_str)

# weapon
weapon = check_weapon(
    [
        inventory['inv_contents']['data'], 
        inventory['ender_chest_contents']['data']
    ] + 
    [item['data'] for item in inventory['backpack_contents'].values()]
)
print(weapon)