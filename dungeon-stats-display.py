import minescript

import requests
import json
from pathlib import Path
import base64
import gzip
import io
from nbt import nbt
import sqlite3

DATA_DIR = Path(__file__).parent / "dungeon-stats-display"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "dungeons.db"

def create_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("CREATE TABLE dungeons (name TEXT PRIMARY KEY, data BLOB)")
    con.commit()
    con.close()


def main():
    pass

if __name__ == "__main__":
    main()