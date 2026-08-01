import threading
import time
from pathlib import Path

import minescript

from src.core.dispatcher import (
    add_chat_hook,
    dispatch_chat,
    dispatch_command,
    register_command,
)
from src.core.setup import init_core

BASE_DIR = Path(__file__).parent
MC_LOG_PATH = BASE_DIR.parent / "logs" / "latest.log"

init_core(BASE_DIR)

from src.core import constants as core_const
from src.core.constants import DSDCategory, dsd_prefix
from src.stats_display.handler import on_chat as stats_on_chat
from src.stats_display.handler import on_key_command
from src.stats_display.handler import on_search_command
from src.user_block.handler import on_chat as block_on_chat
from src.user_block.handler import on_command as block_on_command


def _on_help(message: str):
    minescript.echo_json(dsd_prefix() + [
        {"text": "Commands:", "color": "white"}
    ])
    minescript.echo_json([
        {"text": "  !dsd key", "color": "white"},
        {"text": "  - Preview stored API key", "color": "gray"},
    ])
    minescript.echo_json([
        {"text": "  !dsd key <api_key>", "color": "white"},
        {"text": "  - Set Hypixel API key", "color": "gray"},
    ])
    minescript.echo_json([
        {"text": "  !dsd search <username>", "color": "white"},
        {"text": "  - Search and display player stats", "color": "gray"},
    ])
    minescript.echo_json([
        {"text": "  !dsd block", "color": "white"},
        {"text": "  - Block list management", "color": "gray"},
    ])


def _on_bare(message: str):
    minescript.echo_json(dsd_prefix() + [
        {"text": "Use ", "color": "white"},
        {"text": "!dsd help", "color": "white", "bold": True},
        {"text": " to see available commands.", "color": "white"},
    ])


add_chat_hook(block_on_chat)
add_chat_hook(stats_on_chat)
register_command("!dsd key", on_key_command)
register_command("!dsd block", block_on_command)
register_command("!dsd search", on_search_command)
register_command("!dsd help", _on_help)
register_command("!dsd", _on_bare)


def main():
    def log_loop():
        with open(MC_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)
            last_size = MC_LOG_PATH.stat().st_size

            while True:
                time.sleep(0.2)
                try:
                    current_size = MC_LOG_PATH.stat().st_size
                except OSError:
                    continue

                if current_size < last_size:
                    f.seek(0)
                    last_size = current_size
                    continue

                if current_size > last_size:
                    for line in f:
                        line = line.rstrip("\n\r")
                        if line:
                            dispatch_chat(line)
                    last_size = current_size

    def event_loop():
        with minescript.EventQueue() as event_queue:
            event_queue.register_outgoing_chat_interceptor(prefix="!dsd")
            while True:
                event = event_queue.get()
                try:
                    if event.type == minescript.EventType.OUTGOING_CHAT_INTERCEPT:
                        dispatch_command(event.message)
                except Exception as e:
                    _log = core_const.logger
                    assert _log is not None
                    _log.exception("Event loop error")
                    minescript.echo_json(dsd_prefix(DSDCategory.StatsDisplay) + [
                        {"text": f"Error: {e}", "color": "white"}
                    ])

    log_thread = threading.Thread(target=log_loop, daemon=True)
    log_thread.start()

    try:
        event_loop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
