import re
from collections.abc import Callable
from re import Match, Pattern

from .constants import CHAT_PATTERN, LEAP_PATTERN

_ChatHook = Callable[[str, Match[str]], bool]

_chat_hooks: dict[str, list[_ChatHook]] = {}
_chat_patterns: dict[str, Pattern[str]] = {
    "party_finder": CHAT_PATTERN,
    "leap": LEAP_PATTERN,
}
_command_routes: dict[str, Callable[[str], None]] = {}


def add_chat_hook(pattern_id: str, fn: _ChatHook):
    _chat_hooks.setdefault(pattern_id, []).append(fn)


def register_command(prefix: str, fn: Callable[[str], None]):
    _command_routes[prefix] = fn


def dispatch_chat(message: str):
    clean = re.sub(r"\u00a7.", "", message)
    for pattern_id, pattern in _chat_patterns.items():
        match = pattern.search(clean)
        if match:
            for fn in _chat_hooks.get(pattern_id, []):
                if fn(clean, match):
                    break
            break


def dispatch_command(message: str):
    for prefix, fn in _command_routes.items():
        if message.startswith(prefix):
            fn(message)
            return
