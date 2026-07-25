import logging
import re
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.stats_display.cache import Cache


class DSDCategory(Enum):
    StatsDisplay = "StatsDisplay"
    Block = "Block"


def dsd_prefix(category: DSDCategory):
    return [
        {"text": "DSD", "color": "aqua"},
        {"text": f" ({category.value})", "color": "gray"},
        {"text": "> ", "color": "aqua"},
    ]


CHAT_PATTERN = re.compile(
    r"\[CHAT\].*?Party Finder > (\w+) joined the dungeon group! \((\w+) Level (\d+)\)"
)

DATA_DIR: Path | None = None
DB_PATH: Path | None = None
ENV_PATH: Path | None = None
LOG_PATH: Path | None = None
logger: logging.Logger | None = None
cache: "Cache | None" = None
