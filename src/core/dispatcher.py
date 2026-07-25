import re
from collections.abc import Callable
from re import Match

from .constants import CHAT_PATTERN

_ChatHook = Callable[[str, Match[str] | None], bool]

_chat_hooks: list[_ChatHook] = []
_command_routes: dict[str, Callable[[str], None]] = {}


def add_chat_hook(fn: _ChatHook):
    _chat_hooks.append(fn)


def register_command(prefix: str, fn: Callable[[str], None]):
    _command_routes[prefix] = fn


def dispatch_chat(message: str):
    clean = re.sub(r"\u00a7.", "", message)
    match = CHAT_PATTERN.search(clean)
    if not match:
        return
    for fn in _chat_hooks:
        if fn(clean, match):
            break


def dispatch_command(message: str):
    for prefix, fn in _command_routes.items():
        if message.startswith(prefix):
            fn(message)
            return
