import re
from collections.abc import Callable
from re import Match, Pattern

from .constants import CHAT_PATTERN, LEAP_PATTERN

_ChatHook = Callable[[str, Match[str]], None]
_ChatListener = Callable[[str], None]

_chat_hooks: dict[str, list[_ChatHook]] = {}
_chat_patterns: dict[str, Pattern[str]] = {
    "party_finder": CHAT_PATTERN,
    "leap": LEAP_PATTERN,
}
_command_routes: dict[str, Callable[[str], None]] = {}
_chat_listeners: list[_ChatListener] = []


def add_chat_hook(pattern_id: str, fn: _ChatHook):
    """註冊某個 pattern 的 hook；同一個 pattern 的 hook 會依註冊順序全部執行。"""
    _chat_hooks.setdefault(pattern_id, []).append(fn)


def add_chat_listener(fn: _ChatListener):
    """註冊會收到每一則訊息的 listener（不會影響 pattern hook 的分派）。"""
    _chat_listeners.append(fn)


def register_command(prefix: str, fn: Callable[[str], None]):
    _command_routes[prefix] = fn


def dispatch_chat(message: str):
    clean = re.sub(r"\u00a7.", "", message)
    for pattern_id, pattern in _chat_patterns.items():
        match = pattern.search(clean)
        if match:
            # 只有第一個命中的 pattern 會執行 hook，後面的 pattern 不再比對
            for fn in _chat_hooks.get(pattern_id, []):
                fn(clean, match)
            break

    for fn in _chat_listeners:
        fn(clean)


def dispatch_command(message: str):
    for prefix, fn in _command_routes.items():
        if message.startswith(prefix):
            fn(message)
            return
