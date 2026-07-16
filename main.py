import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import minescript

from dungeon_stats_display.app import setup
from dungeon_stats_display.handler import handle_chat_message, handle_dsd_command
from dungeon_stats_display.constants import logger

BASE_DIR = Path(__file__).parent
MC_LOG_PATH = BASE_DIR.parent / "logs" / "latest.log"

setup(BASE_DIR)


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
                            handle_chat_message(line)
                    last_size = current_size

    def event_loop():
        with minescript.EventQueue() as event_queue:
            event_queue.register_outgoing_chat_interceptor(prefix="!dsd")
            while True:
                event = event_queue.get()
                try:
                    if event.type == minescript.EventType.OUTGOING_CHAT_INTERCEPT:
                        handle_dsd_command(event.message)
                except Exception as e:
                    logger.exception("Event loop error")
                    minescript.echo(f"DSD: Error: {e}")

    log_thread = threading.Thread(target=log_loop, daemon=True)
    log_thread.start()

    try:
        event_loop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
