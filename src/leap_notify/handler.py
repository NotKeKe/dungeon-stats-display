from re import Match

import minescript


def on_chat(clean_text: str, match: Match[str]) -> bool:
    username = match.group(1)

    player = minescript.player()
    if player and username.lower() == player.name.lower():
        return False

    minescript.execute(f"/pc Leaped to {username}")
    return False
