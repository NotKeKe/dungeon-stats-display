import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import constants


def init_core(base_dir: Path):
    constants.DATA_DIR = base_dir / "dungeon-stats-display"
    constants.DATA_DIR.mkdir(exist_ok=True)
    constants.DB_PATH = constants.DATA_DIR / "dungeons.db"
    constants.ENV_PATH = constants.DATA_DIR / ".env"
    constants.CRASH_LOG_DIR = constants.DATA_DIR / "crash_logs"
    constants.CRASH_LOG_DIR.mkdir(exist_ok=True)
    constants.LOG_PATH = constants.DATA_DIR / "dsd.log"

    _log_handler = RotatingFileHandler(
        constants.LOG_PATH, maxBytes=100000, backupCount=0, encoding="utf-8"
    )
    _log_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    constants.logger = logging.getLogger("dsd")
    constants.logger.setLevel(logging.INFO)
    constants.logger.addHandler(_log_handler)
    constants.logger.propagate = False

    from src.stats_display.cache import Cache
    constants.cache = Cache(constants.DB_PATH)
    constants.cache.clear()
