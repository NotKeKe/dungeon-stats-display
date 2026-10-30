import re
import threading
from collections.abc import Callable
from re import Match, Pattern

from . import constants
from .constants import CHAT_PATTERN, LEAP_PATTERN

_HookErrorHandler = Callable[[str, BaseException], None]
_ChatHook = Callable[[str, Match[str]], None]
_ChatListener = Callable[[str], None]

_chat_hooks: dict[str, list[_ChatHook]] = {}
_chat_patterns: dict[str, Pattern[str]] = {
    "party_finder": CHAT_PATTERN,
    "leap": LEAP_PATTERN,
}
_command_routes: dict[str, Callable[[str], None]] = {}
_chat_listeners: list[_ChatListener] = []
_hook_error_handler: _HookErrorHandler | None = None


def add_chat_hook(pattern_id: str, fn: _ChatHook):
    """註冊某個 pattern 的 hook；命中時每個 hook 會各自在背景 thread 執行。"""
    _chat_hooks.setdefault(pattern_id, []).append(fn)


def add_chat_listener(fn: _ChatListener):
    """註冊會收到每一則訊息的 listener；每個 listener 也在背景 thread 執行。"""
    _chat_listeners.append(fn)


def set_hook_error_handler(fn: _HookErrorHandler):
    """設定 hook／listener 在背景 thread 拋出例外時的處理函式（main.py 用它寫 crash log）。"""
    global _hook_error_handler
    _hook_error_handler = fn


def register_command(prefix: str, fn: Callable[[str], None]):
    _command_routes[prefix] = fn


def _handle_error(fn: Callable[..., None], e: Exception):
    handler = _hook_error_handler
    if handler is not None:
        handler(getattr(fn, "__name__", repr(fn)), e)
        return
    logger = constants.logger
    if logger is not None:
        logger.exception("Unhandled error in chat handler %s", getattr(fn, "__name__", repr(fn)))
        return
    raise e


def _run_hook(fn: _ChatHook, clean: str, match: Match[str]):
    try:
        fn(clean, match)
    except Exception as e:
        _handle_error(fn, e)


def _run_listener(fn: _ChatListener, clean: str):
    try:
        fn(clean)
    except Exception as e:
        _handle_error(fn, e)


def dispatch_chat(message: str):
    clean = re.sub(r"\u00a7.", "", message)
    for pattern_id, pattern in _chat_patterns.items():
        match = pattern.search(clean)
        if match:
            # 只有第一個命中的 pattern 會執行 hook；每個 hook 各自開一條 daemon
            # thread 執行，dispatch_chat 不會等待它們完成。
            for fn in _chat_hooks.get(pattern_id, []):
                threading.Thread(
                    target=_run_hook,
                    args=(fn, clean, match),
                    name=f"chat-hook:{getattr(fn, '__name__', 'anonymous')}",
                    daemon=True,
                ).start()
            break

    for fn in _chat_listeners:
        threading.Thread(
            target=_run_listener,
            args=(fn, clean),
            name=f"chat-listener:{getattr(fn, '__name__', 'anonymous')}",
            daemon=True,
        ).start()


def dispatch_command(message: str):
    for prefix, fn in _command_routes.items():
        if message.startswith(prefix):
            fn(message)
            return
