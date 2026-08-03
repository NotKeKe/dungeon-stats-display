import sqlite3
from pathlib import Path

from src.core import constants as core_const

DEFAULT_TEMPLATE = "Leaped to {name}"


def _get_db_path() -> Path:
    db_path = core_const.DB_PATH
    assert db_path is not None
    return db_path


def _init_db():
    con = sqlite3.connect(str(_get_db_path()))
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS leap_settings "
        "(key TEXT PRIMARY KEY, value TEXT)"
    )
    con.commit()
    con.close()


def load_template() -> str:
    _init_db()
    con = sqlite3.connect(str(_get_db_path()))
    cur = con.cursor()
    cur.execute("SELECT value FROM leap_settings WHERE key = 'template'")
    row = cur.fetchone()
    con.close()
    return row[0] if row else DEFAULT_TEMPLATE


def save_template(template: str):
    _init_db()
    con = sqlite3.connect(str(_get_db_path()))
    cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO leap_settings (key, value) VALUES (?, ?)",
        ("template", template),
    )
    con.commit()
    con.close()
