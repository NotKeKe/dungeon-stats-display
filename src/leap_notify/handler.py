from re import Match

import minescript

from src.core.constants import dsd_prefix

from .database import load_template, save_template


def on_chat(clean_text: str, match: Match[str]) -> bool:
    username = match.group(1)

    player = minescript.player()
    if player and username.lower() == player.name.lower():
        return False

    template = load_template()
    minescript.execute(f"/pc {template.format(name=username)}")
    return False


def on_command(message: str):
    parts = message.split(maxsplit=2)
    if len(parts) < 3:
        template = load_template()
        minescript.echo_json(dsd_prefix() + [
            {"text": "Current template: ", "color": "white"},
            {"text": template, "color": "yellow"},
        ])
        minescript.echo_json(dsd_prefix() + [
            {"text": "Usage: !dsd leap <message> (ex. !dsd leap ", "color": "gray"},
            {"text": "Hello {name}", "color": "yellow"},
            {"text": ")", "color": "gray"},
        ])
        return

    template = parts[2].strip()
    if "{name}" not in template:
        minescript.echo_json(dsd_prefix() + [
            {"text": "Template must include ", "color": "red"},
            {"text": "{name}", "color": "yellow", "bold": True},
            {"text": " placeholder.", "color": "red"},
        ])
        return

    save_template(template)
    minescript.echo_json(dsd_prefix() + [
        {"text": "Template set to: ", "color": "white"},
        {"text": template, "color": "yellow"},
    ])
