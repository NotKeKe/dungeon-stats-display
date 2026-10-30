import re
import time

import minescript

from src.core import constants as core_const
from src.core.constants import DSDCategory, dsd_prefix

from .database import (
    AutoFillRule,
    delete_rule,
    load_rules,
    save_rule,
    set_rule_enabled,
)

_rules: list[AutoFillRule] | None = None


def _log():
    logger = core_const.logger
    assert logger is not None
    return logger


def get_rules() -> list[AutoFillRule]:
    global _rules
    if _rules is None:
        _rules = load_rules()
    return _rules


def _reload_rules() -> list[AutoFillRule]:
    global _rules
    _rules = load_rules()
    return _rules


def _echo_lines(lines: list[tuple[str, str]]):
    """把多行內容合成單一則訊息：只有開頭一個 prefix，之後直接換行。"""
    pieces: list[dict] = list(dsd_prefix(DSDCategory.AutoFill))
    for i, (text, color) in enumerate(lines):
        if i > 0:
            pieces.append({"text": "\n"})
        pieces.append({"text": text, "color": color})
    minescript.echo_json(pieces)


def _echo(text: str, color: str = "white"):
    _echo_lines([(text, color)])


_ITEM_NAME_TRANSLATE_RE = re.compile(
    r'minecraft:(?:item_name|custom_name)"?\s*:\s*\{[^{}]*?"?translate"?\s*:\s*"([^"]+)"'
)
_CUSTOM_DATA_START_RE = re.compile(r'minecraft:custom_data"?\s*:\s*\{')
_CUSTOM_DATA_ID_RE = re.compile(r'(?:\{|,)\s*"?id"?\s*:\s*"([^"]+)"')
_EXTRA_ATTRIBUTES_ID_RE = re.compile(
    r'ExtraAttributes"?\s*:\s*\{[^{}]*?\bid"?\s*:\s*"([^"]+)"'
)
_SKYBLOCK_UPPER_RE = re.compile(r"skyblock:([A-Z][A-Z0-9_]*)")


def _extract_compound(text: str, start: int) -> str:
    """回傳 text[start]（'{'）開始、配對到的 compound 字串。"""
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:]


def _add_skyblock_id(found: list[str], value: str):
    value = value.strip()
    if value.startswith("skyblock:"):
        value = value[len("skyblock:"):]
    value = value.upper()
    if value and value not in found:
        found.append(value)


def extract_skyblock_ids(nbt: str) -> list[str]:
    """從 ItemStack 的 SNBT 取出 Skyblock item id。"""
    found: list[str] = []

    # custom_data.id（用大括號配對整段 compound，id 可能在 nested compound 後面）
    for match in _CUSTOM_DATA_START_RE.finditer(nbt):
        compound = _extract_compound(nbt, match.end() - 1)
        for id_match in _CUSTOM_DATA_ID_RE.finditer(compound):
            _add_skyblock_id(found, id_match.group(1))

    # item_name / custom_name 的 translate key
    for match in _ITEM_NAME_TRANSLATE_RE.finditer(nbt):
        if match.group(1).startswith("skyblock:"):
            _add_skyblock_id(found, match.group(1))

    # 舊版 ExtraAttributes.id
    for match in _EXTRA_ATTRIBUTES_ID_RE.finditer(nbt):
        _add_skyblock_id(found, match.group(1))

    # fallback：有些物品的 id 只出現在名稱字串裡；小寫的 skyblock:item／skyblock:mythic 之類是雜訊
    for match in _SKYBLOCK_UPPER_RE.finditer(nbt):
        _add_skyblock_id(found, match.group(1))

    return found


def _vanilla_item_id(item_id: str) -> str:
    """把 Skyblock item id（如 ENDER_PEARL）轉成原版 registry id（minecraft:ender_pearl）。"""
    normalized = item_id.strip().lower()
    if ":" in normalized:
        return normalized
    return f"minecraft:{normalized}"


def _matches_item(stack, item_id: str) -> bool:
    """優先用 NBT 裡的 Skyblock id 比對，NBT 沒有可辨識的 id 時才 fallback 到原版 registry id。"""
    skyblock_ids = extract_skyblock_ids(stack.nbt or "")
    if skyblock_ids:
        return item_id.upper() in skyblock_ids
    target = _vanilla_item_id(item_id)
    return bool(stack.item) and stack.item.lower() == target


def count_inventory_item(item_id: str) -> int:
    """回傳原版背包（hotbar + 主背包）中指定 item 的總數量。"""
    total = 0
    for stack in minescript.player_inventory():
        if _matches_item(stack, item_id):
            total += stack.count
    return total


def _normalize_item_id(item_id: str) -> str:
    return item_id.strip().upper()


def _get_rule_by_number(raw: str) -> AutoFillRule | None:
    try:
        index = int(raw.strip())
    except ValueError:
        return None
    rules = get_rules()
    if 1 <= index <= len(rules):
        return rules[index - 1]
    return None


