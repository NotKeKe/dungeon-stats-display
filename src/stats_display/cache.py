import sqlite3
import time
from pathlib import Path


class Cache:
    CACHE_TTL = 180

    def __init__(self, db_path: Path):
        self._db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, data TEXT, timestamp REAL)"
        )
        con.commit()
        con.close()

    def get(self, key: str) -> str | None:
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute("SELECT data, timestamp FROM cache WHERE key = ?", (key,))
        row = cur.fetchone()
        con.close()
        if row and time.time() - row[1] < self.CACHE_TTL:
            return row[0]
        return None

    def clear(self):
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute("DELETE FROM cache")
        con.commit()
        con.close()

    def set(self, key: str, data: str):
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO cache (key, data, timestamp) VALUES (?, ?, ?)",
            (key, data, time.time()),
        )
        con.commit()
        con.close()
