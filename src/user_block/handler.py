import minescript
from datetime import datetime

from src.core import constants as core_const
from src.core.api import get_uuid
from .constants import DEFAULT_KICK_REASON
from .database import BlockDatabase


def _get_db():
    db_path = core_const.DB_PATH
    assert db_path is not None
    return BlockDatabase(db_path)


def on_chat(clean_text: str, match) -> bool:
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

    minescript.execute(f"/pc {kick_reason}")
    minescript.execute(f"/party kick {username}")
    return True


def on_command(message: str):
    parts = message.split()
    if len(parts) < 3:
        minescript.echo("DSD Block: use !dsd block add/remove/list")
        return

    sub = parts[2].lower()

    if sub == "list":
        db = _get_db()
        rows = db.get_all()
        if not rows:
            minescript.echo("DSD Block: No blocked users.")
            return
        minescript.echo("DSD Block: Blocked users:")
        for uuid, username, reason, added_at in rows:
            rsn = reason or DEFAULT_KICK_REASON
            minescript.echo(f"  - {username} ({uuid}) [{rsn}] {added_at}")
        return

    if sub not in ("add", "remove"):
        minescript.echo(f"DSD Block: unknown subcommand '{sub}'")
        return

    if len(parts) < 4:
        minescript.echo(f"DSD Block: !dsd block {sub} <username> [reason]")
        return

    username = parts[3]
    reason = " ".join(parts[4:]) if len(parts) > 4 else ""

    uuid = get_uuid(username)
    if uuid is None:
        minescript.echo(f"DSD Block: Cannot find user '{username}'")
        return

    if sub == "add":
        db = _get_db()
        db.add(uuid, username, reason)
        minescript.echo(f"DSD Block: Added '{username}' ({uuid}) to block list.")
    elif sub == "remove":
        db = _get_db()
        if db.remove(uuid):
            minescript.echo(f"DSD Block: Removed '{username}' ({uuid}) from block list.")
        else:
            minescript.echo(f"DSD Block: '{username}' was not in block list.")