def _help_lines() -> list[tuple[str, str]]:
    return [
        ("AutoFill help:", "white"),
        ("  !dsd autofill <item_id> <target_count> <trigger>", "white"),
        ("  - Add or update a rule", "gray"),
        ("  !dsd autofill list", "white"),
        ("  - Show all rules (numbered)", "gray"),
        ("  !dsd autofill pause|resume <rule_id>", "white"),
        ("  - Pause or resume a rule", "gray"),
        ("  !dsd autofill remove|rm <rule_id>", "white"),
        ("  - Delete a rule", "gray"),
        ("Run !dsd autofill list to see the current rules.", "white"),
    ]


def _echo_help():
    _echo_lines(_help_lines())


def _echo_rules(rules: list[AutoFillRule]):
    if not rules:
        _echo_lines([
            ("AutoFill: no rules set.", "white"),
            ("Add one with !dsd autofill <item_id> <target_count> <trigger>", "gray"),
        ])
        return

    lines: list[tuple[str, str]] = [(f"AutoFill rules ({len(rules)}):", "white")]
    for i, rule in enumerate(rules, start=1):
        if i > 1:
            lines.append(("", "white"))
        status = "enabled" if rule.enabled else "paused"
        lines.append((
            f"  id: {i}\n"
            f"  item: {rule.item_id}\n"
            f"  count: {rule.target_count}\n"
            f'  trigger: "{rule.trigger}"\n'
            f"  status: {status}",
            "gray",
        ))
    _echo_lines(lines)


def _chat_content(clean_text: str) -> str | None:
    """從 log 行取出 `[CHAT]` 後面的聊天內容；不是聊天行時回傳 None。"""
    marker = "[CHAT]"
    index = clean_text.find(marker)
    if index == -1:
        return None
    return clean_text[index + len(marker):].strip()


def on_chat(clean_text: str):
    content = _chat_content(clean_text)
    if content is None:
        return

    for rule in get_rules():
        if not rule.enabled:
            continue
        if rule.trigger != content:
            continue

        try:
            current = count_inventory_item(rule.item_id)
        except Exception:
            _log().exception("auto_fill: failed to read player inventory")
            continue

        if current >= rule.target_count:
            continue

        need = rule.target_count - current
        minescript.execute(f"/gfs {rule.item_id} {need}")
        _echo(
            f"{rule.item_id}: {current}/{rule.target_count}, "
            f"gfs {rule.item_id} {need}"
        )

        time.sleep(0.1) # 避免訊息之間間隔太短


def on_command(message: str):
    parts = message.split(maxsplit=4)

    if len(parts) == 2:
        _echo_help()
        return

    sub = parts[2].strip().lower()

    if sub == "list":
        _echo_rules(get_rules())
        return

    if sub in ("pause", "resume"):
        if len(parts) < 4:
            _echo(f"!dsd autofill {sub} <rule_id>")
            return
        rule = _get_rule_by_number(parts[3])
        if rule is None:
            _echo(f"Invalid rule number: {parts[3].strip()}", "red")
            return
        enabled = sub == "resume"
        set_rule_enabled(rule.item_id, enabled)
        _reload_rules()
        state = "resumed" if enabled else "paused"
        _echo(f"Rule #{parts[3].strip()} ({rule.item_id}) {state}.")
        return

    if sub in ("remove", "rm", "delete", "del"):
        if len(parts) < 4:
            _echo(f"!dsd autofill {sub} <rule_id>")
            return
        rule = _get_rule_by_number(parts[3])
        if rule is None:
            _echo(f"Invalid rule number: {parts[3].strip()}", "red")
            return
        delete_rule(rule.item_id)
        _reload_rules()
        _echo(f"Removed rule #{parts[3].strip()} ({rule.item_id}).")
        return

    if len(parts) < 5:
        _echo("!dsd autofill <item_id> <target_count> <trigger>")
        return

    item_id = _normalize_item_id(parts[2])
    try:
        target_count = int(parts[3])
    except ValueError:
        _echo("target_count must be an integer.", "red")
        return
    if target_count <= 0:
        _echo("target_count must be greater than 0.", "red")
        return

    trigger = parts[4].strip()
    if not trigger:
        _echo("trigger cannot be empty.", "red")
        return

    save_rule(AutoFillRule(
        item_id=item_id,
        target_count=target_count,
        trigger=trigger,
    ))
    rules = _reload_rules()
    number = next(
        (i for i, rule in enumerate(rules, start=1) if rule.item_id == item_id),
        None,
    )
    _echo_lines([
        ("AutoFill set:", "white"),
        (f"  id: {number if number is not None else '?'}", "gray"),
        (f"  item: {item_id}", "gray"),
        (f"  count: {target_count}", "gray"),
        (f'  trigger: "{trigger}"', "gray"),
    ])
