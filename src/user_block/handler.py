from datetime import datetime
from re import Match

import minescript

from src.core import constants as core_const
from src.core.api import get_uuid
from src.core.constants import DSDCategory, dsd_prefix

from .constants import DEFAULT_KICK_REASON
from .database import BlockDatabase


def _get_db() -> BlockDatabase:
    db_path = core_const.DB_PATH
    assert db_path is not None
    return BlockDatabase(db_path)


def on_chat(clean_text: str, match: Match[str]) -> bool:
    username = match.group(1)

    player = minescript.player()
    if player and username.lower() == player.name.lower():
        return False

    uuid = get_uuid(username)
    if uuid is None:
        return False

    db = _get_db()
    if not db.is_blocked(uuid):
        return False

    info = db.get_info(uuid)
    if info is None:
        return False

    db_reason, added_at = info
    dt = datetime.fromisoformat(added_at)
    time_str = dt.strftime("%Y-%m-%d %H:%M %Z%z")
    base_reason = db_reason or DEFAULT_KICK_REASON
    kick_reason = f"{base_reason} (added at {time_str})"

    minescript.execute(f"/pc Kicking {username}, reason: \"{kick_reason}\"")
    minescript.execute(f"/party kick {username}")
    return True


def on_command(message: str):
    parts = message.split()
    if len(parts) < 3:
        minescript.echo_json(dsd_prefix(DSDCategory.Block) + [
            {"text": "use !dsd block add/remove/list", "color": "white"}
        ])
        return

    sub = parts[2].lower()

    if sub == "list":
        db = _get_db()
        rows = db.get_all()
        if not rows:
            minescript.echo_json(dsd_prefix(DSDCategory.Block) + [
                {"text": "No blocked users.", "color": "white"}
            ])
            return
        minescript.echo_json(dsd_prefix(DSDCategory.Block) + [
            {"text": "Blocked users:", "color": "white"}
        ])
        for uuid, username, reason, added_at in rows:
            dt = datetime.fromisoformat(added_at)
            time_str = dt.strftime("%Y-%m-%d %H:%M %Z%z")
            rsn = reason or "None"
            minescript.echo_json([
                {"text": " * "},
                {"text": username, "color": "yellow"},
                {"text": " - ", "color": "white"},
                {"text": rsn, "color": "white"},
                {"text": f" (added at {time_str})", "color": "gray"},
            ])
        return

    if sub not in ("add", "remove"):
        minescript.echo_json(dsd_prefix(DSDCategory.Block) + [
            {"text": f"unknown subcommand '{sub}'", "color": "white"}
        ])
        return

    if len(parts) < 4:
        minescript.echo_json(dsd_prefix(DSDCategory.Block) + [
            {"text": f"!dsd block {sub} <username> [reason]", "color": "white"}
        ])
        return

    username = parts[3]
    reason = " ".join(parts[4:]) if len(parts) > 4 else ""

    uuid = get_uuid(username)
    if uuid is None:
        minescript.echo_json(dsd_prefix(DSDCategory.Block) + [
            {"text": f"Cannot find user '{username}'", "color": "white"}
        ])
        return

    if sub == "add":
        db = _get_db()
        db.add(uuid, username, reason)
        minescript.echo_json(dsd_prefix(DSDCategory.Block) + [
            {"text": f"Added '{username}' ({uuid}) to block list.", "color": "white"}
        ])
    elif sub == "remove":
        db = _get_db()
        if db.remove(uuid):
            minescript.echo_json(dsd_prefix(DSDCategory.Block) + [
                {"text": f"Removed '{username}' ({uuid}) from block list.", "color": "white"}
            ])
        else:
            minescript.echo_json(dsd_prefix(DSDCategory.Block) + [
                {"text": f"'{username}' was not in block list.", "color": "white"}
            ])
