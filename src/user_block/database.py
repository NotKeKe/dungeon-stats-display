import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class BlockDatabase:
    def __init__(self, db_path: Path):
        self._db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS blocked_users "
            "(uuid TEXT PRIMARY KEY, username TEXT, reason TEXT, added_at TEXT)"
        )
        con.commit()
        con.close()

    def add(self, uuid: str, username: str, reason: str = ""):
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO blocked_users (uuid, username, reason, added_at) "
            "VALUES (?, ?, ?, ?)",
            (uuid, username.lower(), reason, datetime.now(timezone.utc).isoformat()),
        )
        con.commit()
        con.close()

    def remove(self, uuid: str) -> bool:
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute("DELETE FROM blocked_users WHERE uuid = ?", (uuid,))
        removed = cur.rowcount > 0
        con.commit()
        con.close()
        return removed

    def is_blocked(self, uuid: str) -> bool:
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute("SELECT 1 FROM blocked_users WHERE uuid = ?", (uuid,))
        row = cur.fetchone()
        con.close()
        return row is not None

    def get_reason(self, uuid: str) -> str | None:
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute("SELECT reason FROM blocked_users WHERE uuid = ?", (uuid,))
        row = cur.fetchone()
        con.close()
        return row[0] if row else None

    def get_info(self, uuid: str) -> tuple[str, str] | None:
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT reason, added_at FROM blocked_users WHERE uuid = ?", (uuid,)
        )
        row = cur.fetchone()
        con.close()
        if row:
            return row[0], row[1]
        return None

    def get_all(self) -> list[tuple[str, str, str, str]]:
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT uuid, username, reason, added_at FROM blocked_users ORDER BY added_at"
        )
        rows = cur.fetchall()
        con.close()
        return rows
